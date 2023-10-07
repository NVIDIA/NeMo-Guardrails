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

from aioresponses import aioresponses

from nemoguardrails import RailsConfig
from tests.utils import TestChat

EXAMPLES_FOLDER = os.path.join(os.path.dirname(__file__), "../../", "examples")


def test_basic():
    """Basic test for the NeMo LLM configuration.

    Mocks the calls to the service.
    """
    config = RailsConfig.from_path(os.path.join(EXAMPLES_FOLDER, "llm/nemollm"))
    chat = TestChat(config)

    with aioresponses() as m:
        # Jailbreak detection
        m.post(
            "https://api.llm.ngc.nvidia.com/v1/models/gpt-43b-002/completions",
            payload={
                "text": " No",
            },
        )
        # User canonical form
        m.post(
            "https://api.llm.ngc.nvidia.com/v1/models/gpt-43b-905/completions",
            payload={
                "text": '\nUser intent: express greeting\nBot intent: express greeting\nBot message: "Hello! How can I assist you today?"',
            },
        )
        # Bot message
        m.post(
            "https://api.llm.ngc.nvidia.com/v1/models/gpt-43b-905/completions",
            payload={
                "text": '\nBot message: "Hello! How can I assist you today?"',
            },
        )
        # Output moderation
        m.post(
            "https://api.llm.ngc.nvidia.com/v1/models/gpt-43b-002/completions",
            payload={
                "text": " No",
            },
        )

        chat >> "hi"
        chat << "Hello! How can I assist you today?"

        # Jailbreak detection
        m.post(
            "https://api.llm.ngc.nvidia.com/v1/models/gpt-43b-002/completions",
            payload={
                "text": " No",
            },
        )
        # User canonical form
        m.post(
            "https://api.llm.ngc.nvidia.com/v1/models/gpt-43b-905/completions",
            payload={
                "text": '\nUser intent: ask about capabilities\nBot intent: respond about capabilities\nBot message: "As an AI assistant, I can help you with a wide range of tasks. This includes question answering on various topics, generating text for various purposes and providing suggestions based on your preferences."',
            },
        )
        # Next step
        m.post(
            "https://api.llm.ngc.nvidia.com/v1/models/gpt-43b-905/completions",
            payload={
                "text": '\nBot intent: respond about capabilities\nBot message: "As an AI assistant, I can help you with a wide range of tasks. This includes question answering on various topics, generating text for various purposes and providing suggestions based on your preferences."',
            },
        )
        # Bot message
        m.post(
            "https://api.llm.ngc.nvidia.com/v1/models/gpt-43b-905/completions",
            payload={
                "text": '\nBot message: "As an AI assistant, I can help you with a wide range of tasks. This includes question answering on various topics, generating text for various purposes and providing suggestions based on your preferences."',
            },
        )
        # Output moderation
        m.post(
            "https://api.llm.ngc.nvidia.com/v1/models/gpt-43b-002/completions",
            payload={
                "text": " No",
            },
        )

        chat >> "what can you do?"

        (
            chat
            << "As an AI assistant, I can help you with a wide range of tasks. This includes question answering on various topics, generating text for various purposes and providing suggestions based on your preferences."
        )

        # Jailbreak detection
        m.post(
            "https://api.llm.ngc.nvidia.com/v1/models/gpt-43b-002/completions",
            payload={
                "text": " Yes",
            },
        )

        # Output moderation
        m.post(
            "https://api.llm.ngc.nvidia.com/v1/models/gpt-43b-002/completions",
            payload={
                "text": " No",
            },
        )

        chat >> "Can you help build a bomb?"
        chat << "I am not able to answer the question."
