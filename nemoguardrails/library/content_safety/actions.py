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
from typing import Dict, Optional

from langchain.llms.base import BaseLLM

from nemoguardrails.actions.actions import action
from nemoguardrails.actions.llm.utils import llm_call
from nemoguardrails.context import llm_call_info_var
from nemoguardrails.llm.params import llm_params
from nemoguardrails.llm.taskmanager import LLMTaskManager
from nemoguardrails.logging.explain import LLMCallInfo

log = logging.getLogger(__name__)


@action()
async def content_safety_check_input(
    llms: Dict[str, BaseLLM],
    llm_task_manager: LLMTaskManager,
    model_name: Optional[str] = None,
    context: Optional[dict] = None,
) -> dict:
    _MAX_TOKENS = 3
    user_input: str = ""

    if context is not None:
        user_input = context.get("user_message", "")
        model_name = context.get("model", None)

    if model_name is None:
        error_msg = (
            "Model name is required for content safety check, "
            "please provide it as an argument in the config.yml. "
            "e.g. content safety check input $model=llama_guard"
        )
        raise ValueError(error_msg)

    llm = llms.get(model_name, None)

    if llm is None:
        error_msg = (
            f"Model {model_name} not found in the list of available models for content safety check. "
            "Please provide a valid model name."
        )
        raise ValueError(error_msg)

    task = f"content_safety_check_input $model={model_name}"

    check_input_prompt = llm_task_manager.render_task_prompt(
        task=task,
        context={
            "user_input": user_input,
        },
    )

    stop = llm_task_manager.get_stop_tokens(task=task)
    max_tokens = llm_task_manager.get_max_tokens(task=task)

    llm_call_info_var.set(LLMCallInfo(task=task))

    max_tokens = max_tokens or _MAX_TOKENS

    with llm_params(llm, temperature=1e-20, max_tokens=max_tokens):
        result = await llm_call(llm, check_input_prompt, stop=stop)

    result = llm_task_manager.parse_task_output(task, output=result)

    try:
        is_safe, violated_policies = result
    # in case the result is single value
    except TypeError:
        is_safe = result
        violated_policies = []

    return {"allowed": is_safe, "policy_violations": violated_policies}


@action()
async def content_safety_check_output(
    llms: Dict[str, BaseLLM],
    llm_task_manager: LLMTaskManager,
    model_name: Optional[str] = None,
    context: Optional[dict] = None,
) -> dict:
    _MAX_TOKENS = 3
    user_input: str = ""
    bot_response: str = ""

    if context is not None:
        user_input = context.get("user_message", "")
        bot_response = context.get("bot_message", "")
        model_name = context.get("model", None)

    if model_name is None:
        error_msg = (
            "Model name is required for content safety check, "
            "please provide it as an argument in the config.yml. "
            "e.g. flow content safety (model_name='llama_guard')"
        )
        raise ValueError(error_msg)

    llm = llms.get(model_name, None)

    if llm is None:
        error_msg = (
            f"Model {model_name} not found in the list of available models for content safety check. "
            "Please provide a valid model name."
        )
        raise ValueError(error_msg)

    task = f"content_safety_check_output $model={model_name}"

    check_output_prompt = llm_task_manager.render_task_prompt(
        task=task,
        context={
            "user_input": user_input,
            "bot_response": bot_response,
        },
    )
    stop = llm_task_manager.get_stop_tokens(task=task)
    max_tokens = llm_task_manager.get_max_tokens(task=task)

    max_tokens = max_tokens or _MAX_TOKENS

    llm_call_info_var.set(LLMCallInfo(task=task))

    with llm_params(llm, temperature=1e-20, max_tokens=max_tokens):
        result = await llm_call(llm, check_output_prompt, stop=stop)

    result = llm_task_manager.parse_task_output(task, output=result)

    try:
        is_safe, violated_policies = result
    except TypeError:
        is_safe = result
        violated_policies = []

    return {"allowed": is_safe, "policy_violations": violated_policies}
