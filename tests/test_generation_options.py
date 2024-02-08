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


def test_output_vars_1():
    config = RailsConfig.from_content(
        colang_content="""
                define user express greeting
                  "hi"

                define flow
                  user express greeting
                  $user_greeted = True
                  bot express greeting

                define bot express greeting
                  "Hello! How can I assist you today?"
            """,
    )
    chat = TestChat(
        config,
        llm_completions=[
            "  express greeting",
            "  express greeting",
        ],
    )

    res = chat.app.generate(
        "hi", options={"output_vars": ["user_greeted", "something_else"]}
    )
    output_data = res.dict().get("output_data", {})

    # We check also that a non-existent variable returns None.
    assert output_data == {"user_greeted": True, "something_else": None}

    # We also test again by trying to return the full context
    res = chat.app.generate("hi", options={"output_vars": True})
    output_data = res.dict().get("output_data", {})

    # There should be many keys
    assert len(output_data.keys()) > 5
