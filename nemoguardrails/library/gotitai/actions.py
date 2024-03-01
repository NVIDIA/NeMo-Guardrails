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
import json
import logging
import os
from typing import Optional

import aiohttp

from nemoguardrails.actions import action

log = logging.getLogger(__name__)


@action(name="call gotitai truthchecker api", is_system_action=True)
async def call_gotitai_truthchecker_api(context: Optional[dict] = None):
    api_key = os.environ.get("GOTITAI_API_KEY")

    if api_key is None:
        raise ValueError("GOTITAI_API_KEY environment variable not set.")

    if context is None:
        raise ValueError(
            "Context is empty. `user_message`, `bot_response` and `relevant_chunks` keys are required to call the GotIt AI Truthchecker api."
        )

    user_message = context.get("user_message", "")
    response = context.get("bot_message", "")
    knowledge = context.get("relevant_chunks", [])

    if not isinstance(knowledge, list):
        raise ValueError("`relevant_chunks` must be a list of knowledge.")

    if not knowledge:
        raise ValueError("At least 1 relevant chunk is required.")

    url = "https://api.got-it.ai/api/v1/hallucination-manager/truthchecker"
    headers = {
        "Content-Type": "application/json",
        "Authorization": "Bearer " + api_key,
    }
    data = {
        "knowledge": [
            {
                "text": chunk,
            }
            for chunk in knowledge
        ],
        "prompt": user_message,
        "generated_text": response,
        # Messages is empty for now since there is no standard way to get them.
        # This should be updated once 0.8.0 is released.
        # Reference: https://github.com/NVIDIA/NeMo-Guardrails/issues/246
        "messages": [],
    }

    async with aiohttp.ClientSession() as session:
        async with session.post(
            url=url,
            headers=headers,
            json=data,
        ) as response:
            if response.status != 200:
                raise ValueError(
                    f"GotItAI TruthChecking call failed with status code {response.status}.\n"
                    f"Details: {await response.json()}"
                )
            response_json = await response.json()
            log.info(json.dumps(response_json, indent=True))
            hallucination = response_json["hallucination"]

            return {"hallucination": hallucination}
