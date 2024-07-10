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

from dataclasses import dataclass, field
from typing import Any, List, Optional


def action(
    is_system_action: bool = False,
    name: Optional[str] = None,
    execute_async: bool = False,
):
    """Decorator to mark a function or class as an action.

    Args:
        is_system_action (bool): Flag indicating if the action is a system action.
        name (Optional[str]): The name to associate with the action.
        execute_async: Whether the function should be executed in async mode.

    Returns:
        callable: The decorated function or class.
    """

    def decorator(fn_or_cls):
        """Inner decorator function to add metadata to the action.

        Args:
            fn_or_cls: The function or class being decorated.
        """

        # Detect the decorator being applied to staticmethod or classmethod.
        # Will annotate the the inner function in that case as otherwise
        # metaclass will be giving us the unannotated enclosed function on
        # attribute lookup.
        if hasattr(fn_or_cls, "__func__"):
            fn_or_cls_target = fn_or_cls.__func__
        else:
            fn_or_cls_target = fn_or_cls

        fn_or_cls_target.action_meta = {
            "name": name or fn_or_cls.__name__,
            "is_system_action": is_system_action,
            "execute_async": execute_async,
        }
        return fn_or_cls

    return decorator


@dataclass
class ActionResult:
    """Data class representing the result of an action.

    Attributes:
        return_value (Optional[Any]): The value returned by the action.
        events (Optional[List[dict]]): The events to be added to the stream.
        context_updates (Optional[dict]): Updates made to the context by this action.
    """

    # The value returned by the action
    return_value: Optional[Any] = None

    # The events that should be added to the stream
    events: Optional[List[dict]] = None

    # The updates made to the context by this action
    context_updates: Optional[dict] = field(default_factory=dict)
