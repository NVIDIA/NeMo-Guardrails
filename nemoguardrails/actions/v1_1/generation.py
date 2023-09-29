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
import textwrap
from typing import List, Optional

from langchain.llms import BaseLLM

from nemoguardrails.actions.actions import action
from nemoguardrails.actions.llm.generation import LLMGenerationActions
from nemoguardrails.actions.llm.utils import (
    get_first_nonempty_line,
    get_last_user_utterance_event,
    llm_call,
)
from nemoguardrails.llm.params import llm_params
from nemoguardrails.llm.types import Task

log = logging.getLogger(__name__)


class LLMGenerationActionsV1dot1(LLMGenerationActions):
    """A container objects for multiple related actions."""

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

    @action(name="GenerateFlowFromInstructionsAction", is_system_action=True)
    async def generate_flow_from_instructions(
        self,
        instructions: str,
        events: List[dict],
        llm: Optional[BaseLLM] = None,
    ):
        """Generate a flow from the provided instructions."""

        # Use action specific llm if registered else fallback to main llm
        llm = llm or self.llm

        log.info(f"Generating flow for instructions: {instructions}")

        prompt = textwrap.dedent(
            f"""
        # Please tell a joke
        flow tell a joke
          bot say "Why don't scientists trust atoms? Because they make up everything!"
          bot smile

        # Count from 1 to 5
        flow count
          bot say "1"
          bot say "2"
          bot say "3"
          bot say "4"
          bot say "5"

        # Tell me the capital of France
        flow answer question about france
          bot say "The capital of France it's Paris."

        # {instructions}
        """
        )

        # We make this call with temperature 0 to have it as deterministic as possible.
        with llm_params(llm, temperature=self.config.lowest_temperature):
            result = await llm_call(llm, prompt)

        lines = result.split("\n")
        if lines[0].startswith("flow "):
            print(f"Generated flow:\n{result}\n")
            return {
                "name": lines[0][5:],
                "body": result,
            }
        else:
            return {
                "name": "bot express unsure",
                "body": "flow bot express unsure\n  bot say 'I'm sure, I don't know how to do that.'",
            }
