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
from functools import lru_cache

from langchain import HuggingFacePipeline
from torch.cuda import device_count

from nemoguardrails.llm.helpers import get_llm_instance_wrapper
from nemoguardrails.llm.providers import register_llm_provider


@lru_cache
def get_dolly_v2_3b_llm():
    repo_id = "databricks/dolly-v2-3b"
    params = {"temperature": 0, "max_length": 1024}

    # Use the first CUDA-enabled GPU, if any
    device = 0 if device_count() else -1

    llm = HuggingFacePipeline.from_model_id(
        model_id=repo_id, device=device, task="text-generation", model_kwargs=params
    )

    return llm


HFPipelineDolly = get_llm_instance_wrapper(
    llm_instance=get_dolly_v2_3b_llm(), llm_type="hf_pipeline_dolly"
)

register_llm_provider("hf_pipeline_dolly", HFPipelineDolly)
