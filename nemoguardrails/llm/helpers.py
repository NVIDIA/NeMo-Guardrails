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

from typing import List, Optional, Type

from langchain.callbacks.manager import (
    AsyncCallbackManagerForLLMRun,
    CallbackManagerForLLMRun,
)
from langchain.llms.base import LLM


def get_llm_instance_wrapper(llm_instance: LLM, llm_type: str) -> Type[LLM]:
    """Wraps an LLM instance in a class that can be registered with LLMRails.

    This is useful to create specific types of LLMs using a generic LLM provider
    from HuggingFace, e.g., HuggingFacePipeline or HuggingFaceEndpoint.
    """

    class WrapperLLM(LLM):
        @property
        def model_kwargs(self):
            """Return the model's kwargs.

            These are needed to allow changes to the arguments of the LLM calls.
            """
            if hasattr(llm_instance, "model_kwargs"):
                return llm_instance.model_kwargs
            return {}

        @property
        def _llm_type(self) -> str:
            """Return type of llm.

            This type can be used to customize the prompts.
            """
            return llm_type

        def _call(
            self,
            prompt: str,
            stop: Optional[List[str]] = None,
            run_manager: Optional[CallbackManagerForLLMRun] = None,
        ) -> str:
            return llm_instance._call(prompt, stop, run_manager)

        async def _acall(
            self,
            prompt: str,
            stop: Optional[List[str]] = None,
            run_manager: Optional[AsyncCallbackManagerForLLMRun] = None,
        ) -> str:
            return await llm_instance._acall(prompt, stop, run_manager)

    return WrapperLLM
