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


def get_colang_history(
    events: List[dict],
    include_texts: bool = True,
    remove_retrieval_events: bool = False,
):
    """Creates a history of user messages and bot responses in colang format.
    user "Hi, how are you today?"
      express greeting
    bot express greeting
      "Greetings! I am the official NVIDIA Benefits Ambassador AI bot and I'm here to assist you."
    user "What can you help me with?"
      ask capabilities
    bot inform capabilities
      "As an AI, I can provide you with a wide range of services, such as ..."

    """

    history = ""
    for idx, event in enumerate(events):
        if event["type"] == "user_said" and include_texts:
            history += f'user "{event["content"]}"\n'
        elif event["type"] == "user_intent":
            if include_texts:
                history += f'  {event["intent"]}\n'
            else:
                history += f'user {event["intent"]}\n'
        elif event["type"] == "bot_intent":
            history += f'bot {event["intent"]}\n'
        elif event["type"] == "bot_said" and include_texts:
            history += f'  "{event["content"]}"\n'
        # We skip system actions from this log
        elif event["type"] == "start_action" and not event.get("is_system_action"):
            if (
                remove_retrieval_events
                and event["action_name"] == "retrieve_relevant_chunks"
            ):
                continue
            history += f'execute {event["action_name"]}\n'
        elif event["type"] == "action_finished" and not event.get("is_system_action"):
            if (
                remove_retrieval_events
                and event["action_name"] == "retrieve_relevant_chunks"
            ):
                continue

            # We make sure the return value is a string with no new lines
            return_value = str(event["return_value"]).replace("\n", " ")
            history += f"# The result was {return_value}\n"
        elif event["type"] == "mask_prev_user_message":
            utterance_to_replace = get_last_user_utterance(events[:idx])
            # We replace the last user utterance that led to jailbreak rail trigger with a placeholder text
            split_history = history.rsplit(utterance_to_replace, 1)
            placeholder_text = "unanswerable question"
            history = placeholder_text.join(split_history)
    return history


def flow_to_colang(flow: dict):
    """Converts a flow to colang format.

    Example flow:
    ```
      - user: ask capabilities
      - bot: inform capabilities
    ```

    to colang:

    ```
    user ask capabilities
    bot inform capabilities
    ```

    """

    # TODO: use the source code lines if available.

    colang_flow = ""
    for element in flow["elements"]:
        if "_type" not in element:
            raise Exception("bla")
        if element["_type"] == "user_intent":
            colang_flow += f'user {element["intent_name"]}\n'
        elif element["_type"] == "run_action" and element["action_name"] == "utter":
            colang_flow += f'bot {element["action_params"]["value"]}\n'

    return colang_flow


def get_last_user_utterance(events: List[dict]):
    """Returns the last user utterance from the events."""
    for event in reversed(events):
        if event["type"] == "user_said":
            return event["content"]

    return None


def get_retrieved_relevant_chunks(events: List[dict]):
    """Returns the retrieved chunks for current user utterance from the events."""
    for event in reversed(events):
        if event["type"] == "user_said":
            break
        if event["type"] == "context_update" and "relevant_chunks" in event.get(
            "data", {}
        ):
            return event["data"]["relevant_chunks"]

    return None


def get_last_user_utterance_event(events: List[dict]):
    """Returns the last user utterance from the events."""
    for event in reversed(events):
        if event["type"] == "user_said":
            return event

    return None


def get_last_user_intent_event(events: List[dict]):
    """Returns the last user intent from the events."""
    for event in reversed(events):
        if event["type"] == "user_intent":
            return event

    return None


def get_last_bot_intent_event(events: List[dict]):
    """Returns the last bot intent from the events."""
    for event in reversed(events):
        if event["type"] == "bot_intent":
            return event

    return None


def remove_text_messages_from_history(history: str):
    """Helper that given a history in colang format, removes all texts."""

    # Get rid of messages from the user
    history = re.sub(r'user "[^\n]+"\n {2}', "user ", history)

    # Get rid of one line user messages
    history = re.sub(r"^\s*user [^\n]+\n\n", "", history)

    # Get rid of bot messages
    history = re.sub(r'bot ([^\n]+)\n {2}"[\s\S]*?"', r"bot \1", history)

    return history


def get_first_nonempty_line(s: str):
    """Helper that returns the first non-empty line from a string"""
    if not s:
        return None

    first_nonempty_line = None
    lines = [line.strip() for line in s.split("\n")]
    for line in lines:
        if len(line) > 0:
            first_nonempty_line = line
            break

    return first_nonempty_line


def strip_quotes(s: str):
    """Helper that removes quotes from a string if the entire string is between quotes"""
    if s and s[0] == '"':
        if s[-1] == '"':
            s = s[1:-1]
        else:
            s = s[1:]
    return s


def get_multiline_response(s: str):
    """Helper that extracts multi-line responses from the LLM.
    Stopping conditions: when a non-empty line ends with a quote or when the token "user" appears after a newline.
    Empty lines at the begging of the string are skipped."""

    # Check if the token "user" appears after a newline, as this would mark a new dialogue turn.
    # Remove everything after this marker.
    if "\nuser" in s:
        # Remove everything after the interrupt signal
        s = s.split("\nuser")[0]

    lines = [line.strip() for line in s.split("\n")]
    result = ""
    for line in lines:
        # Keep getting additional non-empty lines until the message ends
        if len(line) > 0:
            if len(result) == 0:
                result = line
            else:
                result += "\n" + line
            if line.endswith('"'):
                break

    return result


def print_completion(completion):
    print(f"\033[42m\033[97m{completion}\033[0m")
