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
from typing import Optional

from langchain.llms import BaseLLM

from nemoguardrails.actions import action
from nemoguardrails.library.llama_guard.request import llama_guard_request
from nemoguardrails.library.self_check.facts.actions import self_check_facts
from nemoguardrails.llm.taskmanager import LLMTaskManager
from nemoguardrails.llm.types import Task

log = logging.getLogger(__name__)


@action()
async def llama_guard_check_input(
    llm_task_manager: LLMTaskManager,
    context: Optional[dict] = None,
):
    """
    Assumes that a Llama Guard inference endpoint is running locally/on-prem.

    Checks user messages against safety guidelines using Llama Guard.
    Expects the prompt to contain the safety guidelines.
    """
    user_input = context.get("user_message")

    llama_guard_config = llm_task_manager.config.rails.config.llama_guard
    llama_guard_input_check_prompt = llm_task_manager.render_task_prompt(
        task=Task.LLAMA_GUARD_CHECK_INPUT,
        context={
            "user_input": user_input,
        },
    )
    # Testing shows the \n characters lead to inaccurate LLM predictions.
    llama_guard_input_check_prompt = llama_guard_input_check_prompt.replace(
        "\n", " "
    ).strip()
    llama_guard_api_url = llama_guard_config.parameters.get("endpoint")

    result = await llama_guard_request(
        llama_guard_input_check_prompt, api_url=llama_guard_api_url
    )
    if result is None:
        log.debug("DEBUG! Llama Guard API request failed.")
        return None

    log.info(f"Llama Guard input check: {result}.")
    if result.startswith("safe"):
        return True

    # TODO: If unsafe, extract the violated policy number and return it.
    elif result.startswith("unsafe"):
        return False

    log.warning(f"Unexpected Llama Guard response: {result}")
    return None


@action()
async def llama_guard_check_output(
    llm_task_manager: LLMTaskManager,
    context: Optional[dict] = None,
):
    """
    Assumes that a Llama Guard inference endpoint is running locally/on-prem.

    Checks bot messages against safety guidelines using Llama Guard.
    Expects the prompt to contain the safety guidelines.
    """
    user_input = context.get("user_message")
    bot_response = context.get("bot_message")

    llama_guard_config = llm_task_manager.config.rails.config.llama_guard
    llama_guard_output_check_prompt = llm_task_manager.render_task_prompt(
        task=Task.LLAMA_GUARD_CHECK_OUTPUT,
        context={
            "user_input": user_input,
            "bot_response": bot_response,
        },
    )
    # Testing shows the \n characters lead to inaccurate LLM predictions.
    llama_guard_output_check_prompt = llama_guard_output_check_prompt.replace(
        "\n", " "
    ).strip()
    llama_guard_api_url = llama_guard_config.parameters.get("endpoint")

    result = await llama_guard_request(
        llama_guard_output_check_prompt, api_url=llama_guard_api_url
    )
    if result is None:
        log.debug("DEBUG! Llama Guard API request failed.")
        return None

    log.info(f"Llama Guard output check: {result}.")
    if result.startswith("safe"):
        return True

    # TODO: If unsafe, extract the violated policy number and return it.
    elif result.startswith("unsafe"):
        return False

    log.warning(f"Unexpected Llama Guard response: {result}")
    return None
