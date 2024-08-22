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

from nemoguardrails.cli.migration import convert_colang_2alpha_syntax


class TestColang2AlphaSyntaxConversion:
    def test_orwhen_replacement(self):
        input_lines = ["orwhen condition met"]
        expected_output = ["or when condition met"]
        assert convert_colang_2alpha_syntax(input_lines) == expected_output

    def test_flow_start_uid_replacement(self):
        input_lines = ["flow_start_uid: 12345"]
        expected_output = ["flow_instance_uid: 12345"]
        assert convert_colang_2alpha_syntax(input_lines) == expected_output

    def test_regex_replacement(self):
        input_lines = ['r"(?i).*({{$text}})((\s*\w+\s*){0,2})\W*$"']
        expected_output = ['regex("((?i).*({{$text}})((\\s*\\w+\\s*){0,2})\\W*$)")']
        assert convert_colang_2alpha_syntax(input_lines) == expected_output

    def test_curly_braces_replacement(self):
        input_lines = ['"{{variable}}"']
        expected_output = ['"{variable}"']
        assert convert_colang_2alpha_syntax(input_lines) == expected_output

    def test_findall_replacement(self):
        input_lines = ["findall matches"]
        expected_output = ["find_all matches"]
        assert convert_colang_2alpha_syntax(input_lines) == expected_output

    def test_triple_quotes_replacement(self):
        input_lines = ['$ """some text"""']
        expected_output = ['$ ..."some text"']
        assert convert_colang_2alpha_syntax(input_lines) == expected_output

    def test_specific_phrases_replacement(self):
        input_lines = [
            "catch colang errors",
            "catch undefined flows",
            "catch unexpected user utterance",
            "track bot talking state",
            "track user talking state",
            "track user utterance state",
            "poll llm request response",
            "trigger user intent for unhandled user utterance",
            "generate then continue interaction",
            "track unhandled user intent state",
            "respond to unhandled user intent",
        ]
        expected_output = [
            "notification of colang errors",
            "notification of undefined flow start",
            "notification of unexpected user utterance",
            "tracking bot talking state",
            "tracking user talking state",
            "tracking user talking state",
            "polling llm request response",
            "generating user intent for unhandled user utterance",
            "llm continue interaction",
            "tracking unhandled user intent state",
            "continuation on unhandled user intent",
        ]
        assert convert_colang_2alpha_syntax(input_lines) == expected_output

    def test_meta_decorator_replacement(self):
        input_lines = [
            "flow some_flow:",
            "# meta: loop_id=123",
            "# meta: example meta",
            "some action",
        ]
        expected_output = [
            '@loop("123")',
            "@meta(example_meta=True)",
            "flow some_flow:",
            "some action",
        ]
        assert convert_colang_2alpha_syntax(input_lines) == expected_output

    def test_convert_flow_examples(self):
        input_1 = """
        flow bot inform something like issue
            # meta: bot intent
            (bot inform "ABC"
                or bot inform "DEFG"
                or bot inform "HJKL")
                and (bot gesture "abc def" or bot gesture "hij kl")
        """
        input_lines = textwrap.dedent(input_1).strip().split("\n")

        output_1 = """
        @meta(bot_intent=True)
        flow bot inform something like issue
            (bot inform "ABC"
                or bot inform "DEFG"
                or bot inform "HJKL")
                and (bot gesture "abc def" or bot gesture "hij kl")
        """
        output_lines = textwrap.dedent(output_1).strip().split("\n")

        assert convert_colang_2alpha_syntax(input_lines) == output_lines
