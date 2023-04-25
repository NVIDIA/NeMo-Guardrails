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

from typing import List


def get_history_cache_key(messages: List[dict], include_last: bool) -> str:
    """Computes the cache key for a sequence of messages and a config id."""
    user_messages = [msg["content"] for msg in messages[0:-1] if msg["role"] == "user"]
    if include_last:
        user_messages.append(messages[-1]["content"])

    history_cache_key = ":".join(user_messages)

    return history_cache_key
