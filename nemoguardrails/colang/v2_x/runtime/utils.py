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
