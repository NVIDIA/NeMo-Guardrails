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
from typing import Any, List

from simpleeval import EvalWithCompoundTypes

from nemoguardrails.utils import new_uid

log = logging.getLogger(__name__)

from nemoguardrails.colang.v1_1.runtime import system_functions
from nemoguardrails.colang.v1_1.runtime.utils import AttributeDict


def eval_expression(expr, context) -> Any:
    """Evaluates the provided expression in the given context."""
    # If it's not a string, we should return it as such
    if expr is None:
        return None

    if not isinstance(expr, str):
        assert isinstance(expr, bool) or isinstance(expr, int)

        return expr

    # We search for all inner expressions and evaluate them first
    inner_expression_pattern = r"\{\{(.*?)\}\}"
    inner_expressions = re.findall(inner_expression_pattern, expr)
    if inner_expressions:
        inner_expression_values = []
        for inner_expression in inner_expressions:
            try:
                value = eval_expression(inner_expression, context)
            except Exception as ex:
                log.warning(f"Error evaluating inner expression: '{expr}': {str(ex)}")
            if isinstance(value, str):
                value = value.replace('"', '\\"')
            inner_expression_values.append(value)
        expr = re.sub(
            inner_expression_pattern,
            lambda x: str(inner_expression_values.pop(0)),
            expr,
        )

    index_counter = 0

    def replace_with_index(match):
        nonlocal index_counter
        replacement = f"regex_{index_counter}"
        index_counter += 1
        return replacement

    # If the expression contains the pattern r"(.*?)" it is considered a regular expression
    expr_locals = {}
    regex_pattern = r"(r\"(.*?)\")|(r'(.*?)')"
    regular_expressions = re.findall(regex_pattern, expr)
    updated_expr = re.sub(regex_pattern, replace_with_index, expr)

    for idx, regular_expression in enumerate(regular_expressions):
        try:
            regex = (
                regular_expression[1]
                if regular_expression[1] != ""
                else regular_expression[3]
            )
            compiled_regex = re.compile(regex)
            expr_locals[f"regex_{idx}"] = compiled_regex
        except Exception as ex:
            raise Exception(
                f"Error in compiling regular expression '{expr}': {str(ex)}"
            )

    # We search for all variable names starting with $, remove the $ and add
    # the value in the globals dict for eval
    regex_pattern = r"\$([a-zA-Z_][a-zA-Z0-9_]*)"
    var_names = re.findall(regex_pattern, updated_expr)
    updated_expr = re.sub(regex_pattern, r"var_\1", updated_expr)

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
        s = EvalWithCompoundTypes(
            functions={
                "len": len,
                "flow": system_functions.flow,
                "action": system_functions.action,
                "search": regex_search,
                "findall": regex_findall,
                "uid": new_uid,
            },
            names=expr_locals,
        )
        return s.eval(updated_expr)
    except Exception as ex:
        raise Exception(f"Error evaluating '{expr}': {str(ex)}")


def regex_search(pattern: str, string: str) -> bool:
    return bool(re.search(pattern, string))


def regex_findall(pattern: str, string: str) -> List[str]:
    return re.findall(pattern, string)
