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


class AttributeDict(dict):
    """
    Simple utility to allow accessing dict members as attributes.

    This class allows you to access dictionary keys as if they were attributes of an object.
    For example, if you have a dictionary `my_dict` with a key "key1", you can access it as
    `my_dict.key1`.

    Usage:
    ```python
    my_dict = AttributeDict({"key1": "value1", "key2": {"subkey": "subvalue"}})
    print(my_dict.key1)  # Accessing a top-level key
    print(my_dict.key2.subkey)  # Accessing a nested key
    ```

    Note: Be careful when using this class, as it may not handle all cases perfectly,
    especially if your dictionary keys contain special characters or conflict with
    Python's reserved attribute names.
    """

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
