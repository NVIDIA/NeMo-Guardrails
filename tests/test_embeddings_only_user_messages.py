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
from nemoguardrails.llm.filters import colang
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
                    embeddings_only_similarity_threshold: 0.8
                    embeddings_only_fallback_intent: "express greeting"
        """,
    )


@pytest.fixture
def colang_2_config():
    return RailsConfig.from_content(
        """
    import core
    import llm

    flow main
        activate greeting
        activate llm continuation

    flow user expressed greeting
        user said "hi"
        or user said "hello"

    flow bot express greeting
        bot say "Hello!"

    flow greeting
        user expressed greeting
        bot express greeting
    """,
        """
    colang_version: "2.x"
    rails:
        dialog:
            user_messages:
                embeddings_only: True
                embeddings_only_similarity_threshold: 0.8
                embeddings_only_fallback_intent: "user expressed greeting"
    """,
    )


def test_greeting_1(config):
    """Test that the bot responds with 'Hello!' when the user says 'hello'."""

    chat = TestChat(
        config,
        llm_completions=[],
    )

    chat >> "hello"
    chat << "Hello!"


def test_greeting_2(colang_2_config):
    """Test that the bot responds with 'Hello!' when the user says 'hello'."""

    chat = TestChat(
        colang_2_config,
        llm_completions=[],
    )

    chat >> "hi"
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
        chat >> "how is your day?"
        chat << "Hello!"


def test_error_when_embeddings_only_is_false_2(colang_2_config):
    """Test that an error is raised when the 'embeddings_only' option is False."""

    # Check that if we deactivate the embeddings_only option we get an error
    colang_2_config.rails.dialog.user_messages.embeddings_only = False
    chat = TestChat(
        colang_2_config,
        llm_completions=[],
    )

    with pytest.raises(LLMCallException):
        chat >> "how is your day?"
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


def test_fallback_intent_2(colang_2_config):
    """Test that the bot uses the fallback intent when it doesn't recognize the user's message."""

    rails = LLMRails(colang_2_config)
    res = rails.generate(messages=[{"role": "user", "content": "lets use fallback"}])
    assert res["content"] == "Hello!"

    colang_2_config.rails.dialog.user_messages.embeddings_only_fallback_intent = None
    rails = LLMRails(colang_2_config)
    with pytest.raises(LLMCallException):
        rails.generate(messages=[{"role": "user", "content": "lets use fallback"}])
