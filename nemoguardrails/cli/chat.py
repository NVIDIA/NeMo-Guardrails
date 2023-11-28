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
import os
from typing import Optional

import aiohttp

from nemoguardrails import LLMRails, RailsConfig
from nemoguardrails.context import streaming_handler_var
from nemoguardrails.streaming import StreamingHandler

os.environ["TOKENIZERS_PARALLELISM"] = "false"


async def input_async(prompt_message: str = "") -> str:
    loop = asyncio.get_event_loop()
    return await loop.run_in_executor(None, input, prompt_message)


async def run_chat_async(
    config_path: Optional[str] = None,
    verbose: bool = False,
    streaming: bool = False,
    server_url: Optional[str] = None,
    config_id: Optional[str] = None,
):
    if config_path is None and server_url is None:
        raise RuntimeError(
            "At least one of `config_path` or `server-url` must be provided."
        )

    if not server_url:
        rails_config = RailsConfig.from_path(config_path)
        rails_app = LLMRails(rails_config, verbose=verbose)
        if streaming and not rails_config.streaming_supported:
            print(
                f"WARNING: The config `{config_path}` does not support streaming. "
                "Falling back to normal mode."
            )
            streaming = False
    else:
        rails_app = None

    history = []
    # And go into the default listening loop.
    while True:
        print("")
        user_message = input("> ")

        history.append({"role": "user", "content": user_message})

        if not server_url:
            # If we have streaming from a locally loaded config, we initialize the handler.
            if streaming and not server_url and rails_app.main_llm_supports_streaming:
                streaming_handler = StreamingHandler(enable_print=True)
            else:
                streaming_handler = None

            bot_message = await rails_app.generate_async(
                messages=history, streaming_handler=streaming_handler
            )

            if not streaming or not rails_app.main_llm_supports_streaming:
                # We print bot messages in green.
                print(f"\033[92m{bot_message['content']}\033[0m")
        else:
            data = {
                "config_id": config_id,
                "messages": history,
                "stream": streaming,
            }
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    f"{server_url}/v1/chat/completions",
                    json=data,
                ) as response:
                    # If the response is streaming, we show each chunk as it comes
                    if response.headers.get("Transfer-Encoding") == "chunked":
                        bot_message_text = ""
                        async for chunk in response.content.iter_any():
                            chunk = chunk.decode("utf-8")
                            print(f"\033[92m{chunk}\033[0m", end="")
                            bot_message_text += chunk
                        print("")

                        bot_message = {"role": "assistant", "content": bot_message_text}
                    else:
                        result = await response.json()
                        bot_message = result["messages"][0]

                        # We print bot messages in green.
                        print(f"\033[92m{bot_message['content']}\033[0m")

        history.append(bot_message)


def run_chat(
    config_path: Optional[str] = None,
    verbose: bool = False,
    streaming: bool = False,
    server_url: Optional[str] = None,
    config_id: Optional[str] = None,
):
    """Runs a chat session in the terminal."""
    asyncio.run(
        run_chat_async(
            config_path=config_path,
            verbose=verbose,
            streaming=streaming,
            server_url=server_url,
            config_id=config_id,
        )
    )
