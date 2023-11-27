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


# A decorator that sets a property on the function to indicate if it's a system action or not.
def action(is_system_action: bool = False, name: Optional[str] = None):
    """
    Decorator for defining actions.

    Args:
        is_system_action (bool, optional): Whether the action is a system action. Defaults to False.
        name (Optional[str], optional): The name of the action. If not provided, the function or class name will be used.

    Returns:
        decorator: A decorator function to associate metadata with the action.

    Usage:
        ```python
        @action(is_system_action=True, name="MySystemAction")
        def my_action_function():
            # Your action logic here
            pass
        ```

    """

    def decorator(fn_or_cls):
        """
        Decorator function to associate metadata with the action.

        Args:
            fn_or_cls: The function or class to associate metadata with.

        Returns:
            fn_or_cls: The same function or class with added action metadata.

        """
        fn_or_cls.action_meta = {
            "name": name or fn_or_cls.__name__,
            "is_system_action": is_system_action,
        }
        return fn_or_cls

    return decorator


@dataclass
class ActionResult:
    """
    Data class representing the result of an action.

    Attributes:
        return_value (Optional[Any], optional): The value returned by the action. Defaults to None.
        events (Optional[List[dict]], optional): The events that should be added to the stream. Defaults to None.
        context_updates (Optional[dict], optional): The updates made to the context by this action. Defaults to an empty dictionary.

    Usage:
        ```python
        result = ActionResult(return_value=42, events=[{"type": "event"}], context_updates={"key": "value"})
        ```

    """

    # The value returned by the action
    return_value: Optional[Any] = None

    # The events that should be added to the stream
    events: Optional[List[dict]] = None

    # The updates made to the context by this action
    context_updates: Optional[dict] = field(default_factory=dict)
