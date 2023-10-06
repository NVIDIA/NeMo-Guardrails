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
from typing import Any, List, Optional

from langchain.llms import BaseLLM

from nemoguardrails.actions.actions import action
from nemoguardrails.actions.llm.generation import LLMGenerationActions
from nemoguardrails.actions.llm.utils import (
    get_first_nonempty_line,
    get_last_user_utterance_event,
    llm_call,
)
from nemoguardrails.colang.v1_1.lang.utils import new_uuid
from nemoguardrails.colang.v1_1.runtime.flows import (
    FlowEvent,
    find_all_active_event_matchers,
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
            if "# llm: exclude" in colang_flow:
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
        event = get_last_user_utterance_event(events)
        assert event["type"] == "UtteranceUserActionFinished"
        return event["final_transcript"]

    @action(name="GenerateUserIntentAction", is_system_action=True)
    async def generate_user_intent(
        self, events: List[dict], llm: Optional[BaseLLM] = None
    ):
        """Generate the canonical form for what the user said i.e. user intent."""

        # The last event should be the "StartInternalSystemAction" and the one before it the "UtteranceUserActionFinished".
        event = get_last_user_utterance_event(events)
        assert event["type"] == "UtteranceUserActionFinished"

        # Use action specific llm if registered else fallback to main llm
        llm = llm or self.llm

        log.info("Phase 1: Generating user intent")

        # We search for the most relevant similar user utterance
        examples = ""
        potential_user_intents = []

        if self.user_message_index:
            results = await self.user_message_index.search(
                text=event["final_transcript"], max_results=5
            )

            # We add these in reverse order so the most relevant is towards the end.
            for result in reversed(results):
                examples += (
                    f"user said \"{result.text}\"\nuser {result.meta['intent']}\n\n"
                )
                potential_user_intents.append(result.meta["intent"])

        prompt = self.llm_task_manager.render_task_prompt(
            task=Task.GENERATE_USER_INTENT,
            events=events,
            context={
                "examples": examples,
                "potential_user_intents": ", ".join(potential_user_intents),
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

        if user_intent and user_intent.startswith("user "):
            user_intent = user_intent[5:]

        log.info(
            "Canonical form for user intent: "
            + (user_intent if user_intent else "None")
        )

        return f"user {user_intent}" or "user unknown intent"

    @action(name="CheckIfFlowExistsAction", is_system_action=True)
    async def check_if_flow_exists(self, state: "State", flow_id: str):
        return flow_id in state.flow_id_states

    @action(name="CheckForActiveFlowFinishedMatchAction", is_system_action=True)
    async def check_for_active_flow_finished_match(
        self, state: "State", **arguments: Any
    ):
        event = FlowEvent(name="FlowFinished", arguments=arguments)
        heads = find_all_active_event_matchers(state, event)
        return len(heads) > 0

    @action(name="GenerateFlowFromInstructionsAction", is_system_action=True)
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
            print(f"Generated flow:\n{result}\n")
            return {
                "name": flow_name,
                "body": f"flow {flow_name}\n" + "\n".join(lines),
            }
        else:
            return {
                "name": "bot express unsure",
                "body": "flow bot express unsure\n  bot say 'I'm sure, I don't know how to do that.'",
            }

    @action(name="GenerateFlowFromNameAction", is_system_action=True)
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
            print(f"Generated flow:\n{result}\n")
            return f"flow {name}\n" + "\n".join(lines)
        else:
            return "flow bot express unsure\n  bot say 'I don't know how to do that.'"

    @action(name="GenerateFlowContinuationAction", is_system_action=True)
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

        results = await self.flows_index.search(text=search_text, max_results=5)

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

        flow_id = new_uuid()[0:4]
        flow_name = f"dynamic_{flow_id}"

        if lines[0].startswith("  "):
            print(f"Generated flow:\n{result}\n")
            return {
                "name": flow_name,
                "body": f"flow {flow_name}\n" + "\n".join(lines),
            }
        else:
            return {
                "name": "bot express unsure",
                "body": 'flow bot express unsure\n  bot say "I\'m not sure what to do next."',
            }
