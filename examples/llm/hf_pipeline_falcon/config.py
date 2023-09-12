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
from torch import float16
from torch.cuda import device_count
from transformers import AutoModelForCausalLM, AutoTokenizer, pipeline

from nemoguardrails.llm.helpers import get_llm_instance_wrapper
from nemoguardrails.llm.providers import register_llm_provider


@lru_cache
def get_falcon_40b_instruct_llm():
    repo_id = "tiiuae/falcon-40b-instruct"
    params = {
        "temperature": 0.01,
        "max_length": 1024,
        "do_sample": True,
        "trust_remote_code": True,
    }

    # Use the first CUDA-enabled GPU, if any
    device = 0 if device_count() else -1

    llm = HuggingFacePipeline.from_model_id(
        model_id=repo_id, device=device, task="text-generation", model_kwargs=params
    )

    return llm


def get_falcon_40b_llm():
    repo_id = "tiiuae/falcon-40b"
    params = {"temperature": 0, "max_length": 1024}

    # Use the first CUDA-enabled GPU, if any
    device = 0 if device_count() else -1

    llm = HuggingFacePipeline.from_model_id(
        model_id=repo_id, device=device, task="text-generation", model_kwargs=params
    )

    return llm


def get_falcon_7b_llm():
    repo_id = "tiiuae/falcon-7b"
    params = {"temperature": 0, "max_length": 200}

    # Use the first CUDA-enabled GPU, if any
    device = 0 if device_count() else -1

    llm = HuggingFacePipeline.from_model_id(
        model_id=repo_id, device=device, task="text-generation", model_kwargs=params
    )

    return llm


def get_falcon_7b_instruct_llm():
    repo_id = "tiiuae/falcon-7b-instruct"
    params = {
        "temperature": 0,
        "max_length": 200,
        "do_sample": True,
        "trust_remote_code": True,
    }

    # Use the first CUDA-enabled GPU, if any
    device = 0 if device_count() else -1

    llm = HuggingFacePipeline.from_model_id(
        model_id=repo_id, device=device, task="text-generation", model_kwargs=params
    )

    return llm


def _load_model(model_name, device, num_gpus, debug=False):
    """Helper function to load the model."""
    if device == "cpu":
        kwargs = {}
    elif device == "cuda":
        kwargs = {"torch_dtype": float16}
        if num_gpus == "auto":
            kwargs["device_map"] = "auto"
        else:
            num_gpus = int(num_gpus)
            if num_gpus != 1:
                kwargs.update(
                    {
                        "device_map": "auto",
                        "max_memory": {i: "13GiB" for i in range(num_gpus)},
                    }
                )
    elif device == "mps":
        kwargs = {"torch_dtype": float16}
        # Avoid bugs in mps backend by not using in-place operations.
        print("mps not supported")
    else:
        raise ValueError(f"Invalid device: {device}")

    tokenizer = AutoTokenizer.from_pretrained(model_name, use_fast=False)
    model = AutoModelForCausalLM.from_pretrained(
        model_name, low_cpu_mem_usage=True, **kwargs
    )

    if device == "cuda" and num_gpus == 1:
        model.to(device)

    if debug:
        print(model)

    return model, tokenizer


def get_falcon_llm_from_path(model_path: str = "/workspace/ckpt/"):
    """Loads the Falcon LLM from a local path."""
    device = "cuda"
    num_gpus = 2  # making sure GPU-GPU are NVlinked, GPUs-GPUS with NVSwitch
    model, tokenizer = _load_model(model_path, device, num_gpus, debug=False)

    pipe = pipeline(
        "text-generation",
        model=model,
        tokenizer=tokenizer,
        max_new_tokens=100,
        temperature=0,
        do_sample=True,
    )

    llm = HuggingFacePipeline(pipeline=pipe)
    return llm


HFPipelineFalcon = get_llm_instance_wrapper(
    llm_instance=get_falcon_7b_instruct_llm(),
    llm_type="hf_pipeline_falcon",  # change the Falcon LLM instance depending on your needs
)

register_llm_provider("hf_pipeline_falcon", HFPipelineFalcon)
