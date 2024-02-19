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
from tests.utils import TestChat


@pytest.fixture
def config_1():
    return RailsConfig.from_content(
        colang_content="""
            flow user said $text
              match UtteranceUserActionFinished(final_transcript=$text)

            flow bot say $text
              await UtteranceBotAction(script=$text)

            flow wait
              await SomeRandomAction()

            # ---

            flow greeting_1
              user said "hi"
              $flow_name = "some flow"
              $flow = flow($flow_name)
              bot say "Conversion successful."

            flow main
              activate greeting_1
              wait
            """,
        yaml_content="""
            colang_version: "2.x"
            """,
    )


# TODO: fix this test; the parsing for the casting is not working correctly.
@pytest.mark.skip
def test_2_x(config_1):
    chat = TestChat(
        config_1,
        llm_completions=[],
    )

    chat >> "hi"
    chat << "Conversion successful."
