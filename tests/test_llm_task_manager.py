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
from nemoguardrails.llm.filters import conversation_to_events
from nemoguardrails.llm.prompts import get_prompt
from nemoguardrails.llm.taskmanager import LLMTaskManager
from nemoguardrails.llm.types import Task

# TODO: Fix this test
# def test_openai_text_davinci_prompts():
#     """Test the prompts for the OpenAI text-davinci-003 model."""
#     config = RailsConfig.from_content(
#         yaml_content=textwrap.dedent(
#             """
#             models:
#              - type: main
#                engine: openai
#                model: text-davinci-003
#             """
#         )
#     )

#     assert config.models[0].engine == "openai"


def test_openai_text_davinci_prompts():
    """Test the prompts for the OpenAI gpt-3.5-turbo-instruct model."""
    config = RailsConfig.from_content(
        yaml_content=textwrap.dedent(
            """
            models:
             - type: main
               engine: openai
               model: gpt-3.5-turbo-instruct
            """
        )
    )


#     llm_task_manager = LLMTaskManager(config)

#     generate_user_intent_prompt = llm_task_manager.render_task_prompt(
#         task=Task.GENERATE_USER_INTENT
#     )

#     assert isinstance(generate_user_intent_prompt, str)
#     assert "This is how the user talks" in generate_user_intent_prompt


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
    """Test the prompts for the OpenAI GPT-3.5 Turbo model."""
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


@pytest.mark.parametrize(
    "task, expected_prompt",
    [
        ("summarize_text", "Text: test.\nSummarize the above text."),
        ("compose_response", "Text: test.\nCompose a response using the above text."),
    ],
)
def test_custom_task_prompts(task, expected_prompt):
    """Test the prompts for the OpenAI GPT-3 5 Turbo model with custom
    prompts for custom tasks."""
    config = RailsConfig.from_content(
        yaml_content=textwrap.dedent(
            """
            models:
             - type: main
               engine: openai
               model: gpt-3.5-turbo
            prompts:
            - task: summarize_text
              content: |-
                  Text: {{ user_input }}
                  Summarize the above text.
            - task: compose_response
              content: |-
                  Text: {{ user_input }}
                  Compose a response using the above text.
            """
        )
    )

    assert config.models[0].engine == "openai"

    llm_task_manager = LLMTaskManager(config)

    user_input = "test."
    task_prompt = llm_task_manager.render_task_prompt(
        task=task,
        context={"user_input": user_input},
    )

    assert task_prompt == expected_prompt


def test_prompt_length_exceeded_empty_events():
    """Test the prompts for the OpenAI GPT-3 5 Turbo model."""
    config = RailsConfig.from_content(
        yaml_content=textwrap.dedent(
            """
            models:
             - type: main
               engine: openai
               model: gpt-3.5-turbo-instruct
            prompts:
            - task: generate_user_intent
              max_length: 2000
              content: |-
                {{ general_instructions }}

                # This is how a conversation between a user and the bot can go:
                {{ sample_conversation }}

                # This is how the user talks:
                {{ examples }}

                # This is the current conversation between the user and the bot:
                {{ sample_conversation | first_turns(2) }}
                {{ history | colang }}
                    )
                )"""
        )
    )

    assert config.models[0].engine == "openai"
    llm_task_manager = LLMTaskManager(config)

    with pytest.raises(Exception):
        generate_user_intent_prompt = llm_task_manager.render_task_prompt(
            task=Task.GENERATE_USER_INTENT,
            context={"examples": 'user "Hello there!"\n  express greeting'},
            events=[],
        )


def test_prompt_length_exceeded_compressed_history():
    """Test the prompts for the OpenAI GPT-3 5 Turbo model."""
    config = RailsConfig.from_content(
        yaml_content=textwrap.dedent(
            """
            models:
             - type: main
               engine: openai
               model: gpt-3.5-turbo-instruct
            prompts:
            - task: generate_user_intent
              max_length: 3000
              content: |-
                {{ general_instructions }}

                # This is how a conversation between a user and the bot can go:
                {{ sample_conversation }}

                # This is how the user talks:
                {{ examples }}

                # This is the current conversation between the user and the bot:
                {{ sample_conversation | first_turns(2) }}
                {{ history | colang }}
                    )
                )"""
        )
    )

    max_task_prompt_length = get_prompt(config, Task.GENERATE_USER_INTENT).max_length
    assert config.models[0].engine == "openai"
    llm_task_manager = LLMTaskManager(config)

    conversation = [
        {
            "user": "Hello there!",
            "user_intent": "express greeting",
            "bot": "Greetings! How can I help you?",
            "bot_intent": "ask how can help",
        }
        for _ in range(100)
    ]

    conversation.append(
        {
            "user": "I would like to know the unemployment rate for July 2023.",
        }
    )

    events = conversation_to_events(conversation)
    generate_user_intent_prompt = llm_task_manager.render_task_prompt(
        task=Task.GENERATE_USER_INTENT,
        context={"examples": 'user "Hello there!"\n  express greeting'},
        events=events,
    )
    assert len(generate_user_intent_prompt) <= max_task_prompt_length

    # Test to check the stop configuration parameter


def test_stop_configuration_parameter():
    """Test the prompts for the OpenAI GPT-3 5 Turbo model."""
    config = RailsConfig.from_content(
        yaml_content=textwrap.dedent(
            """
            models:
            - type: main
              engine: openai
              model: gpt-3.5-turbo-instruct
            prompts:
            - task: generate_user_intent
              stop:
              - <<end>>
              - <<stop>>
              max_length: 3000
              content: |-
                {{ general_instructions }}

                # This is how a conversation between a user and the bot can go:
                {{ sample_conversation }}

                # This is how the user talks:
                {{ examples }}

                # This is the current conversation between the user and the bot:
                {{ sample_conversation | first_turns(2) }}
                {{ history | colang }}
                    )
                )"""
        )
    )

    task_prompt = get_prompt(config, Task.GENERATE_USER_INTENT)

    # Assuming the stop parameter is a list of strings
    expected_stop_tokens = ["<<end>>", "<<stop>>"]
    llm_task_manager = LLMTaskManager(config)

    # Render the task prompt with the stop configuration
    rendered_prompt = llm_task_manager.render_task_prompt(
        task=Task.GENERATE_USER_INTENT,
        context={"examples": 'user "Hello there!"\n  express greeting'},
        events=[],
    )

    # Check if the stop tokens are correctly set in the rendered prompt
    for stop_token in expected_stop_tokens:
        assert stop_token in task_prompt.stop
