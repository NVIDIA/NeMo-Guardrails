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

from nemoguardrails.actions.fact_checking import alignscore_request
from nemoguardrails.actions.llm.utils import llm_call
from nemoguardrails.llm.params import llm_params
from nemoguardrails.llm.taskmanager import LLMTaskManager
from nemoguardrails.llm.types import Task

log = logging.getLogger(__name__)


def _get_evidence_and_claim_from_context(context: Optional[dict] = None):
    """Extract the evidence and claim from the context."""
    evidence = context.get("relevant_chunks", [])
    response = context.get("last_bot_message")

    if response is None:
        raise Exception("No claim or context was provided to AlignScore.")

    return evidence, response


async def check_facts(
    llm_task_manager: LLMTaskManager,
    context: Optional[dict] = None,
    llm: Optional[BaseLLM] = None,
):
    """Checks the facts for the bot response."""
    if (
        llm_task_manager.config.custom_data["fact_checking"]["provider"]
        == "align_score"
    ):
        return await check_facts_align_score(llm_task_manager, context, llm)
    else:
        return await check_facts_ask_llm(llm_task_manager, context, llm)


async def check_facts_ask_llm(
    llm_task_manager: LLMTaskManager,
    context: Optional[dict] = None,
    llm: Optional[BaseLLM] = None,
):
    """Checks the facts for the bot response by appropriately prompting the base llm."""
    evidence, response = _get_evidence_and_claim_from_context(context)
    if not evidence:
        # If there is no evidence, we always return true
        return True

    prompt = llm_task_manager.render_task_prompt(
        task=Task.FACT_CHECKING,
        context={
            "evidence": evidence,
            "response": response,
        },
    )

    with llm_params(llm, temperature=0.0):
        entails = await llm_call(llm, prompt)

    entails = entails.lower().strip()
    result = float("yes" in entails)
    return result


async def check_facts_align_score(
    llm_task_manager: LLMTaskManager,
    context: Optional[dict] = None,
    llm: Optional[BaseLLM] = None,
):
    """Checks the facts for the bot response using an information alignment score."""
    fact_checking_config = llm_task_manager.config.custom_data["fact_checking"]

    alignscore_api_url = fact_checking_config["parameters"]["endpoint"]

    evidence, response = _get_evidence_and_claim_from_context(context)
    alignscore = await alignscore_request(alignscore_api_url, evidence, response)
    if alignscore is None:
        log.warning(
            "AlignScore endpoint not set up properly. Falling back to the ask_llm approach for fact-checking."
        )
        return await check_facts_ask_llm(llm_task_manager, context, llm)
    else:
        return alignscore
