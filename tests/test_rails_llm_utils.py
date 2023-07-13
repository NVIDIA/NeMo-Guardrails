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

from nemoguardrails.rails.llm.utils import get_history_cache_key


def test_basic():
    assert get_history_cache_key([]) == ""

    assert get_history_cache_key([{"role": "user", "content": "hi"}]) == "hi"

    assert (
        get_history_cache_key(
            [
                {"role": "user", "content": "hi"},
                {"role": "assistant", "content": "Hello!"},
                {"role": "user", "content": "How are you?"},
            ],
        )
        == "hi:Hello!:How are you?"
    )


def test_with_context():
    assert (
        get_history_cache_key(
            [
                {"role": "context", "content": {"user_name": "John"}},
                {"role": "user", "content": "hi"},
            ],
        )
        == '{"user_name": "John"}:hi'
    )

    assert (
        get_history_cache_key(
            [
                {"role": "context", "content": {"user_name": "John"}},
                {"role": "user", "content": "hi"},
                {"role": "assistant", "content": "Hello!"},
                {"role": "user", "content": "How are you?"},
            ],
        )
        == '{"user_name": "John"}:hi:Hello!:How are you?'
    )
