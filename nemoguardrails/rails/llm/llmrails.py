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

"""LLM Rails entry point."""
import asyncio
import logging
import os
from typing import List, Optional

from langchain.llms import BaseLLM, OpenAI

from nemoguardrails.actions.llm.generation import LLMGenerationActions
from nemoguardrails.actions.llm.utils import get_colang_history
from nemoguardrails.flows.runtime import Runtime
from nemoguardrails.language.parser import parse_colang_file
from nemoguardrails.rails.llm.config import RailsConfig
from nemoguardrails.rails.llm.utils import get_history_cache_key

log = logging.getLogger(__name__)


class LLMRails:
    """Rails based on a given configuration."""

    def __init__(
        self, config: RailsConfig, llm: Optional[BaseLLM] = None, verbose: bool = False
    ):
        self.config = config
        self.llm = llm
        self.verbose = verbose

        # We keep a cache of the events history associated with a sequence of user messages.
        # TODO: when we update the interface to allow to return a "state object", this
        #   should be removed
        self.events_history_cache = {}

        # We also load the default flows from the `default_flows.yml` file in the current folder.
        current_folder = os.path.dirname(__file__)
        default_flows_path = os.path.join(current_folder, "llm_flows.co")
        with open(default_flows_path, "r") as f:
            default_flows_content = f.read()
            default_flows = parse_colang_file("llm_flows.co", default_flows_content)[
                "flows"
            ]

        # We add the default flows to the config.
        self.config.flows.extend(default_flows)

        # First, we initialize the runtime.
        self.runtime = Runtime(config=config, verbose=verbose)

        # Next, we initialize the LLM engine.
        self._init_llm()
        self.runtime.register_action_param("llm", self.llm)

        # Next, we initialize the LLM Generate actions and register them.
        actions = LLMGenerationActions(config=config, llm=self.llm, verbose=verbose)
        self.runtime.register_actions(actions)
        # We also register the kb as a parameter that can be passed to actions.
        self.runtime.register_action_param("kb", actions.kb)

    def _init_llm(self):
        """Initializes the right LLM engine based on the configuration."""

        # If we already have a pre-configured one, we do nothing.
        if self.llm is not None:
            return

        # TODO: Currently we assume the first model is the main one. Add proper support
        #  to search for the main model config.
        main_llm_config = self.config.models[0]

        if main_llm_config.engine == "openai":
            self.llm = OpenAI(model_name=main_llm_config.model, temperature=0.1)
        else:
            raise Exception(f"Unknown LLM engine: {main_llm_config.engine}")

    async def generate_async(
        self, prompt: Optional[str] = None, messages: Optional[List[dict]] = None
    ):
        """Generates a completion or a next message.

        The format for messages is currently the following:
        [
            {"role": "user", "content": "Hello! How are you?"},
            {"role": "assistant", "content": "I am fine, thank you!"},
        ]
        System messages are not yet supported.

        """
        if prompt is not None:
            # Currently, we transform the prompt request into a single turn conversation
            new_message = await self.generate_async(
                messages=[{"role": "user", "content": prompt}]
            )

            assert new_message["role"] == "assistant"
            return new_message["content"]

        # TODO: Add support to load back history of events, next to history of messages
        #   This is important as without it, the LLM prediction is not as good.

        # First, we turn the messages into a history of events.
        cache_key = get_history_cache_key(messages, include_last=False)
        events = self.events_history_cache.get(cache_key, []).copy()

        events.append({"type": "user_said", "content": messages[-1]["content"]})

        new_events = await self.runtime.generate_events(events)

        # Save the new events in the history and update the cache
        events.extend(new_events)
        cache_key = get_history_cache_key(messages, include_last=True)
        self.events_history_cache[cache_key] = events

        # Extract and join all the messages from bot_said events as the response.
        responses = []
        for event in new_events:
            if event["type"] == "bot_said":
                # Check if we need to remove a message
                if event["content"] == "(remove last message)":
                    responses = responses[0:-1]
                else:
                    responses.append(event["content"])

        # If logging is enabled, we log the conversation
        # TODO: add support for logging flag
        if self.verbose:
            history = get_colang_history(events)
            log.info(f"Conversation history so far: \n{history}")

        return {"role": "assistant", "content": "\n".join(responses)}

    def generate(
        self, prompt: Optional[str] = None, messages: Optional[List[dict]] = None
    ):
        """Synchronous version of generate_async."""

        try:
            loop = asyncio.get_running_loop()
        except RuntimeError:
            loop = None

        if loop and loop.is_running():
            raise RuntimeError(
                "You are using the sync `generate` inside async code. "
                "You should replace with `await generate_async(...)."
            )

        return asyncio.run(self.generate_async(prompt=prompt, messages=messages))

    def register_action(self, action: callable, name: Optional[str] = None):
        """Register a custom action for the rails configuration."""
        self.runtime.register_action(action, name)
