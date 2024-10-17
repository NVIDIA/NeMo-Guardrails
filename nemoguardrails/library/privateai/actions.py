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

"""PII detection using Private AI."""

import logging

from nemoguardrails import RailsConfig
from nemoguardrails.actions import action
from nemoguardrails.library.privateai.request import private_ai_detection_request
from nemoguardrails.rails.llm.config import PrivateAIDetection

log = logging.getLogger(__name__)


@action(is_system_action=True)
async def detect_pii(source: str, text: str, config: RailsConfig):
    """Checks whether the provided text contains any PII.

    Args
        source: The source for the text, i.e. "input", "output", "retrieval".
        text: The text to check.
        config: The rails configuration object.

    Returns
        True if PII is detected, False otherwise.
    """

    pai_config: PrivateAIDetection = getattr(config.rails.config, "privateai")

    assert source in ["input", "output", "retrieval"], f"Private AI can only be defined in the input, output and retrieval flows. The current flow {source} is not allowed."

    entity_detected = await private_ai_detection_request(
        text,
        getattr(pai_config, source).entities,
        pai_config.server_endpoint,
        pai_config.api_key,
    )

    if entity_detected is None:
        log.error("Private AI detection API request failed.")
        # if the request fails, we assume that PII is detected
        return True

    return entity_detected
