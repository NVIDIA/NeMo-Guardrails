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
    """Checks if the bot response is appropriate and passes moderation."""

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
