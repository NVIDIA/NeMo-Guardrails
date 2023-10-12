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
from nemoguardrails.actions.actions import ActionResult
from tests.utils import TestChat

CONFIGS_FOLDER = os.path.join(os.path.dirname(__file__), ".", "test_configs")


def build_kb():
    with open(os.path.join(CONFIGS_FOLDER, "fact_checking", "kb", "kb.md"), 'r') as f:
        content = f.readlines()
        
    return content


async def retrieve_relevant_chunks():
    """Retrieve relevant chunks from the knowledge base and add them to the context."""
    context_updates = {}
    relevant_chunks = "\n".join(build_kb())
    context_updates["relevant_chunks"] = relevant_chunks

    return ActionResult(
        return_value=context_updates["relevant_chunks"],
        context_updates=context_updates,
    )
    

def test_fact_checking_greeting():
    # Test 1 - Greeting - No fact-checking invocation should happen
    config = RailsConfig.from_path(os.path.join(CONFIGS_FOLDER, "fact_checking"))
    chat = TestChat(config)
    chat.app.register_action(retrieve_relevant_chunks, "retrieve_relevant_chunks")

    with aioresponses() as m:
        m.post(
            "https://api.llm.ngc.nvidia.com/v1/models/gpt-43b-002/completions",
            payload={
                "text": "  express greeting"
            }
        )
        m.post(
            "https://api.llm.ngc.nvidia.com/v1/models/gpt-43b-002/completions",
            payload={
                "text": "Hi! How can I assist today?"
            }
        )
        chat >> "hi"
        chat << "Hi! How can I assist today?"


def test_fact_checking_correct():
    # Test 2 - Factual statement - high alignscore
    config = RailsConfig.from_path(os.path.join(CONFIGS_FOLDER, "fact_checking"))
    chat = TestChat(config)
    chat.app.register_action(retrieve_relevant_chunks, "retrieve_relevant_chunks")

    with aioresponses() as m:
        m.post(
            "https://api.llm.ngc.nvidia.com/v1/models/gpt-43b-002/completions",
            payload={
                "text": "  ask about guardrails"
            }
        )
        m.post(
            "https://api.llm.ngc.nvidia.com/v1/models/gpt-43b-002/completions",
            payload={
                "text": "NeMo Guardrails is an open-source toolkit for easily adding programmable guardrails to LLM-based conversational systems."
            }
        )
        ## Fact-checking using AlignScore
        m.post(
            "http://localhost:5000/alignscore_large",
            payload=0.82,
        )
        chat >> "What is NeMo Guardrails?"
        chat << "NeMo Guardrails is an open-source toolkit for easily adding programmable guardrails to LLM-based conversational systems."


def test_fact_checking_wrong():
    # Test 3 - Very low alignscore - Not factual
    config = RailsConfig.from_path(os.path.join(CONFIGS_FOLDER, "fact_checking"))
    chat = TestChat(config)
    chat.app.register_action(retrieve_relevant_chunks, "retrieve_relevant_chunks")

    with aioresponses() as m:
        m.post(
            "https://api.llm.ngc.nvidia.com/v1/models/gpt-43b-002/completions",
            payload={
                "text": "  ask about guardrails"
            }
        )
        m.post(
            "https://api.llm.ngc.nvidia.com/v1/models/gpt-43b-002/completions",
            payload={
                "text": "NeMo Guardrails is a closed-source proprietary toolkit by Nvidia."
            }
        )
        ## Fact-checking using AlignScore
        m.post(
            "http://localhost:5000/alignscore_large",
            payload=0.01,
        )
        m.post(
            "https://api.llm.ngc.nvidia.com/v1/models/gpt-43b-002/completions",
            payload={
                "text": "The fact-checking rail failed. Sorry, I don't know the answer to this question"
            }
        )
        chat >> "What is NeMo Guardrails?"
        chat << "The fact-checking rail failed. Sorry, I don't know the answer to this question"


def test_fact_checking_uncertain():
    # Test 4 - Factual statement - AlignScore not very confident in its prediction
    config = RailsConfig.from_path(os.path.join(CONFIGS_FOLDER, "fact_checking"))
    chat = TestChat(config)
    chat.app.register_action(retrieve_relevant_chunks, "retrieve_relevant_chunks")

    with aioresponses() as m:
        m.post(
            "https://api.llm.ngc.nvidia.com/v1/models/gpt-43b-002/completions",
            payload={
                "text": "  ask about guardrails"
            }
        )
        m.post(
            "https://api.llm.ngc.nvidia.com/v1/models/gpt-43b-002/completions",
            payload={
                "text": "NeMo Guardrails is an open-source toolkit for adding safeguards to conversational systems."
            }
        )
        ## Fact-checking using AlignScore
        m.post(
            "http://localhost:5000/alignscore_large",
            payload=0.58,
        )
        m.post(
            "https://api.llm.ngc.nvidia.com/v1/models/gpt-43b-002/completions",
            payload={
                "text": "The previous answer might have slight inaccuracies, kindly consult the original source."
            }
        )
        chat >> "What is NeMo Guardrails?"
        chat << (
            "NeMo Guardrails is an open-source toolkit for adding safeguards to conversational systems.\n" + 
            "The previous answer might have slight inaccuracies, kindly consult the original source."
        )



def test_fact_checking_fallback_to_ask_llm_correct():
    # Test 4 - Factual statement - AlignScore endpoint not set up properly, use ask llm for fact-checking
    config = RailsConfig.from_path(os.path.join(CONFIGS_FOLDER, "fact_checking"))
    chat = TestChat(config)
    chat.app.register_action(retrieve_relevant_chunks, "retrieve_relevant_chunks")

    with aioresponses() as m:
        m.post(
            "https://api.llm.ngc.nvidia.com/v1/models/gpt-43b-002/completions",
            payload={
                "text": "  ask about guardrails"
            }
        )
        m.post(
            "https://api.llm.ngc.nvidia.com/v1/models/gpt-43b-002/completions",
            payload={
                "text": "NeMo Guardrails is an open-source toolkit for easily adding programmable guardrails to LLM-based conversational systems."
            }
        )
        ## Fact-checking using AlignScore
        m.post(
            "http://localhost:5000/alignscore_large",
            payload="API error 404",
        )
        m.post(
            "https://api.llm.ngc.nvidia.com/v1/models/gpt-43b-002/completions",
            payload={
                "text": "yes"
            }
        )
        chat >> "What is NeMo Guardrails?"
        chat << "NeMo Guardrails is an open-source toolkit for easily adding programmable guardrails to LLM-based conversational systems."



def test_fact_checking_fallback_to_ask_llm_wrong():
    # Test 4 - Factual statement - AlignScore endpoint not set up properly, use ask llm for fact-checking
    config = RailsConfig.from_path(os.path.join(CONFIGS_FOLDER, "fact_checking"))
    chat = TestChat(config)
    chat.app.register_action(retrieve_relevant_chunks, "retrieve_relevant_chunks")

    with aioresponses() as m:
        m.post(
            "https://api.llm.ngc.nvidia.com/v1/models/gpt-43b-002/completions",
            payload={
                "text": "  ask about guardrails"
            }
        )
        m.post(
            "https://api.llm.ngc.nvidia.com/v1/models/gpt-43b-002/completions",
            payload={
                "text": "NeMo Guardrails is an open-source toolkit for easily adding programmable guardrails to LLM-based conversational systems."
            }
        )
        ## Fact-checking using AlignScore
        m.post(
            "http://localhost:5000/alignscore_large",
            payload="API error 404",
        )
        m.post(
            "https://api.llm.ngc.nvidia.com/v1/models/gpt-43b-002/completions",
            payload={
                "text": "no"
            }
        )
        m.post(
            "https://api.llm.ngc.nvidia.com/v1/models/gpt-43b-002/completions",
            payload={
                "text": "The fact-checking rail failed. Sorry, I don't know the answer to this question"
            }
        )
        chat >> "What is NeMo Guardrails?"
        chat << "The fact-checking rail failed. Sorry, I don't know the answer to this question"