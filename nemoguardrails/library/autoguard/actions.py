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
import asyncio
import json
import logging
import os
from typing import Any, Dict, List, Optional

import aiohttp

from nemoguardrails.actions import action
from nemoguardrails.llm.taskmanager import LLMTaskManager

log = logging.getLogger(__name__)

GUARDRAIL_RESPONSE_TEXT = {
    "confidential_detection": "Confidential Information violation has been detected by AutoGuard; Sorry, can't process.",
    "gender_bias_detection": "Gender bias in text has been detected by AutoGuard; Sorry, can't process.",
    "harm_detection": "Harm to human violation has been detected by AutoGuard; Sorry, can't process.",
    "text_toxicity_extraction": "Toxicity in text has been detected by AutoGuard; Sorry, can't process.",
    "tonal_detection": "Negative tone in text has been detected by AutoGuard; Sorry, can't process.",
    "racial_bias_detection": "Racial bias in text has been detected by AutoGuard; Sorry, can't process.",
    "jailbreak_detection": "Jailbreak attempt has been detected by AutoGuard; Sorry, can't process.",
    "factcheck": "Factcheck violation in text has been detected by AutoGuard; Sorry, can't process.",
}

DEFAULT_CONFIG = {
    "pii_fast": {
        "mode": "OFF",
        "mask": False,
        "coreference": False,
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


def process_autoguard_output(response: Any):
    """Processes the output provided AutoGuard API"""
    if response["task"] == "text_toxicity_extraction":
        output_str = (
            GUARDRAIL_RESPONSE_TEXT[response["task"]]
            + " Toxic phrases: "
            + " ".join(response["output_data"])
        )
    else:
        output_str = GUARDRAIL_RESPONSE_TEXT[response["task"]]
    return output_str


async def autoguard_infer(
    request_url: str,
    text: str,
    tasks: List[str],
    matching_scores: Dict[str, Dict[str, float]],
    task_config: Optional[Dict[Any, Any]] = None,
):
    """Checks whether the given text passes through the applied guardrails."""
    api_key = os.environ.get("AUTOGUARD_API_KEY")
    if api_key is None:
        raise ValueError("AUTOGUARD_API_KEY environment variable not set.")

    headers = {"x-api-key": api_key}
    config = DEFAULT_CONFIG
    # enable the select guardrail
    for task in tasks:
        if task not in ["text_toxicity_extraction", "pii_fast", "factcheck"]:
            config[task] = {"mode": "DETECT"}
            if matching_scores:
                config[task]["matching_scores"] = matching_scores.get(task, {})
        if task_config:
            config[task].update(task_config)
    request_body = {"prompt": text, "config": config}

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
                        return True, GUARDRAIL_RESPONSE_TEXT[resp["task"]]
    return False, None


async def autoguard_pii_infer(
    request_url: str,
    text: str,
    entities: List[str],
    contextual_rules: List[List[str]],
    matching_scores: Dict[str, Dict[str, float]],
    task_config: Optional[Dict[Any, Any]] = None,
):
    """Provides request body for given text and other configuration"""
    api_key = os.environ.get("AUTOGUARD_API_KEY")
    if api_key is None:
        raise ValueError("AUTOGUARD_API_KEY environment variable not set.")

    headers = {"x-api-key": api_key}
    config = DEFAULT_CONFIG
    # enable the select guardrail
    config["pii_fast"]["mode"] = "DETECT"
    if task_config:
        config["pii_fast"].update(task_config)

    config["pii_fast"]["enabled_types"] = entities
    config["pii_fast"]["contextual_rules"] = contextual_rules
    if matching_scores:
        config["pii_fast"]["matching_scores"] = matching_scores.get("pii_fast", {})
    request_body = {"prompt": text, "config": config}

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
                    if resp["task"] == "pii_fast":
                        return resp["guarded"], resp["response"]
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


@action()
async def autoguard_input_api(
    llm_task_manager: LLMTaskManager, context: Optional[dict] = None
):
    """Calls AutoGuard API for the user message and guardrail configuration provided"""
    user_message = context.get("user_message")
    autoguard_config = llm_task_manager.config.rails.config.autoguard

    autoguard_api_url = autoguard_config.parameters.get("endpoint")
    if not autoguard_api_url:
        raise ValueError("Provide the autoguard endpoint in the config")
    tasks = getattr(autoguard_config.input, "guardrails")
    matching_scores = getattr(autoguard_config.input, "matching_scores", {})
    if not tasks:
        raise ValueError("Provide the guardrails in the config")
    prompt = user_message

    return await autoguard_infer(autoguard_api_url, prompt, tasks, matching_scores)


@action()
async def autoguard_output_api(
    llm_task_manager: LLMTaskManager, context: Optional[dict] = None
):
    """Calls AutoGuard API for the bot message and guardrail configuration provided"""
    bot_message = context.get("bot_message")
    autoguard_config = llm_task_manager.config.rails.config.autoguard
    autoguard_api_url = autoguard_config.parameters.get("endpoint")
    if not autoguard_api_url:
        raise ValueError("Provide the autoguard endpoint in the config")
    tasks = getattr(autoguard_config.output, "guardrails")
    matching_scores = getattr(autoguard_config.output, "matching_scores", {})
    if not tasks:
        raise ValueError("Provide the guardrails in the config")

    prompt = bot_message

    return await autoguard_infer(autoguard_api_url, prompt, tasks, matching_scores)


@action()
async def autoguard_pii_input_api(
    llm_task_manager: LLMTaskManager, context: Optional[dict] = None
):
    """Calls AutoGuard API for the user message and guardrail configuration provided"""
    user_message = context.get("user_message")
    autoguard_config = llm_task_manager.config.rails.config.autoguard

    autoguard_api_url = autoguard_config.parameters.get("endpoint")
    if not autoguard_api_url:
        raise ValueError("Provide the autoguard endpoint in the config")

    entities = getattr(autoguard_config.input, "entities", [])
    contextual_rules = getattr(autoguard_config.input, "contextual_rules", [])
    matching_scores = getattr(autoguard_config.input, "matching_scores", {})
    return await autoguard_pii_infer(
        autoguard_api_url, user_message, entities, contextual_rules, matching_scores
    )


@action()
async def autoguard_pii_output_api(
    llm_task_manager: LLMTaskManager, context: Optional[dict] = None
):
    """Calls AutoGuard API for the bot message and guardrail configuration provided"""
    user_message = context.get("bot_message")
    autoguard_config = llm_task_manager.config.rails.config.autoguard

    autoguard_api_url = autoguard_config.parameters.get("endpoint")
    if not autoguard_api_url:
        raise ValueError("Provide the autoguard endpoint in the config")

    entities = getattr(autoguard_config.output, "entities", [])
    contextual_rules = getattr(autoguard_config.output, "contextual_rules", [])
    matching_scores = getattr(autoguard_config.output, "matching_scores", {})
    return await autoguard_pii_infer(
        autoguard_api_url, user_message, entities, contextual_rules, matching_scores
    )


@action()
async def autoguard_factcheck_api(
    llm_task_manager: LLMTaskManager, context: Optional[dict] = None
):
    """Calls AutoGuard factcheck API and checks whether the bot message is factually correct according to given
    documents"""
    api_key = os.environ.get("AUTOGUARD_API_KEY")

    if api_key is None:
        raise ValueError("AUTOGUARD_API_KEY environment variable not set.")

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
