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
import re
from typing import List, Optional, Tuple, Union

from langchain.llms.base import BaseLLM

from nemoguardrails.actions import action
from nemoguardrails.actions.llm.utils import llm_call
from nemoguardrails.context import llm_call_info_var
from nemoguardrails.llm.params import llm_params
from nemoguardrails.llm.taskmanager import LLMTaskManager
from nemoguardrails.llm.types import Task
from nemoguardrails.logging.explain import LLMCallInfo

log = logging.getLogger(__name__)


def parse_patronus_lynx_response(
    response: str,
) -> Tuple[bool, Union[List[str], None]]:
    """
    Parses the response from the Patronus Lynx LLM and returns a tuple of:
    - Whether the response is hallucinated or not.
    - A reasoning trace explaining the decision.
    """
    log.info(f"Patronus Lynx response: {response}.")
    # Default to hallucinated
    hallucination, reasoning = True, None
    reasoning_pattern = r'"REASONING":\s*\[(.*?)\]'
    score_pattern = r'"SCORE":\s*"?\b(PASS|FAIL)\b"?'

    reasoning_match = re.search(reasoning_pattern, response, re.DOTALL)
    score_match = re.search(score_pattern, response)

    if score_match:
        score = score_match.group(1)
        if score == "PASS":
            hallucination = False
    if reasoning_match:
        reasoning_content = reasoning_match.group(1)
        reasoning = re.split(r"['\"],\s*['\"]", reasoning_content)

    return hallucination, reasoning


@action()
async def patronus_lynx_check_output_hallucination(
    llm_task_manager: LLMTaskManager,
    context: Optional[dict] = None,
    patronus_lynx_llm: Optional[BaseLLM] = None,
) -> dict:
    """
    Check the bot response for hallucinations based on the given chunks
    using the configured Patronus Lynx model.
    """
    user_input = context.get("user_message")
    bot_response = context.get("bot_message")
    provided_context = context.get("relevant_chunks")

    if (
        not provided_context
        or not isinstance(provided_context, str)
        or not provided_context.strip()
    ):
        log.error(
            "Could not run Patronus Lynx. `relevant_chunks` must be passed as a non-empty string."
        )
        return {"hallucination": False, "reasoning": None}

    check_output_hallucination_prompt = llm_task_manager.render_task_prompt(
        task=Task.PATRONUS_LYNX_CHECK_OUTPUT_HALLUCINATION,
        context={
            "user_input": user_input,
            "bot_response": bot_response,
            "provided_context": provided_context,
        },
    )

    stop = llm_task_manager.get_stop_tokens(
        task=Task.PATRONUS_LYNX_CHECK_OUTPUT_HALLUCINATION
    )

    # Initialize the LLMCallInfo object
    llm_call_info_var.set(
        LLMCallInfo(task=Task.PATRONUS_LYNX_CHECK_OUTPUT_HALLUCINATION.value)
    )

    with llm_params(patronus_lynx_llm, temperature=0.0):
        result = await llm_call(
            patronus_lynx_llm, check_output_hallucination_prompt, stop=stop
        )

    hallucination, reasoning = parse_patronus_lynx_response(result)
    print(f"Hallucination: {hallucination}, Reasoning: {reasoning}")
    return {"hallucination": hallucination, "reasoning": reasoning}
