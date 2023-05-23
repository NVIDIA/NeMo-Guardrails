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
from typing import List

import yaml

from nemoguardrails.rails.llm.config import Prompt, RailsConfig

CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))


class Task(Enum):
    """The various tasks that can be performed by the LLM."""

    GENERAL = "general"
    GENERATE_USER_INTENT = "generate_user_intent"
    GENERATE_NEXT_STEPS = "generate_next_steps"
    GENERATE_BOT_MESSAGE = "generate_bot_message"
    GENERATE_VALUE = "generate_value"

    FACT_CHECKING = "fact_checking"
    JAILBREAK_CHECK = "jailbreak_check"
    OUTPUT_MODERATION = "output_moderation"
    CHECK_HALLUCINATION = "check_hallucination"


def _load_prompts() -> List[Prompt]:
    """Load the predefined prompts from the `prompts` directory."""
    prompts = []

    for root, dirs, files in os.walk(os.path.join(CURRENT_DIR, "prompts")):
        for filename in files:
            if filename.endswith(".yml"):
                with open(
                    os.path.join(root, filename), encoding="utf-8"
                ) as prompts_file:
                    prompts.extend(yaml.safe_load(prompts_file.read())["prompts"])

    return [Prompt(**prompt) for prompt in prompts]


_prompts = _load_prompts()


def _get_prompt(task_name: str, model: str, prompts: List) -> Prompt:
    """Return the prompt for the given task.

    We intentionally update the matching model at equal score, to take the last one,
    basically allowing to override a prompt for a specific model.
    """
    matching_prompt = None
    matching_score = 0

    for prompt in prompts:
        if prompt.task != task_name:
            continue

        _score = 0

        # If no model is specified, we are dealing with a general prompt, and it has the
        # lowest score.
        if not prompt.models:
            _score = 0.2
        else:
            for _model in prompt.models:
                # If we have an exact match, the score is 1.
                if _model == model:
                    _score = 1
                    break

                # If we match just the provider, the score is 0.5.
                elif model.startswith(_model + "/"):
                    _score = 0.5
                    break

        if _score >= matching_score:
            matching_score = _score
            matching_prompt = prompt

    if matching_prompt:
        return matching_prompt

    raise ValueError(f"Could not find prompt for task {task_name} and model {model}")


def get_prompt(config: RailsConfig, task: Task) -> Prompt:
    """Return the prompt for the given step."""
    # Currently, we use the main model for all tasks
    # TODO: add support to use different models for different tasks
    task_model = "unknown"
    if config.models:
        task_model = config.models[0].engine
        if config.models[0].model:
            task_model += "/" + config.models[0].model
    task_name = str(task.value)

    prompts = _prompts + (config.prompts or [])
    prompt = _get_prompt(task_name, task_model, prompts)

    if prompt:
        return prompt
    else:
        raise ValueError(f"No prompt found for task: {task}")
