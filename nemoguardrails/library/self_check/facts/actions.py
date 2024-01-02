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

from typing import Optional

from langchain.llms import BaseLLM

from nemoguardrails.actions import action
from nemoguardrails.actions.llm.utils import llm_call
from nemoguardrails.context import llm_call_info_var
from nemoguardrails.llm.params import llm_params
from nemoguardrails.llm.taskmanager import LLMTaskManager
from nemoguardrails.llm.types import Task
from nemoguardrails.logging.explain import LLMCallInfo


@action()
async def self_check_facts(
    llm_task_manager: LLMTaskManager,
    context: Optional[dict] = None,
    llm: Optional[BaseLLM] = None,
):
    """Checks the facts for the bot response by appropriately prompting the base llm."""
    evidence = context.get("relevant_chunks", [])
    response = context.get("bot_message")

    if not evidence:
        # If there is no evidence, we always return true
        return True

    prompt = llm_task_manager.render_task_prompt(
        task=Task.SELF_CHECK_FACTS,
        context={
            "evidence": evidence,
            "response": response,
        },
    )

    # Initialize the LLMCallInfo object
    llm_call_info_var.set(LLMCallInfo(task=Task.SELF_CHECK_FACTS.value))

    with llm_params(llm, temperature=0.0):
        entails = await llm_call(llm, prompt)

    entails = entails.lower().strip()

    # Return 1.0 if LLM response is "yes", otherwise 0.0.
    result = float("yes" in entails)
    return result
