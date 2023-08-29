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

import yaml

from nemoguardrails.colang import parse_colang_file
from nemoguardrails.utils import CustomDumper


def test_1():
    content = """
    flow test
      match UserIntent(intent="express greeting")
      bot express greeting
    """
    result = parse_colang_file(
        filename="", content=content, include_source_mapping=False, version="1.1"
    )
    flows = [flow.to_dict() for flow in result["flows"]]

    print(yaml.dump(flows, sort_keys=False, Dumper=CustomDumper, width=1000))
    assert flows == [
        {
            "_source": None,
            "_type": "flow",
            "elements": [
                {
                    "_source": None,
                    "_type": "spec_op",
                    "op": "match",
                    "ref": None,
                    "spec": {
                        "_source": None,
                        "_type": "spec",
                        "arguments": {"flow_id": "test"},
                        "members": None,
                        "name": "StartFlow",
                        "var_name": None,
                    },
                },
                {
                    "_source": None,
                    "_type": "spec_op",
                    "op": "match",
                    "ref": None,
                    "spec": {
                        "_source": None,
                        "_type": "spec",
                        "arguments": {"intent": '"express greeting"'},
                        "members": None,
                        "name": "UserIntent",
                        "var_name": None,
                    },
                },
                {
                    "_source": None,
                    "_type": "spec_op",
                    "op": "await",
                    "ref": None,
                    "spec": {
                        "_source": None,
                        "_type": "spec",
                        "arguments": {},
                        "members": None,
                        "name": "bot express greeting",
                        "var_name": None,
                    },
                },
            ],
            "name": "test",
        }
    ]


def test_2():
    content = """
    flow test
      match user express greeting

      if $current_time < '12:00'
        bot express good morning
      else
        bot express good afternoon

    """
    result = parse_colang_file(
        filename="", content=content, include_source_mapping=False, version="1.1"
    )
    flows = [flow.to_dict() for flow in result["flows"]]

    print(yaml.dump(flows, sort_keys=False, Dumper=CustomDumper, width=1000))
    assert flows == [
        {
            "_source": None,
            "_type": "flow",
            "elements": [
                {
                    "_source": None,
                    "_type": "spec_op",
                    "op": "match",
                    "ref": None,
                    "spec": {
                        "_source": None,
                        "_type": "spec",
                        "arguments": {"flow_id": "test"},
                        "members": None,
                        "name": "StartFlow",
                        "var_name": None,
                    },
                },
                {
                    "_source": None,
                    "_type": "spec_op",
                    "op": "match",
                    "ref": None,
                    "spec": {
                        "_source": None,
                        "_type": "spec",
                        "arguments": {},
                        "members": None,
                        "name": "user express greeting",
                        "var_name": None,
                    },
                },
                {
                    "_source": None,
                    "_type": "if",
                    "else_elements": [
                        {
                            "_source": None,
                            "_type": "spec_op",
                            "op": "await",
                            "ref": None,
                            "spec": {
                                "_source": None,
                                "_type": "spec",
                                "arguments": {},
                                "members": None,
                                "name": "bot express good " "afternoon",
                                "var_name": None,
                            },
                        }
                    ],
                    "expression": "$current_time < '12:00'",
                    "then_elements": [
                        {
                            "_source": None,
                            "_type": "spec_op",
                            "op": "await",
                            "ref": None,
                            "spec": {
                                "_source": None,
                                "_type": "spec",
                                "arguments": {},
                                "members": None,
                                "name": "bot express good morning",
                                "var_name": None,
                            },
                        }
                    ],
                },
            ],
            "name": "test",
        }
    ]


def test_3():
    content = """
    flow test
      user silent $duration="5s" or user agrees
      user silent "5s"
      user ask $text="what?" $times=3
      user ask (text="what?", times=3)
    """
    result = parse_colang_file(
        filename="", content=content, include_source_mapping=False, version="1.1"
    )
    flows = [flow.to_dict() for flow in result["flows"]]

    print(yaml.dump(flows, sort_keys=False, Dumper=CustomDumper, width=1000))
    assert flows == [
        {
            "_source": None,
            "_type": "flow",
            "elements": [
                {
                    "_source": None,
                    "_type": "spec_op",
                    "op": "match",
                    "ref": None,
                    "spec": {
                        "_source": None,
                        "_type": "spec",
                        "arguments": {"flow_id": "test"},
                        "members": None,
                        "name": "StartFlow",
                        "var_name": None,
                    },
                },
                {
                    "_source": None,
                    "_type": "spec_op",
                    "op": "await",
                    "ref": None,
                    "spec": {
                        "_type": "spec_or",
                        "elements": [
                            {
                                "_source": None,
                                "_type": "spec",
                                "arguments": {"duration": '"5s"'},
                                "members": None,
                                "name": "user silent",
                                "var_name": None,
                            },
                            {
                                "_source": None,
                                "_type": "spec",
                                "arguments": {},
                                "members": None,
                                "name": "user agrees",
                                "var_name": None,
                            },
                        ],
                    },
                },
                {
                    "_source": None,
                    "_type": "spec_op",
                    "op": "await",
                    "ref": None,
                    "spec": {
                        "_source": None,
                        "_type": "spec",
                        "arguments": {"$0": '"5s"'},
                        "members": None,
                        "name": "user silent",
                        "var_name": None,
                    },
                },
                {
                    "_source": None,
                    "_type": "spec_op",
                    "op": "await",
                    "ref": None,
                    "spec": {
                        "_source": None,
                        "_type": "spec",
                        "arguments": {"text": '"what?"', "times": "3"},
                        "members": None,
                        "name": "user ask",
                        "var_name": None,
                    },
                },
                {
                    "_source": None,
                    "_type": "spec_op",
                    "op": "await",
                    "ref": None,
                    "spec": {
                        "_source": None,
                        "_type": "spec",
                        "arguments": {"text": '"what?"', "times": "3"},
                        "members": None,
                        "name": "user ask",
                        "var_name": None,
                    },
                },
            ],
            "name": "test",
        }
    ]


def test_4():
    content = """
    flow test
      match bot express greeting . Finished()
      match bot express greeting . Finished(status="success")
      match $action
      match $action.Finished()
      match $some_flow.some_action.Finished("success")
    """
    result = parse_colang_file(
        filename="", content=content, include_source_mapping=False, version="1.1"
    )
    flows = [flow.to_dict() for flow in result["flows"]]

    print(yaml.dump(flows, sort_keys=False, Dumper=CustomDumper, width=1000))
    assert flows == [
        {
            "_source": None,
            "_type": "flow",
            "elements": [
                {
                    "_source": None,
                    "_type": "spec_op",
                    "op": "match",
                    "ref": None,
                    "spec": {
                        "_source": None,
                        "_type": "spec",
                        "arguments": {"flow_id": "test"},
                        "members": None,
                        "name": "StartFlow",
                        "var_name": None,
                    },
                },
                {
                    "_source": None,
                    "_type": "spec_op",
                    "op": "match",
                    "ref": None,
                    "spec": {
                        "_source": None,
                        "_type": "spec",
                        "arguments": {},
                        "members": [
                            {
                                "_source": None,
                                "_type": "spec",
                                "arguments": {},
                                "members": None,
                                "name": "Finished",
                                "var_name": None,
                            }
                        ],
                        "name": "bot express greeting",
                        "var_name": None,
                    },
                },
                {
                    "_source": None,
                    "_type": "spec_op",
                    "op": "match",
                    "ref": None,
                    "spec": {
                        "_source": None,
                        "_type": "spec",
                        "arguments": {},
                        "members": [
                            {
                                "_source": None,
                                "_type": "spec",
                                "arguments": {"status": '"success"'},
                                "members": None,
                                "name": "Finished",
                                "var_name": None,
                            }
                        ],
                        "name": "bot express greeting",
                        "var_name": None,
                    },
                },
                {
                    "_source": None,
                    "_type": "spec_op",
                    "op": "match",
                    "ref": None,
                    "spec": {
                        "_source": None,
                        "_type": "spec",
                        "arguments": None,
                        "members": None,
                        "name": None,
                        "var_name": "action",
                    },
                },
                {
                    "_source": None,
                    "_type": "spec_op",
                    "op": "match",
                    "ref": None,
                    "spec": {
                        "_source": None,
                        "_type": "spec",
                        "arguments": None,
                        "members": [
                            {
                                "_source": None,
                                "_type": "spec",
                                "arguments": {},
                                "members": None,
                                "name": "Finished",
                                "var_name": None,
                            }
                        ],
                        "name": None,
                        "var_name": "action",
                    },
                },
                {
                    "_source": None,
                    "_type": "spec_op",
                    "op": "match",
                    "ref": None,
                    "spec": {
                        "_source": None,
                        "_type": "spec",
                        "arguments": None,
                        "members": [
                            {
                                "_source": None,
                                "_type": "spec",
                                "arguments": {},
                                "members": None,
                                "name": "some_action",
                                "var_name": None,
                            },
                            {
                                "_source": None,
                                "_type": "spec",
                                "arguments": {"$0": '"success"'},
                                "members": None,
                                "name": "Finished",
                                "var_name": None,
                            },
                        ],
                        "name": None,
                        "var_name": "some_flow",
                    },
                },
            ],
            "name": "test",
        }
    ]
