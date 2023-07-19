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

import pytest

from nemoguardrails import LLMRails, RailsConfig
from nemoguardrails.llm.providers import register_llm_provider
from tests.utils import FakeLLM, clean_providers


@pytest.mark.asyncio
async def test_multimodel_should_use_main():
    rails_config = RailsConfig.parse_object(
        {
            "models": [
                {
                    "type": "secodary",
                    "engine": "fake2",
                    "model": "fake2",
                },
                {
                    "type": "main",
                    "engine": "fake",
                    "model": "fake",
                },
            ],
        }
    )
    register_llm_provider("fake", FakeLLM)
    llm_rails = LLMRails(config=rails_config)
    assert isinstance(llm_rails.llm, FakeLLM) is True
    clean_providers()


@pytest.mark.asyncio
async def test_multimodel_should_raise_error_when_main_not_defined():
    rails_config = RailsConfig.parse_object(
        {
            "models": [
                {
                    "type": "secodary",
                    "engine": "fake2",
                    "model": "fake2",
                },
                {
                    "type": "third",
                    "engine": "fake",
                    "model": "fake",
                },
            ],
        }
    )
    register_llm_provider("fake", FakeLLM)
    with pytest.raises(Exception) as e:
        LLMRails(config=rails_config)
        e.match("Multiple LLM models specified. Please specify a main model.")


@pytest.mark.asyncio
async def test_multimodel_should_raise_error_when_models_not_defined():
    rails_config = RailsConfig.parse_object(
        {
            "models": [],
        }
    )
    register_llm_provider("fake", FakeLLM)
    with pytest.raises(Exception) as e:
        LLMRails(config=rails_config)
        e.match("No LLM model specified.")


@pytest.mark.asyncio
async def test_should_use_as_main_when_only_one_model_defined():
    rails_config = RailsConfig.parse_object(
        {
            "models": [
                {
                    "type": "secondary_but_only_one",
                    "engine": "fake",
                    "model": "fake",
                },
            ],
        }
    )
    register_llm_provider("fake", FakeLLM)
    llm_rails = LLMRails(config=rails_config)
    assert isinstance(llm_rails.llm, FakeLLM) is True
    clean_providers()
