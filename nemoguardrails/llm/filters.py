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
    """Filter that turns an array of events into a colang history."""
    return get_colang_history(events)


def to_messages(colang_history: str) -> List[dict]:
    """Filter that given a history in colang format, returns all messages."""
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
    """Filter that given a history in colang format, returns a verbose version of the history."""
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
    """
    history_items = []
    for event in events:
        if event["type"] == "UserMessage":
            history_items.append("User: " + event["text"])
        elif event["type"] == "StartUtteranceBotAction":
            history_items.append("Assistant: " + event["script"])

    return "\n".join(history_items)


def remove_text_messages(colang_history: str):
    """Filters that given a history in colang format, removes all texts."""

    # Get rid of messages from the user
    colang_history = re.sub(r'user "[^\n]+"\n {2}', "user ", colang_history)

    # Get rid of one line user messages
    colang_history = re.sub(r"^\s*user [^\n]+\n\n", "", colang_history)

    # Get rid of bot messages
    colang_history = re.sub(r'bot ([^\n]+)\n {2}"[\s\S]*?"', r"bot \1", colang_history)

    return colang_history


def first_turns(colang_history: str, n: int) -> str:
    """Returns the first n turns from a given colang history."""
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
    """Returns the last n turns from a given colang history."""
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
        if event["type"] == "UserMessage":
            history_items.append("<extra_id_1>User\n" + event["text"])
        elif event["type"] == "StartUtteranceBotAction":
            history_items.append("<extra_id_1>Assistant\n" + event["script"])

    return "\n".join(history_items)


def _previous_line(lines: List[str], i: int):
    """Returns the previous lines, skipping comments."""
    i = i - 1
    while i > 0 and lines[i].strip().startswith("#"):
        i -= 1
    return lines[i]


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
            if i > 0 and _previous_line(lines, i).startswith('user "'):
                if not line.strip().startswith("#"):
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


def conversation_to_events(conversation: List) -> List[dict]:
    """Filter that given a conversation, returns a list of events."""
    events = []
    for turn in conversation:
        if "user" in turn:
            events.append(
                {
                    "type": "UtteranceUserActionFinished",
                    "final_transcript": turn["user"],
                }
            )

        if "user_intent" in turn:
            events.append(
                {
                    "type": "UserIntent",
                    "intent": turn["user_intent"],
                }
            )

        if "bot" in turn:
            events.append(
                {
                    "type": "StartUtteranceBotAction",
                    "script": turn["bot"],
                }
            )

        if "bot_intent" in turn:
            events.append(
                {
                    "type": "BotIntent",
                    "intent": turn["bot_intent"],
                }
            )

    return events
