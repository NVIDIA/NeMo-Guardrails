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
from typing import List, Tuple


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


def is_content_safe(response: str) -> Tuple[bool, List[str]]:
    """Analyzes a given response from a guardrails check (e.g., content safety check or input check) and determines if the content is safe or not.

    The function operates based on the presence of certain keywords in the response:
    - If the response contains "safe", the content is deemed safe.
    - If the response contains "unsafe" or "yes", the content is deemed unsafe.
    - If the response contains "no", the content is deemed safe.

    Note: If you are using this function for a different task with a custom prompt, ensure to update the logic to match the new context.
    Here, "yes" implies the content should be blocked, is unsafe, or violates a policy, while "no" implies the content is safe or does not violate any policy.


    For example, in the `self_check_facts` action, we have a different interpretation.
    Here, "yes" indicates the content is safe. This is against the default logic of the `is_content_safe` function.
    Therefore, we invert the result of `is_content_safe` to align with this interpretation.
    If `is_content_safe` returns `False` (content is safe), `result` will be `0.0`. If `is_content_safe` returns `True` (content is unsafe), `result` will be `1.0`.



    Args:
        response (str): The response string to analyze.

    Returns:
        Tuple[bool, Optional[List[str]]]: A tuple where the first element is a boolean indicating the safety of the content (True if safe, False otherwise),
        and the second element is a list of violated policies, if any.
    """

    response = response.lower().strip()
    # replace sequences of non word characters in the response with a single space
    response = re.sub(r"\W+", " ", response)
    # we only look at the first 3 words in the response
    splited_response = response.split(" ")[:2]

    response_actions = {
        "safe": lambda: (True, []),
        "unsafe": lambda: (False, response.split("unsafe")[1].strip().split(" ")),
        "yes": lambda: (False, []),
        "no": lambda: (True, []),
    }

    for prefix, action in response_actions.items():
        if prefix in splited_response:
            return action()

    # or
    # raise ValueError(f"Unknown response: {response}")
    return (False, [])
