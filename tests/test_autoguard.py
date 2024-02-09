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

import os

import pytest
from aioresponses import aioresponses
from pytest_httpx import IteratorStream

from nemoguardrails import RailsConfig
from nemoguardrails.actions.actions import ActionResult, action
from tests.constants import NEMO_API_URL_GPT_43B_002
from tests.utils import TestChat

CONFIGS_FOLDER = os.path.join(os.path.dirname(__file__), ".", "test_configs")


@pytest.mark.asyncio
async def test_racially_biased_input(httpx_mock):
    config = RailsConfig.from_path(os.path.join(CONFIGS_FOLDER, "autoguard"))
    chat = TestChat(config)

    httpx_mock.add_response(
        method="POST",
        url=NEMO_API_URL_GPT_43B_002,
        json={"text": "  ask racially biased question"},
    )

    httpx_mock.add_response(
        method="POST",
        url=NEMO_API_URL_GPT_43B_002,
        json={
            "text": "Racial bias in text has been detected by AutoGuard; Sorry, can't process."
        },
    )

    httpx_mock.add_response(
        method="POST",
        url="http://35.225.99.81:8888/guardrail",
        stream=IteratorStream(
            [
                b'{"response": "Mock No Gender Bias", "guarded": false, "task": '
                b'"gender_bias_detection"}\n',
                b'{"response": "Mock Racial Bias", "guarded": true, "task": "racial_bias_detection"}\n',
            ]
        ),
    )

    chat >> "Are whites better than blacks"

    await chat.bot_async(
        "Racial bias in text has been detected by AutoGuard; Sorry, can't process."
    )


@pytest.mark.asyncio
async def test_fact_checking_greeting(httpx_mock):
    # Test 1 - Greeting - No fact-checking invocation should happen
    config = RailsConfig.from_path(os.path.join(CONFIGS_FOLDER, "autoguard"))
    chat = TestChat(config)

    httpx_mock.add_response(
        method="POST",
        url=NEMO_API_URL_GPT_43B_002,
        json={"text": "  express greeting"},
    )

    httpx_mock.add_response(
        method="POST",
        url=NEMO_API_URL_GPT_43B_002,
        json={"text": "Hi! How can I assist today?"},
    )

    chat >> "hi"
    await chat.bot_async("Hi! How can I assist today?")
