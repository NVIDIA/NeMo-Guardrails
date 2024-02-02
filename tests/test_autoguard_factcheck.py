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

from nemoguardrails import LLMRails, RailsConfig
from nemoguardrails.actions.actions import ActionResult, action
from tests.constants import NEMO_API_URL_GPT_43B_002
from tests.utils import TestChat

CONFIGS_FOLDER = os.path.join(os.path.dirname(__file__), ".", "test_configs")


def build_kb():
    with open(
        os.path.join(CONFIGS_FOLDER, "autoguard", "factcheck", "kb", "kb.md"), "r"
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
async def test_fact_checking_correct():
    config = RailsConfig.from_path(os.path.join(CONFIGS_FOLDER, "autoguard/factcheck"))
    chat = TestChat(config)
    chat.history = []
    chat.app.register_action(retrieve_relevant_chunks, "retrieve_relevant_chunks")
    chat >> "What is NeMo Guardrails?"
    await chat.bot_async(
        """NeMo Guardrails is an open-source toolkit for easily adding programmable guardrails to large language model (LLM)-based conversational systems. Guardrails, also known as "rails," are specific ways of controlling the output of a language model. They can be used to ensure the model\'s responses align with certain guidelines or constraints, such as avoiding certain topics, following a predefined dialog path, using a particular language style, or extracting structured data.\nThe purpose of NeMo Guardrails is to make the power of trustworthy, safe, and secure LLMs accessible to everyone. It is currently in its early alpha stages, and the community is invited to contribute towards its development. The examples provided within the documentation are for educational purposes to help users get started with NeMo Guardrails, but they are not meant for use in production applications.\nIf you have any specific questions about NeMo Guardrails or would like more information, feel free to ask!"""
    )


@pytest.mark.asyncio
async def test_fact_checking_uncertain():
    config = RailsConfig.from_path(os.path.join(CONFIGS_FOLDER, "autoguard/factcheck"))
    chat = TestChat(config)
    chat.history = []
    chat.app.register_action(retrieve_relevant_chunks, "retrieve_relevant_chunks")
    chat >> "What is the current version of NeMo Guardrails?"

    await chat.bot_async(
        "I'm sorry, but I don't have access to real-time information about the current version of NeMo Guardrails. However, as mentioned in the sample knowledge base, NeMo Guardrails is currently in its early alpha stages. It's always a good idea to check the official NeMo Guardrails documentation or the project's repository for the most up-to-date information on the current version.Attention: the answer above is potentially inaccurate."
    )
