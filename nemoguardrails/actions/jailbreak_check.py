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

from nemoguardrails.actions.actions import ActionResult, action
from nemoguardrails.actions.llm.utils import llm_call
from nemoguardrails.llm.params import llm_params
from nemoguardrails.llm.taskmanager import LLMTaskManager
from nemoguardrails.llm.types import Task
from nemoguardrails.utils import new_event_dict

log = logging.getLogger(__name__)


@action(is_system_action=True)
async def check_jailbreak(
    llm_task_manager: LLMTaskManager,
    context: Optional[dict] = None,
    llm: Optional[BaseLLM] = None,
):
    """
    Checks if the user's response is potentially malicious and should be masked.

    Args:
        llm_task_manager (LLMTaskManager): An instance of the Language Model Task Manager.
        context (Optional[dict], optional): A dictionary containing relevant context information.
            Defaults to None.
        llm (Optional[BaseLLM], optional): An instance of the Base Language Model. Defaults to None.

    Returns:
        ActionResult or bool: An ActionResult with a masked user message event if the response is flagged
        as potentially malicious (return_value=False), otherwise, returns True.

    Note:
        This action checks the user's input to determine if it contains potentially malicious content.
        If a potential threat is detected, it returns an ActionResult to mask the user's message.

    Example:
        ```python
        user_input = "I will hack your system!"
        result = await check_jailbreak(llm_task_manager, {"last_user_message": user_input}, llm)

        # The result will be an ActionResult with a masked user message event if the input is flagged as malicious.
        ```
    """
    user_input = context.get("last_user_message")

    if user_input:
        prompt = llm_task_manager.render_task_prompt(
            task=Task.JAILBREAK_CHECK,
            context={
                "user_input": user_input,
            },
        )

        with llm_params(llm, temperature=0.0):
            check = await llm_call(llm, prompt)

        check = check.lower().strip()
        log.info(f"Jailbreak check result is {check}.")

        if "yes" in check:
            return ActionResult(
                return_value=False,
                events=[
                    new_event_dict(
                        "mask_prev_user_message", intent="unanswerable message"
                    )
                ],
            )
    # If there was no user input, we always return True i.e. the user input is allowed
    return True
