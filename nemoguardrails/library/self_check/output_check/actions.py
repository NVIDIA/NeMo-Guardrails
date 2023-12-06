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

from langchain.llms.base import BaseLLM

from nemoguardrails.actions import action
from nemoguardrails.actions.llm.utils import llm_call
from nemoguardrails.context import llm_call_info_var
from nemoguardrails.llm.params import llm_params
from nemoguardrails.llm.taskmanager import LLMTaskManager
from nemoguardrails.llm.types import Task
from nemoguardrails.logging.explain import LLMCallInfo

log = logging.getLogger(__name__)


@action(is_system_action=True)
async def self_check_output(
    llm_task_manager: LLMTaskManager,
    context: Optional[dict] = None,
    llm: Optional[BaseLLM] = None,
):
    """Checks if the output from the bot.

    Prompt the LLM, using the `self_check_output` task prompt, to determine if the output
    from the bot should be allowed or not.

    The LLM call should return "yes" if the output is bad and should be blocked
    (this is consistent with self_check_input_prompt).

    Returns:
        True if the output should be allowed, False otherwise.
    """

    bot_response = context.get("bot_message")
    user_input = context.get("user_message")
    if bot_response:
        prompt = llm_task_manager.render_task_prompt(
            task=Task.SELF_CHECK_OUTPUT,
            context={
                "user_input": user_input,
                "bot_response": bot_response,
            },
        )

        # Initialize the LLMCallInfo object
        llm_call_info_var.set(LLMCallInfo(task=Task.SELF_CHECK_OUTPUT.value))

        with llm_params(llm, temperature=0.0):
            response = await llm_call(llm, prompt)

        response = response.lower().strip()
        log.info(f"Output self-checking result is: `{response}`.")

        if "yes" in response:
            return False

    return True
