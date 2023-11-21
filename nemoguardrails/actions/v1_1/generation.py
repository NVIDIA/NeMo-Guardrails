# SPDX-FileCopyrightText: Copyright (c) 2023 NVIDIA CORPORATION & AFFILIATES. All rights reserved.
# SPDX-License-Identifier: Apache-2.0
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
# http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""A set of actions for generating various types of completions using an LLMs."""
import logging
from ast import literal_eval
from typing import Any, List, Optional

from langchain.llms import BaseLLM

from nemoguardrails.actions.actions import action
from nemoguardrails.actions.llm.generation import LLMGenerationActions
from nemoguardrails.actions.llm.utils import (
    get_first_nonempty_line,
    get_last_user_utterance_event_v1_1,
    llm_call,
    remove_action_intent_identifiers,
)
from nemoguardrails.colang.v1_1.lang.utils import new_uuid
from nemoguardrails.colang.v1_1.runtime.flows import ActionEvent, InternalEvent
from nemoguardrails.colang.v1_1.runtime.statemachine import (
    Event,
    InternalEvents,
    State,
    find_all_active_event_matchers,
    get_element_from_head,
    get_event_from_element,
)
from nemoguardrails.embeddings.index import EmbeddingsIndex, IndexItem
from nemoguardrails.llm.filters import colang
from nemoguardrails.llm.params import llm_params
from nemoguardrails.llm.types import Task

log = logging.getLogger(__name__)


def _remove_leading_empty_lines(s: str):
    """Remove the leading empty lines if they exist.

    A line is considered empty if it has only white spaces.
    """
    lines = s.split("\n")
    while lines and lines[0].strip() == "":
        lines = lines[1:]
    return "\n".join(lines)


class LLMGenerationActionsV1dot1(LLMGenerationActions):
    """Adapted version of LLMGenerationActions for Colang 1.1.

    It overrides some methods.
    """

    async def _init_colang_flows_index(
        self, flows: List[str]
    ) -> Optional[EmbeddingsIndex]:
        """Initialize an index with colang flows.

        The flows are expected to have full definition.

        Args
            flows: The list of flows, i.e. the flow definition from the source code.

        Returns
            An initialized index.
        """
        items = []
        for source_code in flows:
            items.append(IndexItem(text=source_code, meta={"flow": source_code}))

        # If we have no patterns, we stop.
        if len(items) == 0:
            return None

        flows_index = self.get_embedding_search_provider_instance(
            self.config.core.embedding_search_provider
        )
        await flows_index.add_items(items)
        await flows_index.build()

        return flows_index

    async def _init_flows_index(self):
        """Initializes the index of flows."""

        if not self.config.flows:
            return

        # The list of all flows that will be added to the index
        all_flows = []

        # The list of flows that have instructions, i.e. docstring at the beginning.
        instruction_flows = []

        for flow in self.config.flows:
            colang_flow = flow.get("source_code")

            # Check if we need to exclude this flow.
            if "# meta: exclude from llm" in colang_flow:
                continue

            all_flows.append(colang_flow)

            # If the first line is a comment, we consider it to be an instruction
            lines = colang_flow.split("\n")
            if len(lines) > 1:
                first_line = lines[1].strip()
                if first_line.startswith("#") or first_line.startswith('"""'):
                    instruction_flows.append(colang_flow)

        self.flows_index = await self._init_colang_flows_index(all_flows)
        self.instruction_flows_index = await self._init_colang_flows_index(
            instruction_flows
        )

    @action(name="GetLastUserMessageAction", is_system_action=True)
    async def get_last_user_message(
        self, events: List[dict], llm: Optional[BaseLLM] = None
    ):
        event = get_last_user_utterance_event_v1_1(events)
        assert event["type"] == "UtteranceUserActionFinished"
        return event["final_transcript"]

    @action(name="GenerateUserIntentAction", is_system_action=True, execute_async=True)
    async def generate_user_intent(
        self,
        state: State,
        events: List[dict],
        user_action: str,
        max_example_flows: int = 5,
        llm: Optional[BaseLLM] = None,
    ):
        """Generate the canonical form for what the user said i.e. user intent."""

        # Use action specific llm if registered else fallback to main llm
        llm = llm or self.llm

        log.info("Phase 1: Generating user intent")

        # We search for the most relevant similar user intents
        examples = ""
        potential_user_intents = []

        if self.user_message_index:
            results = await self.user_message_index.search(
                text=user_action, max_results=max_example_flows
            )

            # We add these in reverse order so the most relevant is towards the end.
            for result in reversed(results):
                examples += f"user action: user said \"{result.text}\"\nuser intent: {result.meta['intent']}\n\n"
                potential_user_intents.append(result.meta["intent"])

        # We add all currently active user intents (heads on match statements)
        heads = find_all_active_event_matchers(state)
        for head in heads:
            element = get_element_from_head(state, head)
            event = get_event_from_element(
                state, state.flow_states[head.flow_state_uid], element
            )
            if (
                event.name == InternalEvents.FLOW_FINISHED
                and "flow_id" in event.arguments
            ):
                flow_id = event.arguments["flow_id"]
                flow_config = state.flow_configs.get(flow_id, None)
                if flow_config is None or (
                    "# meta: user intent" in flow_config.source_code
                    and flow_id not in potential_user_intents
                ):
                    examples += f"user intent: {flow_id}\n\n"
                    potential_user_intents.append(flow_id)

        prompt = self.llm_task_manager.render_task_prompt(
            task=Task.GENERATE_USER_INTENT,
            events=events,
            context={
                "examples": examples,
                "potential_user_intents": ", ".join(potential_user_intents),
                "user_action": user_action,
            },
        )

        # We make this call with temperature 0 to have it as deterministic as possible.
        with llm_params(llm, temperature=self.config.lowest_temperature):
            result = await llm_call(llm, prompt)

        # Parse the output using the associated parser
        result = self.llm_task_manager.parse_task_output(
            Task.GENERATE_USER_INTENT, output=result
        )

        user_intent = get_first_nonempty_line(result)
        if user_intent is None:
            user_intent = "unknown message"

        if user_intent and user_intent.startswith("user intent: "):
            user_intent = user_intent[13:]

        log.info(
            "Canonical form for user intent: "
            + (user_intent if user_intent else "None")
        )

        return f"{user_intent}" or "user unknown intent"

    @action(name="CheckValidFlowExistsAction", is_system_action=True)
    async def check_if_flow_exists(self, state: "State", flow_id: str):
        return flow_id in state.flow_id_states

    @action(name="CheckForActiveEventMatchAction", is_system_action=True)
    async def check_for_active_flow_finished_match(
        self, state: "State", name: str, **arguments: Any
    ):
        event: Event
        if name in InternalEvents.ALL:
            event = InternalEvent(name=name, arguments=arguments)
        elif "Action" in name:
            event = ActionEvent(name=name, arguments=arguments)
        else:
            event = Event(name=name, arguments=arguments)
        heads = find_all_active_event_matchers(state, event)
        return len(heads) > 0

    @action(
        name="GenerateFlowFromInstructionsAction",
        is_system_action=True,
        execute_async=True,
    )
    async def generate_flow_from_instructions(
        self,
        instructions: str,
        events: List[dict],
        llm: Optional[BaseLLM] = None,
    ):
        """Generate a flow from the provided instructions."""

        if self.instruction_flows_index is None:
            raise RuntimeError("No instruction flows index has been created.")

        # Use action specific llm if registered else fallback to main llm
        llm = llm or self.llm

        log.info(f"Generating flow for instructions: {instructions}")

        results = await self.instruction_flows_index.search(
            text=instructions, max_results=5
        )

        examples = ""
        for result in reversed(results):
            examples += f"{result.meta['flow']}\n"

        flow_id = new_uuid()[0:4]
        flow_name = f"dynamic_{flow_id}"

        prompt = self.llm_task_manager.render_task_prompt(
            task=Task.GENERATE_FLOW_FROM_INSTRUCTIONS,
            events=events,
            context={
                "examples": examples,
                "flow_name": flow_name,
                "instructions": instructions,
            },
        )

        # We make this call with temperature 0 to have it as deterministic as possible.
        with llm_params(llm, temperature=self.config.lowest_temperature):
            result = await llm_call(llm, prompt)

        lines = _remove_leading_empty_lines(result).split("\n")

        if lines[0].startswith("  "):
            # print(f"Generated flow:\n{result}\n")
            return {
                "name": flow_name,
                "body": f"flow {flow_name}\n" + "\n".join(lines),
            }
        else:
            return {
                "name": "bot inform LLM issue",
                "body": 'flow bot inform LLM issue\n  bot say "Sorry! There was an issue in the LLM result form GenerateFlowFromInstructionsAction!"',
            }

    @action(
        name="GenerateFlowFromNameAction", is_system_action=True, execute_async=True
    )
    async def generate_flow_from_name(
        self,
        name: str,
        events: List[dict],
        llm: Optional[BaseLLM] = None,
    ):
        """Generate a flow from the provided NAME."""

        if self.flows_index is None:
            raise RuntimeError("No flows index has been created.")

        # Use action specific llm if registered else fallback to main llm
        llm = llm or self.llm

        log.info(f"Generating flow for name: {name}")

        results = await self.instruction_flows_index.search(
            text=f"flow {name}", max_results=5
        )

        examples = ""
        for result in reversed(results):
            examples += f"{result.meta['flow']}\n"

        prompt = self.llm_task_manager.render_task_prompt(
            task=Task.GENERATE_FLOW_FROM_NAME,
            events=events,
            context={
                "examples": examples,
                "flow_name": name,
            },
        )

        # We make this call with temperature 0 to have it as deterministic as possible.
        with llm_params(llm, temperature=self.config.lowest_temperature):
            result = await llm_call(llm, prompt)

        lines = _remove_leading_empty_lines(result).split("\n")

        if lines[0].startswith("  "):
            # print(f"Generated flow:\n{result}\n")
            return f"flow {name}\n" + "\n".join(lines)
        else:
            return "flow bot express unsure\n  bot say 'I don't know how to do that.'"

    @action(
        name="GenerateFlowContinuationAction", is_system_action=True, execute_async=True
    )
    async def generate_flow_continuation(
        self,
        events: List[dict],
        llm: Optional[BaseLLM] = None,
    ):
        """Generate a continuation for the flow representing the current conversation."""

        if self.instruction_flows_index is None:
            raise RuntimeError("No instruction flows index has been created.")

        # Use action specific llm if registered else fallback to main llm
        llm = llm or self.llm

        log.info(f"Generating flow continuation.")

        colang_history = colang(events)

        # We use the last line from the history to search for relevant flows
        search_text = colang_history.split("\n")[-1]

        results = await self.flows_index.search(text=search_text, max_results=10)

        examples = ""
        for result in reversed(results):
            examples += f"{result.meta['flow']}\n"

        # TODO: add examples from the actual running flows

        prompt = self.llm_task_manager.render_task_prompt(
            task=Task.GENERATE_FLOW_CONTINUATION,
            events=events,
            context={
                "examples": examples,
            },
        )

        # We make this call with temperature 0 to have it as deterministic as possible.
        with llm_params(llm, temperature=self.config.lowest_temperature):
            result = await llm_call(llm, prompt)

        lines = _remove_leading_empty_lines(result).split("\n")

        if len(lines) == 0:
            return {
                "name": "bot inform LLM issue",
                "body": 'flow bot inform LLM issue\n  bot say "Sorry! There was an issue in the LLM result form GenerateFlowContinuationAction!"',
            }

        line_0 = lines[0].lstrip(" ")
        uuid = new_uuid()[0:8]
        if line_0.startswith("bot intent:") or line_0.startswith("user intent:"):
            intent = remove_action_intent_identifiers([line_0])[0].strip(" ")
            flow_name = f"_dynamic_{uuid} {intent}"
            # TODO: parse potential parameters from flow name with a regex
            flow_parameters: List[Any] = []
            lines = lines[1:]
        else:
            intent = "unknown"
            flow_name = f"_dynamic_{uuid}"
            flow_parameters = []

        lines = remove_action_intent_identifiers(lines)

        return {
            "name": flow_name,
            "parameters": flow_parameters,
            "body": f"flow {flow_name}\n"
            + f'  # meta: bot intent = "{intent}"\n'
            + "\n".join(["  " + l.strip(" ") for l in lines]),
        }

    @action(name="GenerateValueAction", is_system_action=True, execute_async=True)
    async def generate_value(
        self,
        var_name: str,
        instructions: str,
        events: List[dict],
        llm: Optional[BaseLLM] = None,
    ):
        """Generate a value in the context of the conversation.

        :param instructions: The instructions to generate the value.
        :param events: The full stream of events so far.
        :param var_name: The name of the variable to generate. If not specified, it will use
          the `action_result_key` as the name of the variable.
        :param llm: Custom llm model to generate_value
        """
        # Use action specific llm if registered else fallback to main llm
        llm = llm or self.llm

        # We search for the most relevant flows.
        examples = ""
        if self.flows_index:
            results = await self.flows_index.search(
                text=f"${var_name} = ", max_results=5
            )

            # We add these in reverse order so the most relevant is towards the end.
            for result in reversed(results):
                # If the flow includes "GenerateValueAction", we ignore it as we don't want the LLM
                # to learn to predict it.
                if "GenerateValueAction" not in result.text:
                    examples += f"{result.text}\n\n"

        prompt = self.llm_task_manager.render_task_prompt(
            task=Task.GENERATE_VALUE,
            events=events,
            context={
                "examples": examples,
                "instructions": instructions,
                "var_name": var_name,
            },
        )

        with llm_params(llm, temperature=0.5):
            result = await llm_call(llm, prompt)

        # Parse the output using the associated parser
        result = self.llm_task_manager.parse_task_output(
            Task.GENERATE_VALUE, output=result
        )

        # We only use the first line for now
        # TODO: support multi-line values?
        value = result.strip().split("\n")[0]

        # Because of conventions from other languages, sometimes the LLM might add
        # a ";" at the end of the line. We remove that
        if value.endswith(";"):
            value = value[:-1]

        log.info(f"Generated value for ${var_name}: {value}")

        return literal_eval(value)
