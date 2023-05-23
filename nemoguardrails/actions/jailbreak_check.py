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

from langchain import LLMChain, PromptTemplate
from langchain.llms.base import BaseLLM

from nemoguardrails.actions.actions import ActionResult, action
from nemoguardrails.llm.params import llm_params
from nemoguardrails.llm.prompts import Task, get_prompt
from nemoguardrails.logging.callbacks import logging_callbacks
from nemoguardrails.rails.llm.config import RailsConfig

log = logging.getLogger(__name__)


@action(is_system_action=True)
async def check_jailbreak(
    context: Optional[dict] = None,
    llm: Optional[BaseLLM] = None,
    config: Optional[RailsConfig] = None,
):
    """Checks if the user response is malicious and should be masked."""

    user_input = context.get("last_user_message")

    if user_input:
        jailbreak_check_template = get_prompt(config, Task.JAILBREAK_CHECK).content

        prompt = PromptTemplate(
            template=jailbreak_check_template, input_variables=["user_input"]
        )

        jailbreak_check_chain = LLMChain(prompt=prompt, llm=llm)

        with llm_params(llm, temperature=0):
            check = await jailbreak_check_chain.apredict(
                callbacks=logging_callbacks, user_input=user_input
            )

        check = check.lower().strip()
        log.info(f"Jailbreak check result is {check}.")

        if "yes" in check:
            return ActionResult(
                return_value=False,
                events=[
                    {"type": "mask_prev_user_message", "intent": "unanswerable message"}
                ],
            )
    # If there was no user input, we always return True i.e. the user input is allowed
    return True
