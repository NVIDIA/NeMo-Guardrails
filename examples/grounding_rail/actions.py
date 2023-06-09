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
from typing import Any, List, Optional

from nemoguardrails.actions import action
from nemoguardrails.actions.actions import ActionResult


@action(is_system_action=True)
async def check_if_time_based_query(events: List[dict], context: Optional[dict] = None):
    i = len(events) - 1
    while events[i]["type"] != "user_said" and i > 0:
        i -= 1

    last_user_said = events[i]

    if last_user_said.get("altered"):
        return

    # print(last_user_said)
    # print(f"The last user message is: {last_user_said['content']}")

    return ActionResult(
        events=[
            {
                "type": "user_said",
                "content": last_user_said["content"] + " and nothing",
                "altered": True,
            }
        ]
    )
