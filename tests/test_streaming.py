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

import asyncio

import pytest

from nemoguardrails import RailsConfig
from nemoguardrails.streaming import StreamingHandler
from tests.utils import TestChat


@pytest.fixture
def chat_1():
    config: RailsConfig = RailsConfig.from_content(
        config={"models": [], "streaming": True}
    )
    return TestChat(
        config,
        llm_completions=[
            "Hello there! How are you?",
        ],
        streaming=True,
    )


@pytest.mark.asyncio
async def test_streaming_generate_async_api(chat_1):
    streaming_handler = StreamingHandler()

    chunks = []

    async def process_tokens():
        async for chunk in streaming_handler:
            chunks.append(chunk)

            # Or do something else with the token

    asyncio.create_task(process_tokens())

    response = await chat_1.app.generate_async(
        messages=[{"role": "user", "content": "Hi!"}],
        streaming_handler=streaming_handler,
    )

    assert chunks == ["Hello ", "there! ", "How ", "are ", "you?"]
    assert response == {"content": "Hello there! How are you?", "role": "assistant"}


@pytest.mark.asyncio
async def test_stream_async_api(chat_1):
    """Test the simplified stream_async interface"""

    chunks = []
    async for chunk in chat_1.app.stream_async(
        messages=[{"role": "user", "content": "Hi!"}],
    ):
        chunks.append(chunk)

    assert chunks == ["Hello ", "there! ", "How ", "are ", "you?"]


@pytest.mark.asyncio
async def test_streaming_predefined_messages():
    """Predefined messages should be streamed as a single chunk."""
    config: RailsConfig = RailsConfig.from_content(
        config={"models": [], "streaming": True},
        colang_content="""
        define user express greeting
          "hi"

        define flow
          user express greeting
          bot express greeting

        define bot express greeting
          "Hello there!"
        """,
    )
    chat = TestChat(
        config,
        llm_completions=["  express greeting"],
        streaming=True,
    )

    chunks = []
    async for chunk in chat.app.stream_async(
        messages=[{"role": "user", "content": "Hi!"}],
    ):
        chunks.append(chunk)

    assert chunks == ["Hello there!"]


@pytest.mark.asyncio
async def test_streaming_dynamic_bot_message():
    """Predefined messages should be streamed as a single chunk."""
    config: RailsConfig = RailsConfig.from_content(
        config={"models": [], "streaming": True},
        colang_content="""
        define user express greeting
          "hi"

        define flow
          user express greeting
          bot express greeting
        """,
    )
    chat = TestChat(
        config,
        llm_completions=[
            "User intent: express greeting",
            'Bot message: "Hello there! How are you today?"',
        ],
        streaming=True,
    )

    chunks = []
    async for chunk in chat.app.stream_async(
        messages=[{"role": "user", "content": "Hi!"}],
    ):
        chunks.append(chunk)

    assert chunks == ["Hello ", "there! ", "How ", "are ", "you ", "today?"]


@pytest.mark.asyncio
async def test_streaming_single_llm_call():
    """Predefined messages should be streamed as a single chunk."""
    config: RailsConfig = RailsConfig.from_content(
        config={
            "models": [],
            "rails": {"dialog": {"single_call": {"enabled": True}}},
            "streaming": True,
        },
        colang_content="""
        define user express greeting
          "hi"

        define flow
          user express greeting
          bot express greeting
        """,
    )
    chat = TestChat(
        config,
        llm_completions=[
            '  express greeting\nbot express greeting\n  "Hi, how are you doing?"'
        ],
        streaming=True,
    )

    chunks = []
    async for chunk in chat.app.stream_async(
        messages=[{"role": "user", "content": "Hi!"}],
    ):
        chunks.append(chunk)

    assert chunks == ["Hi, ", "how ", "are ", "you ", "doing?"]


@pytest.mark.asyncio
async def test_streaming_single_llm_call_with_message_override():
    """Predefined messages should be streamed as a single chunk."""
    config: RailsConfig = RailsConfig.from_content(
        config={
            "models": [],
            "rails": {"dialog": {"single_call": {"enabled": True}}},
            "streaming": True,
        },
        colang_content="""
        define user express greeting
          "hi"

        define flow
          user express greeting
          bot express greeting

        define bot express greeting
          "Hey! Welcome back!"
        """,
    )
    chat = TestChat(
        config,
        llm_completions=[
            '  express greeting\nbot express greeting\n  "Hi, how are you doing?"'
        ],
        streaming=True,
    )

    chunks = []
    async for chunk in chat.app.stream_async(
        messages=[{"role": "user", "content": "Hi!"}],
    ):
        chunks.append(chunk)

    assert chunks == ["Hey! Welcome back!"]

    # Wait for proper cleanup, otherwise we get a Runtime Error
    await asyncio.sleep(1)


@pytest.mark.asyncio
async def test_streaming_single_llm_call_with_next_step_override_and_dynamic_message():
    """Predefined messages should be streamed as a single chunk."""
    config: RailsConfig = RailsConfig.from_content(
        config={
            "models": [],
            "rails": {"dialog": {"single_call": {"enabled": True}}},
            "streaming": True,
        },
        colang_content="""
        define user express greeting
          "hi"

        define flow
          user express greeting
          bot tell joke
        """,
    )
    chat = TestChat(
        config,
        llm_completions=[
            'User intent: express greeting\nBot intent: express greeting\nBot message: "Hi, how are you doing?"',
            'Bot message: "This is a funny joke."',
        ],
        streaming=True,
    )

    chunks = []
    async for chunk in chat.app.stream_async(
        messages=[{"role": "user", "content": "Hi!"}],
    ):
        chunks.append(chunk)

    assert chunks == ["This ", "is ", "a ", "funny ", "joke."]

    # Wait for proper cleanup, otherwise we get a Runtime Error
    await asyncio.sleep(1)
