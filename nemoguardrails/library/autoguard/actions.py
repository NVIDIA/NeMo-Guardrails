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

import json
import logging
import os
from typing import Any, Dict, List, Optional

import aiohttp

from nemoguardrails.actions import action
from nemoguardrails.actions.actions import ActionResult
from nemoguardrails.kb.kb import KnowledgeBase
from nemoguardrails.llm.taskmanager import LLMTaskManager

log = logging.getLogger(__name__)

GUARDRAIL_RESPONSE_TEXT = {
    "confidential_detection": "Confidential Information violation",
    "gender_bias_detection": "Stereotypical bias",
    "harm_detection": "Potential harm to human",
    "text_toxicity_extraction": "Toxicity in text",
    "tonal_detection": "Negative tone",
    "racial_bias_detection": "Stereotypical bias",
    "jailbreak_detection": "Jailbreak attempt",
    "intellectual_property": "Intellectual property",
}

DEFAULT_CONFIG = {
    "pii_fast": {
        "mode": "OFF",
        "mask": False,
        "enabled_types": [
            "[BANK ACCOUNT NUMBER]",
            "[CREDIT CARD NUMBER]",
            "[DATE OF BIRTH]",
            "[DATE]",
            "[DRIVER LICENSE NUMBER]",
            "[EMAIL ADDRESS]",
            "[RACE/ETHNICITY]",
            "[GENDER]",
            "[IP ADDRESS]",
            "[LOCATION]",
            "[MONEY]",
            "[ORGANIZATION]",
            "[PASSPORT NUMBER]",
            "[PASSWORD]",
            "[PERSON NAME]",
            "[PHONE NUMBER]",
            "[PROFESSION]",
            "[SOCIAL SECURITY NUMBER]",
            "[USERNAME]",
            "[SECRET_KEY]",
            "[TRANSACTION_ID]",
            "[RELIGION]",
        ],
    },
    "confidential_detection": {"mode": "OFF"},
    "gender_bias_detection": {"mode": "OFF"},
    "harm_detection": {"mode": "OFF"},
    "text_toxicity_extraction": {"mode": "OFF"},
    "racial_bias_detection": {"mode": "OFF"},
    "tonal_detection": {"mode": "OFF"},
    "jailbreak_detection": {"mode": "OFF"},
    "intellectual_property": {"mode": "OFF"},
}


def process_autoguard_output(responses: List[Any]):
    """Processes the output provided AutoGuard API"""

    prefix = []
    suffix = []
    pii_response = ""
    output_str = ""
    suffix_str = ""
    for response in responses:
        if response["task"] == "text_toxicity_extraction":
            suffix += response["output_data"]

        if response["task"] == "pii_fast":
            pii_response = response["response"]
        else:
            prefix += [GUARDRAIL_RESPONSE_TEXT[response["task"]]]

    if len(prefix) > 0:
        output_str = (
            ", ".join(prefix) + " has been detected by AutoGuard; Sorry, can't process."
        )
    if len(suffix) > 0:
        suffix_str += " Toxic phrases: " + ", ".join(suffix)
    if len(pii_response) > 0:
        output_str = pii_response + "\n" + output_str
    return [output_str, suffix_str]


async def autoguard_infer(
    request_url: str,
    text: str,
    task_config: Optional[Dict[Any, Any]] = None,
):
    """Checks whether the given text passes through the applied guardrails."""
    api_key = os.environ.get("AUTOGUARD_API_KEY")
    if api_key is None:
        raise ValueError("AUTOGUARD_API_KEY environment variable not set.")

    headers = {"x-api-key": api_key}
    config = DEFAULT_CONFIG
    # enable the select guardrail
    for task in task_config.keys():
        if task != "factcheck":
            config[task]["mode"] = "DETECT"
        if task_config[task]:
            config[task].update(task_config[task])
    request_body = {"prompt": text, "config": config}

    guardrails_triggered = []

    async with aiohttp.ClientSession() as session:
        async with session.post(
            url=request_url,
            headers=headers,
            json=request_body,
        ) as response:
            if response.status != 200:
                raise ValueError(
                    f"AutoGuard call failed with status code {response.status}.\n"
                    f"Details: {await response.text()}"
                )
            async for line in response.content:
                line_text = line.strip()
                if len(line_text) > 0:
                    resp = json.loads(line_text)
                    if resp["guarded"]:
                        guardrails_triggered.append(resp)
            if len(guardrails_triggered) > 0:
                processed_response = process_autoguard_output(guardrails_triggered)
                return [True] + processed_response
    return False, None


async def autoguard_factcheck_infer(
    request_url: str,
    text: str,
    documents: List[str],
):
    """Checks the facts for the text using the given documents and provides a fact-checking score"""
    api_key = os.environ.get("AUTOGUARD_API_KEY")
    if api_key is None:
        raise ValueError("AUTOGUARD_API_KEY environment variable not set.")
    headers = {"x-api-key": api_key}
    request_body = {
        "prompt": text,
        "documents": documents,
    }
    async with aiohttp.ClientSession() as session:
        async with session.post(
            url=request_url,
            headers=headers,
            json=request_body,
        ) as response:
            if response.status != 200:
                raise ValueError(
                    f"AutoGuard call failed with status code {response.status}.\n"
                    f"Details: {await response.text()}"
                )
            async for line in response.content:
                resp = json.loads(line)
                if resp["task"] == "factcheck":
                    return float(resp["response"][17:])
    return 1.0


@action(name="autoguard_input_api")
async def autoguard_input_api(
    llm_task_manager: LLMTaskManager, context: Optional[dict] = None
):
    """Calls AutoGuard API for the user message and guardrail configuration provided"""
    user_message = context.get("user_message")
    autoguard_config = llm_task_manager.config.rails.config.autoguard
    autoguard_api_url = autoguard_config.parameters.get("endpoint")
    if not autoguard_api_url:
        raise ValueError("Provide the autoguard endpoint in the config")
    task_config = getattr(autoguard_config.input, "guardrails_config")
    if not task_config:
        raise ValueError("Provide the guardrails and their configuration")
    prompt = user_message

    return await autoguard_infer(autoguard_api_url, prompt, task_config)


@action(name="autoguard_output_api")
async def autoguard_output_api(
    llm_task_manager: LLMTaskManager, context: Optional[dict] = None
):
    """Calls AutoGuard API for the bot message and guardrail configuration provided"""
    bot_message = context.get("bot_message")
    autoguard_config = llm_task_manager.config.rails.config.autoguard
    autoguard_api_url = autoguard_config.parameters.get("endpoint")
    if not autoguard_api_url:
        raise ValueError("Provide the autoguard endpoint in the config")
    task_config = getattr(autoguard_config.output, "guardrails_config")
    if not task_config:
        raise ValueError("Provide the guardrails and their configuration")

    prompt = bot_message

    return await autoguard_infer(autoguard_api_url, prompt, task_config)


@action(name="autoguard_factcheck_input_api")
async def autoguard_factcheck_input_api(
    llm_task_manager: LLMTaskManager, context: Optional[dict] = None
):
    """Calls AutoGuard factcheck API and checks whether the user message is factually correct according to given
    documents"""

    user_message = context.get("user_message")
    documents = context.get("relevant_chunks", [])
    autoguard_config = llm_task_manager.config.rails.config.autoguard
    autoguard_fact_check_api_url = autoguard_config.parameters.get(
        "fact_check_endpoint"
    )
    if not autoguard_fact_check_api_url:
        raise ValueError("Provide the autoguard factcheck endpoint in the config")
    if isinstance(documents, str):
        documents = documents.split("\n")
    prompt = user_message
    if isinstance(documents, list) and len(documents) > 0:
        return await autoguard_factcheck_infer(
            autoguard_fact_check_api_url, prompt, documents
        )
    else:
        raise ValueError("Provide relevant documents in proper format")


@action(name="autoguard_factcheck_output_api")
async def autoguard_factcheck_output_api(
    llm_task_manager: LLMTaskManager, context: Optional[dict] = None
):
    """Calls AutoGuard factcheck API and checks whether the bot message is factually correct according to given
    documents"""

    bot_message = context.get("bot_message")
    documents = context.get("relevant_chunks", [])
    autoguard_config = llm_task_manager.config.rails.config.autoguard
    autoguard_fact_check_api_url = autoguard_config.parameters.get(
        "fact_check_endpoint"
    )
    if not autoguard_fact_check_api_url:
        raise ValueError("Provide the autoguard factcheck endpoint in the config")
    if isinstance(documents, str):
        documents = documents.split("\n")
    prompt = bot_message
    if isinstance(documents, list) and len(documents) > 0:
        return await autoguard_factcheck_infer(
            autoguard_fact_check_api_url, prompt, documents
        )
    else:
        raise ValueError("Provide relevant documents in proper format")


@action(name="autoguard_retrieve_relevant_chunks")
async def autoguard_retrieve_relevant_chunks(
    kb: Optional[KnowledgeBase] = None,
):
    """Retrieve knowledge chunks from knowledge base and update the context."""
    context_updates = {}
    chunks = [chunk["body"] for chunk in kb.chunks]

    context_updates["relevant_chunks"] = "\n".join(chunks)
    context_updates["relevant_chunks_sep"] = chunks

    return ActionResult(
        return_value=context_updates["relevant_chunks"],
        context_updates=context_updates,
    )
