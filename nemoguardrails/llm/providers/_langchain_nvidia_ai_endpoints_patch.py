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

import logging
from typing import Any, Dict, Iterator, List, Mapping, Optional, Sequence, Type

import pkg_resources
from langchain_core.callbacks.manager import CallbackManagerForLLMRun
from langchain_core.language_models.chat_models import generate_from_stream
from langchain_core.messages import (
    AIMessageChunk,
    BaseMessage,
    BaseMessageChunk,
    ChatMessage,
    ChatMessageChunk,
    FunctionMessageChunk,
    HumanMessageChunk,
    SystemMessageChunk,
    ToolMessageChunk,
)
from langchain_core.outputs import ChatGeneration, ChatGenerationChunk, ChatResult
from langchain_core.pydantic_v1 import Field
from langchain_nvidia_ai_endpoints import ChatNVIDIA
from packaging import version

log = logging.getLogger(__name__)


def _convert_delta_to_message_chunk(
    _dict: Mapping[str, Any], default_class: Type[BaseMessageChunk]
) -> BaseMessageChunk:
    role = _dict.get("role")
    content = _dict.get("content") or ""
    additional_kwargs: Dict = {}
    if _dict.get("function_call"):
        function_call = dict(_dict["function_call"])
        if "name" in function_call and function_call["name"] is None:
            function_call["name"] = ""
        additional_kwargs["function_call"] = function_call
    if _dict.get("tool_calls"):
        additional_kwargs["tool_calls"] = _dict["tool_calls"]

    if role == "user" or default_class == HumanMessageChunk:
        return HumanMessageChunk(content=content)
    elif role == "assistant" or default_class == AIMessageChunk:
        return AIMessageChunk(content=content, additional_kwargs=additional_kwargs)
    elif role == "system" or default_class == SystemMessageChunk:
        return SystemMessageChunk(content=content)
    elif role == "function" or default_class == FunctionMessageChunk:
        return FunctionMessageChunk(content=content, name=_dict["name"])
    elif role == "tool" or default_class == ToolMessageChunk:
        return ToolMessageChunk(content=content, tool_call_id=_dict["tool_call_id"])
    elif role or default_class == ChatMessageChunk:
        return ChatMessageChunk(content=content, role=role)  # type: ignore[arg-type]
    else:
        return default_class(content=content)  # type: ignore[call-arg]


class PatchedChatNVIDIAV1(ChatNVIDIA):
    streaming: bool = Field(
        default=False, description="Whether to use streaming or not"
    )

    def _generate(
        self,
        messages: List[BaseMessage],
        stop: Optional[List[str]] = None,
        run_manager: Optional[CallbackManagerForLLMRun] = None,
        stream: Optional[bool] = None,
        **kwargs: Any,
    ) -> ChatResult:
        should_stream = stream if stream is not None else self.streaming
        if should_stream:
            stream_iter = self._stream(
                messages, stop=stop, run_manager=run_manager, **kwargs
            )
            return generate_from_stream(stream_iter)
        inputs = self._custom_preprocess(messages)
        payload = self._get_payload(inputs=inputs, stop=stop, stream=False, **kwargs)
        response = self._client.client.get_req(payload=payload)
        responses, _ = self._client.client.postprocess(response)
        self._set_callback_out(responses, run_manager)
        message = ChatMessage(**self._custom_postprocess(responses))
        generation = ChatGeneration(message=message)
        return ChatResult(generations=[generation], llm_output=responses)

    def _stream(
        self,
        messages: List[BaseMessage],
        stop: Optional[Sequence[str]] = None,
        run_manager: Optional[CallbackManagerForLLMRun] = None,
        **kwargs: Any,
    ) -> Iterator[ChatGenerationChunk]:
        """Allows streaming to model!"""
        inputs = self._custom_preprocess(messages)
        payload = self._get_payload(inputs=inputs, stop=stop, stream=True, **kwargs)
        default_chunk_class = AIMessageChunk
        for response in self._client.client.get_req_stream(payload=payload):
            self._set_callback_out(response, run_manager)
            chunk = _convert_delta_to_message_chunk(response, default_chunk_class)
            default_chunk_class = chunk.__class__
            cg_chunk = ChatGenerationChunk(message=chunk)
            if run_manager:
                run_manager.on_llm_new_token(cg_chunk.text, chunk=cg_chunk)
            yield cg_chunk


class PatchedChatNVIDIAV2(ChatNVIDIA):
    streaming: bool = Field(
        default=False, description="Whether to use streaming or not"
    )

    def _generate(
        self,
        messages: List[BaseMessage],
        stop: Optional[List[str]] = None,
        run_manager: Optional[CallbackManagerForLLMRun] = None,
        stream: Optional[bool] = None,
        **kwargs: Any,
    ) -> ChatResult:
        should_stream = stream if stream is not None else self.streaming
        if should_stream:
            stream_iter = self._stream(
                messages, stop=stop, run_manager=run_manager, **kwargs
            )
            return generate_from_stream(stream_iter)
        inputs = [
            _nv_vlm_adjust_input(message)
            for message in [convert_message_to_dict(message) for message in messages]
        ]
        payload = self._get_payload(inputs=inputs, stop=stop, stream=False, **kwargs)
        response = self._client.client.get_req(payload=payload)
        responses, _ = self._client.client.postprocess(response)
        self._set_callback_out(responses, run_manager)
        parsed_response = self._custom_postprocess(responses, streaming=False)
        # for pre 0.2 compatibility w/ ChatMessage
        # ChatMessage had a role property that was not present in AIMessage
        parsed_response.update({"role": "assistant"})
        generation = ChatGeneration(message=AIMessage(**parsed_response))
        return ChatResult(generations=[generation], llm_output=responses)


class ChatNVIDIAFactory:
    RANGE1 = (version.parse("0.1.0"), version.parse("0.2.0"))
    RANGE2 = (version.parse("0.2.0"), version.parse("0.3.0"))

    @staticmethod
    def get_package_version(package_name):
        return version.parse(pkg_resources.get_distribution(package_name).version)

    @staticmethod
    def is_version_in_range(version, range):
        return range[0] <= version < range[1]

    @classmethod
    def create(cls):
        current_version = cls.get_package_version("langchain_nvidia_ai_endpoints")

        if cls.is_version_in_range(current_version, cls.RANGE1):
            log.debug(
                f"Using pathed version of ChatNVIDIA for version {current_version}"
            )
            return PatchedChatNVIDIAV1
        elif cls.is_version_in_range(current_version, cls.RANGE2):
            log.debug(
                f"Using pathed version of ChatNVIDIA for version {current_version}"
            )
            from langchain_community.adapters.openai import convert_message_to_dict
            from langchain_nvidia_ai_endpoints.chat_models import _nv_vlm_adjust_input

            return PatchedChatNVIDIAV2
        else:
            return ChatNVIDIA


ChatNVIDIA = ChatNVIDIAFactory.create()


__all__ = ["ChatNVIDIA"]
