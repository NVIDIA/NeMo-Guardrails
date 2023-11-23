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

"""Demo script."""
import asyncio
import logging

from nemoguardrails import LLMRails, RailsConfig
from nemoguardrails.streaming import StreamingHandler

logging.basicConfig(level=logging.INFO)

YAML_CONFIG = """
models:
  - type: main
    engine: openai
    model: gpt-4

streaming: True
"""


async def demo_1():
    """Demo using the streaming of response chunks directly."""
    config = RailsConfig.from_content(yaml_content=YAML_CONFIG)
    app = LLMRails(config)

    history = [{"role": "user", "content": "What is the capital of France?"}]

    async for chunk in app.stream_async(messages=history):
        print(f"CHUNK: {chunk}")
        # Or do something else with the token


async def demo_2():
    """Demo of using the streaming of chunks with the final response as well."""
    config = RailsConfig.from_content(yaml_content=YAML_CONFIG)
    app = LLMRails(config)

    history = [{"role": "user", "content": "What is the capital of France?"}]

    streaming_handler = StreamingHandler()

    async def process_tokens():
        async for chunk in streaming_handler:
            print(f"CHUNK: {chunk}")
            # Or do something else with the token

    asyncio.create_task(process_tokens())

    result = await app.generate_async(
        messages=history, streaming_handler=streaming_handler
    )
    print(result)


if __name__ == "__main__":
    asyncio.run(demo_1())
    asyncio.run(demo_2())
