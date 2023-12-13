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
from nemoguardrails.language.utils import new_uuid

log = logging.getLogger(__name__)


@action(name="call activefence api", is_system_action=True)
async def call_activefence_api(context: Optional[dict] = None):
    api_key = os.environ.get("ACTIVEFENCE_API_KEY")

    if api_key is None:
        raise ValueError("ACTIVEFENCE_API_KEY environment variable not set.")

    user_message = context.get("user_message")

    url = "https://apis.activefence.com/sync/v3/content/text"
    headers = {"af-api-key": api_key, "af-source": "nemo-guardrails"}
    data = {
        "text": user_message,
        "content_id": "ng-" + new_uuid(),
    }

    async with aiohttp.ClientSession() as session:
        async with session.post(
            url=url,
            headers=headers,
            json=data,
        ) as response:
            if response.status != 200:
                raise ValueError(
                    f"ActiveFence call failed with status code {response.status}.\n"
                    f"Details: {await response.text()}"
                )
            response_json = await response.json()
            log.info(json.dumps(response_json, indent=True))
            violations = response_json["violations"]

            violations_dict = {}
            max_risk_score = 0.0
            for violation in violations:
                if violation["risk_score"] > max_risk_score:
                    max_risk_score = violation["risk_score"]
                violations_dict[violation["violation_type"]] = violation["risk_score"]

            return {"max_risk_score": max_risk_score, "violations": violations_dict}
