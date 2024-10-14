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

import importlib
from typing import Dict, List

from nemoguardrails.rails.llm.config import LogAdapterConfig
from nemoguardrails.tracing.adapters.base import InteractionLogAdapter


def adapter_factory(
    adapter_configs: List[Dict] | List[LogAdapterConfig],
) -> List[InteractionLogAdapter]:
    adapters = []
    for config in adapter_configs:
        if not isinstance(config, LogAdapterConfig):
            config = LogAdapterConfig(**config)
        adapter_name = config.name
        module_name = f"nemoguardrails.tracing.adapters.{adapter_name.lower()}"  # Ensure full module path
        class_name = adapter_name + "Adapter"
        module = importlib.import_module(module_name)
        adapter_class = getattr(module, class_name)
        # pop the name from the config, as the adapter class does not need it
        del config.name
        adapter_instance = adapter_class(**config.model_dump())
        adapters.append(adapter_instance)
    return adapters