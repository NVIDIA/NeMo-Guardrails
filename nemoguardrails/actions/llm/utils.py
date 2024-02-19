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
from typing import List, Optional, Union

from langchain.base_language import BaseLanguageModel
from langchain.callbacks.base import AsyncCallbackHandler, BaseCallbackManager
from langchain.prompts.base import StringPromptValue
from langchain.prompts.chat import ChatPromptValue
from langchain.schema import AIMessage, HumanMessage, SystemMessage

from nemoguardrails.colang.v2_x.lang.colang_ast import Flow
from nemoguardrails.colang.v2_x.runtime.flows import InternalEvent, InternalEvents
from nemoguardrails.context import llm_call_info_var
from nemoguardrails.logging.callbacks import logging_callbacks
from nemoguardrails.logging.explain import LLMCallInfo


async def llm_call(
    llm: BaseLanguageModel,
    prompt: Union[str, List[dict]],
    stop: Optional[List[str]] = None,
    custom_callback_handlers: Optional[List[AsyncCallbackHandler]] = None,
) -> str:
    """Calls the LLM with a prompt and returns the generated text."""

    # We initialize a new LLM call if we don't have one already
    llm_call_info = llm_call_info_var.get()
    if llm_call_info is None:
        llm_call_info = LLMCallInfo()
        llm_call_info_var.set(llm_call_info)

    if custom_callback_handlers and custom_callback_handlers != [None]:
        all_callbacks = BaseCallbackManager(
            handlers=logging_callbacks.handlers + custom_callback_handlers,
            inheritable_handlers=logging_callbacks.handlers + custom_callback_handlers,
        )
    else:
        all_callbacks = logging_callbacks

    if isinstance(prompt, str):
        # stop sinks here
        result = await llm.agenerate_prompt(
            [StringPromptValue(text=prompt)], callbacks=all_callbacks, stop=stop
        )
        llm_call_info.raw_response = result.llm_output

        # TODO: error handling
        return result.generations[0][0].text
    else:
        # We first need to translate the array of messages into LangChain message format
        messages = []
        for _msg in prompt:
            if _msg["type"] == "user":
                messages.append(HumanMessage(content=_msg["content"]))
            elif _msg["type"] in ["bot", "assistant"]:
                messages.append(AIMessage(content=_msg["content"]))
            elif _msg["type"] == "system":
                messages.append(SystemMessage(content=_msg["content"]))
            else:
                raise ValueError(f"Unknown message type {_msg['type']}")
        result = await llm.agenerate_prompt(
            [ChatPromptValue(messages=messages)], callbacks=all_callbacks, stop=stop
        )
        llm_call_info.raw_response = result.llm_output

        return result.generations[0][0].text


def get_colang_history(
    events: List[dict],
    include_texts: bool = True,
    remove_retrieval_events: bool = False,
) -> str:
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

    if not events:
        return history

    # We try to automatically detect if we have a Colang 1.0 or a 2.x history
    # TODO: Think about more robust approach?
    colang_version = "1.0"
    for event in events:
        if isinstance(event, InternalEvent):
            event = {"type": event.name, **event.arguments}

        if event["type"] in InternalEvents.ALL:
            colang_version = "2.x"

    if colang_version == "1.0":
        # We compute the index of the last bot message. We need it so that we include
        # the bot message instruction only for the last one.
        last_bot_intent_idx = len(events) - 1
        while last_bot_intent_idx >= 0:
            if events[last_bot_intent_idx]["type"] == "BotIntent":
                break
            last_bot_intent_idx -= 1

        for idx, event in enumerate(events):
            if event["type"] == "UserMessage" and include_texts:
                history += f'user "{event["text"]}"\n'
            elif event["type"] == "UserIntent":
                if include_texts:
                    history += f'  {event["intent"]}\n'
                else:
                    history += f'user {event["intent"]}\n'
            elif event["type"] == "BotIntent":
                # If we have instructions, we add them before the bot message.
                # But we only do that for the last bot message.
                if "instructions" in event and idx == last_bot_intent_idx:
                    history += f"# {event['instructions']}\n"
                history += f'bot {event["intent"]}\n'
            elif event["type"] == "StartUtteranceBotAction" and include_texts:
                history += f'  "{event["script"]}"\n'
            # We skip system actions from this log
            elif event["type"] == "StartInternalSystemAction" and not event.get(
                "is_system_action"
            ):
                if (
                    remove_retrieval_events
                    and event["action_name"] == "retrieve_relevant_chunks"
                ):
                    continue
                history += f'execute {event["action_name"]}\n'
            elif event["type"] == "InternalSystemActionFinished" and not event.get(
                "is_system_action"
            ):
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
                placeholder_text = "<<<This text is hidden because the assistant should not talk about this.>>>"
                history = placeholder_text.join(split_history)

    elif colang_version == "2.x":
        new_history: List[str] = []

        # Structure the user/bot intent/action events
        action_group: List[InternalEvent] = []
        current_intent: Optional[str] = None

        for event in events:
            if not isinstance(event, InternalEvent):
                continue

            if (
                event.name == InternalEvents.BOT_ACTION_LOG
                or event.name == InternalEvents.USER_ACTION_LOG
            ):
                if len(action_group) > 0 and (
                    current_intent is None
                    or current_intent != event.arguments["intent_flow_id"]
                ):
                    new_history.append(events_to_dialog_history(action_group))
                    new_history.append("")
                    action_group.clear()

                action_group.append(event)
                current_intent = event.arguments["intent_flow_id"]
            elif (
                event.name == InternalEvents.BOT_INTENT_LOG
                or event.name == InternalEvents.USER_INTENT_LOG
            ):
                if event.arguments["flow_id"] == current_intent:
                    # Found parent of current group
                    if event.name == InternalEvents.BOT_INTENT_LOG:
                        new_history.append(events_to_dialog_history([event]))
                        new_history.append(events_to_dialog_history(action_group))
                    elif event.arguments["flow_id"] is not None:
                        new_history.append(events_to_dialog_history(action_group))
                        new_history.append(events_to_dialog_history([event]))
                    new_history.append("")
                else:
                    # New unrelated intent
                    if action_group:
                        new_history.append(events_to_dialog_history(action_group))
                        new_history.append("")
                    new_history.append(events_to_dialog_history([event]))
                    new_history.append("")
                # Start a new group
                action_group.clear()
                current_intent = None

        if action_group:
            new_history.append(events_to_dialog_history(action_group))

        history = "\n".join(new_history).rstrip("\n")

    return history


def events_to_dialog_history(events: List[InternalEvent]) -> str:
    """Create the dialog history based on provided events."""
    result = ""
    for idx, event in enumerate(events):
        identifier = from_log_event_to_identifier(event.name)
        if idx == 0:
            intent = f"{identifier}: {event.arguments['flow_id']}"
        else:
            intent = f"{event.arguments['flow_id']}"
        param_value = event.arguments["parameter"]
        if param_value is not None:
            if isinstance(param_value, str):
                intent = f'{intent} "{param_value}"'
            else:
                intent = f"{intent} {param_value}"
        result += intent
        if idx + 1 < len(events):
            result += "\n  and "
    return result


def from_log_event_to_identifier(event_name: str) -> str:
    """convert log message to prompt interaction identifier."""
    if event_name == InternalEvents.BOT_INTENT_LOG:
        return "bot intent"
    elif event_name == InternalEvents.BOT_ACTION_LOG:
        return "bot action"
    elif event_name == InternalEvents.USER_INTENT_LOG:
        return "user intent"
    elif event_name == InternalEvents.USER_ACTION_LOG:
        return "user action"
    return ""


def flow_to_colang(flow: Union[dict, Flow]) -> str:
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
    if isinstance(flow, Flow):
        # TODO: generate the flow code from the flow.elements array
        pass
    else:
        for element in flow["elements"]:
            if "_type" not in element:
                raise Exception("bla")
            if element["_type"] == "UserIntent":
                colang_flow += f'user {element["intent_name"]}\n'
            elif element["_type"] == "run_action" and element["action_name"] == "utter":
                colang_flow += f'bot {element["action_params"]["value"]}\n'

    return colang_flow


def get_last_user_utterance(events: List[dict]) -> Optional[str]:
    """Returns the last user utterance from the events."""
    for event in reversed(events):
        if event["type"] == "UserMessage":
            return event["text"]

    return None


def get_retrieved_relevant_chunks(events: List[dict]) -> Optional[dict]:
    """Returns the retrieved chunks for current user utterance from the events."""
    for event in reversed(events):
        if event["type"] == "UserMessage":
            break
        if event["type"] == "ContextUpdate" and "relevant_chunks" in event.get(
            "data", {}
        ):
            return event["data"]["relevant_chunks"]

    return None


def get_last_user_utterance_event(events: List[dict]) -> Optional[dict]:
    """Returns the last user utterance from the events."""
    for event in reversed(events):
        if isinstance(event, dict) and event["type"] == "UserMessage":
            return event

    return None


def get_last_user_utterance_event_v2_x(events: List[dict]) -> Optional[dict]:
    """Returns the last user utterance from the events."""
    for event in reversed(events):
        if isinstance(event, dict) and event["type"] == "UtteranceUserActionFinished":
            return event

    return None


def get_last_user_intent_event(events: List[dict]) -> Optional[dict]:
    """Returns the last user intent from the events."""
    for event in reversed(events):
        if event["type"] == "UserIntent":
            return event

    return None


def get_last_bot_intent_event(events: List[dict]) -> Optional[dict]:
    """Returns the last user intent from the events."""
    for event in reversed(events):
        if event["type"] == "BotIntent":
            return event

    return None


def get_last_bot_utterance_event(events: List[dict]) -> Optional[dict]:
    """Returns the last bot utterance from the events."""
    for event in reversed(events):
        if event["type"] == "StartUtteranceBotAction":
            return event

    return None


def remove_text_messages_from_history(history: str) -> str:
    """Helper that given a history in colang format, removes all texts."""

    # Get rid of messages from the user
    history = re.sub(r'user "[^\n]+"\n {2}', "user ", history)

    # Get rid of one line user messages
    history = re.sub(r"^\s*user [^\n]+\n\n", "", history)

    # Get rid of bot messages
    history = re.sub(r'bot ([^\n]+)\n {2}"[\s\S]*?"', r"bot \1", history)

    return history


def get_first_nonempty_line(s: str) -> Optional[str]:
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


def get_top_k_nonempty_lines(s: str, k: int = 1) -> Optional[List[str]]:
    """Helper that returns a list with the top k non-empty lines from a string.

    If there are less than k non-empty lines, it returns a smaller number of lines."""
    if not s:
        return None

    lines = [line.strip() for line in s.split("\n")]
    # Ignore line comments and empty lines
    lines = [line for line in lines if len(line) > 0 and line[0] != "#"]

    return lines[:k]


def strip_quotes(s: str) -> str:
    """Helper that removes quotes from a string if the entire string is between quotes"""
    if s and s[0] == '"':
        if s[-1] == '"':
            s = s[1:-1]
        else:
            s = s[1:]
    return s


def get_multiline_response(s: str) -> str:
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


def remove_action_intent_identifiers(lines: List[str]) -> List[str]:
    """Removes the action/intent identifiers."""
    return [
        s.replace("bot intent: ", "")
        .replace("bot action: ", "")
        .replace("user intent: ", "")
        .replace("user action: ", "")
        for s in lines
    ]


def get_initial_actions(strings: List[str]) -> List[str]:
    """Returns the first action before an empty line."""
    previous_strings = []
    for string in strings:
        if string == "":
            break
        previous_strings.append(string)
    return previous_strings


def escape_flow_name(name: str) -> str:
    """Escape invalid keywords in flow names."""
    # TODO: We need to figure out how we can distinguish from valid flow parameters
    result = (
        name.replace(" and ", "_and_")
        .replace(" or ", "_or_")
        .replace(" as ", "_as_")
        .replace(" not ", "_not_")
        .replace(" is ", "_is_")
        .replace(" in ", "_in_")
        .replace("(", "")
        .replace(")", "")
        .replace("'", "")
        .replace('"', "")
        .replace("-", "_")
    )
    return re.sub(r"\b\d+\b", lambda match: f"_{match.group()}_", result)
