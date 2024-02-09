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
import time
from typing import Optional

import aiohttp

from nemoguardrails import RailsConfig
from nemoguardrails.actions import action
from nemoguardrails.llm.taskmanager import LLMTaskManager

log = logging.getLogger(__name__)

GUARDRAIL_TRIGGER_TEXT = {
    "pii_fast": "PII",
    "confidential_detection": "Confidential Information violation",
    "gender_bias_detection": "Gender bias in text",
    "harm_detection": "Harm to human violation",
    "text_toxicity_extraction": "Toxicity in text",
    "racial_bias_detection": "Racial bias in text",
    "jailbreak_detection": "Jailbreak attempt",
    "intellectual_property": "Intellectual property information in text",
    "factcheck": "Factcheck violation in text",
}


async def autoguard_infer(request_url, text, tasks, task_config=None):
    api_key = os.environ.get("AUTOGUARD_API_KEY")
    if api_key is None:
        raise ValueError("AUTOGUARD_API_KEY environment variable not set.")

    headers = {"x-api-key": api_key}
    # shutting all guardrails off by default
    config = {
        "pii_fast": {
            "mode": "OFF",
            "mask": True,
            "enabled_types": [
                "[PERSON NAME]",
                "[LOCATION]",
                "[DATE OF BIRTH]",
                "[DATE]",
                "[PHONE NUMBER]",
                "[EMAIL ADDRESS]",
                "[CREDIT CARD NUMBER]",
                "[BANK ACCOUNT NUMBER]",
                "[SOCIAL SECURITY NUMBER]",
                "[MONEY]",
                "[INSURANCE POLICY NUMBER]",
                "[PROFESSION]",
                "[ORGANIZATION]",
                "[USERNAME]",
                "[PASSWORD]",
                "[IP ADDRESS]",
                "[PASSPORT NUMBER]",
                "[DRIVER LICENSE NUMBER]",
                "[API_KEY]",
                "[TRANSACTION_ID]",
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
    # enable the select guardrail
    for task in tasks:
        config[task] = {"mode": "DETECT"}
        if task_config:
            config[task].update(task_config)
    request_body = {"prompt": text, "config": config}
    aggregated_responses = []

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
                        return True, GUARDRAIL_TRIGGER_TEXT[resp["task"]]
    return False, None


async def infer_factcheck(request_url, text, documents):
    api_key = os.environ.get("AUTOGUARD_API_KEY")
    if api_key is None:
        raise ValueError("AUTOGUARD_API_KEY environment variable not set.")

    headers = {"x-api-key": api_key}
    request_body = {"prompt": text, "documents": documents}
    json_data = json.dumps(request_body).encode("utf8")
    async with aiohttp.ClientSession() as session:
        async with session.post(
            url=request_url,
            headers=headers,
            json=json_data,
        ) as response:
            if response.status != 200:
                raise ValueError(
                    f"AutoGuard call failed with status code {response.status}.\n"
                    f"Details: {await response.text()}"
                )
            async for line in response.content:
                response = json.loads(line)
                if response["task"] == "factcheck":
                    return response["guarded"]
    return False


@action()
async def autoguard_input_api(
    llm_task_manager: LLMTaskManager, context: Optional[dict] = None
):
    user_message = context.get("user_message")
    autoguard_config = llm_task_manager.config.rails.config.autoguard

    autoguard_api_url = autoguard_config.parameters.get("endpoint")
    if not autoguard_api_url:
        raise ValueError("Provide the autoguard endpoint in the config")
    tasks = getattr(autoguard_config.input, "guardrails")
    if not tasks:
        raise ValueError("Provide the guardrails in the config")

    prompt = user_message

    return await autoguard_infer(autoguard_api_url, prompt, tasks)


@action()
async def autoguard_output_api(
    llm_task_manager: LLMTaskManager, context: Optional[dict] = None
):
    bot_message = context.get("bot_message")
    autoguard_config = llm_task_manager.config.rails.config.autoguard
    autoguard_api_url = autoguard_config.parameters.get("endpoint")
    if not autoguard_api_url:
        raise ValueError("Provide the autoguard endpoint in the config")
    tasks = getattr(autoguard_config.input, "guardrails")
    if not tasks:
        raise ValueError("Provide the guardrails in the config")

    prompt = bot_message

    return await autoguard_infer(autoguard_api_url, prompt, tasks)


@action(name="call autoguard factcheck api", is_system_action=True)
async def call_autoguard_factcheck_api(
    llm_task_manager: LLMTaskManager, context: Optional[dict] = None
):
    api_key = os.environ.get("AUTOGUARD_API_KEY")

    if api_key is None:
        raise ValueError("AUTOGUARD_API_KEY environment variable not set.")

    bot_message = context.get("bot_message")
    documents = context.get("relevant_chunks", [])
    autoguard_config = llm_task_manager.config.rails.config.autoguard
    autoguard_api_url = autoguard_config.parameters.get("fact_check_endpoint")
    if not autoguard_api_url:
        raise ValueError("Provide the autoguard factcheck endpoint in the config")
    if isinstance(documents, str):
        documents = documents.split("\n")
    prompt = bot_message

    if isinstance(documents, list) and len(documents) > 0:
        return (
            await infer_factcheck(autoguard_api_url, prompt, documents),
            GUARDRAIL_TRIGGER_TEXT["factcheck"],
        )
    else:
        raise ValueError("Provide relevant documents in proper format")
