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

import uuid
from typing import Any, Dict, List

from nemoguardrails.colang.v2_x.lang.colang_ast import Decorator, Flow
from nemoguardrails.colang.v2_x.runtime.flows import ColangSyntaxError, FlowConfig


class AttributeDict(dict):
    """Simple utility to allow accessing dict members as attributes."""

    def __getattr__(self, attr):
        val = self.get(attr, None)
        if isinstance(val, dict):
            return AttributeDict(val)
        elif isinstance(val, list) and len(val) > 0 and isinstance(val[0], dict):
            return [AttributeDict(x) for x in val]
        else:
            return val

    def __setattr__(self, attr, value):
        self[attr] = value


def new_readable_uid(name: str) -> str:
    """Creates a new uuid with a human readable prefix."""
    return f"({name}){str(uuid.uuid4())}"


def new_var_uid() -> str:
    """Creates a new uuid that is compatible with variable names."""
    return str(uuid.uuid4()).replace("-", "_")


def convert_decorator_list_to_dictionary(
    decorators: List[Decorator],
) -> Dict[str, Dict[str, Any]]:
    """Convert list of decorators to a dictionary merging the parameters of decorators with same name."""
    decorator_dict: Dict[str, Dict[str, Any]] = {}
    for decorator in decorators:
        item = decorator_dict.get(decorator.name, None)
        if item:
            item.update(decorator.parameters)
        else:
            decorator_dict[decorator.name] = decorator.parameters
    return decorator_dict


def create_flow_configs_from_flow_list(flows: List[Flow]) -> Dict[str, FlowConfig]:
    """Create a flow config dictionary and resolves flow overriding."""
    flow_configs: Dict[str, FlowConfig] = {}
    override_flows: Dict[str, FlowConfig] = {}

    # Create two dictionaries with normal and override flows
    for flow in flows:
        assert isinstance(flow, Flow)

        config = FlowConfig(
            id=flow.name,
            elements=flow.elements,
            decorators=convert_decorator_list_to_dictionary(flow.decorators),
            parameters=flow.parameters,
            return_members=flow.return_members,
            source_code=flow.source_code,
        )

        if config.is_override:
            if flow.name in override_flows:
                raise ColangSyntaxError(
                    f"Multiple override flows with name '{flow.name}' detected! There can only be one!"
                )
            override_flows[flow.name] = config
        elif flow.name in flow_configs:
            raise ColangSyntaxError(
                f"Multiple non-overriding flows with name '{flow.name}' detected! There can only be one!"
            )
        else:
            flow_configs[flow.name] = config

    # Override normal flows
    for override_flow in override_flows.values():
        if override_flow.id not in flow_configs:
            raise ColangSyntaxError(
                f"Override flow with name '{override_flow.id}' does not override any flow with that name!"
            )
        flow_configs[override_flow.id] = override_flow

    return flow_configs
