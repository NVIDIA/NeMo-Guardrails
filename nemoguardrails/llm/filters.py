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

import re
from typing import List

from nemoguardrails.actions.llm.utils import get_colang_history


def colang(events: List[dict]) -> str:
    """
    Convert an array of events into a CoLang history.

    Args:
        events (List[dict]): A list of events to be converted into CoLang history.

    Returns:
        str: The CoLang history generated from the input events.

    """
    return get_colang_history(events)


def to_messages(colang_history: str) -> List[dict]:
    """
    Parse a CoLang history and extract individual messages.

    Given a history in CoLang format, this function extracts and returns individual messages.

    Args:
        colang_history (str): The CoLang history to be parsed.

    Returns:
        List[dict]: A list of dictionaries, each representing a message with its type and content.

    """
    messages = []

    # For now, we use a simple heuristic. The line `user "xxx"` gets translated to
    # a message from the user, and the rest gets translated to messages from the assistant.
    lines = colang_history.split("\n")

    bot_lines = []
    for i, line in enumerate(lines):
        if line.startswith('user "'):
            # If we have bot lines in the buffer, we first add a bot message.
            if bot_lines:
                messages.append({"type": "assistant", "content": "\n".join(bot_lines)})
                bot_lines = []

            messages.append({"type": "user", "content": line[6:-1]})

        elif line.strip() == "":
            # On empty lines, we also reset the bot buffer.
            if bot_lines:
                messages.append({"type": "assistant", "content": "\n".join(bot_lines)})
                bot_lines = []
        else:
            if i > 0 and lines[i - 1].startswith('user "'):
                line = "User intent: " + line.strip()
            elif line.startswith("user "):
                line = "User intent: " + line[5:].strip()
            elif line.startswith("bot "):
                line = "Bot intent: " + line[4:].strip()
            elif line.startswith('  "'):
                line = "Bot message: " + line[2:].strip()
            bot_lines.append(line)

    # Check if there is a last message from the bot.
    if bot_lines:
        messages.append({"type": "bot", "content": "\n".join(bot_lines)})

    return messages


def verbose_v1(colang_history: str) -> str:
    """
    Generate a verbose version of a CoLang history.

    This function takes a history in CoLang format and returns a verbose version of the same history.

    Args:
        colang_history (str): The input CoLang history.

    Returns:
        str: A verbose version of the CoLang history with expanded message types.

    """
    lines = colang_history.split("\n")
    for i, line in enumerate(lines):
        if line.startswith('user "'):
            lines[i] = 'User message: "' + line[6:]
        elif (
            line.startswith("  ")
            and i > 0
            and lines[i - 1].startswith("User message: ")
        ):
            lines[i] = "User intent: " + line.strip()
        elif line.startswith("user "):
            lines[i] = "User intent: " + line[5:].strip()
        elif line.startswith("bot "):
            lines[i] = "Bot intent: " + line[4:]
        elif line.startswith('  "'):
            lines[i] = "Bot message: " + line[2:]

    return "\n".join(lines)


def user_assistant_sequence(events: List[dict]) -> str:
    """Filter that turns an array of events into a sequence of user/assistant messages.

    The output will look like:
       ```
       User: hi
       Assistant: Hello there!
       User: What can you do?
       Assistant: I can help with many things.
       ```
    Convert an array of events into a sequence of user and assistant messages.

    This function takes an array of events and converts them into a human-readable sequence of user and assistant messages.

    Args:
        events (List[dict]): A list of events to be converted into a message sequence.

    Returns:
        str: A formatted sequence of user and assistant messages.

    """
    history_items = []
    for event in events:
        if event["type"] == "UtteranceUserActionFinished":
            history_items.append("User: " + event["final_transcript"])
        elif event["type"] == "StartUtteranceBotAction":
            history_items.append("Assistant: " + event["script"])

    return "\n".join(history_items)


def remove_text_messages(colang_history: str):
    """
    Remove text messages from a CoLang history.

    This function removes text messages (both user and bot) from a CoLang history.

    Args:
        colang_history (str): The input CoLang history.

    Returns:
        str: The CoLang history with text messages removed.

    """
    # Get rid of messages from the user
    colang_history = re.sub(r'user "[^\n]+"\n {2}', "user ", colang_history)

    # Get rid of one line user messages
    colang_history = re.sub(r"^\s*user [^\n]+\n\n", "", colang_history)

    # Get rid of bot messages
    colang_history = re.sub(r'bot ([^\n]+)\n {2}"[\s\S]*?"', r"bot \1", colang_history)

    return colang_history


def first_turns(colang_history: str, n: int) -> str:
    """
    Retrieve the first n turns from a CoLang history.

    This function returns the first n turns from a CoLang history.

    Args:
        colang_history (str): The input CoLang history.
        n (int): The number of turns to retrieve.

    Returns:
        str: The first n turns from the CoLang history.

    """
    lines = colang_history.split("\n")
    turn_count = 0
    i = 0
    while i < len(lines):
        if lines[i].startswith('user "'):
            turn_count += 1
        if turn_count == n + 1:
            break
        i += 1

    return "\n".join(lines[0:i])


def last_turns(colang_history: str, n: int) -> str:
    """
    Retrieve the last n turns from a CoLang history.

    This function returns the last n turns from a CoLang history.

    Args:
        colang_history (str): The input CoLang history.
        n (int): The number of turns to retrieve.

    Returns:
        str: The last n turns from the CoLang history.

    """
    lines = colang_history.split("\n")
    turn_count = 0
    i = len(lines) - 1
    while i > 0:
        if lines[i].startswith('user "'):
            turn_count += 1
        if turn_count == n:
            break
        i -= 1

    return "\n".join(lines[i:])


def user_assistant_sequence_nemollm(events: List[dict]) -> str:
    """Filter that turns an array of events into a sequence of user/assistant messages.

    The output will look like:
       ```
       <extra_id_1>User
       hi
       <extra_id_1>Assistant
       Hello there!
       <extra_id_1>User
       What can you do?
       <extra_id_1>Assistant
       I can help with many things.
       ```
    """
    history_items = []
    for event in events:
        if event["type"] == "UtteranceUserActionFinished":
            history_items.append("<extra_id_1>User\n" + event["final_transcript"])
        elif event["type"] == "StartUtteranceBotAction":
            history_items.append("<extra_id_1>Assistant\n" + event["script"])

    return "\n".join(history_items)


def to_messages_nemollm(colang_history: str) -> str:
    """Filter that given a history in colang format, returns a messages string
    in the chat format used by NeMo LLM models."""
    messages = []

    # For now, we use a simple heuristic. The line `user "xxx"` gets translated to
    # a message from the user, and the rest gets translated to messages from the assistant.
    lines = colang_history.split("\n")

    bot_lines = []
    for i, line in enumerate(lines):
        if line.startswith('user "'):
            # If we have bot lines in the buffer, we first add a bot message.
            if bot_lines:
                messages.append({"type": "assistant", "content": "\n".join(bot_lines)})
                bot_lines = []

            messages.append({"type": "user", "content": line[6:-1]})

        elif line.strip() == "":
            # On empty lines, we also reset the bot buffer.
            if bot_lines:
                messages.append({"type": "assistant", "content": "\n".join(bot_lines)})
                bot_lines = []
        else:
            if i > 0 and lines[i - 1].startswith('user "'):
                line = "User intent: " + line.strip()
            elif line.startswith("user "):
                line = "User intent: " + line[5:].strip()
            elif line.startswith("bot "):
                line = "Bot intent: " + line[4:].strip()
            elif line.startswith('  "'):
                line = "Bot message: " + line[2:].strip()
            bot_lines.append(line)

    # Check if there is a last message from the bot.
    if bot_lines:
        messages.append({"type": "bot", "content": "\n".join(bot_lines)})

    messages_string = ""
    for m in messages:
        if m["type"] == "assistant" or m["type"] == "bot":
            messages_string += "<extra_id_1>Assistant\n" + m["content"] + "\n"
        elif m["type"] == "user":
            messages_string += "<extra_id_1>User\n" + m["content"] + "\n"
    return messages_string


def remove_trailing_new_line(s: str):
    if s.endswith("\n"):
        s = s[:-1]
    return s
