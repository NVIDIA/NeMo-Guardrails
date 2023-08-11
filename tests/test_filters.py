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

import textwrap

from nemoguardrails.llm.filters import first_turns, last_turns


def test_first_turns():
    colang_history = textwrap.dedent(
        """
        user "Hi, how are you today?"
          express greeting
        bot express greeting
          "Greetings! I am the official NVIDIA Benefits Ambassador AI bot and I'm here to assist you."
        user "What can you help me with?"
          ask capabilities
        bot inform capabilities
          "As an AI, I can provide you with a wide range of services, such as ..."
        """
    ).strip()

    output_1_turn = textwrap.dedent(
        """
        user "Hi, how are you today?"
          express greeting
        bot express greeting
          "Greetings! I am the official NVIDIA Benefits Ambassador AI bot and I'm here to assist you."
        """
    ).strip()

    assert first_turns(colang_history, 1) == output_1_turn
    assert first_turns(colang_history, 2) == colang_history
    assert first_turns(colang_history, 3) == colang_history


def test_last_turns():
    colang_history = textwrap.dedent(
        """
        user "Hi, how are you today?"
          express greeting
        bot express greeting
          "Greetings! I am the official NVIDIA Benefits Ambassador AI bot and I'm here to assist you."
        user "What can you help me with?"
          ask capabilities
        bot inform capabilities
          "As an AI, I can provide you with a wide range of services, such as ..."
        """
    ).strip()

    output_1_turn = textwrap.dedent(
        """
        user "What can you help me with?"
          ask capabilities
        bot inform capabilities
          "As an AI, I can provide you with a wide range of services, such as ..."
        """
    ).strip()

    assert last_turns(colang_history, 1) == output_1_turn
    assert last_turns(colang_history, 2) == colang_history
    assert last_turns(colang_history, 3) == colang_history

    colang_history = textwrap.dedent(
        """
        user "Hi, how are you today?"
          express greeting
        """
    ).strip()

    assert last_turns(colang_history, 1) == colang_history
    assert last_turns(colang_history, 2) == colang_history
