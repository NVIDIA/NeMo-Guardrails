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

import os

import pytest

from nemoguardrails import LLMRails, RailsConfig

CONFIGS_FOLDER = os.path.join(os.path.dirname(__file__), "test_configs")


@pytest.fixture
def app():
    config = RailsConfig.from_path(
        os.path.join(CONFIGS_FOLDER, "with_actions_override")
    )

    return LLMRails(config)


def test_live_query(app):
    result = app.generate(messages=[{"role": "user", "content": "hello!"}])

    assert result == {
        "content": "How are you doing?",
        "role": "assistant",
    }
