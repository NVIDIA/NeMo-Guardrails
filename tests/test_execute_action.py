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

from nemoguardrails import LLMRails, RailsConfig
from tests.utils import FakeLLM

TEST_CONFIGS_PATH = os.path.join(os.path.dirname(__file__), "test_configs")


@pytest.fixture
def rails_config():
    return RailsConfig.from_path(os.path.join(TEST_CONFIGS_PATH, "simple_actions"))


def _get_llm_rails(rails_config, llm):
    """Helper to return a LLMRails instance."""

    llm_rails = LLMRails(config=rails_config, llm=llm)

    async def fetch_profile():
        return {
            "name": "John",
        }

    async def check_access(account):
        return account["name"] == "John"

    llm_rails.runtime.register_action(fetch_profile)
    llm_rails.runtime.register_action(check_access)

    return llm_rails


@pytest.mark.asyncio
async def test_action_execution_with_result(rails_config):
    llm = FakeLLM(
        responses=[
            "  express greeting",
        ]
    )

    llm_rails = _get_llm_rails(rails_config, llm)

    events = [{"type": "UtteranceUserActionFinished", "final_transcript": "Hello!"}]
    new_events = await llm_rails.runtime.generate_events(events)

    assert new_events == [
        {
            "action_name": "generate_user_intent",
            "action_params": {},
            "action_result_key": None,
            "is_system_action": True,
            "type": "start_action",
        },
        {
            "action_name": "generate_user_intent",
            "action_params": {},
            "action_result_key": None,
            "events": [{"intent": "express greeting", "type": "UserIntent"}],
            "is_system_action": True,
            "return_value": None,
            "status": "success",
            "type": "action_finished",
        },
        {"intent": "express greeting", "type": "UserIntent"},
        {
            "action_name": "fetch_profile",
            "action_params": {},
            "action_result_key": "account",
            "is_system_action": False,
            "type": "start_action",
        },
        {"data": {"account": {"name": "John"}}, "type": "context_update"},
        {
            "action_name": "fetch_profile",
            "action_params": {},
            "action_result_key": "account",
            "events": [],
            "is_system_action": False,
            "return_value": {"name": "John"},
            "status": "success",
            "type": "action_finished",
        },
        {"intent": "express greeting", "type": "BotIntent"},
        {
            "action_name": "retrieve_relevant_chunks",
            "action_params": {},
            "action_result_key": None,
            "is_system_action": True,
            "type": "start_action",
        },
        {"data": {"relevant_chunks": ""}, "type": "context_update"},
        {
            "action_name": "retrieve_relevant_chunks",
            "action_params": {},
            "action_result_key": None,
            "events": None,
            "is_system_action": True,
            "return_value": "",
            "status": "success",
            "type": "action_finished",
        },
        {
            "action_name": "generate_bot_message",
            "action_params": {},
            "action_result_key": None,
            "is_system_action": True,
            "type": "start_action",
        },
        {
            "action_name": "generate_bot_message",
            "action_params": {},
            "action_result_key": None,
            "events": [{"content": "Hello!", "type": "bot_said"}],
            "is_system_action": True,
            "return_value": None,
            "status": "success",
            "type": "action_finished",
        },
        {"content": "Hello!", "type": "bot_said"},
        {"type": "listen"},
    ]


@pytest.mark.asyncio
async def test_action_execution_with_parameter(rails_config):
    llm = FakeLLM(
        responses=["  express greeting", "  request access", '  "Access granted!"']
    )

    llm_rails = _get_llm_rails(rails_config, llm)

    events = [{"type": "UtteranceUserActionFinished", "final_transcript": "hello!"}]
    new_events = await llm_rails.runtime.generate_events(events)
    events.extend(new_events)

    events.append(
        {"type": "UtteranceUserActionFinished", "final_transcript": "Please let me in"}
    )
    new_events = await llm_rails.runtime.generate_events(events)

    # We check that is_allowed was correctly set to True
    assert {"data": {"is_allowed": True}, "type": "context_update"} in new_events


@pytest.mark.asyncio
async def test_action_execution_with_if(rails_config):
    llm = FakeLLM(responses=["  request access", '  "Access denied!"'])

    llm_rails = _get_llm_rails(rails_config, llm)

    events = [
        {"type": "context_update", "data": {"account": {"name": "Josh"}}},
        {"type": "UtteranceUserActionFinished", "final_transcript": "Please let me in"},
    ]

    new_events = await llm_rails.runtime.generate_events(events)

    # We check that is_allowed was correctly set to True
    assert {"intent": "inform access denied", "type": "BotIntent"} in new_events
