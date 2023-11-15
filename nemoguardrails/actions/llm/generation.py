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
import asyncio
import logging
import random
import re
import sys
import threading
import uuid
from ast import literal_eval
from functools import lru_cache
from time import time
from typing import Callable, List, Optional

from jinja2 import Environment, meta
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
    get_top_k_nonempty_lines,
    llm_call,
    strip_quotes,
)
from nemoguardrails.context import llm_call_info_var, streaming_handler_var
from nemoguardrails.embeddings.index import EmbeddingsIndex, IndexItem
from nemoguardrails.kb.kb import KnowledgeBase
from nemoguardrails.language.parser import parse_colang_file
from nemoguardrails.llm.params import llm_params
from nemoguardrails.llm.prompts import get_prompt
from nemoguardrails.llm.taskmanager import LLMTaskManager
from nemoguardrails.llm.types import Task
from nemoguardrails.logging.explain import LLMCallInfo
from nemoguardrails.patch_asyncio import check_sync_call_from_async_loop
from nemoguardrails.rails.llm.config import EmbeddingSearchProvider, RailsConfig
from nemoguardrails.streaming import StreamingHandler
from nemoguardrails.utils import new_event_dict

log = logging.getLogger(__name__)


local_streaming_handlers = {}


class LLMGenerationActions:
    """A container objects for multiple related actions."""

    def __init__(
        self,
        config: RailsConfig,
        llm: BaseLLM,
        llm_task_manager: LLMTaskManager,
        get_embedding_search_provider_instance: Callable[
            [Optional[EmbeddingSearchProvider]], EmbeddingsIndex
        ],
        verbose: bool = False,
    ):
        self.config = config
        self.llm = llm
        self.verbose = verbose

        # If we have user messages, we build an index with them
        self.user_message_index = None
        self.bot_message_index = None
        self.flows_index = None

        self.get_embedding_search_provider_instance = (
            get_embedding_search_provider_instance
        )

        # There are still some edge cases not covered by nest_asyncio.
        # Using a separate thread always for now.
        if True or check_sync_call_from_async_loop():
            t = threading.Thread(target=asyncio.run, args=(self.init(),))
            t.start()
            t.join()
        else:
            asyncio.run(self.init())

        self.llm_task_manager = llm_task_manager

        # We also initialize the environment for rendering bot messages
        self.env = Environment()

    async def init(self):
        await asyncio.gather(
            self._init_user_message_index(),
            self._init_bot_message_index(),
            self._init_flows_index(),
        )

    async def _init_user_message_index(self):
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

        self.user_message_index = self.get_embedding_search_provider_instance(
            self.config.core.embedding_search_provider
        )
        await self.user_message_index.add_items(items)

        # NOTE: this should be very fast, otherwise needs to be moved to separate thread.
        await self.user_message_index.build()

    async def _init_bot_message_index(self):
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

        self.bot_message_index = self.get_embedding_search_provider_instance(
            self.config.core.embedding_search_provider
        )
        await self.bot_message_index.add_items(items)

        # NOTE: this should be very fast, otherwise needs to be moved to separate thread.
        await self.bot_message_index.build()

    async def _init_flows_index(self):
        """Initializes the index of flows."""

        if not self.config.flows:
            return

        items = []
        for flow in self.config.flows:
            # We don't include the system flows in the index because we don't want
            # the LLM to predict system actions.
            if flow.get("is_system_flow", False):
                continue

            # TODO: check if the flow has system actions and ignore the flow.

            colang_flow = flow.get("source_code") or flow_to_colang(flow)

            # We index on the full body for now
            # items.append(IndexItem(text=colang_flow, meta={"flow": colang_flow}))

            # EXPERIMENTAL: We create an index entry for every line in the flow
            for line in colang_flow.split("\n"):
                if line.strip() != "":
                    items.append(IndexItem(text=line, meta={"flow": colang_flow}))

        # If we have no patterns, we stop.
        if len(items) == 0:
            return

        self.flows_index = self.get_embedding_search_provider_instance(
            self.config.core.embedding_search_provider
        )
        await self.flows_index.add_items(items)

        # NOTE: this should be very fast, otherwise needs to be moved to separate thread.
        await self.flows_index.build()

    def _get_general_instructions(self):
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
    async def generate_user_intent(
        self,
        events: List[dict],
        config: RailsConfig,
        llm: Optional[BaseLLM] = None,
        kb: Optional[KnowledgeBase] = None,
    ):
        """Generate the canonical form for what the user said i.e. user intent."""
        # If using a single LLM call, use the specific action defined for this task.
        if self.config.rails.dialog.single_call.enabled:
            return await self.generate_intent_steps_message(
                events=events, llm=llm, kb=kb
            )

        # The last event should be the "StartInternalSystemAction" and the one before it the "UtteranceUserActionFinished".
        event = get_last_user_utterance_event(events)
        assert event["type"] == "UserMessage"

        # Use action specific llm if registered else fallback to main llm
        llm = llm or self.llm

        streaming_handler = streaming_handler_var.get()

        # TODO: check for an explicit way of enabling the canonical form detection

        if self.config.user_messages:
            # TODO: based on the config we can use a specific canonical forms model
            #  or use the LLM to detect the canonical form. The below implementation
            #  is for the latter.

            log.info("Phase 1: Generating user intent")

            # We search for the most relevant similar user utterance
            examples = ""
            potential_user_intents = []

            if self.user_message_index:
                results = await self.user_message_index.search(
                    text=event["text"], max_results=5
                )

                # If the option to use only the embeddings is activated, we take the first
                # canonical form.
                if results and config.rails.dialog.user_messages.embeddings_only:
                    return ActionResult(
                        events=[
                            new_event_dict(
                                "UserIntent", intent=results[0].meta["intent"]
                            )
                        ]
                    )

                # We add these in reverse order so the most relevant is towards the end.
                for result in reversed(results):
                    examples += f"user \"{result.text}\"\n  {result.meta['intent']}\n\n"
                    if result.meta["intent"] not in potential_user_intents:
                        potential_user_intents.append(result.meta["intent"])

            prompt = self.llm_task_manager.render_task_prompt(
                task=Task.GENERATE_USER_INTENT,
                events=events,
                context={
                    "examples": examples,
                    "potential_user_intents": ", ".join(potential_user_intents),
                },
            )

            # Initialize the LLMCallInfo object
            llm_call_info_var.set(LLMCallInfo(task=Task.GENERATE_USER_INTENT.value))

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

            if user_intent is None:
                return ActionResult(
                    events=[new_event_dict("UserIntent", intent="unknown message")]
                )
            else:
                return ActionResult(
                    events=[new_event_dict("UserIntent", intent=user_intent)]
                )
        else:
            prompt = self.llm_task_manager.render_task_prompt(
                task=Task.GENERAL, events=events
            )

            # Initialize the LLMCallInfo object
            llm_call_info_var.set(LLMCallInfo(task=Task.GENERAL.value))

            # We make this call with temperature 0 to have it as deterministic as possible.
            result = await llm_call(
                llm,
                prompt,
                custom_callback_handlers=[streaming_handler_var.get()],
                stop=["User:"],
            )

            text = result.strip()
            if text.startswith('"'):
                text = text[1:-1]

            # In streaming mode, we also push this.
            if streaming_handler:
                await streaming_handler.push_chunk(text)

            return ActionResult(
                events=[new_event_dict("BotMessage", text=text)],
            )

    async def _search_flows_index(self, text, max_results):
        """Search the index of flows."""
        results = await self.flows_index.search(text=text, max_results=10)

        # we filter the results to keep only unique flows
        flows = set()
        final_results = []
        for result in results:
            if result.meta["flow"] not in flows:
                flows.add(result.meta["flow"])
                # For backwards compatibility we also replace the text with the full version
                result.text = result.meta["flow"]
                final_results.append(result)

        return final_results[0:max_results]

    @action(is_system_action=True)
    async def generate_next_step(
        self, events: List[dict], llm: Optional[BaseLLM] = None
    ):
        """Generate the next step in the current conversation flow.

        Currently, only generates a next step after a user intent.
        """
        log.info("Phase 2 :: Generating next step ...")

        # Use action specific llm if registered else fallback to main llm
        llm = llm or self.llm

        # The last event should be the "StartInternalSystemAction" and the one before it the "UserIntent".
        event = get_last_user_intent_event(events)

        # Currently, we only predict next step after a user intent using LLM
        if event["type"] == "UserIntent":
            # If using a single LLM call, use the results computed in the first call.
            if self.config.rails.dialog.single_call.enabled:
                bot_intent_event = event["additional_info"]["bot_intent_event"]
                return ActionResult(events=[bot_intent_event])

            user_intent = event["intent"]

            # We search for the most relevant similar flows
            examples = ""
            if self.flows_index:
                results = await self._search_flows_index(
                    text=user_intent, max_results=5
                )

                # We add these in reverse order so the most relevant is towards the end.
                for result in reversed(results):
                    examples += f"{result.text}\n\n"

            prompt = self.llm_task_manager.render_task_prompt(
                task=Task.GENERATE_NEXT_STEPS,
                events=events,
                context={"examples": examples},
            )

            # Initialize the LLMCallInfo object
            llm_call_info_var.set(LLMCallInfo(task=Task.GENERATE_NEXT_STEPS.value))

            # We use temperature 0 for next step prediction as well
            with llm_params(llm, temperature=self.config.lowest_temperature):
                result = await llm_call(llm, prompt)

            # Parse the output using the associated parser
            result = self.llm_task_manager.parse_task_output(
                Task.GENERATE_NEXT_STEPS, output=result
            )

            # If we don't have multi-step generation enabled, we only look at the first line.
            if not self.config.enable_multi_step_generation:
                result = get_first_nonempty_line(result)

                if result and result.startswith("bot "):
                    next_step = {"bot": result[4:]}
                else:
                    next_step = {"bot": "general response"}

                # If we have to execute an action, we return the event to start it
                if next_step.get("execute"):
                    return ActionResult(
                        events=[
                            new_event_dict(
                                "StartInternalSystemAction",
                                action_name=next_step["execute"],
                            )
                        ]
                    )
                else:
                    bot_intent = next_step.get("bot")

                    return ActionResult(
                        events=[new_event_dict("BotIntent", intent=bot_intent)]
                    )
            else:
                # Otherwise, we parse the output as a single flow.
                # If we have a parsing error, we try to reduce size of the flow, potentially
                # up to a single step.
                lines = result.split("\n")
                while True:
                    try:
                        parse_colang_file("dynamic.co", content="\n".join(lines))
                        break
                    except Exception as e:
                        # If we could not parse the flow on the last line, we return a general response
                        if len(lines) == 1:
                            log.info("Exception while parsing single line: %s", e)
                            return ActionResult(
                                events=[
                                    new_event_dict(
                                        "BotIntent", intent="general response"
                                    )
                                ]
                            )

                        log.info("Could not parse %s lines, reducing size", len(lines))
                        lines = lines[:-1]

                return ActionResult(
                    events=[
                        # We generate a random UUID as the flow_id
                        new_event_dict(
                            "start_flow",
                            flow_id=str(uuid.uuid4()),
                            flow_body="\n".join(lines),
                        )
                    ]
                )

        return ActionResult(return_value=None)

    def _render_string(
        self,
        template_str: str,
        context: Optional[dict] = None,
    ) -> str:
        """Render a string using the provided context information.

        Args:
            template_str: The string template to render.
            context: The context for rendering.

        Returns:
            The rendered string.
        """
        # First, if we have any direct usage of variables in the string,
        # we replace with correct Jinja syntax.
        for param in re.findall(r"\$([^ \"'!?\-,;</]*(?:\w|]))", template_str):
            template_str = template_str.replace(f"${param}", "{{" + param + "}}")

        template = self.env.from_string(template_str)

        # First, we extract all the variables from the template.
        variables = meta.find_undeclared_variables(self.env.parse(template_str))

        # This is the context that will be passed to the template when rendering.
        render_context = {}

        # Copy the context variables to the render context.
        if context:
            for variable in variables:
                if variable in context:
                    render_context[variable] = context[variable]

        return template.render(render_context)

    @action(is_system_action=True)
    async def generate_bot_message(
        self, events: List[dict], context: dict, llm: Optional[BaseLLM] = None
    ):
        """Generate a bot message based on the desired bot intent."""
        log.info("Phase 3 :: Generating bot message ...")

        # Use action specific llm if registered else fallback to main llm
        llm = llm or self.llm

        # The last event should be the "StartInternalSystemAction" and the one before it the "BotIntent".
        event = get_last_bot_intent_event(events)
        assert event["type"] == "BotIntent"
        bot_intent = event["intent"]
        context_updates = {}

        streaming_handler = streaming_handler_var.get()

        if bot_intent in self.config.bot_messages:
            # Choose a message randomly from self.config.bot_messages[bot_message]
            # However, in test mode, we always choose the first one, to keep it predictable.
            if "pytest" in sys.modules:
                bot_utterance = self.config.bot_messages[bot_intent][0]
            else:
                bot_utterance = random.choice(self.config.bot_messages[bot_intent])

            log.info("Found existing bot message: " + bot_utterance)

            # We also need to render
            bot_utterance = self._render_string(bot_utterance, context)

            # We skip output rails for predefined messages.
            context_updates["skip_output_rails"] = True

        # Check if the output is supposed to be the content of a context variable
        elif bot_intent[0] == "$" and bot_intent[1:] in context:
            bot_utterance = context[bot_intent[1:]]

        else:
            # Generate the bot message using an LLM call

            # If using a single LLM call, use the results computed in the first call.
            if self.config.rails.dialog.single_call.enabled:
                event = get_last_user_intent_event(events)

                if event["type"] == "UserIntent":
                    bot_message_event = event["additional_info"]["bot_message_event"]

                    # We only need to use the bot message if it corresponds to the
                    # generate bot intent as well.
                    last_bot_intent = get_last_bot_intent_event(events)

                    if (
                        last_bot_intent["intent"]
                        == event["additional_info"]["bot_intent_event"]["intent"]
                    ):
                        text = bot_message_event["text"]
                        # If the bot message is being generated in streaming mode
                        if text.startswith('Bot message: "<<STREAMING['):
                            # Format: `Bot message: "<<STREAMING[...]>>"`
                            # Extract the streaming handler uid and get a reference.
                            streaming_handler_uid = text[26:-4]
                            _streaming_handler = local_streaming_handlers[
                                streaming_handler_uid
                            ]

                            # We pipe the content from this handler to the main one.
                            _streaming_handler.set_pipe_to(streaming_handler)
                            await _streaming_handler.disable_buffering()

                            # And wait for it to finish.
                            # We stop after the closing double quotes for the bot message.
                            _streaming_handler.stop = [
                                '"\n',
                            ]
                            text = await _streaming_handler.wait()
                            return ActionResult(
                                events=[new_event_dict("BotMessage", text=text)]
                            )
                        else:
                            if streaming_handler:
                                await streaming_handler.push_chunk(
                                    bot_message_event["text"]
                                )

                            return ActionResult(events=[bot_message_event])

            # We search for the most relevant similar bot utterance
            examples = ""
            # NOTE: disabling bot message index when there are no user messages
            if self.config.user_messages and self.bot_message_index:
                results = await self.bot_message_index.search(
                    text=event["intent"], max_results=5
                )

                # We add these in reverse order so the most relevant is towards the end.
                for result in reversed(results):
                    examples += f"bot {result.text}\n  \"{result.meta['text']}\"\n\n"

            # We compute the relevant chunks to be used as context
            relevant_chunks = get_retrieved_relevant_chunks(events)

            prompt_config = get_prompt(self.config, Task.GENERATE_BOT_MESSAGE)
            prompt = self.llm_task_manager.render_task_prompt(
                task=Task.GENERATE_BOT_MESSAGE,
                events=events,
                context={"examples": examples, "relevant_chunks": relevant_chunks},
            )

            t0 = time()

            if streaming_handler:
                # TODO: Figure out a more generic way to deal with this
                if prompt_config.output_parser == "verbose_v1":
                    streaming_handler.set_pattern(prefix='Bot message: "', suffix='"')
                else:
                    streaming_handler.set_pattern(prefix='  "', suffix='"')

            # Initialize the LLMCallInfo object
            llm_call_info_var.set(LLMCallInfo(task=Task.GENERATE_BOT_MESSAGE.value))

            result = await llm_call(
                llm, prompt, custom_callback_handlers=[streaming_handler]
            )
            log.info(
                "--- :: LLM Bot Message Generation call took %.2f seconds", time() - t0
            )

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
            # In streaming mode, we also push this.
            if streaming_handler:
                await streaming_handler.push_chunk(bot_utterance)

            return ActionResult(
                events=[new_event_dict("BotMessage", text=bot_utterance)],
                context_updates=context_updates,
            )
        else:
            # In streaming mode, we also push this.
            bot_utterance = "I'm not sure what to say."
            if streaming_handler:
                await streaming_handler.push_chunk(bot_utterance)

            return ActionResult(
                events=[new_event_dict("BotMessage", text=bot_utterance)],
                context_updates=context_updates,
            )

    @action(is_system_action=True)
    async def generate_value(
        self,
        instructions: str,
        events: List[dict],
        var_name: Optional[str] = None,
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

        last_event = events[-1]
        assert last_event["type"] == "StartInternalSystemAction"

        if not var_name:
            var_name = last_event["action_result_key"]

        # We search for the most relevant flows.
        examples = ""
        if self.flows_index:
            results = await self._search_flows_index(
                text=f"${var_name} = ", max_results=5
            )

            # We add these in reverse order so the most relevant is towards the end.
            for result in reversed(results):
                # If the flow includes "= ...", we ignore it as we don't want the LLM
                # to learn to predict "...".
                if not re.findall(r"=\s+\.\.\.", result.text):
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

        # Initialize the LLMCallInfo object
        llm_call_info_var.set(LLMCallInfo(task=Task.GENERATE_VALUE.value))

        with llm_params(llm, temperature=self.config.lowest_temperature):
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

    @action(is_system_action=True)
    async def generate_intent_steps_message(
        self,
        events: List[dict],
        llm: Optional[BaseLLM] = None,
        kb: Optional[KnowledgeBase] = None,
    ):
        """Generate all three main Guardrails phases with a single LLM call.
        The three phases are: user canonical from (user intent), next flow steps (i.e. bot canonical form)
        and bot message.
        """

        # The last event should be the "StartInternalSystemAction" and the one before it the "UtteranceUserActionFinished".
        event = get_last_user_utterance_event(events)
        assert event["type"] == "UserMessage"

        # Use action specific llm if registered else fallback to main llm
        llm = llm or self.llm

        streaming_handler = streaming_handler_var.get()

        if self.config.user_messages:
            # TODO: based on the config we can use a specific canonical forms model
            #  or use the LLM to detect the canonical form. The below implementation
            #  is for the latter.

            log.info("Generate all three phases in one LLM call...")

            # We search for the most relevant similar user utterance
            examples = []
            potential_user_intents = []
            intent_results = []
            flow_results = {}

            if self.user_message_index:
                # Get the top 10 intents even if we use less in the selected examples.
                # Some of these intents might not have an associated flow and will be
                # skipped from the few-shot examples.
                intent_results = await self.user_message_index.search(
                    text=event["text"], max_results=10
                )

                # We fill in the list of potential user intents
                for result in intent_results:
                    if result.meta["intent"] not in potential_user_intents:
                        potential_user_intents.append(result.meta["intent"])

            if self.flows_index:
                for intent in potential_user_intents:
                    flow_results_intent = await self._search_flows_index(
                        text=intent, max_results=2
                    )
                    flow_results[intent] = flow_results_intent

            # We add the intent to the examples in reverse order
            # so the most relevant is towards the end.
            for result in intent_results:
                # Stop after the first 5 flow examples, in case more than 5 intents
                # have been selected from the index.
                if len(examples) >= 5:
                    break

                intent = result.meta["intent"]
                example = f'user "{result.text}"\n  {intent}\n'

                flow_results_intent = flow_results.get(intent, [])
                found_flow_for_intent = False
                for result_flow in flow_results_intent:
                    # Assumption: each flow should contain at least two lines, the first is the user intent.
                    # Just in case there are some flows with only one line
                    if "\n" not in result_flow.text:
                        continue
                    (flow_user_intent, flow_continuation) = result_flow.text.split(
                        "\n", 1
                    )
                    flow_user_intent = flow_user_intent[5:]
                    if flow_user_intent == intent:
                        found_flow_for_intent = True
                        example += f"{flow_continuation}\n"

                        # Also add the bot message if the last line in the flow is a bot canonical form
                        last_flow_line = flow_continuation
                        if "\n" in flow_continuation:
                            (_, last_flow_line) = flow_continuation.rsplit("\n", 1)
                        if last_flow_line.startswith("bot "):
                            bot_canonical_form = last_flow_line[4:]

                            found_bot_message = False
                            if self.bot_message_index:
                                bot_messages_results = (
                                    await self.bot_message_index.search(
                                        text=bot_canonical_form, max_results=1
                                    )
                                )

                                for bot_message_result in bot_messages_results:
                                    if bot_message_result.text == bot_canonical_form:
                                        found_bot_message = True
                                        example += (
                                            f"  \"{bot_message_result.meta['text']}\"\n"
                                        )
                                        # Only use the first bot message for now
                                        break

                            if not found_bot_message:
                                # This is for canonical forms that do not have an associated message.
                                # Create a simple message for the bot canonical form.
                                # In a later version we could generate a message with the LLM at app initialization.
                                example += f"  # On the next line generate a bot message related to {bot_canonical_form}\n"

                        # For now, only use the first flow for each intent.
                        break
                if not found_flow_for_intent:
                    # Skip intents that do not have an associated flow.
                    continue

                example += "\n"
                examples.append(example)

            if kb:
                chunks = await kb.search_relevant_chunks(event["text"])
                relevant_chunks = "\n".join([chunk["body"] for chunk in chunks])
            else:
                relevant_chunks = ""

            prompt = self.llm_task_manager.render_task_prompt(
                task=Task.GENERATE_INTENT_STEPS_MESSAGE,
                events=events,
                context={
                    "examples": "\n\n".join(reversed(examples)),
                    "potential_user_intents": ", ".join(potential_user_intents),
                    "relevant_chunks": relevant_chunks,
                },
            )
            prompt_config = get_prompt(self.config, Task.GENERATE_INTENT_STEPS_MESSAGE)

            # We make this call with temperature 0 to have it as deterministic as possible.
            # This is important for canonical forms, but not a great choice for bot messages.

            if streaming_handler:
                # Create a new "inner" streaming handler and save the reference
                _streaming_handler = StreamingHandler()
                local_streaming_handlers[_streaming_handler.uid] = _streaming_handler

                # We buffer the content, so we can get a chance to look at the
                # first k lines.
                await _streaming_handler.enable_buffering()
                with llm_params(llm, temperature=self.config.lowest_temperature):
                    asyncio.create_task(
                        llm_call(
                            llm,
                            prompt,
                            custom_callback_handlers=[_streaming_handler],
                            stop=["\nuser ", "\nUser "],
                        )
                    )
                    result = await _streaming_handler.wait_top_k_nonempty_lines(k=2)

                    # We also mark that the message is still being generated
                    # by a streaming handler.
                    result += (
                        f'\nBot message: "<<STREAMING[{_streaming_handler.uid}]>>"'
                    )

                    # Moving forward we need to set the expected pattern to correctly
                    # parse the message.
                    # TODO: Figure out a more generic way to deal with this.
                    if prompt_config.output_parser == "verbose_v1":
                        _streaming_handler.set_pattern(
                            prefix='Bot message: "', suffix='"'
                        )
                    else:
                        _streaming_handler.set_pattern(prefix='  "', suffix='"')
            else:
                # Initialize the LLMCallInfo object
                llm_call_info_var.set(
                    LLMCallInfo(task=Task.GENERATE_INTENT_STEPS_MESSAGE.value)
                )

                with llm_params(llm, temperature=self.config.lowest_temperature):
                    result = await llm_call(llm, prompt)

            # Parse the output using the associated parser
            result = self.llm_task_manager.parse_task_output(
                Task.GENERATE_INTENT_STEPS_MESSAGE, output=result
            )

            # TODO: Implement logic for generating more complex Colang next steps (multi-step),
            #  not just a single bot intent.

            # Get the next 2 non-empty lines, these should contain:
            # line 1 - user intent, line 2 - bot intent.
            # Afterwards we have the bot message.
            next_three_lines = get_top_k_nonempty_lines(result, k=2)
            user_intent = next_three_lines[0] if len(next_three_lines) > 0 else None
            bot_intent = next_three_lines[1] if len(next_three_lines) > 1 else None
            bot_message = None
            if bot_intent:
                pos = result.find(bot_intent)
                if pos != -1:
                    # The bot message could be multiline
                    bot_message = result[pos + len(bot_intent) :]
                    bot_message = get_multiline_response(bot_message)
                    bot_message = strip_quotes(bot_message)
                    # Quick hack for degenerated / empty bot messages
                    if bot_message and len(bot_message.strip()) == 0:
                        bot_message = None

            if user_intent:
                if user_intent.startswith("user "):
                    user_intent = user_intent[5:]
            else:
                user_intent = "unknown message"

            if bot_intent and bot_intent.startswith("bot "):
                bot_intent = bot_intent[4:]
            else:
                bot_intent = "general response"

            if not bot_message:
                bot_message = "I'm not sure what to say."

            log.info(
                "Canonical form for user intent: "
                + (user_intent if user_intent else "None")
            )
            log.info(
                "Canonical form for bot intent: "
                + (bot_intent if bot_intent else "None")
            )
            log.info(
                f"Generated bot message: " + (bot_message if bot_message else "None")
            )

            additional_info = {
                "bot_intent_event": new_event_dict("BotIntent", intent=bot_intent),
                "bot_message_event": new_event_dict("BotMessage", text=bot_message),
            }
            events = [
                new_event_dict(
                    "UserIntent", intent=user_intent, additional_info=additional_info
                )
            ]

            return ActionResult(events=events)

        else:
            prompt = self.llm_task_manager.render_task_prompt(
                task=Task.GENERAL, events=events
            )

            # Initialize the LLMCallInfo object
            llm_call_info_var.set(LLMCallInfo(task=Task.GENERAL.value))

            # We make this call with temperature 0 to have it as deterministic as possible.
            result = await llm_call(llm, prompt)

            text = result.strip()
            if text.startswith('"'):
                text = text[1:-1]

            # In streaming mode, we also push this.
            if streaming_handler:
                await streaming_handler.push_chunk(text)

            return ActionResult(
                events=[new_event_dict("BotMessage", text=text)],
            )
