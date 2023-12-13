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

from enum import Enum


class Task(Enum):
    """The various tasks that can be performed by the LLM."""

    # Core LLM tasks
    GENERAL = "general"
    GENERATE_USER_INTENT = "generate_user_intent"
    GENERATE_NEXT_STEPS = "generate_next_steps"
    GENERATE_BOT_MESSAGE = "generate_bot_message"
    GENERATE_INTENT_STEPS_MESSAGE = "generate_intent_steps_message"
    GENERATE_VALUE = "generate_value"

    # Tasks for various rails
    SELF_CHECK_INPUT = "self_check_input"
    SELF_CHECK_OUTPUT = "self_check_output"
    SELF_CHECK_FACTS = "fact_checking"
    CHECK_HALLUCINATION = "check_hallucination"
