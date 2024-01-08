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
