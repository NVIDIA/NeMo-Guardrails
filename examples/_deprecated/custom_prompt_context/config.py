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

from datetime import datetime

from nemoguardrails import LLMRails


def get_current_date_str():
    """Helper function returning a string of the form: "{month} {day}, {year}. It's a {weekday}." """
    return datetime.now().strftime("%B %d, %Y. It's a %A.")


def init(llm_rails: LLMRails):
    # We register the additional prompt context for the current date.
    llm_rails.register_prompt_context("current_date", get_current_date_str)
