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

import logging
from typing import Optional

import aiohttp

from nemoguardrails.actions import action

log = logging.getLogger(__name__)

API_URL = f"http://localhost:5000/alignscore_large"
ALIGNSCORE_THRESHOLD = 0.6


@action(name="alignscore request")
async def alignscore_request(
    context: Optional[str] = None
):
    """Checks the facts for the bot response by making a request to the AlignScore API."""
    evidence = context.get("relevant_chunks", [])
    response = context.get("last_bot_message")

    if not evidence:
        return True

    if response is None:
        raise Exception("No claim or context was provided to AlignScore.")
    
    payload = {"evidence": evidence, "claim": response}

    async with aiohttp.ClientSession() as session:
        async with session.post(API_URL, json=payload) as resp:
            
            if resp.status != 200:
                print(f"AlignScore API request failed with status {resp.status}")
                return None

            result = await resp.text()

            log.info(f"AlignScore was {result}.")
            try:
                result = float(result)
            except Exception:
                result = None
            return result
