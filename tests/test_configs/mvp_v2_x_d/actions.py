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

from nemoguardrails.actions import action


@action(name="GenerateFlowAction")
async def generate_flow(instructions: str, flow_name: str):
    flow_source = f"""
        flow {flow_name}
          bot say "Why don't scientists trust atoms? Because they make up everything!"
          bot say "I'm smiling."
        """
    return flow_source


# @action(name="GenerateUserIntentAction")
# async def generate_user_intent_action(user_message: str):
#     if "hello" in user_message:
#         return "user express greeting"
#     elif "i want" in user_message:
#         return "user provide custom instructions"
#     else:
#         return "unknown"
