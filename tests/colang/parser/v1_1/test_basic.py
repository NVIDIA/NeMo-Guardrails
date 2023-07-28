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


def test_1():
    content = """
    define flow
      match UserIntent(intent="dfdf")
      bot express greeting
    """
    result = parse_colang_file(filename="", content=content, version="1.1")

    print(json.dumps(result, indent=True))

    assert result["flows"][0]["elements"] == [
        {
            "_source_mapping": {
                "comment": None,
                "filename": "",
                "line_number": 3,
                "line_text": 'match UserIntent(intent="dfdf")',
            },
            "_type": "UserIntent",
            "intent": "dfdf",
        },
        {
            "_source_mapping": {
                "comment": None,
                "filename": "",
                "line_number": 4,
                "line_text": "bot express greeting",
            },
            "_type": "run_action",
            "action_name": "utter",
            "action_params": {"value": "express greeting"},
        },
    ]
