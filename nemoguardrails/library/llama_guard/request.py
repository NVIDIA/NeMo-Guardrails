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


@action(name="llama guard request")
async def llama_guard_request(
    prompt: str,
    max_tokens: Optional[int] = 300,
    temperature: Optional[float] = 0.0,
    api_url: str = "http://localhost:5123/generate",
):
    """
    Assumes that a Llama Guard inference endpoint is running locally/on-prem.

    Checks messages against safety guidelines using Llama Guard.
    Expects the prompt to contain the safety guidelines.
    """

    payload = {"prompt": prompt, "max_tokens": max_tokens, "temperature": temperature}

    async with aiohttp.ClientSession() as session:
        async with session.post(api_url, json=payload) as resp:
            if resp.status != 200:
                log.error(f"LlamaGuard API request failed with status {resp.status}")
                return None

            result = await resp.json()
            try:
                result = result["text"][0]
                # For some reason, the vLLM implementation adds the prompt to the beginning of the result.
                # Perhaps rewrite the inference code.
                result = result.replace(prompt, "").strip()
                return result

            except Exception as e:
                log.error(f"Error parsing Llama Guard response: {e}")

    # In case of error, return None
    return None
