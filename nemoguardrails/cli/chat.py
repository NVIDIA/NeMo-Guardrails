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
from prompt_toolkit import prompt
from prompt_toolkit.patch_stdout import patch_stdout

from nemoguardrails import LLMRails, RailsConfig
from nemoguardrails.streaming import StreamingHandler
from nemoguardrails.utils import new_event_dict

os.environ["TOKENIZERS_PARALLELISM"] = "false"


async def input_async(prompt_message: str = "") -> str:
    """Asynchronously read user input with a prompt.

    Args:
        prompt_message (str): The message to display as a prompt. Defaults to an empty string.

    Returns:
        str: The user's input.
    """
    loop = asyncio.get_event_loop()
    return await loop.run_in_executor(None, prompt, prompt_message)


async def _run_chat_v1_0(
    config_path: Optional[str] = None,
    verbose: bool = False,
    streaming: bool = False,
    server_url: Optional[str] = None,
    config_id: Optional[str] = None,
):
    """Asynchronously run a chat session in the terminal.

    Args:
        config_path (Optional[str]): The path to the configuration file. Defaults to None.
        verbose (bool): Whether to run in verbose mode. Defaults to False.
        streaming (bool): Whether to enable streaming mode. Defaults to False.
        server_url (Optional[str]): The URL of the chat server. Defaults to None.
        config_id (Optional[str]): The configuration ID. Defaults to None.
    """
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

        # We print bot messages in green.
        print(f"\033[92m{bot_message['content']}\033[0m")


async def _run_chat_v1_1(rails_app: LLMRails):
    """Simple chat loop for v1.1 using the stateful events API."""
    state = None
    waiting_user_input = False
    running_timer_tasks = {}
    output_events = []
    output_state = None

    # Start an asynchronous timer
    async def _start_timer(timer_name: str, delay_seconds: float, action_uid: str):
        nonlocal input_events
        print(f"Timer {timer_name}/{action_uid} started.")
        await asyncio.sleep(delay_seconds)
        print(f"Timer {timer_name}/{action_uid} is up!")
        input_events.append(
            new_event_dict(
                "TimerBotActionFinished",
                action_uid=action_uid,
                is_success=True,
                timer_name=timer_name,
            )
        )
        running_timer_tasks.pop(action_uid)
        if waiting_user_input:
            await _process_input_events()

    def _process_output():
        """Helper to process the output events."""
        nonlocal output_events, output_state, input_events, state

        # We detect any "StartUtteranceBotAction" events, show the message, and
        # generate the corresponding Finished events as new input events.
        for event in output_events:
            # Add all output events also to input events
            input_events.append(event)

            if event["type"] == "StartUtteranceBotAction":
                # We print bot messages in green.
                print(f"\033[92m{event['script']}\033[0m")

                input_events.append(
                    new_event_dict(
                        "UtteranceBotActionStarted",
                        action_uid=event["action_uid"],
                    )
                )
                input_events.append(
                    new_event_dict(
                        "UtteranceBotActionFinished",
                        action_uid=event["action_uid"],
                        is_success=True,
                        final_script=event["script"],
                    )
                )
            elif event["type"] == "StartGestureBotAction":
                # We print gesture messages in green.
                print(f"\033[92mgesture: {event['gesture']}\033[0m")

                input_events.append(
                    new_event_dict(
                        "GestureBotActionStarted",
                        action_uid=event["action_uid"],
                    )
                )
                input_events.append(
                    new_event_dict(
                        "GestureBotActionFinished",
                        action_uid=event["action_uid"],
                        is_success=True,
                    )
                )

            elif event["type"] == "StartPostureBotAction":
                # We print posture messages in green.
                print(
                    f"\033[92mstart: posture (posture={event['posture']}, action_uid={event['action_uid']}))\033[0m"
                )
                input_events.append(
                    new_event_dict(
                        "PostureBotActionStarted",
                        action_uid=event["action_uid"],
                    )
                )

            elif event["type"] == "StopPostureBotAction":
                print(
                    f"\033[92mstop: posture (action_uid={event['action_uid']})\033[0m"
                )
                input_events.append(
                    new_event_dict(
                        "PostureBotActionFinished",
                        action_uid=event["action_uid"],
                        is_success=True,
                    )
                )

            elif event["type"] == "StartVisualInformationSceneAction":
                # We print scene messages in green.
                print(
                    f"\033[92mshow: scene information (title={event['title']}, action_uid={event['action_uid']})\033[0m"
                )
                input_events.append(
                    new_event_dict(
                        "VisualInformationSceneActionStarted",
                        action_uid=event["action_uid"],
                    )
                )

            elif event["type"] == "StopVisualInformationSceneAction":
                print(
                    f"\033[92mhide: scene information (action_uid={event['action_uid']})\033[0m"
                )
                input_events.append(
                    new_event_dict(
                        "VisualInformationSceneActionFinished",
                        action_uid=event["action_uid"],
                        is_success=True,
                    )
                )

            elif event["type"] == "StartVisualChoiceSceneAction":
                # We print scene messages in green.
                print(
                    f"\033[92mshow: scene choice (prompt={event['prompt']}, action_uid={event['action_uid']})\033[0m"
                )
                input_events.append(
                    new_event_dict(
                        "VisualChoiceSceneActionStarted",
                        action_uid=event["action_uid"],
                    )
                )

            elif event["type"] == "StopVisualChoiceSceneAction":
                print(
                    f"\033[92mhide: scene choice (action_uid={event['action_uid']})\033[0m"
                )
                input_events.append(
                    new_event_dict(
                        "VisualChoiceSceneActionFinished",
                        action_uid=event["action_uid"],
                        is_success=True,
                    )
                )

            elif event["type"] == "StartTimerBotAction":
                # print(f"\033[92mstart timer: {event['timer_name']} {event['duration']}\033[0m")
                action_uid = event["action_uid"]
                timer = _start_timer(event["timer_name"], event["duration"], action_uid)
                # Manage timer tasks
                if action_uid not in running_timer_tasks:
                    task = asyncio.create_task(timer)
                    running_timer_tasks.update({action_uid: task})
                input_events.append(
                    new_event_dict(
                        "TimerBotActionStarted",
                        action_uid=event["action_uid"],
                    )
                )

            elif event["type"] == "StopTimerBotAction":
                # print(f"\033[92mstart timer: {event['timer_name']} {event['duration']}\033[0m")
                action_uid = event["action_uid"]
                if action_uid in running_timer_tasks:
                    running_timer_tasks[action_uid].cancel()
                    print(f"Timer {action_uid} was stopped!")
                    running_timer_tasks.pop(action_uid)

        # TODO: deserialize the output state
        # state = State.from_dict(output_state)
        # Simulate serialization for testing
        # data = pickle.dumps(output_state)
        # output_state = pickle.loads(data)
        state = output_state

    async def _check_local_async_actions():
        nonlocal output_events, output_state, input_events, check_task

        while True:
            # We only run the check when we wait for user input, but not the first time.
            if not waiting_user_input or first_time:
                await asyncio.sleep(0.1)
                continue

            if len(input_events) == 0:
                input_events = [new_event_dict("CheckLocalAsync")]

            output_events, output_state = await rails_app.process_events_async(
                input_events, state
            )
            input_events = []

            # Process output_events and potentially generate new input_events
            _process_output()

            if (
                len(output_events) == 1
                and output_events[0]["type"] == "LocalAsyncCounter"
                and output_events[0]["counter"] == 0
            ):
                # If there are no pending actions, we stop
                check_task.cancel()
                check_task = None
                return

            output_events.clear()

            await asyncio.sleep(0.2)

    async def _process_input_events():
        nonlocal first_time, output_events, output_state, input_events, check_task
        while input_events or first_time:
            output_events, output_state = await rails_app.process_events_async(
                input_events, state
            )
            input_events = []
            _process_output()
            # If we don't have a check task, we start it
            if check_task is None:
                check_task = asyncio.create_task(_check_local_async_actions())

            first_time = False

    # Start the task for checking async actions
    check_task = asyncio.create_task(_check_local_async_actions())

    # And go into the default listening loop.
    first_time = True
    with patch_stdout(raw=True):
        while True:
            if first_time:
                input_events = []
            else:
                waiting_user_input = True
                user_message = await input_async("> ")
                waiting_user_input = False
                if user_message == "":
                    input_events = [
                        {
                            "type": "CheckLocalAsync",
                        }
                    ]
                elif user_message.startswith("/"):
                    # Non-UtteranceBotAction actions
                    pass
                else:
                    input_events = [
                        {
                            "type": "UtteranceUserActionFinished",
                            "final_transcript": user_message,
                        }
                    ]

            await _process_input_events()


def run_chat(
    config_path: Optional[str] = None,
    verbose: bool = False,
    streaming: bool = False,
    server_url: Optional[str] = None,
    config_id: Optional[str] = None,
):
    """Run a chat session in the terminal.

    Args:
        config_path (Optional[str]): The path to the configuration file. Defaults to None.
        verbose (bool): Whether to run in verbose mode. Defaults to False.
        streaming (bool): Whether to enable streaming mode. Defaults to False.
        server_url (Optional[str]): The URL of the chat server. Defaults to None.
        config_id (Optional[str]): The configuration ID. Defaults to None.
    """

    rails_config = RailsConfig.from_path(config_path)
    rails_app = LLMRails(rails_config, verbose=verbose)

    if rails_config.colang_version == "1.0":
        asyncio.run(
            _run_chat_v1_0(
                config_path=config_path,
                verbose=verbose,
                streaming=streaming,
                server_url=server_url,
                config_id=config_id,
            )
        )
    elif rails_config.colang_version == "1.1":
        asyncio.run(_run_chat_v1_1(rails_app))
    else:
        raise Exception(f"Invalid colang version: {rails_config.colang_version}")
