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

import json

from nemoguardrails.llm.providers import get_llm_provider, get_llm_provider_names
from nemoguardrails.rails.llm.config import Model


def initialize_llm(model_config: Model):
    """Initializes the model from LLM provider."""
    if model_config.engine not in get_llm_provider_names():
        raise Exception(f"Unknown LLM engine: {model_config.engine}")
    provider_cls = get_llm_provider(model_config)
    kwargs = {"temperature": 0, "max_tokens": 10}
    if model_config.engine in [
        "azure",
        "openai",
        "gooseai",
        "nlpcloud",
        "petals",
    ]:
        kwargs["model_name"] = model_config.model
    else:
        kwargs["model"] = model_config.model
    return provider_cls(**kwargs)


def load_dataset(dataset_path: str):
    """Loads a dataset from a file."""

    with open(dataset_path, "r") as f:
        if dataset_path.endswith(".json"):
            dataset = json.load(f)
        else:
            dataset = f.readlines()

    return dataset
