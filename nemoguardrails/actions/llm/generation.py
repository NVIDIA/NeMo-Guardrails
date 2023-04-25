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
from functools import lru_cache
from typing import List

from langchain import LLMChain, PromptTemplate
from langchain.llms import BaseLLM

from nemoguardrails.actions.actions import ActionResult, action
from nemoguardrails.actions.llm.utils import (
    flow_to_colang,
    get_colang_history,
    get_first_nonempty_line,
    get_last_bot_intent_event,
    get_last_user_intent_event,
    get_last_user_utterance_event,
    get_multiline_response,
    get_retrieved_relevant_chunks,
    print_completion,
    remove_text_messages_from_history,
    strip_quotes,
)
from nemoguardrails.kb.basic import BasicEmbeddingsIndex
from nemoguardrails.kb.index import IndexItem
from nemoguardrails.kb.kb import KnowledgeBase
from nemoguardrails.llm.prompts.prompts import Step, get_prompt
from nemoguardrails.rails.llm.config import RailsConfig

log = logging.getLogger(__name__)


class LLMGenerationActions:
    """A container objects for multiple related actions."""

    def __init__(self, config: RailsConfig, llm: BaseLLM, verbose: bool = False):
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

        return "\n".join(lines[0:i])

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

            # Compute the conversation history
            history = get_colang_history(events)

            # We search for the most relevant similar user utterance
            examples = ""
            if self.user_message_index:
                results = self.user_message_index.search(
                    text=event["content"], max_results=5
                )

                # We add these in reverse order so the most relevant is towards the end.
                for result in reversed(results):
                    examples += f"user \"{result.text}\"\n  {result.meta['intent']}\n\n"

            # We have user messages, so we need to identify the canonical form.
            canonical_form_prompt = PromptTemplate(
                input_variables=[
                    "history",
                    "examples",
                    "sample_conversation",
                    "general_instruction",
                    "sample_conversation_two_turns",
                ],
                template=get_prompt(
                    self.config, Step.DETECT_USER_MESSAGE_CANONICAL_FORM
                )["content"],
            )

            # Create and run the general chain.
            chain = LLMChain(
                prompt=canonical_form_prompt, llm=self.llm, verbose=self.verbose
            )
            result = await chain.apredict(
                history=history,
                examples=examples,
                sample_conversation=self.config.sample_conversation,
                general_instruction=self._get_general_instruction(),
                sample_conversation_two_turns=self._get_sample_conversation_two_turns(),
            )
            if self.verbose:
                print_completion(result)
            user_intent = get_first_nonempty_line(result)

            log.info("Canonical form for user intent: " + user_intent)

            if user_intent is None:
                return ActionResult(
                    events=[{"type": "user_intent", "intent": "unknown message"}]
                )
            else:
                return ActionResult(
                    events=[{"type": "user_intent", "intent": user_intent}]
                )
        else:
            # This is the pass-through behavior.
            # First, we compute the general instructions.
            instruction_items = []
            if self.config.instructions:
                for instruction in self.config.instructions:
                    instruction_items.append(instruction.content)
            general_instructions = "\n".join(instruction_items)

            # Next, we compute the history from all the messages
            history_items = []
            for event in events:
                if event["type"] == "user_said":
                    history_items.append("User: " + event["content"])
                elif event["type"] == "bot_said":
                    history_items.append("Assistant: " + event["content"])
            history = "\n".join(history_items)

            general_prompt = PromptTemplate(
                input_variables=["general_instructions", "history"],
                template=get_prompt(self.config, Step.GENERAL)["content"],
            )

            # Create and run the general chain.
            chain = LLMChain(prompt=general_prompt, llm=self.llm, verbose=self.verbose)

            result = await chain.apredict(
                general_instructions=general_instructions,
                history=history,
                stop=["User: "],
            )
            if self.verbose:
                print_completion(result)

            return ActionResult(
                events=[{"type": "bot_said", "content": result.strip()}]
            )

    @action(is_system_action=True)
    async def generate_next_step(self, events: List[dict]):
        """Generate the next step in the current conversation flow.

        Currently, only generates a next step after a user intent.
        """
        # The last event should be the "start_action" and the one before it the "user_intent".
        event = get_last_user_intent_event(events)

        # Currently, we only predict next step after a user intent using LLM
        if event["type"] == "user_intent":
            user_intent = event["intent"]

            # We use the LLM to predict the next step
            # Compute the conversation history
            history = get_colang_history(events, include_texts=False)

            # We search for the most relevant similar user utterance
            examples = ""
            if self.flows_index:
                results = self.flows_index.search(text=user_intent, max_results=5)

                # We add these in reverse order so the most relevant is towards the end.
                for result in reversed(results):
                    examples += f"{result.text}\n"

            predict_next_step_prompt = PromptTemplate(
                input_variables=[
                    "history",
                    "examples",
                    "sample_conversation",
                    "general_instruction",
                    "sample_conversation_two_turns",
                ],
                template=get_prompt(self.config, Step.PREDICT_NEXT_STEP)["content"],
            )

            # Create and run the general chain.
            chain = LLMChain(
                prompt=predict_next_step_prompt, llm=self.llm, verbose=self.verbose
            )
            result = await chain.apredict(
                history=history,
                examples=examples,
                sample_conversation=remove_text_messages_from_history(
                    self.config.sample_conversation
                ),
                general_instruction=self._get_general_instruction(),
                sample_conversation_two_turns=remove_text_messages_from_history(
                    self._get_sample_conversation_two_turns()
                ),
            )
            if self.verbose:
                print_completion(result)

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
            history = get_colang_history(events, remove_retrieval_events=True)
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

            # Otherwise, we generate a message with the LLM
            bot_message_prompt = PromptTemplate(
                input_variables=[
                    "history",
                    "examples",
                    "sample_conversation",
                    "general_instruction",
                    "sample_conversation_two_turns",
                    "relevant_chunks",
                ],
                template=get_prompt(self.config, Step.GENERATE_BOT_MESSAGE)["content"],
            )

            # Save the current bot message prompt in the context as a string.
            # The last bot message prompt is needed for the hallucination rail.
            prompt_inputs = {
                "history": history,
                "examples": examples,
                "relevant_chunks": relevant_chunks,
                "sample_conversation": self.config.sample_conversation,
                "general_instruction": self._get_general_instruction(),
                "sample_conversation_two_turns": self._get_sample_conversation_two_turns(),
            }
            bot_message_prompt_string = bot_message_prompt.format(**prompt_inputs)
            # Context variable starting with "_" are considered private (not used in tests or logging)
            context_updates["_last_bot_prompt"] = bot_message_prompt_string

            chain = LLMChain(
                prompt=bot_message_prompt, llm=self.llm, verbose=self.verbose
            )
            # TODO: catch openai.error.InvalidRequestError from exceeding max token length
            result = await chain.apredict(**prompt_inputs)

            if self.verbose:
                print_completion(result)

            result = get_multiline_response(result)
            result = strip_quotes(result)

            bot_utterance = result

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
