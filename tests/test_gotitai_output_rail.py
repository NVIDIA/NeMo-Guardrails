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
from tests.utils import TestChat

CONFIGS_FOLDER = os.path.join(os.path.dirname(__file__), ".", "test_configs")

GOTITAI_API_URL = "https://api.got-it.ai/api/v1/hallucination-manager/truthchecker"


@action(is_system_action=True)
async def retrieve_relevant_chunks():
    """Retrieve relevant chunks from the knowledge base and add them to the context."""
    context_updates = {}
    context_updates["relevant_chunks"] = ["Shipping takes at least 3 days."]

    return ActionResult(
        return_value=context_updates["relevant_chunks"],
        context_updates=context_updates,
    )


@pytest.mark.asyncio
async def test_hallucination(monkeypatch):
    monkeypatch.setenv("GOTITAI_API_KEY", "xxx")
    config = RailsConfig.from_path(os.path.join(CONFIGS_FOLDER, "gotitai_truthchecker"))
    chat = TestChat(
        config,
        llm_completions=[
            "user ask general question",  # user intent
            "Yes, shipping can be done in 2 days.",  # bot response that will be intercepted
        ],
    )

    with aioresponses() as m:
        chat.app.register_action(retrieve_relevant_chunks, "retrieve_relevant_chunks")
        m.post(
            GOTITAI_API_URL,
            payload={
                "hallucination": "yes",
            },
        )

        chat >> "Do you ship within 2 days?"
        await chat.bot_async("I don't know the answer to that.")


@pytest.mark.asyncio
async def test_not_hallucination(monkeypatch):
    monkeypatch.setenv("GOTITAI_API_KEY", "xxx")
    config = RailsConfig.from_path(os.path.join(CONFIGS_FOLDER, "gotitai_truthchecker"))
    chat = TestChat(
        config,
        llm_completions=[
            # "  express greeting",
            "user ask general question",  # user intent
            "No, shipping takes at least 3 days.",  # bot response that will not be intercepted
        ],
    )

    with aioresponses() as m:
        chat.app.register_action(retrieve_relevant_chunks, "retrieve_relevant_chunks")
        m.post(
            GOTITAI_API_URL,
            payload={
                "hallucination": "no",
            },
        )

        chat >> "Do you ship within 2 days?"
        await chat.bot_async("No, shipping takes at least 3 days.")
