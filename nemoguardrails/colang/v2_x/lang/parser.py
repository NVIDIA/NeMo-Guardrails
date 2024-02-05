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
import os
import re

import yaml

from nemoguardrails.colang.v2_x.lang.colang_ast import Flow
from nemoguardrails.colang.v2_x.lang.grammar.load import load_lark_parser
from nemoguardrails.colang.v2_x.lang.transformer import ColangTransformer
from nemoguardrails.utils import CustomDumper

log = logging.getLogger(__name__)


class ColangParser:
    """Colang 2.x parser class"""

    def __init__(self, include_source_mapping: bool = False):
        self.include_source_mapping = include_source_mapping
        self.grammar_path = os.path.join(
            os.path.dirname(__file__), "grammar", "colang.lark"
        )

        # Initialize the Lark Parser
        self._lark_parser = load_lark_parser(self.grammar_path)

    def get_parsing_tree(self, content: str) -> dict:
        """Helper to get only the parsing tree.

        Args:
            content: The Colang content.

        Returns:
            An instance of a parsing tree as returned by Lark.
        """
        # NOTE: dealing with EOF is a bit tricky in Lark; the easiest solution
        # to avoid some issues arising from that is to append a new line at the end
        return self._lark_parser.parse(content + "\n")

    def parse_content(
        self, content: str, print_tokens: bool = False, print_parsing_tree: bool = False
    ) -> dict:
        """Parse the provided content and create element structure."""
        if print_tokens:
            tokens = list(self._lark_parser.lex(content))
            for token in tokens:
                print(token.__repr__())

        tree = self.get_parsing_tree(content)

        if print_parsing_tree:
            print(tree.pretty())

        exclude_flows_from_llm = self._contains_exclude_from_llm_tag(content)

        transformer = ColangTransformer(
            source=content, include_source_mapping=self.include_source_mapping
        )
        data = transformer.transform(tree)

        result: dict = {"flows": []}

        # For the special case when we only have one flow in the colang file
        if isinstance(data, Flow):
            data.file_info["exclude_from_llm"] = exclude_flows_from_llm
            result["flows"].append(data)
        else:
            # Otherwise, it's a sequence and we take all the flow elements and return them
            for element in data["elements"]:
                if element["_type"] == "flow":
                    element.file_info["exclude_from_llm"] = exclude_flows_from_llm
                    result["flows"].append(element)

        return result

    def _contains_exclude_from_llm_tag(self, content: str) -> bool:
        pattern = r"^# meta: exclude from llm"
        return bool(re.search(pattern, content, re.MULTILINE))


def parse_colang_file(
    _filename: str, content: str, include_source_mapping: bool = True
) -> dict:
    """Parse the content of a .co."""

    colang_parser = ColangParser(include_source_mapping=include_source_mapping)
    result = colang_parser.parse_content(content, print_tokens=False)

    # flows = []
    # for flow_data in result["flows"]:
    #     # elements = parse_flow_elements(items)
    #     # TODO: extract the source code here
    #     source_code = ""
    #     flows.append(
    #         {
    #             "id": flow_data["name"],
    #             "elements": flow_data["elements"],
    #             "source_code": source_code,
    #         }
    #     )

    data = {
        "flows": result["flows"],
    }

    return data


def main() -> None:
    paths = [
        "../../../../tests/colang/parser/v2_x/inputs/test6.co",
    ]

    filenames = []
    for path in paths:
        if os.path.isdir(path):
            for root, dirs, files in os.walk(path):
                for filename in files:
                    if filename.endswith(".co"):
                        filenames.append(os.path.join(root, filename))
        else:
            filenames.append(path)

    colang_parser = ColangParser()

    for filename in filenames:
        log.info("========================================")
        log.info(f"{filename}")
        log.info("========================================")
        with open(filename, "r") as file:
            content = file.read()

        tree = colang_parser.get_parsing_tree(content)
        log.info(tree.pretty())

        data = colang_parser.parse_content(content)
        print(yaml.dump(data, sort_keys=False, Dumper=CustomDumper, width=1000))


if __name__ == "__main__":
    main()
