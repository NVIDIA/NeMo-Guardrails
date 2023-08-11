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


def _replace_prefix(s: str, prefix: str, repl: str):
    """Helper function to replace a prefix from a string."""
    if s.startswith(prefix):
        return repl + s[len(prefix) :].strip()

    return s


def user_intent_parser(s: str):
    """Parses the user intent."""
    return _replace_prefix(s.strip(), "User intent: ", "  ")


def bot_intent_parser(s: str):
    """Parses the bot intent."""
    return _replace_prefix(s.strip(), "Bot intent: ", "bot ")


def bot_message_parser(s: str):
    """Parses the bot messages."""
    return _replace_prefix(s.strip(), "Bot message: ", "  ")


def verbose_v1_parser(s: str):
    """Parses completions generated using the `verbose_v1` formatter.

    This will convert text from the following format:
      User message: "Hello"
      User intent: express greeting
      Bot intent: express greeting
      Bot message: "Hi"

    To:
      user "Hello"
        express greeting
      bot express greeting
        "Hi"
    """
    lines = s.split("\n")

    prefixes = [
        ("User message: ", "user "),
        ("Bot message: ", "  "),
        ("User intent: ", "  "),
        ("Bot intent: ", "bot "),
    ]

    for i in range(len(lines)):
        # Some LLMs generate a space at the beginning of the first line
        lines[i] = lines[i].strip()
        for prefix, repl in prefixes:
            # Also allow prefixes to be in lower-case
            lines[i] = _replace_prefix(lines[i], prefix, repl)
            lines[i] = _replace_prefix(lines[i], prefix.lower(), repl)

    return "\n".join(lines)
