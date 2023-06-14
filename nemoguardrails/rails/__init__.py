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

from nvlangchain.apis import service
from nvlangchain.llm import NeMo

from .llm.config import RailsConfig
from .llm.llmrails import LLMRails


# Monkey patching to enable async call, even though in a blocking way.
async def _acall(self, prompt, stop):
    return self._call(prompt, stop)


NeMo._acall = _acall

# Quick hackish way to connect to staging
# TODO: Is there a better way?
service.API_HOST = "https://api.stg.llm.ngc.nvidia.com/v1"
