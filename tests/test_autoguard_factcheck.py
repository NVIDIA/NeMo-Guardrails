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

from nemoguardrails import RailsConfig
from nemoguardrails.actions.actions import ActionResult, action
from tests.constants import NEMO_API_URL_GPT_43B_002
from tests.utils import TestChat

CONFIGS_FOLDER = os.path.join(os.path.dirname(__file__), ".", "test_configs")


def build_kb():
    with open(
        os.path.join(CONFIGS_FOLDER, "autoguard_factcheck", "kb", "kb.md"), "r"
    ) as f:
        content = f.readlines()

    return content


@action(is_system_action=True)
async def retrieve_relevant_chunks():
    """Retrieve relevant chunks from the knowledge base and add them to the context."""
    context_updates = {}
    relevant_chunks = "\n".join(build_kb())
    context_updates["relevant_chunks"] = relevant_chunks

    return ActionResult(
        return_value=context_updates["relevant_chunks"],
        context_updates=context_updates,
    )


@pytest.mark.asyncio
async def test_fact_checking_greeting(httpx_mock):
    # Test 1 - Greeting - No fact-checking invocation should happen
    config = RailsConfig.from_path(os.path.join(CONFIGS_FOLDER, "autoguard_factcheck"))
    chat = TestChat(config)
    chat.app.register_action(retrieve_relevant_chunks, "retrieve_relevant_chunks")

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


@pytest.mark.asyncio
async def test_fact_checking_correct(httpx_mock):
    # Test 2 - Factual statement - high score
    config = RailsConfig.from_path(os.path.join(CONFIGS_FOLDER, "autoguard_factcheck"))
    chat = TestChat(config)
    chat.app.register_action(retrieve_relevant_chunks, "retrieve_relevant_chunks")

    httpx_mock.add_response(
        method="POST",
        url=NEMO_API_URL_GPT_43B_002,
        json={"text": "  ask about guardrails"},
    )

    httpx_mock.add_response(
        method="POST",
        url=NEMO_API_URL_GPT_43B_002,
        json={
            "text": "NeMo Guardrails is an open-source toolkit for easily adding programmable guardrails to LLM-based conversational systems."
        },
    )

    with aioresponses() as m:
        # Fact-checking using score
        m.post(
            "http://35.225.99.81:8888/factcheck",
            payload={
                "response": "Factcheck Score: 0.82",
                "guarded": False,
                "task": "factcheck",
            },
        )

        # Succeeded, no more generations needed
        chat >> "What is NeMo Guardrails?"

        await chat.bot_async(
            "NeMo Guardrails is an open-source toolkit for easily adding programmable guardrails to LLM-based conversational systems."
        )


@pytest.mark.asyncio
async def test_fact_checking_wrong(httpx_mock):
    # Test 3 - Very low score - Not factual
    config = RailsConfig.from_path(os.path.join(CONFIGS_FOLDER, "autoguard_factcheck"))
    chat = TestChat(config)
    chat.app.register_action(retrieve_relevant_chunks, "retrieve_relevant_chunks")

    httpx_mock.add_response(
        method="POST",
        url=NEMO_API_URL_GPT_43B_002,
        json={"text": "  ask about guardrails"},
    )

    httpx_mock.add_response(
        method="POST",
        url=NEMO_API_URL_GPT_43B_002,
        json={
            "text": "NeMo Guardrails is a closed-source proprietary toolkit by Nvidia."
        },
    )

    with aioresponses() as m:
        # Fact-checking using score
        m.post(
            "http://35.225.99.81:8888/factcheck",
            payload={
                "response": "Factcheck Score: 0.01",
                "guarded": False,
                "task": "factcheck",
            },
        )

        chat >> "What is NeMo Guardrails?"

        await chat.bot_async("I don't know the answer that.")


@pytest.mark.asyncio
async def test_fact_checking_uncertain(httpx_mock):
    # Test 4 - Factual statement - score not very confident in its prediction
    config = RailsConfig.from_path(os.path.join(CONFIGS_FOLDER, "autoguard_factcheck"))
    chat = TestChat(config)
    chat.app.register_action(retrieve_relevant_chunks, "retrieve_relevant_chunks")

    httpx_mock.add_response(
        method="POST",
        url=NEMO_API_URL_GPT_43B_002,
        json={"text": "  ask about guardrails"},
    )

    httpx_mock.add_response(
        method="POST",
        url=NEMO_API_URL_GPT_43B_002,
        json={
            "text": "NeMo Guardrails is a closed-source proprietary toolkit by Nvidia."
        },
    )

    with aioresponses() as m:
        ## Fact-checking using score
        m.post(
            "http://35.225.99.81:8888/factcheck",
            payload={
                "response": "Factcheck Score: 0.58",
                "guarded": False,
                "task": "factcheck",
            },
        )

        chat >> "What is NeMo Guardrails?"
        await chat.bot_async(
            "NeMo Guardrails is a closed-source proprietary toolkit by Nvidia.\n"
            + "Attention: the answer above is potentially inaccurate."
        )
