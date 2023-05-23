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

from nemoguardrails.actions import action
from nemoguardrails.llm.params import llm_params
from nemoguardrails.llm.prompts import Task, get_prompt
from nemoguardrails.logging.callbacks import logging_callbacks
from nemoguardrails.rails.llm.config import RailsConfig

log = logging.getLogger(__name__)


@action(is_system_action=True)
async def output_moderation(
    context: Optional[dict] = None,
    llm: Optional[BaseLLM] = None,
    config: Optional[RailsConfig] = None,
):
    """Checks if the bot response is appropriate and passes moderation."""

    bot_response = context.get("last_bot_message")
    if bot_response:
        output_moderation_template = get_prompt(config, Task.OUTPUT_MODERATION).content

        prompt = PromptTemplate(
            template=output_moderation_template, input_variables=["bot_response"]
        )

        output_moderation_chain = LLMChain(prompt=prompt, llm=llm)

        with llm_params(llm, temperature=0):
            check = await output_moderation_chain.apredict(
                callbacks=logging_callbacks, bot_response=bot_response
            )

        check = check.lower().strip()
        log.info(f"Output moderation check result is {check}.")

        if "no" in check:
            return False
    return True
