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

from __future__ import annotations

from typing import Any, List, Optional

from langchain_core.language_models import BaseLanguageModel
from langchain_core.messages import AIMessage, HumanMessage
from langchain_core.prompt_values import ChatPromptValue
from langchain_core.runnables import Runnable
from langchain_core.runnables.config import RunnableConfig
from langchain_core.runnables.utils import Input, Output
from langchain_core.tools import Tool

from nemoguardrails import LLMRails, RailsConfig


class RunnableRails(Runnable[Input, Output]):
    def __init__(
        self,
        config: RailsConfig,
        llm: BaseLanguageModel,
        tools: Optional[List[Tool]] = None,
    ) -> None:
        self.rails = LLMRails(config=config, llm=llm)

        if tools:
            for tool in tools:
                self.rails.register_action(tool, tool.name)

    @property
    def InputType(self) -> Any:
        return Any

    @property
    def OutputType(self) -> Any:
        """The type of the output of this runnable as a type annotation."""
        return Any

    @staticmethod
    def _transform_input_to_rails_format(_input):
        if isinstance(_input, ChatPromptValue):
            messages = []
            for msg in _input.messages:
                if isinstance(msg, AIMessage):
                    messages.append({"role": "assistant", "content": msg.content})
                elif isinstance(msg, HumanMessage):
                    messages.append({"role": "user", "content": msg.content})
            return messages
        raise Exception(f"Can't handle input of type {type(_input).__name__}")

    def invoke(
        self,
        input: Input,
        config: Optional[RunnableConfig] = None,
        **kwargs: Optional[Any],
    ) -> Output:
        """Invoke this runnable synchronously."""
        input_messages = self._transform_input_to_rails_format(input)
        result = self.rails.generate(messages=input_messages)

        return AIMessage(content=result["content"])
