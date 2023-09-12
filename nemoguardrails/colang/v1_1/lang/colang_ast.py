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

"""The data types that are used when constructing the Abstract Syntax Tree after parsing."""

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Union

from dataclasses_json import dataclass_json


@dataclass_json
@dataclass
class Source:
    """Information about the source of an element."""

    line: int
    column: int
    start_pos: int
    end_pos: int


@dataclass_json
@dataclass
class FlowParamDef:
    """The definition for a flow parameter.

    Explicit typing is not yet supported.
    """

    name: str
    default_value_expr: Optional[str] = None


@dataclass_json
@dataclass
class Element:
    """Base class for all elements in the AST."""

    _type: str
    _source: Optional[Source] = None

    def __getitem__(self, key):
        return getattr(self, key, None)

    def get(self, key, default_value=None):
        """Getter for backward compatibility with dict elements.

        TODO: to remove at some point.
        """
        return self[key] or default_value


@dataclass_json
@dataclass
class Value(Element):
    """Element that contains a value."""

    value: Any = None
    _type: str = "value"


@dataclass_json
@dataclass
class Elements(Element):
    """Element that encapsulates multiple sub-elements."""

    elements: List[Element] = field(default_factory=list())
    _type: str = "value"


@dataclass_json
@dataclass
class Flow(Element):
    """Element that represents a flow."""

    name: str = ""
    parameters: List[FlowParamDef] = field(default_factory=list)
    elements: List[Element] = field(default_factory=list())
    _type: str = "flow"


@dataclass_json
@dataclass
class Spec(Element):
    """Element that represents a spec.

    A spec can represent a flow, an action or an event. Currently, we will determine
    at runtime what the spec is.

    A spec is either specified directly through a name and arguments, or through a
    variable. In both cases, additional members can be accessed, e.g., .Finished().
    """

    name: Optional[str] = None
    arguments: Dict[str, Any] = field(default_factory=dict)
    members: Optional[List["Spec"]] = None
    var_name: Optional[str] = None
    _type: str = "spec"


@dataclass_json
@dataclass
class SpecAnd(Element):
    """A conjunction of specs."""

    specs: List[Spec] = field(default_factory=list())
    _type: str = "spec_and"


@dataclass_json
@dataclass
class SpecOr(Element):
    """A disjunction of spects."""

    specs: List[Spec] = field(default_factory=list())
    _type: str = "spec_or"


@dataclass_json
@dataclass
class SpecOp(Element):
    """An operation performed on a spec.

    Valid operations are: await, start, match, activate, send.
    """

    op: str = ""
    spec: Union[Spec, SpecAnd, SpecOr] = Spec()
    ref: Optional[str] = field(default=None)
    _type: str = "spec_op"


@dataclass_json
@dataclass
class If(Element):
    expression: str = ""
    then_elements: List[Element] = field(default_factory=list())
    else_elements: Optional[List[Element]] = None
    _type: str = "if"


@dataclass_json
@dataclass
class While(Element):
    expression: str = ""
    do: List[Element] = field(default_factory=list())
    _type: str = "while"


@dataclass_json
@dataclass
class Set(Element):
    key: str = ""
    expression: str = ""
    _type: str = "set"


@dataclass_json
@dataclass
class Continue(Element):
    _type: str = "continue"


@dataclass_json
@dataclass
class Abort(Element):
    # TODO: update this to "abort" after the sliding logic is updated
    _type: str = "stop"


@dataclass_json
@dataclass
class Break(Element):
    _type: str = "break"


@dataclass_json
@dataclass
class Return(Element):
    _type: str = "return"
    _next = "-1"
    _absolute = True


@dataclass_json
@dataclass
class Label(Element):
    name: str = ""
    _type: str = "label"


@dataclass_json
@dataclass
class Goto(Element):
    label: str = ""
    expression: str = "True"
    _type: str = "goto"


@dataclass_json
@dataclass
class Meta(Element):
    meta: dict = field(default_factory=dict())
    _type: str = "meta"
