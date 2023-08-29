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

from typing import Any, List, Optional

from lark import Token, Transformer, Tree
from lark.tree import Meta

from nemoguardrails.colang.v1_1.lang.colang_ast import (
    Flow,
    If,
    Set,
    Source,
    Spec,
    SpecOp,
)


class ColangTransformer(Transformer):
    """A Lark transformer for transforming the parsing tree into the right internal structure.

    It extracts the following:
    1. Flows
    2. Imports (TODO)
    """

    def __init__(
        self, source: str, include_source_mapping=True, expand_await: bool = False
    ):
        """Constructor.

        Args:
            source: The original source code.
            include_source_mapping: If set to True, a "_source" field will be included.
            expand_await: If set to True, await statements will be expanded to `start` + `match`.
              Default to False.
        """
        super().__init__()

        self.source = source
        self.include_source_mapping = include_source_mapping
        self.expand_await = expand_await

    def element(
        self,
        _type: str,
        elements: Optional[List[Any]] = None,
        meta: Optional[Meta] = None,
    ):
        """Helper to create an element of the specified type."""
        element = {"_type": _type}
        if elements is not None:
            element["elements"] = elements

        if meta and self.include_source_mapping:
            element["_source"] = {
                "line": meta.line,
                "column": meta.column,
                "start_pos": meta.start_pos,
                "end_pos": meta.end_pos,
            }

        return element

    def __source(self, meta):
        """Helper to extract a simplified source information from a `meta` object.

        Args:
            meta: A `meta` object as provided by Lark.
        """
        if not self.include_source_mapping:
            return None

        return Source(
            line=meta.line,
            column=meta.column,
            start_pos=meta.start_pos,
            end_pos=meta.end_pos,
        )

    def _name(self, children, meta):
        """Processing for `name` tree nodes.

        We just copy the values from the children, which should be tokens.
        """
        return " ".join([child["elements"][0] for child in children])

    def _flow_def(self, children, meta):
        """Processing for `flow` tree nodes."""
        assert children[0]["_type"] == "spec_name"
        assert children[2]["_type"] == "suite"

        name = children[0]["elements"][0]
        elements = children[2]["elements"]

        elements[0:0] = [
            SpecOp(
                op="match",
                spec=Spec(name="StartFlow", arguments={"flow_id": name}),
            )
        ]

        return Flow(name=name, elements=elements, _source=self.__source(meta))

    def _spec_op(self, children, meta):
        """Processing for `spec_op` tree nodes.

        Rule:
            spec_op: [spec_operator] spec_expr [capture_ref]
        """
        assert len(children) >= 3

        op = children[0] or "await"
        if isinstance(op, dict):
            op = op["_type"].split("_")[0]

        spec = children[1]
        ref = children[2]

        return SpecOp(op=op, spec=spec, ref=ref, _source=self.__source(meta))

    def __parse_classical_arguments(self, arg_elements):
        arguments = {}
        positional_index = 0
        for arg_element in arg_elements:
            if arg_element["_type"] == "expr":
                arguments[f"${positional_index}"] = arg_element["elements"][0]
                positional_index += 1
            else:
                assert arg_element["_type"] == "argvalue"

                if len(arg_element["elements"]) == 1:
                    expr_element = arg_element["elements"][0]
                    assert expr_element["_type"] == "expr"
                    arguments[f"${positional_index}"] = expr_element["elements"][0]
                    positional_index += 1
                else:
                    name = arg_element["elements"][0]
                    expr_el = arg_element["elements"][1]
                    expr = expr_el["elements"][0]
                    arguments[name] = expr
        return arguments

    def _spec(self, children, meta):
        """Processing for `spec` tree nodes.

        Rule:
            spec: spec_name [classic_arguments | simple_arguments] (spec_member)*
                | var_name (spec_member)*"""

        assert len(children) >= 1
        if children[0]["_type"] == "spec_name":
            spec_name = children[0]["elements"][0]

            arguments = {}
            if children[1]:
                if children[1]["_type"] == "classic_arguments":
                    arg_elements = children[1]["elements"]
                    arguments = self.__parse_classical_arguments(arg_elements)

                elif children[1]["_type"] == "simple_arguments":
                    positional_index = 0
                    arg_elements = children[1]["elements"]
                    for arg_element in arg_elements:
                        if arg_element["_type"] == "expr":
                            arguments[f"${positional_index}"] = arg_element["elements"][
                                0
                            ]
                            positional_index += 1
                        else:
                            assert arg_element["_type"] == "simple_argvalue"
                            name = arg_element["elements"][0]["elements"][0][1:]
                            expr_el = arg_element["elements"][1]
                            expr = expr_el["elements"][0]
                            arguments[name] = expr
            spec = Spec(name=spec_name, arguments=arguments)

        elif children[0]["_type"] == "var_name":
            var_name = children[0]["elements"][0][1:]
            spec = Spec(var_name=var_name)
        else:
            raise Exception(f"Invalid element '{children[0]['_type']}'")

        members = []
        # Check if there are any members specified
        for child in children:
            if (
                not child
                or not isinstance(child, dict)
                or child["_type"] != "spec_member"
            ):
                continue

            name = child["elements"][0]
            arguments = {}
            if child["elements"][1]:
                arg_elements = child["elements"][1]["elements"]
                arguments = self.__parse_classical_arguments(arg_elements)
            members.append(Spec(name=name, arguments=arguments))

        if members:
            spec.members = members

        return spec

    def _spec_name(self, children, meta):
        return self.element("spec_name", [" ".join(children)], meta)

    def _var_name(self, children, meta):
        return self.element("var_name", [children[0]["elements"][0]])

    def _expr(self, children, meta):
        return self.element("expr", [self.source[meta.start_pos : meta.end_pos]], meta)

    def _test(self, children, meta):
        return self.element("expr", [self.source[meta.start_pos : meta.end_pos]], meta)

    def _set_stmt(self, children, meta):
        assert children[0]["_type"] == "var_name"
        assert children[2]["_type"] == "expr"

        return Set(
            key=children[0]["elements"][0],
            expression=children[2]["elements"][0],
            _source=self.__source(meta),
        )

    def _if_stmt(self, children, meta):
        """Processing for `spec` tree nodes.

        Rule:
            if_stmt: "if" test suite elifs ["else" suite]
        """
        assert len(children) == 4
        expression = children[0]["elements"][0]
        then_elements = children[1]["elements"]
        else_elements = children[3]["elements"] if children[3] else None

        return If(
            expression=expression,
            then_elements=then_elements,
            else_elements=else_elements,
        )

    def __default__(self, data, children, meta):
        """Default function that is called if there is no attribute matching ``data``

        Can be overridden. Defaults to creating a new copy of the tree node (i.e. ``return Tree(data, children, meta)``)
        """
        if isinstance(data, Token):
            data = data.value

        # Transform tokens to dicts
        children = [
            child
            if not isinstance(child, Token)
            else {"_type": child.type, "elements": [child.value]}
            for child in children
        ]

        method_name = f"_{data}"
        if hasattr(self, method_name):
            return getattr(self, method_name)(children, meta)
        else:
            value = {
                "_type": data,
                "elements": children,
            }

            if self.include_source_mapping:
                value["_source"] = {
                    "line": meta.line,
                    "column": meta.column,
                    "start_pos": meta.start_pos,
                    "end_pos": meta.end_pos,
                }

            return value
