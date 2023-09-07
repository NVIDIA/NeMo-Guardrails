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

from nemoguardrails import RailsConfig
from tests.utils import TestChat


def test_1():
    config = RailsConfig.from_content(
        colang_content="""
        flow user express greeting
          match UtteranceUserActionFinished(final_transcript="hi")

        flow bot express greeting
          await UtteranceBotAction(script="Hello world!")

        flow main
          user express greeting
          await FetchNameAction()
          bot express greeting
        """,
        yaml_content="""
        colang_version: "1.1"
        """,
    )

    chat = TestChat(
        config,
        llm_completions=[],
    )

    async def fetch_name():
        return "John"

    chat.app.register_action(fetch_name, "FetchNameAction")

    chat >> "hi"
    chat << "Hello world!"
