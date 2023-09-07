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
from typing import Optional

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


def _run_chat_v1_1(rails_app: LLMRails):
    """Simple chat loop for v1.1 using the stateful events API."""
    state = None
    first = True

    # And go into the default listening loop.
    while True:
        if first:
            # We first need to initialize the state by starting the main flow.
            # TODO: a better way to do this?
            first = False
            input_events = [
                {
                    "type": "StartFlow",
                    "flow_id": "main",
                },
            ]
        else:
            user_message = input("> ")
            input_events = [
                {
                    "type": "UtteranceUserActionFinished",
                    "final_transcript": user_message,
                }
            ]

        while input_events:
            output_events, output_state = rails_app.process_events(input_events, state)

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

            # TODO: deserialize the output state
            # state = State.from_dict(output_state)
            state = output_state


def run_chat(config_path: Optional[str] = None, verbose: bool = False):
    """Runs a chat session in the terminal."""

    rails_config = RailsConfig.from_path(config_path)
    rails_app = LLMRails(rails_config, verbose=verbose)

    if rails_config.colang_version == "1.0":
        _run_chat_v1_0(rails_app)
    elif rails_config.colang_version == "1.1":
        _run_chat_v1_1(rails_app)
    else:
        raise Exception(f"Invalid colang version: {rails_config.colang_version}")
