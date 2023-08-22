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

import logging
import os.path

from lark import Lark
from lark.indenter import PythonIndenter

log = logging.getLogger("colang_parser")
logging.basicConfig(level=logging.INFO)

# Initialize the Colang Parser
with open("colang.lark", "r") as file:
    grammar = file.read()

parser = Lark(
    grammar,
    start="start",
    parser="earley",
    lexer="basic",
    postlex=PythonIndenter(),
)


def parse_file(file_path: str, print_tokens=False):
    with open(file_path, "r") as file:
        text = file.read()

        if print_tokens:
            tokens = list(parser.lex(text))
            for token in tokens:
                print(token.__repr__())

        # NOTE: dealing with EOF is a bit tricky in Lark; the easiest solution
        # to avoid some issues arising from that is to append a new line at the end
        return parser.parse(text + "\n")


if __name__ == "__main__":
    paths = [
        "tests/test.co",
        "tests/test2.co",
        "tests/test3.co",
        "tests/test4.co",
        "tests/test5.co",
        "../../../../../tests/test_configs/example_interactions/faq_questions.co",
        "../../../../../tests/test_configs/example_interactions/core_flows.co",
        "../../../../../tests/test_configs/example_interactions/confirmation_question.co",
        "../../../../../tests/test_configs/example_interactions/multi_modal_actions.co",
        "../../../../../tests/test_configs/example_interactions/action_conflicts.co",
    ]

    for path in paths:
        if os.path.isdir(path):
            for root, dirs, files in os.walk(path):
                for filename in files:
                    if filename.endswith(".co"):
                        log.info("========================================")
                        log.info(f"{filename}")
                        log.info("========================================")
                        filepath = os.path.join(root, filename)
                        tree = parse_file(filepath)
                        log.info(tree.pretty())
        else:
            tree = parse_file(path, print_tokens=True)
            # This will print the parse tree in a human-readable format
            log.info(tree.pretty())
