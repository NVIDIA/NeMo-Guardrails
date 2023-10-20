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

from aioresponses import aioresponses

from nemoguardrails import RailsConfig
from tests.utils import TestChat


def test_1(monkeypatch):
    monkeypatch.setenv("ACTIVE_FENCE_API_KEY", "xxx")

    config = RailsConfig.from_content(
        colang_content="""
            define user express greeting
              "hi"

            define flow
              user express greeting
              bot express greeting

            define bot express greeting
              "Hello! How can I assist you today?"
        """,
        yaml_content="""
            models:
              - type: main
                engine: openai
                model: text-davinci-003

            rails:
              input:
                flows:
                  - active fence moderation
        """,
    )
    chat = TestChat(
        config,
        llm_completions=[
            "  express greeting",
        ],
    )

    with aioresponses() as m:
        # First call to ActiveFence should flag no violations.
        m.post(
            "https://apis.activefence.com/sync/v3/content/text",
            payload={
                "response_id": "36f76a43-ddbe-4308-bc86-1a2b068a00ea",
                "entity_id": "59fe8fe0-5036-494f-970c-8e28305a3716",
                "entity_type": "content",
                "violations": [],
                "errors": [],
            },
        )

        chat >> "Hello!"
        chat << "Hello! How can I assist you today?"

        # Second call will flag an abusive_or_harmful violation.
        m.post(
            "https://apis.activefence.com/sync/v3/content/text",
            payload={
                "response_id": "36f76a43-ddbe-4308-bc86-1a2b068a00ea",
                "entity_id": "59fe8fe0-5036-494f-970c-8e28305a3716",
                "entity_type": "content",
                "violations": [
                    {
                        "violation_type": "abusive_or_harmful.harassment_or_bullying",
                        "risk_score": 0.95,
                    }
                ],
                "errors": [],
            },
        )

        chat >> "you are stupid!"
        chat << "I am not able to answer the question."
