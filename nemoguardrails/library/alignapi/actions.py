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


@action(name="call alignapi", is_system_action=True)
async def call_alignapi(context: Optional[dict] = None):
    api_key = os.environ.get("ALIGNAPI_KEY")

    if api_key is None:
        raise ValueError("ALIGNAPI_KEY environment variable not set.")

    user_message = context.get("user_message")

    url = "https://api.alignapi.com/align"
    headers = {"access_token": api_key}
    data = {
        "text": user_message,
    }

    async with aiohttp.ClientSession() as session:
        async with session.get(
            url=url,
            headers=headers,
            json=data,
        ) as response:
            if response.status != 200:
                raise ValueError(
                    f"Alignapi call failed with status code {response.status}.\n"
                    f"Details: {await response.text()}"
                )
            response_json = await response.json()

            violations_dict = {}
            max_risk_score = 0
            for violation in response_json:
                if response_json[violation] > max_risk_score:
                    max_risk_score = response_json[violation]

                violations_dict[violation] = response_json[violation]

            return {"max_risk_score": max_risk_score, "violations": violations_dict}
