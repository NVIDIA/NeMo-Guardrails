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
import importlib.util
import logging
import os
import time
from typing import Any, List, Optional, Type, Union

from langchain.llms.base import BaseLLM

from nemoguardrails.actions.fact_checking import check_facts
from nemoguardrails.actions.hallucination import check_hallucination
from nemoguardrails.actions.jailbreak_check import check_jailbreak
from nemoguardrails.actions.llm.generation import LLMGenerationActions
from nemoguardrails.actions.llm.utils import get_colang_history
from nemoguardrails.actions.math import wolfram_alpha_request
from nemoguardrails.actions.output_moderation import output_moderation
from nemoguardrails.actions.retrieve_relevant_chunks import retrieve_relevant_chunks
from nemoguardrails.embeddings.index import EmbeddingsIndex
from nemoguardrails.flows.runtime import Runtime
from nemoguardrails.kb.kb import KnowledgeBase
from nemoguardrails.language.parser import parse_colang_file
from nemoguardrails.llm.providers import get_llm_provider, get_llm_provider_names
from nemoguardrails.logging.stats import llm_stats
from nemoguardrails.patch_asyncio import check_sync_call_from_async_loop
from nemoguardrails.rails.llm.config import EmbeddingSearchProvider, RailsConfig
from nemoguardrails.rails.llm.utils import get_history_cache_key

log = logging.getLogger(__name__)


class LLMRails:
    """Rails based on a given configuration."""

    def __init__(
        self, config: RailsConfig, llm: Optional[BaseLLM] = None, verbose: bool = False
    ):
        """Initializes the LLMRails instance.

        Args:
            config: A rails configuration.
            llm: An optional LLM engine to use.
            verbose: Whether the logging should be verbose or not.
        """
        self.config = config
        self.llm = llm
        self.verbose = verbose

        # We allow the user to register additional embedding search providers, so we keep
        # an index of them.
        self.embedding_search_providers = {}

        # The default embeddings model is using SentenceTransformers
        self.default_embedding_model = "all-MiniLM-L6-v2"
        self.default_embedding_engine = "SentenceTransformers"

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

        # We check if the configuration has a config.py module associated with it.
        config_module = None
        if self.config.config_path:
            filepath = os.path.join(self.config.config_path, "config.py")
            if os.path.exists(filepath):
                filename = os.path.basename(filepath)
                spec = importlib.util.spec_from_file_location(filename, filepath)
                config_module = importlib.util.module_from_spec(spec)
                spec.loader.exec_module(config_module)

        # First, we initialize the runtime.
        self.runtime = Runtime(config=config, verbose=verbose)

        # If we have a config_module with an `init` function, we call it.
        # We need to call this here because the `init` might register additional
        # LLM providers.
        if config_module is not None and hasattr(config_module, "init"):
            config_module.init(self)

        # Register any default actions that have not yet been registered in the custom
        # init function from config.py.
        default_actions = {
            "wolfram alpha request": wolfram_alpha_request,
            "check_facts": check_facts,
            "check_jailbreak": check_jailbreak,
            "output_moderation": output_moderation,
            "check_hallucination": check_hallucination,
            "retrieve_relevant_chunks": retrieve_relevant_chunks,
        }

        for action_name, action_fn in default_actions.items():
            self.runtime.register_action(action_fn, action_name, override=False)

        # If we have a customized embedding model, we'll use it.
        for model in self.config.models:
            if model.type == "embeddings":
                self.default_embedding_model = model.model
                self.default_embedding_engine = model.engine
                break

        # Next, we initialize the LLM engines (main engine and action engines if specified).
        self._init_llms()

        # Next, we initialize the LLM Generate actions and register them.
        self.llm_generation_actions = LLMGenerationActions(
            config=config,
            llm=self.llm,
            llm_task_manager=self.runtime.llm_task_manager,
            get_embedding_search_provider_instance=self._get_embeddings_search_provider_instance,
            verbose=verbose,
        )

        # If there's already an action registered, we don't override.
        self.runtime.register_actions(self.llm_generation_actions, override=False)

        # Next, we initialize the Knowledge Base
        asyncio.run(self._init_kb())

        # We also register the kb as a parameter that can be passed to actions.
        self.runtime.register_action_param("kb", self.kb)

    async def _init_kb(self):
        """Initializes the knowledge base."""
        self.kb = None

        if not self.config.docs:
            return

        documents = [doc.content for doc in self.config.docs]
        self.kb = KnowledgeBase(
            documents=documents,
            config=self.config.knowledge_base,
            get_embedding_search_provider_instance=self._get_embeddings_search_provider_instance,
        )
        self.kb.init()
        await self.kb.build()

    def _init_llms(self):
        """
        Initializes the right LLM engines based on the configuration.
        There can be multiple LLM engines and types that can be specified in the config.
        The main LLM engine is the one that will be used for all the core guardrails generations.
        Other LLM engines can be specified for use in specific actions.

        The reason we provide an option for decoupling the main LLM engine from the action LLM
        is to allow for flexibility in using specialized LLM engines for specific actions.
        """

        # If we already have a pre-configured one, we do nothing.
        if self.llm is not None:
            return

        # TODO: Currently we assume the first model is the main one. Add proper support
        #  to search for the main model config.

        for llm_config in self.config.models:
            if llm_config.type == "embeddings":
                pass
            else:
                if llm_config.engine not in get_llm_provider_names():
                    raise Exception(f"Unknown LLM engine: {llm_config.engine}")

                provider_cls = get_llm_provider(llm_config)
                # We need to compute the kwargs for initializing the LLM
                kwargs = llm_config.parameters

                # We also need to pass the model, if specified
                if llm_config.model:
                    # Some LLM providers use `model_name` instead of model. For backward compatibility
                    # we keep this hard-coded mapping.
                    if llm_config.engine in [
                        "azure",
                        "openai",
                        "gooseai",
                        "nlpcloud",
                        "petals",
                    ]:
                        kwargs["model_name"] = llm_config.model
                    else:
                        # The `__fields__` attribute is computed dynamically by pydantic.
                        if "model" in provider_cls.__fields__:
                            kwargs["model"] = llm_config.model

                if llm_config.type == "main" or len(self.config.models) == 1:
                    self.llm = provider_cls(**kwargs)
                    self.runtime.register_action_param("llm", self.llm)
                else:
                    model_name = f"{llm_config.type}_llm"
                    setattr(self, model_name, provider_cls(**kwargs))
                    self.runtime.register_action_param(
                        model_name, getattr(self, model_name)
                    )

    def _get_embeddings_search_provider_instance(
        self, esp_config: Optional[EmbeddingSearchProvider] = None
    ) -> EmbeddingsIndex:
        if esp_config is None:
            esp_config = EmbeddingSearchProvider()

        if esp_config.name == "default":
            from nemoguardrails.embeddings.basic import BasicEmbeddingsIndex

            return BasicEmbeddingsIndex(
                embedding_model=esp_config.parameters.get(
                    "embedding_model", self.default_embedding_model
                ),
                embedding_engine=esp_config.parameters.get(
                    "embedding_engine", self.default_embedding_engine
                ),
            )
        else:
            if esp_config.name not in self.embedding_search_providers:
                raise Exception(f"Unknown embedding search provider: {esp_config.name}")
            else:
                kwargs = esp_config.parameters
                return self.embedding_search_providers[esp_config.name](**kwargs)

    def _get_events_for_messages(self, messages: List[dict]):
        """Return the list of events corresponding to the provided messages.

        Tries to find a prefix of messages for which we have already a list of events
        in the cache. For the rest, they are converted as is.

        The reason this cache exists is that we want to benefit from events generated in
        previous turns, which can't be computed again because it would be expensive (e.g.,
        involving multiple LLM calls).

        When an explicit state object will be added, this mechanism can be removed.

        Args:
            messages: The list of messages.

        Returns:
            A list of events.
        """
        events = []

        # We try to find the longest prefix of messages for which we have a cache
        # of events.
        p = len(messages) - 1
        while p > 0:
            cache_key = get_history_cache_key(messages[0:p])
            if cache_key in self.events_history_cache:
                events = self.events_history_cache[cache_key].copy()
                break

            p -= 1

        # For the rest of the messages, we transform them directly into events.
        # TODO: Move this to separate function once more types of messages are supported.
        for msg in messages[p:]:
            if msg["role"] == "user":
                events.append(
                    {
                        "type": "UtteranceUserActionFinished",
                        "final_transcript": msg["content"],
                    }
                )
            elif msg["role"] == "assistant":
                events.append(
                    {"type": "StartUtteranceBotAction", "script": msg["content"]}
                )
            elif msg["role"] == "context":
                events.append({"type": "ContextUpdate", "data": msg["content"]})
            elif msg["role"] == "event":
                events.append(msg["event"])

        return events

    async def generate_async(
        self, prompt: Optional[str] = None, messages: Optional[List[dict]] = None
    ) -> Union[str, dict]:
        """Generate a completion or a next message.

        The format for messages is the following:

        ```python
            [
                {"role": "context", "content": {"user_name": "John"}},
                {"role": "user", "content": "Hello! How are you?"},
                {"role": "assistant", "content": "I am fine, thank you!"},
                {"role": "event", "event": {"type": "UserSilent"}},
                ...
            ]
        ```

        Args:
            prompt: The prompt to be used for completion.
            messages: The history of messages to be used to generate the next message.

        Returns:
            The completion (when a prompt is provided) or the next message.

        System messages are not yet supported."""
        if prompt is not None:
            # Currently, we transform the prompt request into a single turn conversation
            new_message = await self.generate_async(
                messages=[{"role": "user", "content": prompt}]
            )

            assert new_message["role"] == "assistant"
            return new_message["content"]

        # TODO: Add support to load back history of events, next to history of messages
        #   This is important as without it, the LLM prediction is not as good.

        t0 = time.time()
        llm_stats.reset()

        # The array of events corresponding to the provided sequence of messages.
        events = self._get_events_for_messages(messages)

        # Compute the new events.
        new_events = await self.runtime.generate_events(events)

        # Extract and join all the messages from StartUtteranceBotAction events as the response.
        responses = []
        for event in new_events:
            if event["type"] == "StartUtteranceBotAction":
                # Check if we need to remove a message
                if event["script"] == "(remove last message)":
                    responses = responses[0:-1]
                else:
                    responses.append(event["script"])

        new_message = {"role": "assistant", "content": "\n".join(responses)}

        # Save the new events in the history and update the cache
        events.extend(new_events)
        cache_key = get_history_cache_key(messages + [new_message])
        self.events_history_cache[cache_key] = events

        # If logging is enabled, we log the conversation
        # TODO: add support for logging flag
        if self.verbose:
            history = get_colang_history(events)
            log.info(f"Conversation history so far: \n{history}")

        log.info("--- :: Total processing took %.2f seconds." % (time.time() - t0))
        log.info("--- :: Stats: %s" % llm_stats)

        return new_message

    def generate(
        self, prompt: Optional[str] = None, messages: Optional[List[dict]] = None
    ):
        """Synchronous version of generate_async."""

        if check_sync_call_from_async_loop():
            raise RuntimeError(
                "You are using the sync `generate` inside async code. "
                "You should replace with `await generate_async(...)."
            )

        return asyncio.run(self.generate_async(prompt=prompt, messages=messages))

    async def generate_events_async(self, events: List[dict]) -> List[dict]:
        """Generate the next events based on the provided history.

        The format for events is the following:

        ```python
            [
                {"type": "...", ...},
                ...
            ]
        ```

        Args:
            events: The history of events to be used to generate the next events.

        Returns:
            The newly generate event(s).

        """
        t0 = time.time()
        llm_stats.reset()

        # Compute the new events.
        new_events = await self.runtime.generate_events(events)

        # If logging is enabled, we log the conversation
        # TODO: add support for logging flag
        if self.verbose:
            history = get_colang_history(events)
            log.info(f"Conversation history so far: \n{history}")

        log.info("--- :: Total processing took %.2f seconds." % (time.time() - t0))
        log.info("--- :: Stats: %s" % llm_stats)

        return new_events

    def generate_events(self, events: List[dict]) -> List[dict]:
        """Synchronous version of `LLMRails.generate_events_async`."""

        if check_sync_call_from_async_loop():
            raise RuntimeError(
                "You are using the sync `generate_events` inside async code. "
                "You should replace with `await generate_events_async(...)."
            )

        return asyncio.run(self.generate_events_async(events=events))

    def register_action(self, action: callable, name: Optional[str] = None):
        """Register a custom action for the rails configuration."""
        self.runtime.register_action(action, name)

    def register_action_param(self, name: str, value: Any):
        """Registers a custom action parameter."""
        self.runtime.register_action_param(name, value)

    def register_filter(self, filter_fn: callable, name: Optional[str] = None):
        """Register a custom filter for the rails configuration."""
        self.runtime.llm_task_manager.register_filter(filter_fn, name)

    def register_output_parser(self, output_parser: callable, name: str):
        """Register a custom output parser for the rails configuration."""
        self.runtime.llm_task_manager.register_output_parser(output_parser, name)

    def register_prompt_context(self, name: str, value_or_fn: Any):
        """Register a value to be included in the prompt context.

        :name: The name of the variable or function that will be used.
        :value_or_fn: The value or function that will be used to generate the value.
        """
        self.runtime.llm_task_manager.register_prompt_context(name, value_or_fn)

    def register_embedding_search_provider(
        self, name: str, cls: Type[EmbeddingsIndex]
    ) -> None:
        """Register a new embedding search provider.

        Args:
            name: The name of the embedding search provider that will be used.
            cls: The class that will be used to generate and search embedding
        """

        self.embedding_search_providers[name] = cls
