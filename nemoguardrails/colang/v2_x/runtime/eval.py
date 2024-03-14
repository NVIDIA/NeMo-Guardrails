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
import re
from functools import partial
from typing import Any, List

from simpleeval import EvalWithCompoundTypes

from nemoguardrails.colang.v2_x.runtime import system_functions
from nemoguardrails.colang.v2_x.runtime.flows import ColangValueError
from nemoguardrails.colang.v2_x.runtime.utils import AttributeDict
from nemoguardrails.utils import new_uid

log = logging.getLogger(__name__)


def eval_expression(expr: str, context: dict) -> Any:
    """Evaluates the provided expression in the given."""
    # If it's not a string, we should return it as such
    if expr is None:
        return None

    if not isinstance(expr, str):
        assert isinstance(expr, bool) or isinstance(expr, int)

        return expr

    # We search for all expressions in strings within curly brackets and evaluate them first
    # Find first all strings
    string_pattern = r'("(?:\\"|[^"])*?")|(\'(?:\\\'|[^\'])*?\')'
    string_expressions_matches = re.findall(string_pattern, expr)
    string_expression_values = []
    for string_expression_match in string_expressions_matches:
        string_expression = (
            string_expression_match[0]
            if string_expression_match[0]
            else string_expression_match[1]
        )
        if string_expression:
            # Find expressions within curly brackets, ignoring double curly brackets
            expression_pattern = r"{(?!\{)([^{}]+)\}(?!\})"
            inner_expressions = re.findall(expression_pattern, string_expression)
            if inner_expressions:
                inner_expression_values = []
                for inner_expression in inner_expressions:
                    try:
                        value = eval_expression(inner_expression, context)
                    except Exception as ex:
                        raise ColangValueError(
                            f"Error evaluating inner expression: '{inner_expression}'"
                        ) from ex
                    value = str(value).replace('"', '\\"').replace("'", "\\'")
                    inner_expression_values.append(value)
                string_expression = re.sub(
                    expression_pattern,
                    lambda x: inner_expression_values.pop(0),
                    string_expression,
                )
                string_expression = string_expression.replace("{{", "{").replace(
                    "}}", "}"
                )
            string_expression_values.append(string_expression)
    if string_expression_values:
        expr = re.sub(
            string_pattern,
            lambda x: string_expression_values.pop(0),
            expr,
        )

    index_counter = 0

    def replace_with_index(name, _match):
        nonlocal index_counter
        if _match.group(1) or _match.group(3):
            replacement = f"{name}_{index_counter}"
            index_counter += 1
            return replacement
        else:
            return _match.group(0)

    # We search for all variable names starting with $, remove the $ and add
    # the value in the dict for eval
    expr_locals = {}
    regex_pattern = r"\$([a-zA-Z_][a-zA-Z0-9_]*)"
    var_names = re.findall(regex_pattern, expr)
    updated_expr = re.sub(regex_pattern, r"var_\1", expr)

    for var_name in var_names:
        # if we've already computed the value, we skip
        if f"var_{var_name}" in expr_locals:
            continue

        val = context.get(var_name, None)

        # We transform dicts to AttributeDict so we can access their keys as attributes
        # e.g. write things like $speaker.name
        if isinstance(val, dict):
            val = AttributeDict(val)

        expr_locals[f"var_{var_name}"] = val

    # Finally, just evaluate the expression
    try:
        # TODO: replace this with something even more restrictive.
        functions = {
            "len": len,
            "flow": system_functions.flow,
            "action": system_functions.action,
            "regex": _create_regex,
            "search": _regex_search,
            "findall": _regex_findall,
            "uid": new_uid,
            "str": _to_str,
            "escape": _escape_string,
            "isint": _is_int,
            "isfloat": _is_float,
            "isbool": _is_bool,
            "isstr": _is_str,
        }
        # TODO: replace this with something even more restrictive.
        s = EvalWithCompoundTypes(
            functions=functions,
            names=expr_locals,
        )
        return s.eval(updated_expr)
    except Exception as e:
        raise ColangValueError(f"Error evaluating '{expr}'") from e


def _create_regex(pattern: str) -> re.Pattern:
    return re.compile(pattern)


def _regex_search(pattern: str, string: str) -> bool:
    return bool(re.search(pattern, string))


def _regex_findall(pattern: str, string: str) -> List[str]:
    return re.findall(pattern, string)


def _to_str(data: Any) -> str:
    return str(data)


def _escape_string(string: str) -> str:
    """Escape a string and inner expressions."""
    return string.replace("\\", "\\\\").replace("{{", "\\{").replace("}}", "\\}")


def _is_int(val: Any) -> bool:
    """Check if it is an integer."""
    return isinstance(val, int)


def _is_float(val: Any) -> bool:
    """Check if it is an integer."""
    return isinstance(val, float)


def _is_bool(val: Any) -> bool:
    """Check if it is an integer."""
    return isinstance(val, bool)


def _is_str(val: Any) -> bool:
    """Check if it is an integer."""
    return isinstance(val, str)
