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
    Abort,
    Assignment,
    Break,
    Continue,
    Flow,
    FlowParamDef,
    If,
    Return,
    Source,
    Spec,
    SpecOp,
    SpecType,
    When,
    While,
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
        parameters = children[1]
        elements = children[2]["elements"]

        param_defs = []
        if parameters:
            for flow_param_def in parameters["elements"]:
                assert flow_param_def["_type"] == "flow_param_def"
                param_name_el = flow_param_def["elements"][0]

                assert param_name_el["_type"] == "var_name"
                param_name = param_name_el["elements"][0][1:]
                param_def = FlowParamDef(name=param_name)

                # If we have a default value, we also use that
                if len(flow_param_def["elements"]) == 2:
                    default_value_el = flow_param_def["elements"][1]
                    assert default_value_el["_type"] == "expr"
                    param_def.default_value_expr = default_value_el["elements"][0]

                param_defs.append(param_def)

        elements[0:0] = [
            SpecOp(
                op="match",
                spec=Spec(
                    name="StartFlow",
                    spec_type=SpecType.EVENT,
                    arguments={"flow_id": f'"{name}"'},
                ),
            )
        ]

        return Flow(
            name=name,
            elements=elements,
            parameters=param_defs,
            _source=self.__source(meta),
            source_code=self.source[meta.start_pos : meta.end_pos]
            if self.include_source_mapping
            else None,
        )

    def _spec_op(self, children, meta):
        """Processing for `spec_op` tree nodes.

        Rule:
            spec_op: [spec_operator] spec_expr
                   | on_var_spec_expr
        """
        if len(children) == 1:
            children = [None] + children

        op = children[0] or "await"
        if isinstance(op, dict):
            op = op["_type"].split("_")[0]

        spec = children[1]

        return SpecOp(op=op, spec=spec, _source=self.__source(meta))

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
            spec: spec_name [classic_arguments | simple_arguments] (spec_member)* [capture_ref]
                | var_name (spec_member)* [capture_ref]"""

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
            if not child:
                continue

            if child["_type"] == "capture_ref":
                spec.ref = child
            elif isinstance(child, dict) and child["_type"] == "spec_member":
                name = child["elements"][0]
                arguments = {}
                if child["elements"][1]:
                    arg_elements = child["elements"][1]["elements"]
                    arguments = self.__parse_classical_arguments(arg_elements)
                member_spec = Spec(name=name, arguments=arguments)
                members.append(member_spec)

        if members:
            spec.members = members

        # This is a temporary solution until we have a better way of deriving spec types
        # TODO: Support this by e.g. Colang UMIM action imports
        if spec.name is not None:
            if spec.name.islower():
                spec.spec_type = SpecType.FLOW
            elif spec.name.endswith("Action"):
                spec.spec_type = SpecType.ACTION
            else:
                spec.spec_type = SpecType.EVENT
        elif spec.var_name is not None:
            spec.spec_type = SpecType.REFERENCE

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
        """The set statement can result in either a Set operation, or a SpecOp with a
        return value capturing."""
        assert children[0]["_type"] == "var_name"

        assert children[2]["_type"] in ["expr", "spec_op"]

        # Extract the var name (getting rid of the $)
        var_name = children[0]["elements"][0][1:]

        if children[2]["_type"] == "expr":
            return Assignment(
                key=var_name,
                expression=children[2]["elements"][0],
                _source=self.__source(meta),
            )
        elif children[2]["_type"] == "spec_op":
            spec_op = children[2]
            spec_op.return_var_name = var_name
            return spec_op

    def _while_stmt(self, children, meta):
        assert len(children) == 2
        return While(
            expression=children[0]["elements"][0],
            elements=children[1]["elements"],
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
        elif_elements = []
        if children[2]:
            for _el in children[2]["elements"]:
                assert _el["_type"] == "elif_"
                expr_el = _el["elements"][0]
                suite_el = _el["elements"][1]
                elif_elements.append(
                    {"expr": expr_el["elements"][0], "body": suite_el["elements"]}
                )
        else_elements = children[3]["elements"] if children[3] else None

        main_if_element = if_element = If(
            expression=expression,
            then_elements=then_elements,
            else_elements=else_elements,
        )

        # If we have elif elements, we need to add additional If elements.
        while elif_elements:
            # We create a new one which takes the else body from the current one
            new_if_element = If(
                expression=elif_elements[0]["expr"],
                then_elements=elif_elements[0]["body"],
                else_elements=if_element.else_elements,
            )
            # The new element becomes the "else body"
            if_element.else_elements = [new_if_element]
            if_element = new_if_element
            elif_elements = elif_elements[1:]

        return main_if_element

    def _when_stmt(self, children, meta):
        """Processing for `spec` tree nodes.

        Rule:
            when_stmt: "when" spec_expr suite orwhens ["else" suite]
        """
        assert len(children) == 4
        when_specs = []
        then_elements = []
        when_specs.append(children[0])
        then_elements.append(children[1]["elements"])
        if children[2]:
            for _el in children[2]["elements"]:
                assert _el["_type"] == "orwhen_"
                when_specs.append(_el["elements"][0])
                then_elements.append(_el["elements"][1]["elements"])
        else_elements = children[3]["elements"] if children[3] else None

        main_when_element = When(
            when_specs=when_specs,
            then_elements=then_elements,
            else_elements=else_elements,
        )

        return main_when_element

    def _return_stmt(self, children, meta):
        assert len(children) == 1 and children[0]["_type"] == "expr"
        return Return(
            expression=children[0]["elements"][0],
            _source=self.__source(meta),
        )

    def _abort_stmt(self, children, meta):
        assert len(children) == 0
        return Abort(_source=self.__source(meta))

    def _break_stmt(self, children, meta):
        assert len(children) == 0
        return Break(
            label=None,
            _source=self.__source(meta),
        )

    def _continue_stmt(self, children, meta):
        assert len(children) == 0
        return Continue(
            label=None,
            _source=self.__source(meta),
        )

    def _non_var_spec_or(self, children, meta):
        val = {
            "_type": "spec_or",
            "elements": children,
        }
        if self.include_source_mapping:
            val["_source"] = self.__source(meta)
        return val

    def _non_var_spec_and(self, children, meta):
        val = {
            "_type": "spec_and",
            "elements": children,
        }
        if self.include_source_mapping:
            val["_source"] = self.__source(meta)
        return val

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
                if not meta.empty:
                    value["_source"] = {
                        "line": meta.line,
                        "column": meta.column,
                        "start_pos": meta.start_pos,
                        "end_pos": meta.end_pos,
                    }
                else:
                    value["_source"] = {
                        "line": 0,
                        "column": 0,
                        "start_pos": 0,
                        "end_pos": 0,
                    }

            return value
