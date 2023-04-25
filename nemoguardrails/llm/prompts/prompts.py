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

"""Prompts for the various steps in the interaction."""
import os
from enum import Enum

import yaml

from nemoguardrails.rails.llm.config import RailsConfig

CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))


class Step(Enum):
    """Enumeration for the current step in the process."""

    GENERAL = "general"
    DETECT_USER_MESSAGE_CANONICAL_FORM = "detect_user_message_canonical_form"
    PREDICT_NEXT_STEP = "predict_next_step"
    GENERATE_BOT_MESSAGE = "generate_bot_message"


# Load the dictionary of prompts from the `prompts.yml` file
def _load_prompts():
    """Load the dictionary of prompts from the `prompts.yml` file."""
    with open(
        os.path.join(CURRENT_DIR, "prompts.yml"), encoding="utf-8"
    ) as prompts_file:
        return yaml.safe_load(prompts_file.read())["prompts"]


_prompts = _load_prompts()


def get_prompt(config: RailsConfig, step: Step) -> dict:
    """Return the prompt for the given step."""
    if step == Step.GENERAL:
        prompt = _prompts["general"][0]

        # If we have a prompt that is specific to the LLM, we use it.
        for _prompt in _prompts["general"]:
            if _prompt.get("model") == config.models[0].model:
                prompt = _prompt
                break

        return prompt

    if step == Step.DETECT_USER_MESSAGE_CANONICAL_FORM:
        return _prompts["detect_user_message_canonical_form"][0]

    if step == Step.PREDICT_NEXT_STEP:
        return _prompts["predict_next_step"][0]

    if step == Step.GENERATE_BOT_MESSAGE:
        return _prompts["generate_bot_message"][0]

    raise ValueError(f"Unknown step: {step}")
