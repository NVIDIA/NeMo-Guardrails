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

import textwrap

import pytest

from nemoguardrails import RailsConfig
from nemoguardrails.llm.taskmanager import LLMTaskManager
from nemoguardrails.llm.types import Task


def test_openai_text_davinci_prompts():
    """Test the prompts for the OpenAI text-davinci-003 model."""
    config = RailsConfig.from_content(
        yaml_content=textwrap.dedent(
            """
            models:
             - type: main
               engine: openai
               model: text-davinci-003
            """
        )
    )

    assert config.models[0].engine == "openai"

    llm_task_manager = LLMTaskManager(config)

    generate_user_intent_prompt = llm_task_manager.render_task_prompt(
        task=Task.GENERATE_USER_INTENT
    )

    assert isinstance(generate_user_intent_prompt, str)
    assert "This is how the user talks" in generate_user_intent_prompt


@pytest.mark.parametrize(
    "task",
    [
        Task.GENERATE_USER_INTENT,
        Task.GENERATE_NEXT_STEPS,
        Task.GENERATE_BOT_MESSAGE,
        Task.GENERATE_VALUE,
    ],
)
def test_openai_gpt_3_5_turbo_prompts(task):
    """Test the prompts for the OpenAI GPT-3 5 Turbo model."""
    config = RailsConfig.from_content(
        yaml_content=textwrap.dedent(
            """
            models:
             - type: main
               engine: openai
               model: gpt-3.5-turbo
            """
        )
    )

    assert config.models[0].engine == "openai"

    llm_task_manager = LLMTaskManager(config)

    task_prompt = llm_task_manager.render_task_prompt(
        task=task,
        context={"examples": 'user "Hello there!"\n  express greeting'},
    )

    assert isinstance(task_prompt, list)
