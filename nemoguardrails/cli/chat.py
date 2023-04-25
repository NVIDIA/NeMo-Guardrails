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

os.environ["TOKENIZERS_PARALLELISM"] = "false"


def run_chat(config_path: Optional[str] = None, verbose: bool = False):
    """Runs a chat session in the terminal."""

    rails_config = RailsConfig.from_path(config_path)

    # TODO: add support for loading a config directly from live playground
    # rails_config = RailsConfig.from_playground(model="...")

    # TODO: add support to register additional actions
    # rails_app.register_action(...)

    rails_app = LLMRails(rails_config, verbose=verbose)

    history = []
    # And go into the default listening loop.
    while True:
        user_message = input("> ")

        history.append({"role": "user", "content": user_message})
        bot_message = rails_app.generate(messages=history)
        history.append(bot_message)

        # We print bot messages in green.
        print(f"\033[92m{bot_message['content']}\033[0m")
