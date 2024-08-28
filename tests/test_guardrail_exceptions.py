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

from typing import Optional

import pytest
from jinja2 import Template

from nemoguardrails import RailsConfig
from tests.utils import TestChat

colang_content = """
    define user express greeting
        "hello"
        "hi"
        "how are you"

    define bot express greeting
        "Hey!"

    define flow greeting
        user express greeting
        bot express greeting
"""


def create_yaml_content(
    input_params: Optional[str] = None, output_params: Optional[str] = None
):
    input_prompt_param = input_params.replace(" ", "_") if input_params else None
    output_prompt_param = output_params.replace(" ", "_") if output_params else None

    template = Template(
        """
    models: []
    rails:
        {% if input_params %}input:
            flows:
                - {{ input_params }}
        {% endif %}
        {% if output_params %}output:
            flows:
                - {{ output_params }}
        {% endif %}
    {% if input_prompt_param or output_prompt_param %}prompts:
        {% if input_prompt_param %}- task: {{ input_prompt_param }}
          content: '...'
        {% endif %}
        {% if output_prompt_param %}- task: {{ output_prompt_param }}
          content: '...'
        {% endif %}
    {% endif %}
    enable_rails_exceptions: True
    """
    )

    yaml_content = template.render(
        input_params=input_params,
        output_params=output_params,
        input_prompt_param=input_prompt_param,
        output_prompt_param=output_prompt_param,
    )

    return yaml_content


def create_config(
    input_params: Optional[str] = None, output_params: Optional[str] = None
):
    yaml_content = create_yaml_content(input_params, output_params)
    config = RailsConfig.from_content(
        colang_content=colang_content, yaml_content=yaml_content
    )
    return config


def test_self_check_input_exception():
    config = create_config(
        input_params="self check input", output_params="self check output"
    )
    chat = TestChat(
        config,
        llm_completions=[
            "Yes",
        ],
    )

    rails = chat.app
    messages = [
        {"role": "user", "content": "Hi 1!"},
    ]
    new_message = rails.generate(messages=messages)

    assert new_message["role"] == "exception"
    assert new_message["content"]["type"] == "InputRailException"


def test_self_check_output_exception():
    config = create_config(
        input_params="self check input", output_params="self check output"
    )
    chat = TestChat(
        config,
        llm_completions=[
            "No",
            "  ask general question",
            "  respond",
            '  "Something that should be blocked"',
            "Yes",
        ],
    )

    rails = chat.app
    messages = [
        {"role": "user", "content": "Something that generates bad output"},
    ]
    new_message = rails.generate(messages=messages)

    assert new_message["role"] == "exception"
    assert new_message["content"]["type"] == "OutputRailException"
