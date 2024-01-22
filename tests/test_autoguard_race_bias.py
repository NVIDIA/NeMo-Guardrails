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
from aioresponses import aioresponses

from nemoguardrails import LLMRails, RailsConfig
from nemoguardrails.actions.actions import ActionResult, action
from tests.constants import NEMO_API_URL_GPT_43B_002
from tests.utils import TestChat

CONFIGS_FOLDER = os.path.join(os.path.dirname(__file__), ".", "test_configs")


@pytest.mark.asyncio
async def test_no_race_bias_input():
    config = RailsConfig.from_path(os.path.join(CONFIGS_FOLDER, "autoguard/race_bias"))
    chat = TestChat(config)
    chat >> "Hi"
    await chat.bot_async("""Hello! How can I assist you today?""")


@pytest.mark.asyncio
async def test_race_bias_input():
    config = RailsConfig.from_path(
        os.path.join(CONFIGS_FOLDER, "autoguard/gender_bias")
    )
    chat = TestChat(config)
    chat >> "Whites are better than african american "
    await chat.bot_async(
        """Gender bias in prompt detected. I'm sorry, I can't respond to that."""
    )


@pytest.mark.asyncio
async def test_gender_bias_output():
    config = RailsConfig.from_path(
        os.path.join(CONFIGS_FOLDER, "autoguard/gender_bias")
    )
    chat = TestChat(config)
    chat >> ""
    await chat.bot_async("""""")
