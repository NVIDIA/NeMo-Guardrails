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

"""Module that exposes all the supported LLM providers.

Currently, this module automatically discovers all the LLM providers available in LangChain
and registers them.

Additional providers can be registered using the `register_llm_provider` function.
"""
import logging
from typing import Any, Dict, List, Optional, Type

from langchain import llms
from langchain.base_language import BaseLanguageModel
from langchain.callbacks.manager import CallbackManagerForLLMRun
from langchain.chat_models import ChatOpenAI
from langchain.llms.base import LLM
from langchain.llms.huggingface_pipeline import HuggingFacePipeline

from nemoguardrails.rails.llm.config import Model

from .nemollm import NeMoLLM
from .trtllm.llm import TRTLLM

log = logging.getLogger(__name__)

# Initialize the providers with the default ones, for now only NeMo LLM.
_providers: Dict[str, Type[BaseLanguageModel]] = {"nemollm": NeMoLLM, "trt_llm": TRTLLM}


class HuggingFacePipelineCompatible(HuggingFacePipeline):
    """
    Hackish way to add backward-compatibility functions to the Langchain class.
    TODO: Planning to add this fix directly to Langchain repo.
    """

    def _call(
        self,
        prompt: str,
        stop: Optional[List[str]] = None,
        run_manager: Optional[CallbackManagerForLLMRun] = None,
        **kwargs: Any,
    ) -> str:
        """
        Hackish way to perform a single llm call since Langchain dropped support
        """
        if not isinstance(prompt, str):
            raise ValueError(
                "Argument `prompt` is expected to be a string. Instead found "
                f"{type(prompt)}. If you want to run the LLM on multiple prompts, use "
                "`generate` instead."
            )
        llm_result = self._generate(
            [prompt],
            stop=stop,
            run_manager=run_manager,
            **kwargs,
        )
        return llm_result.generations[0][0].text

    async def _acall(
        self,
        prompt: str,
        stop: Optional[List[str]] = None,
        run_manager: Optional[CallbackManagerForLLMRun] = None,
        **kwargs: Any,
    ) -> str:
        """
        Hackish way to add async support
        """
        if not isinstance(prompt, str):
            raise ValueError(
                "Argument `prompt` is expected to be a string. Instead found "
                f"{type(prompt)}. If you want to run the LLM on multiple prompts, use "
                "`generate` instead."
            )
        llm_result = await self._agenerate(
            [prompt],
            stop=stop,
            run_manager=run_manager,
            **kwargs,
        )
        return llm_result.generations[0][0].text


async def _acall(self, *args, **kwargs):
    """Hackish way to add async support to LLM providers that don't have it.

    We just call the sync version of the function.
    """
    # TODO: run this in a thread pool!
    return self._call(*args, **kwargs)


def discover_langchain_providers():
    """Automatically discover all LLM providers from LangChain."""
    _providers.update(llms.type_to_cls_dict)

    # We also do some monkey patching to make sure that all LLM providers have async support
    for provider_cls in _providers.values():
        # If the "_acall" method is not defined, we add it.
        if issubclass(provider_cls, LLM) and "_acall" not in provider_cls.__dict__:
            log.debug("Adding async support to %s", provider_cls.__name__)
            provider_cls._acall = _acall


# Discover all the additional providers from LangChain
discover_langchain_providers()


def register_llm_provider(name: str, provider_cls: Type[BaseLanguageModel]):
    """Register an additional LLM provider."""
    _providers[name] = provider_cls


def get_llm_provider(model_config: Model) -> Type[BaseLanguageModel]:
    if model_config.engine not in _providers:
        raise RuntimeError(f"Could not find LLM provider '{model_config.engine}'")

    # For OpenAI, we use a different provider depending on whether it's a chat model or not
    if (
        model_config.engine == "openai"
        and ("gpt-3.5" in model_config.model or "gpt-4" in model_config.model)
        and "instruct" not in model_config.model
    ):
        return ChatOpenAI
    else:
        return _providers[model_config.engine]


def get_llm_provider_names() -> List[str]:
    """Returns the list of supported LLM providers."""
    return list(sorted(list(_providers.keys())))
