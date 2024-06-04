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

from nemoguardrails import RailsConfig
from nemoguardrails.actions.llm.utils import LLMCallException
from tests.utils import TestChat

config = RailsConfig.from_content(
    """
    define user express greeting
      "hi"

    define bot express greeting
      "Hello!"

    define flow
      user express greeting
      bot express greeting
    """,
    """
    rails:
        dialog:
            user_messages:
                embeddings_only: True
    """,
)


def test_1():
    chat = TestChat(
        config,
        llm_completions=[],
    )

    chat >> "hello"
    chat << "Hello!"


def test_2():
    # Check that if we deactivate the embeddings_only option we get an error
    config.rails.dialog.user_messages.embeddings_only = False
    chat = TestChat(
        config,
        llm_completions=[],
    )

    with pytest.raises(LLMCallException):
        chat >> "hello"
        chat << "Hello!"
