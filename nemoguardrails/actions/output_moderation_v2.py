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
from nemoguardrails.llm.params import llm_params
from nemoguardrails.llm.taskmanager import LLMTaskManager
from nemoguardrails.llm.types import Task

log = logging.getLogger(__name__)


@action(is_system_action=True)
async def output_moderation_v2(
    llm_task_manager: LLMTaskManager,
    context: Optional[dict] = None,
    llm: Optional[BaseLLM] = None,
):
    """
    Checks if the bot's response is appropriate and passes content moderation.

    Args:
        llm_task_manager (LLMTaskManager): An instance of the Language Model Task Manager.
        context (Optional[dict], optional): A dictionary containing relevant context information.
            Defaults to None.
        llm (Optional[BaseLLM], optional): An instance of the Base Language Model. Defaults to None.

    Returns:
        bool: True if the bot's response is deemed appropriate, False otherwise.

    Note:
        This action checks the bot's response to ensure it meets content moderation criteria.
        If the response is flagged as inappropriate, it returns False.

    Example:
        ```python
        bot_response = "I'm sorry, I can't assist with that."
        user_input = "Tell me a joke."

        result = await output_moderation_v2(llm_task_manager, {"last_user_message": user_input, "last_bot_message": bot_response}, llm)

        # The result will be True if the response is considered appropriate, otherwise, it will be False.
        ```
    """
    bot_response = context.get("last_bot_message")
    user_input = context.get("last_user_message")
    if bot_response:
        prompt = llm_task_manager.render_task_prompt(
            task=Task.OUTPUT_MODERATION_V2,
            context={
                "user_input": user_input,
                "bot_response": bot_response,
            },
        )

        with llm_params(llm, temperature=0.0):
            check = await llm_call(llm, prompt)

        check = check.lower().strip()
        log.info(f"Output moderation check result is {check}.")

        if "yes" in check:
            return False

    return True
