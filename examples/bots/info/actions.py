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

import os
from typing import Any, List, Optional

from nemoguardrails.actions import action


@action()
async def block_list(file_name: Optional[str] = None, context: Optional[dict] = None):
    bot_response = context.get("last_bot_message")
    root_path = os.path.dirname(__file__)

    with open(os.path.join(root_path, file_name)) as f:
        lines = [line.rstrip() for line in f]

    for line in lines:
        if line in bot_response:
            return True
    return False
