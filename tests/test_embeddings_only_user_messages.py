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
from nemoguardrails.actions.llm.utils import LLMCallException
from tests.utils import TestChat


@pytest.fixture
def config():
    return RailsConfig.from_content(
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
                    embeddings_only_similarity_threshold: 0.5
                    embeddings_only_fallback_intent: "express greeting"
        """,
    )


def test_greeting(config):
    """Test that the bot responds with 'Hello!' when the user says 'hello'."""

    chat = TestChat(
        config,
        llm_completions=[],
    )

    chat >> "hello"
    chat << "Hello!"


def test_error_when_embeddings_only_is_false(config):
    """Test that an error is raised when the 'embeddings_only' option is False."""

    # Check that if we deactivate the embeddings_only option we get an error
    config.rails.dialog.user_messages.embeddings_only = False
    chat = TestChat(
        config,
        llm_completions=[],
    )

    with pytest.raises(LLMCallException):
        chat >> "hello"
        chat << "Hello!"


def test_fallback_intent(config):
    """Test that the bot uses the fallback intent when it doesn't recognize the user's message."""

    rails = LLMRails(config)
    res = rails.generate(messages=[{"role": "user", "content": "lets use fallback"}])
    assert res["content"] == "Hello!"

    config.rails.dialog.user_messages.embeddings_only_fallback_intent = None
    rails = LLMRails(config)
    with pytest.raises(LLMCallException):
        rails.generate(messages=[{"role": "user", "content": "lets use fallback"}])
    #
    # Check the bot's response
