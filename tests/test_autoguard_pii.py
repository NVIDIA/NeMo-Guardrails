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
from typing import Optional

import pytest

from nemoguardrails import RailsConfig
from tests.utils import TestChat

CONFIGS_FOLDER = os.path.join(os.path.dirname(__file__), ".", "test_configs")


@pytest.mark.asyncio
async def test_fact_checking_greeting():
    # Test 1 - Greeting - No fact-checking invocation should happen
    config = RailsConfig.from_path(os.path.join(CONFIGS_FOLDER, "autoguard_pii"))

    chat = TestChat(
        config,
        llm_completions=["  express greeting", "Hi! How can I assist today?"],
    )

    chat >> "hi"
    await chat.bot_async("Hi! How can I assist today?")


@pytest.mark.asyncio
async def test_pii_input():
    config = RailsConfig.from_path(os.path.join(CONFIGS_FOLDER, "autoguard_pii"))

    chat = TestChat(
        config,
        llm_completions=[
            "  ask pii question",
            "My name is Bob and my email is bob@gmail.com. Im from Toronto and I love rock music. My SIN number "
            "76543235 was stolen by Tom Smith. In other words, Mr. Smith stole Bob's identity. Mr. Dylan's checking "
            "account is 5432123, and his username is dylan123",
            "PII redacted text: My name is [PERSON NAME] and my email is [EMAIL ADDRESS]. Im from [LOCATION] and I "
            "love rock music. My SIN number [SOCIAL SECURITY NUMBER] was stolen by [PERSON NAME]. In other words, "
            "[PERSON NAME] stole [PERSON NAME]'s identity. [PERSON NAME]'s checking account is [BANK ACCOUNT NUMBER], "
            "and his username is [USERNAME] ",
        ],
    )

    async def mock_autoguard_pii_api(context: Optional[dict] = None, **kwargs):
        query = context.get("user_message")
        if (
            query
            == "My name is Bob and my email is bob@gmail.com. Im from Toronto and I love rock music. My SIN number "
            "76543235 was stolen by Tom Smith. In other words, Mr. Smith stole Bob's identity. Mr. Dylan's "
            "checking account is 5432123, and his username is dylan123 "
        ):
            return (
                True,
                "PII redacted text: My name is [PERSON NAME] and my email is [EMAIL ADDRESS]. Im from [LOCATION] and "
                "I love rock music. My SIN number [SOCIAL SECURITY NUMBER] was stolen by [PERSON NAME]. In other "
                "words, [PERSON NAME] stole [PERSON NAME]'s identity. [PERSON NAME]'s checking account is [BANK "
                "ACCOUNT NUMBER], and his username is [USERNAME] ",
            )
        else:
            return False, None

    chat.app.register_action(mock_autoguard_pii_api, "autoguard_pii_api")

    (
        chat
        >> "My name is Bob and my email is bob@gmail.com. Im from Toronto and I love rock music. My SIN number "
        "76543235 was stolen by Tom Smith. In other words, Mr. Smith stole Bob's identity. Mr. Dylan's checking "
        "account is 5432123, and his username is dylan123 "
    )

    await chat.bot_async(
        "PII redacted text: My name is [PERSON NAME] and my email is [EMAIL ADDRESS]. Im from [LOCATION] and I love "
        "rock music. My SIN number [SOCIAL SECURITY NUMBER] was stolen by [PERSON NAME]. In other words, "
        "[PERSON NAME] stole [PERSON NAME]'s identity. [PERSON NAME]'s checking account is [BANK ACCOUNT NUMBER], "
        "and his username is [USERNAME] "
    )


@pytest.mark.asyncio
async def test_pii_contextual_input():
    config = RailsConfig.from_path(os.path.join(CONFIGS_FOLDER, "autoguard_pii"))

    chat = TestChat(
        config,
        llm_completions=[
            "  ask pii question",
            "Alice recently set up her new application. She uses the following credentials:Username: aliceSmith01, "
            "Password: Al!c3$ecretP@ss, API Key: AKIAIOSFODNN7EXAMPLE1Bob. Bob, working on a separate project, "
            "logged into his dashboard with: Username: bobJohnson02, Password: B0b$P@ssw0rd2U$e, "
            "API Key: AKIAIOSFODNN7EXAMPLE2.",
            "PII redacted text: Alice recently set up her new application. She uses the following "
            "credentials:Username: aliceSmith01, Password: Al!c3$ecretP@ss, API Key: AKIAIOSFODNN7EXAMPLE1Bob. Bob, "
            "working on a separate project, logged into his dashboard with: Username: bobJohnson02, Password: "
            "B0b$P@ssw0rd2U$e, API Key: AKIAIOSFODNN7EXAMPLE2.",
        ],
    )

    async def mock_autoguard_pii_api(context: Optional[dict] = None, **kwargs):
        query = context.get("user_message")
        if (
            query
            == "Alice recently set up her new application. She uses the following credentials:Username: aliceSmith01, "
            "Password: Al!c3$ecretP@ss, API Key: AKIAIOSFODNN7EXAMPLE1Bob. Bob, working on a separate project, "
            "logged into his dashboard with: Username: bobJohnson02, Password: B0b$P@ssw0rd2U$e, "
            "API Key: AKIAIOSFODNN7EXAMPLE2."
        ):
            return (
                True,
                "PII redacted text: Alice recently set up her new application. She uses the following "
                "credentials:Username: aliceSmith01, Password: Al!c3$ecretP@ss, API Key: AKIAIOSFODNN7EXAMPLE1Bob. "
                "Bob, working on a separate project, logged into his dashboard with: Username: bobJohnson02, "
                "Password: B0b$P@ssw0rd2U$e, API Key: AKIAIOSFODNN7EXAMPLE2.",
            )
        else:
            return False, None

    chat.app.register_action(mock_autoguard_pii_api, "autoguard_pii_api")

    (
        chat
        >> "Alice recently set up her new application. She uses the following credentials:Username: aliceSmith01, "
        "Password: Al!c3$ecretP@ss, API Key: AKIAIOSFODNN7EXAMPLE1Bob. Bob, working on a separate project, "
        "logged into his dashboard with: Username: bobJohnson02, Password: B0b$P@ssw0rd2U$e, "
        "API Key: AKIAIOSFODNN7EXAMPLE2."
    )

    await chat.bot_async(
        "PII redacted text: Alice recently set up her new application. She uses the following credentials:Username: "
        "aliceSmith01, Password: Al!c3$ecretP@ss, API Key: AKIAIOSFODNN7EXAMPLE1Bob. Bob, working on a separate "
        "project, logged into his dashboard with: Username: bobJohnson02, Password: B0b$P@ssw0rd2U$e, "
        "API Key: AKIAIOSFODNN7EXAMPLE2."
    )
