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
from typing import Optional

import aiohttp

from nemoguardrails.actions import action

log = logging.getLogger(__name__)


@action(name="call autoguard gender bias api", is_system_action=True)
async def call_autoguard_gender_bias_api(context: Optional[dict] = None):
    api_key = os.environ.get("AUTOGUARD_API_KEY")

    if api_key is None:
        raise ValueError("AUTOGUARD_API_KEY environment variable not set.")

    user_message = context.get("user_message")
    bot_message = context.get("bot_message")
    if user_message:
        prompt = user_message
    else:
        prompt = bot_message

    model = context.get("model")
    url = "http://35.225.99.81:8888/"

    if model:
        url = url + "query"
    else:
        url = url + "guardrail"

    headers = {"x-api-key": api_key}

    data = {
        "config": {
            "tonal_detection": {"mode": "OFF"},
            "pii_fast": {
                "mode": "OFF",
                "enabled_types": [],
                "mask": False,
                "coreference": False,
            },
            "factcheck": {"mode": "OFF"},
            "confidential_detection": {"mode": "OFF"},
            "jailbreak_detection": {"mode": "OFF"},
            "text_toxicity_extraction": {"mode": "OFF"},
            "harm_detection": {"mode": "OFF"},
            "racial_bias_detection": {"mode": "OFF"},
            "gender_bias_detection": {"mode": "DETECT"},
        },
        "prompt": prompt,
    }
    if model:
        data["model"] = model
    async with aiohttp.ClientSession() as session:
        async with session.post(
            url=url,
            headers=headers,
            json=data,
        ) as response:
            if response.status != 200:
                raise ValueError(
                    f"AutoGuard call failed with status code {response.status}.\n"
                    f"Details: {await response.text()}"
                )
            data = await response.text()
            response_json = []
            for line in data.split("\n"):
                line = line.strip()
                if len(line) > 0:
                    response_json.append(json.loads(line))
            log.info(json.dumps(response_json, indent=True))
            for i in response_json:
                if i["guarded"]:
                    return True
            return False


@action(name="call autoguard race bias api", is_system_action=True)
async def call_autoguard_race_bias_api(context: Optional[dict] = None):
    api_key = os.environ.get("AUTOGUARD_API_KEY")

    if api_key is None:
        raise ValueError("AUTOGUARD_API_KEY environment variable not set.")

    user_message = context.get("user_message")
    bot_message = context.get("bot_message")
    if user_message:
        prompt = user_message
    else:
        prompt = bot_message

    model = context.get("model")
    url = "http://35.225.99.81:8888/"

    if model:
        url = url + "query"
    else:
        url = url + "guardrail"

    headers = {"x-api-key": api_key}

    data = {
        "config": {
            "gender_bias_detection": {"mode": "OFF"},
            "tonal_detection": {"mode": "OFF"},
            "pii_fast": {
                "mode": "OFF",
                "enabled_types": [],
                "mask": False,
                "coreference": False,
            },
            "factcheck": {"mode": "OFF"},
            "confidential_detection": {"mode": "OFF"},
            "jailbreak_detection": {"mode": "OFF"},
            "text_toxicity_extraction": {"mode": "OFF"},
            "harm_detection": {"mode": "OFF"},
            "racial_bias_detection": {"mode": "DETECT"},
        },
        "prompt": prompt,
    }
    if model:
        data["model"] = model
    async with aiohttp.ClientSession() as session:
        async with session.post(
            url=url,
            headers=headers,
            json=data,
        ) as response:
            if response.status != 200:
                raise ValueError(
                    f"AutoGuard call failed with status code {response.status}.\n"
                    f"Details: {await response.text()}"
                )
            data = await response.text()
            response_json = []
            for line in data.split("\n"):
                line = line.strip()
                if len(line) > 0:
                    response_json.append(json.loads(line))
            log.info(json.dumps(response_json, indent=True))
            for i in response_json:
                if i["guarded"]:
                    return True
            return False


@action(name="call autoguard harm detection api", is_system_action=True)
async def call_autoguard_harm_detection_api(context: Optional[dict] = None):
    api_key = os.environ.get("AUTOGUARD_API_KEY")

    if api_key is None:
        raise ValueError("AUTOGUARD_API_KEY environment variable not set.")

    user_message = context.get("user_message")
    bot_message = context.get("bot_message")
    if user_message:
        prompt = user_message
    else:
        prompt = bot_message

    model = context.get("model")
    url = "http://35.225.99.81:8888/"

    if model:
        url = url + "query"
    else:
        url = url + "guardrail"

    headers = {"x-api-key": api_key}

    data = {
        "config": {
            "gender_bias_detection": {"mode": "OFF"},
            "racial_bias_detection": {"mode": "OFF"},
            "tonal_detection": {"mode": "OFF"},
            "pii_fast": {
                "mode": "OFF",
                "enabled_types": [],
                "mask": False,
                "coreference": False,
            },
            "factcheck": {"mode": "OFF"},
            "confidential_detection": {"mode": "OFF"},
            "jailbreak_detection": {"mode": "OFF"},
            "text_toxicity_extraction": {"mode": "OFF"},
            "harm_detection": {"mode": "DETECT"},
        },
        "prompt": prompt,
    }
    if model:
        data["model"] = model
    async with aiohttp.ClientSession() as session:
        async with session.post(
            url=url,
            headers=headers,
            json=data,
        ) as response:
            if response.status != 200:
                raise ValueError(
                    f"AutoGuard call failed with status code {response.status}.\n"
                    f"Details: {await response.text()}"
                )
            data = await response.text()
            response_json = []
            for line in data.split("\n"):
                line = line.strip()
                if len(line) > 0:
                    response_json.append(json.loads(line))
            log.info(json.dumps(response_json, indent=True))
            for i in response_json:
                if i["guarded"]:
                    return True
            return False


@action(name="call autoguard toxicity detection api", is_system_action=True)
async def call_autoguard_toxicity_detection_api(context: Optional[dict] = None):
    api_key = os.environ.get("AUTOGUARD_API_KEY")

    if api_key is None:
        raise ValueError("AUTOGUARD_API_KEY environment variable not set.")

    user_message = context.get("user_message")
    bot_message = context.get("bot_message")
    if user_message:
        prompt = user_message
    else:
        prompt = bot_message

    model = context.get("model")
    url = "http://35.225.99.81:8888/"

    if model:
        url = url + "query"
    else:
        url = url + "guardrail"

    headers = {"x-api-key": api_key}

    data = {
        "config": {
            "gender_bias_detection": {"mode": "OFF"},
            "harm_detection": {"mode": "OFF"},
            "racial_bias_detection": {"mode": "OFF"},
            "tonal_detection": {"mode": "OFF"},
            "pii_fast": {
                "mode": "OFF",
                "enabled_types": [],
                "mask": False,
                "coreference": False,
            },
            "factcheck": {"mode": "OFF"},
            "confidential_detection": {"mode": "OFF"},
            "jailbreak_detection": {"mode": "OFF"},
            "text_toxicity_extraction": {"mode": "DETECT"},
        },
        "prompt": prompt,
    }
    if model:
        data["model"] = model
    async with aiohttp.ClientSession() as session:
        async with session.post(
            url=url,
            headers=headers,
            json=data,
        ) as response:
            if response.status != 200:
                raise ValueError(
                    f"AutoGuard call failed with status code {response.status}.\n"
                    f"Details: {await response.text()}"
                )
            data = await response.text()
            response_json = []
            for line in data.split("\n"):
                line = line.strip()
                if len(line) > 0:
                    response_json.append(json.loads(line))
            log.info(json.dumps(response_json, indent=True))
            for i in response_json:
                if i["guarded"]:
                    return True
            return False


@action(name="call autoguard jailbreak detection api", is_system_action=True)
async def call_autoguard_jailbreak_detection_api(context: Optional[dict] = None):
    api_key = os.environ.get("AUTOGUARD_API_KEY")

    if api_key is None:
        raise ValueError("AUTOGUARD_API_KEY environment variable not set.")

    user_message = context.get("user_message")
    bot_message = context.get("bot_message")
    if user_message:
        prompt = user_message
    else:
        prompt = bot_message

    model = context.get("model")
    url = "http://35.225.99.81:8888/"

    if model:
        url = url + "query"
    else:
        url = url + "guardrail"

    headers = {"x-api-key": api_key}

    data = {
        "config": {
            "gender_bias_detection": {"mode": "OFF"},
            "harm_detection": {"mode": "OFF"},
            "text_toxicity_extraction": {"mode": "OFF"},
            "racial_bias_detection": {"mode": "OFF"},
            "tonal_detection": {"mode": "OFF"},
            "pii_fast": {
                "mode": "OFF",
                "enabled_types": [],
                "mask": False,
                "coreference": False,
            },
            "factcheck": {"mode": "OFF"},
            "confidential_detection": {"mode": "OFF"},
            "jailbreak_detection": {"mode": "DETECT"},
        },
        "prompt": prompt,
    }
    if model:
        data["model"] = model
    async with aiohttp.ClientSession() as session:
        async with session.post(
            url=url,
            headers=headers,
            json=data,
        ) as response:
            if response.status != 200:
                raise ValueError(
                    f"AutoGuard call failed with status code {response.status}.\n"
                    f"Details: {await response.text()}"
                )
            data = await response.text()
            response_json = []
            for line in data.split("\n"):
                line = line.strip()
                if len(line) > 0:
                    response_json.append(json.loads(line))
            log.info(json.dumps(response_json, indent=True))
            for i in response_json:
                if i["guarded"]:
                    return True
            return False


@action(name="call autoguard confidential detection api", is_system_action=True)
async def call_autoguard_confidential_detection_api(context: Optional[dict] = None):
    api_key = os.environ.get("AUTOGUARD_API_KEY")

    if api_key is None:
        raise ValueError("AUTOGUARD_API_KEY environment variable not set.")

    user_message = context.get("user_message")
    bot_message = context.get("bot_message")
    if user_message:
        prompt = user_message
    else:
        prompt = bot_message

    model = context.get("model")
    url = "http://35.225.99.81:8888/"

    if model:
        url = url + "query"
    else:
        url = url + "guardrail"

    headers = {"x-api-key": api_key}

    data = {
        "config": {
            "gender_bias_detection": {"mode": "OFF"},
            "harm_detection": {"mode": "OFF"},
            "text_toxicity_extraction": {"mode": "OFF"},
            "racial_bias_detection": {"mode": "OFF"},
            "tonal_detection": {"mode": "OFF"},
            "jailbreak_detection": {"mode": "OFF"},
            "pii_fast": {
                "mode": "OFF",
                "enabled_types": [],
                "mask": False,
                "coreference": False,
            },
            "factcheck": {"mode": "OFF"},
            "confidential_detection": {"mode": "DETECT"},
        },
        "prompt": prompt,
    }
    if model:
        data["model"] = model
    async with aiohttp.ClientSession() as session:
        async with session.post(
            url=url,
            headers=headers,
            json=data,
        ) as response:
            if response.status != 200:
                raise ValueError(
                    f"AutoGuard call failed with status code {response.status}.\n"
                    f"Details: {await response.text()}"
                )
            data = await response.text()
            response_json = []
            for line in data.split("\n"):
                line = line.strip()
                if len(line) > 0:
                    response_json.append(json.loads(line))
            log.info(json.dumps(response_json, indent=True))
            for i in response_json:
                if i["guarded"]:
                    return True
            return False


@action(name="call autoguard factcheck api", is_system_action=True)
async def call_autoguard_factcheck_api(context: Optional[dict] = None):
    api_key = os.environ.get("AUTOGUARD_API_KEY")

    if api_key is None:
        raise ValueError("AUTOGUARD_API_KEY environment variable not set.")

    bot_message = context.get("bot_message")
    documents = context.get("relevant_chunks", [])
    if isinstance(documents, str):
        documents = documents.split("\n")
    prompt = bot_message

    headers = {"x-api-key": api_key}

    if isinstance(documents, list) and len(documents) > 0:
        factcheck_request_body = {"prompt": prompt, "documents": documents}
        factcheck_url = "http://35.225.99.81:8888/factcheck"
        async with aiohttp.ClientSession() as session:
            async with session.post(
                url=factcheck_url,
                headers=headers,
                json=factcheck_request_body,
            ) as response:
                if response.status != 200:
                    raise ValueError(
                        f"AutoGuard call failed with status code {response.status}.\n"
                        f"Details: {await response.text()}"
                    )
                data = await response.text()
                response_json = []
                for line in data.split("\n"):
                    line = line.strip()
                    if len(line) > 0:
                        response_json.append(json.loads(line))
                log.info(json.dumps(response_json, indent=True))
                for i in response_json:
                    if i["guarded"]:
                        return True
                return False
    else:
        raise ValueError("Provide relevant documents in proper format")
