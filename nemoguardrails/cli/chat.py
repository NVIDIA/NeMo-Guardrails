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
import pickle
from typing import Any, Dict, List, Optional

from prompt_toolkit import prompt
from prompt_toolkit.patch_stdout import patch_stdout

from nemoguardrails import LLMRails, RailsConfig
from nemoguardrails.utils import new_event_dict

os.environ["TOKENIZERS_PARALLELISM"] = "false"


def _run_chat_v1_0(rails_app: LLMRails):
    """Simple chat loop for v1.0 using the messages API."""
    history = []
    # And go into the default listening loop.
    while True:
        user_message = input("> ")

        history.append({"role": "user", "content": user_message})
        bot_message = rails_app.generate(messages=history)
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
        input_events = []
        for event in output_events:
            if event["type"] == "StartUtteranceBotAction":
                # We print bot messages in green.
                print(f"\033[92m{event['script']}\033[0m")

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

            elif event["type"] == "StopTimerBotAction":
                # print(f"\033[92mstart timer: {event['timer_name']} {event['duration']}\033[0m")
                action_uid = event["action_uid"]
                if action_uid in running_timer_tasks:
                    running_timer_tasks[action_uid].cancel()
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

            # Process output_events and potentially generate new input_events
            _process_output()

            if (
                len(output_events) == 1
                and output_events[0]["type"] == "LocalAsyncCounter"
                and output_events[0]["counter"] == 0
            ):
                # If there are no pending actions, we stop
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


async def input_async(prompt_message: str = "") -> str:
    loop = asyncio.get_event_loop()
    return await loop.run_in_executor(None, prompt, prompt_message)


def run_chat(config_path: Optional[str] = None, verbose: bool = False):
    """Runs a chat session in the terminal."""

    rails_config = RailsConfig.from_path(config_path)
    rails_app = LLMRails(rails_config, verbose=verbose)

    if rails_config.colang_version == "1.0":
        _run_chat_v1_0(rails_app)
    elif rails_config.colang_version == "1.1":
        asyncio.run(_run_chat_v1_1(rails_app))
    else:
        raise Exception(f"Invalid colang version: {rails_config.colang_version}")
