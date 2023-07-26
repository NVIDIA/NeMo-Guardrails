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

from typing import Optional

import pytest

from nemoguardrails import LLMRails, RailsConfig
from tests.utils import FakeLLM, clean_events, event_sequence_conforms


@pytest.fixture
def rails_config():
    return RailsConfig.parse_object(
        {
            "models": [
                {
                    "type": "main",
                    "engine": "fake",
                    "model": "fake",
                }
            ],
            "user_messages": {
                "express greeting": ["Hello!"],
                "ask math question": ["What is 2 + 2?", "5 + 9"],
            },
            "flows": [
                {
                    "elements": [
                        {"user": "express greeting"},
                        {"bot": "express greeting"},
                    ]
                },
                {
                    "elements": [
                        {"user": "ask math question"},
                        {"execute": "compute"},
                        {"bot": "provide math response"},
                        {"bot": "ask if user happy"},
                    ]
                },
            ],
            "bot_messages": {
                "express greeting": ["Hello! How are you?"],
                "provide response": ["The answer is 234", "The answer is 1412"],
            },
        }
    )


@pytest.mark.asyncio
async def test_1(rails_config):
    llm = FakeLLM(
        responses=[
            "  express greeting",
            "  ask math question",
            '  "The answer is 5"',
            '  "Are you happy with the result?"',
        ]
    )

    async def compute(context: dict, what: Optional[str] = "2 + 3"):
        return eval(what)

    llm_rails = LLMRails(config=rails_config, llm=llm)
    llm_rails.runtime.register_action(compute)

    events = [{"type": "UtteranceUserActionFinished", "final_transcript": "Hello!"}]

    new_events = await llm_rails.runtime.generate_events(events)
    clean_events(new_events)

    expected_events = [
        {
            "action_name": "generate_user_intent",
            "action_params": {},
            "action_result_key": None,
            "is_system_action": True,
            "type": "StartInternalSystemAction",
        },
        {
            "action_name": "generate_user_intent",
            "action_params": {},
            "action_result_key": None,
            "events": [{"intent": "express greeting", "type": "UserIntent"}],
            "is_system_action": True,
            "return_value": None,
            "status": "success",
            "type": "InternalSystemActionFinished",
        },
        {"intent": "express greeting", "type": "UserIntent"},
        {"intent": "express greeting", "type": "BotIntent"},
        {
            "action_name": "retrieve_relevant_chunks",
            "action_params": {},
            "action_result_key": None,
            "is_system_action": True,
            "type": "StartInternalSystemAction",
        },
        {"data": {"relevant_chunks": ""}, "type": "ContextUpdate"},
        {
            "action_name": "retrieve_relevant_chunks",
            "action_params": {},
            "action_result_key": None,
            "events": None,
            "is_system_action": True,
            "return_value": "",
            "status": "success",
            "type": "InternalSystemActionFinished",
        },
        {
            "action_name": "generate_bot_message",
            "action_params": {},
            "action_result_key": None,
            "is_system_action": True,
            "type": "StartInternalSystemAction",
        },
        {
            "action_name": "generate_bot_message",
            "action_params": {},
            "action_result_key": None,
            "events": [
                {"script": "Hello! How are you?", "type": "StartUtteranceBotAction"}
            ],
            "is_system_action": True,
            "return_value": None,
            "status": "success",
            "type": "InternalSystemActionFinished",
        },
        {"script": "Hello! How are you?", "type": "StartUtteranceBotAction"},
        {"type": "Listen"},
    ]
    assert event_sequence_conforms(expected_events, new_events)

    events.extend(new_events)
    events.append({"type": "UtteranceUserActionFinished", "final_transcript": "2 + 3"})

    new_events = await llm_rails.runtime.generate_events(events)
    clean_events(new_events)

    expected_events = [
        {
            "action_name": "generate_user_intent",
            "action_params": {},
            "action_result_key": None,
            "is_system_action": True,
            "type": "StartInternalSystemAction",
        },
        {
            "action_name": "generate_user_intent",
            "action_params": {},
            "action_result_key": None,
            "events": [{"intent": "ask math question", "type": "UserIntent"}],
            "is_system_action": True,
            "return_value": None,
            "status": "success",
            "type": "InternalSystemActionFinished",
        },
        {"intent": "ask math question", "type": "UserIntent"},
        {
            "action_name": "compute",
            "action_params": {},
            "action_result_key": None,
            "is_system_action": False,
            "type": "StartInternalSystemAction",
        },
        {
            "action_name": "compute",
            "action_params": {},
            "action_result_key": None,
            "events": [],
            "is_system_action": False,
            "return_value": 5,
            "status": "success",
            "type": "InternalSystemActionFinished",
        },
        {"intent": "provide math response", "type": "BotIntent"},
        {
            "action_name": "retrieve_relevant_chunks",
            "action_params": {},
            "action_result_key": None,
            "is_system_action": True,
            "type": "StartInternalSystemAction",
        },
        {
            "action_name": "retrieve_relevant_chunks",
            "action_params": {},
            "action_result_key": None,
            "events": None,
            "is_system_action": True,
            "return_value": "",
            "status": "success",
            "type": "InternalSystemActionFinished",
        },
        {
            "action_name": "generate_bot_message",
            "action_params": {},
            "action_result_key": None,
            "is_system_action": True,
            "type": "StartInternalSystemAction",
        },
        {
            "action_name": "generate_bot_message",
            "action_params": {},
            "action_result_key": None,
            "events": [
                {"script": "The answer is 5", "type": "StartUtteranceBotAction"}
            ],
            "is_system_action": True,
            "return_value": None,
            "status": "success",
            "type": "InternalSystemActionFinished",
        },
        {"script": "The answer is 5", "type": "StartUtteranceBotAction"},
        {"intent": "ask if user happy", "type": "BotIntent"},
        {
            "action_name": "retrieve_relevant_chunks",
            "action_params": {},
            "action_result_key": None,
            "is_system_action": True,
            "type": "StartInternalSystemAction",
        },
        {
            "action_name": "retrieve_relevant_chunks",
            "action_params": {},
            "action_result_key": None,
            "events": None,
            "is_system_action": True,
            "return_value": "",
            "status": "success",
            "type": "InternalSystemActionFinished",
        },
        {
            "action_name": "generate_bot_message",
            "action_params": {},
            "action_result_key": None,
            "is_system_action": True,
            "type": "StartInternalSystemAction",
        },
        {
            "action_name": "generate_bot_message",
            "action_params": {},
            "action_result_key": None,
            "events": [
                {
                    "script": "Are you happy with the result?",
                    "type": "StartUtteranceBotAction",
                }
            ],
            "is_system_action": True,
            "return_value": None,
            "status": "success",
            "type": "InternalSystemActionFinished",
        },
        {
            "script": "Are you happy with the result?",
            "type": "StartUtteranceBotAction",
        },
        {"type": "Listen"},
    ]

    assert event_sequence_conforms(expected_events, new_events)


@pytest.mark.asyncio
async def test_2(rails_config):
    llm = FakeLLM(
        responses=[
            "  express greeting",
            "  ask math question",
            '  "The answer is 5"',
            '  "Are you happy with the result?"',
        ]
    )

    async def compute(what: Optional[str] = "2 + 3"):
        return eval(what)

    llm_rails = LLMRails(config=rails_config, llm=llm)
    llm_rails.runtime.register_action(compute)

    messages = [{"role": "user", "content": "Hello!"}]
    bot_message = await llm_rails.generate_async(messages=messages)

    assert bot_message == {"role": "assistant", "content": "Hello! How are you?"}
    messages.append(bot_message)

    messages.append({"role": "user", "content": "2 + 3"})
    bot_message = await llm_rails.generate_async(messages=messages)
    assert bot_message == {
        "role": "assistant",
        "content": "The answer is 5\nAre you happy with the result?",
    }
