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

import sys

from nemoguardrails.llm.providers import register_llm_provider

# adding current to the system path
sys.path.append("/workspace/NeMo-Guardrails/nemoguardrails/examples/hf_dolly")
# from .dolly import HFDollyLLM

from typing import Optional

from langchain import HuggingFacePipeline
from langchain.base_language import BaseLanguageModel
from langchain.llms.base import LLM


# below class is inspired from https://github.com/databrickslabs/dolly/blob/master/examples/langchain.py#L57
class HFDollyLLM(LLM):
    """A HuggingFace LLM."""

    llm: Optional[BaseLanguageModel] = None

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # self.name = 'HF Dolly 3B'
        repo_id = "databricks/dolly-v2-3b"
        temperature = 0
        params = {"temperature": temperature, "max_length": 1024}

        self.llm = HuggingFacePipeline.from_model_id(
            model_id=repo_id, device=0, task="text-generation", model_kwargs=params
        )

    @property
    def _llm_type(self) -> str:
        """Return type of llm."""
        return "hf_dolly"

    def _call(self, prompt, stop, run_manager) -> str:
        return self.llm._call(prompt, stop, run_manager)

    async def _acall(self, prompt, stop, run_manager) -> str:
        return await self.llm._acall(prompt, stop, run_manager)


register_llm_provider("hf_dolly", HFDollyLLM)
