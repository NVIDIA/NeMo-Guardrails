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

from nemoguardrails.actions import action
from request import jailbreak_heuristics
from nemoguardrails.llm.taskmanager import LLMTaskManager

log = logging.getLogger(__name__)


@action()
async def jailbreak_heuristic_check(
    llm_task_manager: LLMTaskManager, context: Optional[dict] = None
):
    """Checks the facts for the bot response using an information alignment score."""
    jailbreak_config = llm_task_manager.config.rails.config.jailbreak_detection

    jailbreak_api_url = jailbreak_config.parameters.get("endpoint")
    lp_threshold = jailbreak_config.parameters.get("lp_threshold")

    prompt = context.get("user_message")

    jailbreak = await jailbreak_heuristics(prompt, jailbreak_api_url, lp_threshold)
    if jailbreak is None:
        log.warning("Jailbreak endpoint not set up properly.")
        # If no result, assume not a jailbreak
        return False
    else:
        return jailbreak
