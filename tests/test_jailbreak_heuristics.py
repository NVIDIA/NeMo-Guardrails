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

from nemoguardrails import RailsConfig
from tests.utils import TestChat

CONFIGS_FOLDER = os.path.join(os.path.dirname(__file__), ".", "test_configs")
len_ppl = "asdf"
ps_ppl = "asdf"
safe = "asdf"


@pytest.mark.asyncio
async def test_jb_len_ppl_detected():
    # Test 1 - should detect a jailbreak attempt via the check_jb_lp heuristic
    config = RailsConfig.from_path(os.path.join(CONFIGS_FOLDER, "jailbreak_heuristics"))
    chat = TestChat(config)
    chat >> len_ppl


@pytest.mark.asyncio
async def test_jb_ps_ppl_detected():
    # Test 2 - should detect a jailbreak attempt via the check_jb_ps_ppl heuristic
    config = RailsConfig.from_path(os.path.join(CONFIGS_FOLDER, "jailbreak_heuristics"))
    chat = TestChat(config)
    chat >> ps_ppl


def test_safe():
    # Test 3 - user input should not be detected as a jailbreak
    config = RailsConfig.from_path(os.path.join(CONFIGS_FOLDER, "jailbreak_heuristics"))
    chat = TestChat(config)
    chat >> safe
    chat << "A message"
