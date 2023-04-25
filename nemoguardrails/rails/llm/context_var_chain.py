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

from typing import Any, Dict, List

from langchain import LLMChain, PromptTemplate
from pydantic import Extra, root_validator


class ContextVarChain(LLMChain):
    """Chain that always returns the value of a context variable.

    The context variable must be provided as input in a key that starts with "__context__".
    """

    var_name: str
    output_key: str = "value"
    prompt: Any = None
    llm: Any = None

    class Config:
        """Configuration for this pydantic object."""

        extra = Extra.forbid
        arbitrary_types_allowed = True

    @root_validator()
    def validate_all(cls, values: Dict) -> Dict:
        """Validate that prompt input variables are consistent."""
        _input = f"__context__{values['var_name']}"
        values["prompt"] = PromptTemplate(
            template="{" + _input + "}", input_variables=[_input]
        )

        return values

    @property
    def input_keys(self) -> List[str]:
        """Expect input key.

        :meta private:
        """
        return ["__context__" + self.var_name]

    @property
    def output_keys(self) -> List[str]:
        """Expect output key.

        :meta private:
        """
        return [self.output_key]

    def run(self, *args: Any, **kwargs: Any) -> str:
        value = kwargs.get(f"__context__{self.var_name}")
        return value

    async def arun(self, *args: Any, **kwargs: Any) -> str:
        return self.run(*args, **kwargs)

    @property
    def _chain_type(self) -> str:
        return "context__var_chain"
