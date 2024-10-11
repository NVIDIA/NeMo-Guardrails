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

import pytest

from nemoguardrails import RailsConfig
from nemoguardrails.rails.llm.options import GenerationResponse
from tests.utils import TestChat

colang_content = '''
    import core
    import llm

    import guardrails
    import nemoguardrails.library

    flow input rails $input_text
        dummy input rail $input_text

    flow output rails $output_text
        dummy output rail $output_text

    flow main
        activate llm continuation
        activate greeting
        activate other reactions

    flow dummy input rail $input_text
        if "dummy" in $input_text
            bot refuse to respond
            abort

    flow dummy output rail $output_text
        if "dummy" in $output_text
            bot refuse to respond
            abort

    flow greeting
        user expressed greeting
        bot say "Hello world! It is a dummy message."

    flow other reactions
        user expressed to be bored
        bot say "No problem!"

    flow user expressed greeting
        """"User expressed greeting in any way or form."""
        user said "hi"

    flow user expressed to be bored
        """"User expressed to be bored."""
        user said "This is boring"
    '''

yaml_content = """
colang_version: "2.x"
models:
  - type: main
    engine: openai
    model: gpt-3.5-turbo-instruct

    """


def test_triggered_rails_info_2():
    config = RailsConfig.from_content(colang_content, yaml_content)

    chat = TestChat(
        config,
        llm_completions=[
            "user expressed greeting",
        ],
    )

    res: GenerationResponse = chat.app.generate(
        "Hello!",
        options={
            "log": {
                "activated_rails": True,
                "llm_calls": True,
                "internal_events": True,
            }
        },
    )

    assert res.response == "I'm sorry, I can't respond to that."

    assert res.log, "GenerationLog is not present although it is set in options"
    assert (
        res.log.activated_rails
    ), "Activated Rails are not present although it is set in options"

    assert len(res.log.activated_rails) == 36
    assert len(res.log.llm_calls) == 0
    assert len(res.log.internal_events) > 0

    input_rails = [rail for rail in res.log.activated_rails if rail.type == "input"]
    output_rails = [rail for rail in res.log.activated_rails if rail.type == "output"]

    assert len(input_rails) > 0, "No input rails found"
    assert len(output_rails) > 0, "No output rails found"
