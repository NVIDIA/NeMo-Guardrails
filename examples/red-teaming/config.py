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

import csv
import json

from nemoguardrails.server.api import register_logger


async def custom_logger(item):
    """Custom logger that writes the ratings to a CSV file in the current directory."""
    data = json.loads(item["body"])
    config_id = data["config_id"]
    messages = data["messages"]

    # We only track on rating events
    if messages[-1]["role"] != "event" or messages[-1]["event"].get("type") != "rating":
        print("Skipping")
        return

    # Extract the data from the event
    str_messages = ""
    for message in messages:
        if message["role"] == "user":
            str_messages += f"User: {message['content']}\n"
        if message["role"] == "assistant":
            str_messages += f"Assistant: {message['content']}\n"

    event_data = messages[-1]["event"]["data"]

    row = [
        config_id,
        event_data["challenge"]["id"],
        event_data["challenge"]["name"],
        event_data["challenge"]["description"],
        event_data["success"],
        event_data["effort"],
        event_data["comment"],
        str_messages.strip(),
    ]

    with open("ratings.csv", "a", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(row)


register_logger(custom_logger)
