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


def user_intent_parser(s: str):
    """Parses the user intent."""
    s = s.strip()
    if s.startswith("User intent: "):
        s = s.split("\n")[0]
        return s[13:].strip()

    return s


def bot_intent_parser(s: str):
    """Parses the bot intent."""
    s = s.strip()
    if s.startswith("Bot intent: "):
        s = s.split("\n")[0]
        return s[13:].strip()

    return s


def bot_message_parser(s: str):
    """Parses the bot messages."""
    s = s.strip()
    if s.startswith("Bot message: "):
        s = s.split("\n")[0]
        return s[14:].strip()

    return s
