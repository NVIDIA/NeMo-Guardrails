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

"""Module for handling Private AI detection requests."""

import json
import logging
from typing import Any, Dict, List, Optional

import aiohttp

log = logging.getLogger(__name__)


async def private_ai_detection_request(
    text: str,
    enabled_entities: List[str],
    server_endpoint: str,
    api_key: Optional[str] = None,
):
    """
    Send a detection request to the Private AI API.

    Args:
        text: The text to analyze.
        enabled_entities: List of entity types to detect.
        server_endpoint: The API endpoint URL.
        api_key: The API key for the Private AI service.

    Returns:
        True if entities detected, False if not, None if request failed.
    """
    if "api.private-ai.com" in server_endpoint and not api_key:
        log.error("'api_key' is required for Private AI cloud API.")
        return None

    payload_dict: Dict[str, Any] = {
        "text": [text],
        "link_batch": False,
        "entity_detection": {"accuracy": "high_automatic", "return_entity": False},
    }

    headers: Dict[str, str] = {
        "Content-Type": "application/json",
    }

    if api_key:
        headers["x-api-key"] = api_key

    if enabled_entities:
        payload_dict["entity_detection"]["entity_types"] = [
            {"type": "ENABLE", "value": enabled_entities}
        ]

    payload = json.dumps(payload_dict)

    async with aiohttp.ClientSession() as session:
        async with session.post(server_endpoint, data=payload, headers=headers) as resp:
            if resp.status != 200:
                log.error(
                    f"Private AI detection API request failed with status {resp.status}"
                )
                return None

            result = await resp.json()

            return any(res["entities_present"] for res in result)
