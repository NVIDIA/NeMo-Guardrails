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
import random
import sys
from ast import literal_eval
from functools import lru_cache
from typing import List, Optional

from langchain.llms import BaseLLM

from nemoguardrails.actions.actions import ActionResult, action
from nemoguardrails.actions.llm.utils import (
    flow_to_colang,
    get_first_nonempty_line,
    get_last_bot_intent_event,
    get_last_user_intent_event,
    get_last_user_utterance_event,
    get_multiline_response,
    get_retrieved_relevant_chunks,
    llm_call,
    strip_quotes,
)
from nemoguardrails.kb.basic import BasicEmbeddingsIndex
from nemoguardrails.kb.index import IndexItem
from nemoguardrails.kb.kb import KnowledgeBase
from nemoguardrails.llm.params import llm_params
from nemoguardrails.llm.taskmanager import LLMTaskManager
from nemoguardrails.llm.types import Task
from nemoguardrails.rails.llm.config import RailsConfig

log = logging.getLogger(__name__)


class LLMGenerationActions:
    """A container objects for multiple related actions."""

    def __init__(
        self,
        config: RailsConfig,
        llm: BaseLLM,
        llm_task_manager: LLMTaskManager,
        verbose: bool = False,
    ):
        self.config = config
        self.llm = llm
        self.verbose = verbose

        # If we have user messages, we build an index with them
        self.user_message_index = None
        self._init_user_message_index()

        self.bot_message_index = None
        self._init_bot_message_index()

        self.flows_index = None
        self._init_flows_index()

        # If we have documents, we'll also initialize a knowledge base.
        self.kb = None
        self._init_kb()

        self.llm_task_manager = llm_task_manager

    def _init_user_message_index(self):
        """Initializes the index of user messages."""

        if not self.config.user_messages:
            return

        items = []
        for intent, utterances in self.config.user_messages.items():
            for text in utterances:
                items.append(IndexItem(text=text, meta={"intent": intent}))

        # If we have no patterns, we stop.
        if len(items) == 0:
            return

        self.user_message_index = BasicEmbeddingsIndex()
        self.user_message_index.add_items(items)

        # NOTE: this should be very fast, otherwise needs to be moved to separate thread.
        self.user_message_index.build()

    def _init_bot_message_index(self):
        """Initializes the index of bot messages."""

        if not self.config.bot_messages:
            return

        items = []
        for intent, utterances in self.config.bot_messages.items():
            for text in utterances:
                items.append(IndexItem(text=intent, meta={"text": text}))

        # If we have no patterns, we stop.
        if len(items) == 0:
            return

        self.bot_message_index = BasicEmbeddingsIndex()
        self.bot_message_index.add_items(items)

        # NOTE: this should be very fast, otherwise needs to be moved to separate thread.
        self.bot_message_index.build()

    def _init_flows_index(self):
        """Initializes the index of flows."""

        if not self.config.flows:
            return

        items = []
        for flow in self.config.flows:
            # We don't include the default system flows in the index because we don't want
            # the LLM to predict system actions.
            if flow.get("id") in [
                "generate user intent",
                "generate next step",
                "generate bot message",
            ]:
                continue

            # TODO: check if the flow has system actions and ignore the flow.

            colang_flow = flow.get("source_code") or flow_to_colang(flow)

            # We index on the full body for now
            items.append(IndexItem(text=colang_flow, meta={"flow": colang_flow}))

        # If we have no patterns, we stop.
        if len(items) == 0:
            return

        self.flows_index = BasicEmbeddingsIndex()
        self.flows_index.add_items(items)

        # NOTE: this should be very fast, otherwise needs to be moved to separate thread.
        self.flows_index.build()

    def _init_kb(self):
        """Initializes the knowledge base."""

        if not self.config.docs:
            return

        documents = [doc.content for doc in self.config.docs]
        self.kb = KnowledgeBase(documents=documents)
        self.kb.init()
        self.kb.build()

    def _get_general_instruction(self):
        """Helper to extract the general instruction."""
        text = ""
        for instruction in self.config.instructions:
            if instruction.type == "general":
                text = instruction.content

                # We stop at the first one for now
                break

        return text

    @lru_cache
    def _get_sample_conversation_two_turns(self):
        """Helper to extract only the two turns from the sample conversation.

        This is needed to be included to "seed" the conversation so that the model
        can follow the format more easily.
        """
        lines = self.config.sample_conversation.split("\n")
        i = 0
        user_count = 0
        while i < len(lines):
            if lines[i].startswith("user "):
                user_count += 1

            if user_count == 3:
                break

            i += 1

        sample_conversation = "\n".join(lines[0:i])

        # Remove any trailing new lines
        sample_conversation = sample_conversation.strip()

        return sample_conversation

    @action(is_system_action=True)
    async def generate_user_intent(self, events: List[dict]):
        """Generate the canonical form for what the user said i.e. user intent."""

        # The last event should be the "start_action" and the one before it the "user_said".
        event = get_last_user_utterance_event(events)
        assert event["type"] == "user_said"

        # TODO: check for an explicit way of enabling the canonical form detection

        if self.config.user_messages:
            # TODO: based on the config we can use a specific canonical forms model
            #  or use the LLM to detect the canonical form. The below implementation
            #  is for the latter.

            log.info("Phase 1: Generating user intent")

            # We search for the most relevant similar user utterance
            examples = ""
            if self.user_message_index:
                results = self.user_message_index.search(
                    text=event["content"], max_results=5
                )

                # We add these in reverse order so the most relevant is towards the end.
                candidate_intents = set()
                for result in reversed(results):
                    examples += f"user \"{result.text}\"\n  {result.meta['intent']}\n\n"
                    candidate_intents.add(result.meta["intent"])

            prompt = self.llm_task_manager.render_task_prompt(
                task=Task.GENERATE_USER_INTENT,
                events=events,
                context={"examples": examples},
            )

            # We make this call with temperature 0 to have it as deterministic as possible.
            with llm_params(self.llm, temperature=0.0):
                result = await llm_call(self.llm, prompt)

            # Parse the output using the associated parser
            result = self.llm_task_manager.parse_task_output(
                Task.GENERATE_USER_INTENT, output=result
            )

            user_intent = get_first_nonempty_line(result)
            if user_intent is None:
                user_intent = "unknown message"

            if user_intent and user_intent.startswith("user "):
                user_intent = user_intent[5:]

            log.info("Canonical form for user intent: %s", user_intent)

            if user_intent is None:
                return ActionResult(
                    events=[{"type": "user_intent", "intent": "unknown message"}]
                )
            else:
                return ActionResult(
                    events=[{"type": "user_intent", "intent": user_intent}]
                )
        else:
            prompt = self.llm_task_manager.render_task_prompt(
                task=Task.GENERAL, events=events
            )

            # We make this call with temperature 0 to have it as deterministic as possible.
            result = await llm_call(self.llm, prompt)

            return ActionResult(
                events=[{"type": "bot_said", "content": result.strip()}]
            )

    @action(is_system_action=True)
    async def generate_next_step(self, events: List[dict]):
        """Generate the next step in the current conversation flow.

        Currently, only generates a next step after a user intent.
        """
        log.info("Phase 2 :: Generating next step ...")

        # The last event should be the "start_action" and the one before it the "user_intent".
        event = get_last_user_intent_event(events)

        # Currently, we only predict next step after a user intent using LLM
        if event["type"] == "user_intent":
            user_intent = event["intent"]

            # We search for the most relevant similar flows
            examples = ""
            if self.flows_index:
                results = self.flows_index.search(text=user_intent, max_results=5)

                # We add these in reverse order so the most relevant is towards the end.
                for result in reversed(results):
                    examples += f"{result.text}\n\n"

            prompt = self.llm_task_manager.render_task_prompt(
                task=Task.GENERATE_NEXT_STEPS,
                events=events,
                context={"examples": examples},
            )

            # We use temperature 0 for next step prediction as well
            with llm_params(self.llm, temperature=0.0):
                result = await llm_call(self.llm, prompt)

            # Parse the output using the associated parser
            result = self.llm_task_manager.parse_task_output(
                Task.GENERATE_NEXT_STEPS, output=result
            )

            result = get_first_nonempty_line(result)

            if result and result.startswith("bot "):
                next_step = {"bot": result[4:]}
            else:
                next_step = {"bot": "general response"}

            # If we have to execute an action, we return the event to start it
            if next_step.get("execute"):
                return ActionResult(
                    events=[
                        {"type": "start_action", "action_name": next_step["execute"]}
                    ]
                )
            else:
                bot_intent = next_step.get("bot")

                return ActionResult(
                    events=[{"type": "bot_intent", "intent": bot_intent}]
                )

        return ActionResult(return_value=None)

    @action(is_system_action=True)
    async def generate_bot_message(self, events: List[dict], context: dict):
        """Generate a bot message based on the desired bot intent."""
        log.info("Phase 3 :: Generating bot message ...")

        # The last event should be the "start_action" and the one before it the "bot_intent".
        event = get_last_bot_intent_event(events)
        assert event["type"] == "bot_intent"
        bot_intent = event["intent"]
        context_updates = {}

        if bot_intent in self.config.bot_messages:
            # Choose a message randomly from self.config.bot_messages[bot_message]
            # However, in test mode, we always choose the first one, to keep it predictable.
            if "pytest" in sys.modules:
                bot_utterance = self.config.bot_messages[bot_intent][0]
            else:
                bot_utterance = random.choice(self.config.bot_messages[bot_intent])

            log.info("Found existing bot message: " + bot_utterance)

        # Check if the output is supposed to be the content of a context variable
        elif bot_intent[0] == "$" and bot_intent[1:] in context:
            bot_utterance = context[bot_intent[1:]]

        else:
            # We search for the most relevant similar bot utterance
            examples = ""
            if self.bot_message_index:
                results = self.bot_message_index.search(
                    text=event["intent"], max_results=5
                )

                # We add these in reverse order so the most relevant is towards the end.
                for result in reversed(results):
                    examples += f"bot {result.text}\n  \"{result.meta['text']}\"\n\n"

            # We compute the relevant chunks to be used as context
            relevant_chunks = get_retrieved_relevant_chunks(events)

            prompt = self.llm_task_manager.render_task_prompt(
                task=Task.GENERATE_BOT_MESSAGE,
                events=events,
                context={"examples": examples, "relevant_chunks": relevant_chunks},
            )

            result = await llm_call(self.llm, prompt)

            # Parse the output using the associated parser
            result = self.llm_task_manager.parse_task_output(
                Task.GENERATE_BOT_MESSAGE, output=result
            )

            # TODO: catch openai.error.InvalidRequestError from exceeding max token length

            result = get_multiline_response(result)
            result = strip_quotes(result)

            bot_utterance = result

            # Context variable starting with "_" are considered private (not used in tests or logging)
            context_updates["_last_bot_prompt"] = prompt

            log.info(f"Generated bot message: {bot_utterance}")

        if bot_utterance:
            return ActionResult(
                events=[{"type": "bot_said", "content": bot_utterance}],
                context_updates=context_updates,
            )
        else:
            return ActionResult(
                events=[{"type": "bot_said", "content": "I'm not sure what to say."}],
                context_updates=context_updates,
            )

    @action(is_system_action=True)
    async def generate_value(
        self, instructions: str, events: List[dict], var_name: Optional[str] = None
    ):
        """Generate a value in the context of the conversation.

        :param instructions: The instructions to generate the value.
        :param events: The full stream of events so far.
        :param var_name: The name of the variable to generate. If not specified, it will use
          the `action_result_key` as the name of the variable.
        """
        last_event = events[-1]
        assert last_event["type"] == "start_action"

        if not var_name:
            var_name = last_event["action_result_key"]

        # We search for the most relevant flows.
        examples = ""
        if self.flows_index:
            results = self.flows_index.search(text=f"${var_name} = ", max_results=5)

            # We add these in reverse order so the most relevant is towards the end.
            for result in reversed(results):
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

        with llm_params(self.llm, temperature=0):
            result = await llm_call(self.llm, prompt)

        # Parse the output using the associated parser
        result = self.llm_task_manager.parse_task_output(
            Task.GENERATE_VALUE, output=result
        )

        # We only use the first line for now
        # TODO: support multi-line values?
        value = result.strip().split("\n")[0]

        log.info(f"Generated value for ${var_name}: {value}")

        return literal_eval(value)
