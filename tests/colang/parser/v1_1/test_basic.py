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

import json

from nemoguardrails.colang import parse_colang_file
from nemoguardrails.colang.v1_1.lang.colang_parser import parse_coflows_to_yml_flows


def test_1():
    content = """
    define flow
      match UserIntent(intent="dfdf")
      bot express greeting
    """
    result = parse_colang_file(
        filename="", content=content, include_source_mapping=False, version="1.1"
    )

    print(json.dumps(result, indent=True))

    assert result["flows"][0]["elements"] == [
        {"_type": "UserIntent", "intent": "dfdf"},
        {
            "_type": "run_action",
            "action_name": "utter",
            "action_params": {"value": "express greeting"},
        },
    ]


def test_2():
    content = """
        define flow
          match UserSilent(duration="5")
          bot ask if more time needed
        """

    result = parse_coflows_to_yml_flows(
        filename="", content=content, snippets={}, include_source_mapping=False
    )

    flow = list(result["flows"].values())[0]

    assert flow == [
        {"event": 'UserSilent(duration="5")'},
        {"bot": "ask if more time needed"},
    ]
