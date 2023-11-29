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

""" Generation options give more control over the generation and the result.

For example, to run only the input rails::

    # Since everything is enabled by default, we disable explicitly the others
    options = {
        "rails": {
            "output": False,
            "dialog": False,
            "retrieval": False
        }
    }
    messages = [{
        "role": "user",
        "content": "Am I allowed to say this?"
    }]

    rails.generate(messages=messages, options=options)

To invoke only some specific input/output rails:

    rails.generate(messages=messages, options={
        "rails": {
            "input": ["check jailbreak"],
            "output": ["output moderation v2"]
        }
    })

To provide additional parameters to the main LLM call:

    rails.generate(messages=messages, options={
        "llm_params": {
            "temperature": 0.5
        }
    })

To return additional information from the generation (i.e., context variables):

    # This will include the relevant chunks in the returned response, as part
    # of the `output_data` field.
    rails.generate(messages=messages, options={
        "output_vars": ["relevant_chunks"]
    })

To skip enforcing the rails, and only inform the user if they were triggered:

    rails.generate(messages=messages, options={
        "enforce": False
    })

    # {..., log: {"triggered_rails": {"type": "input", "name": "check jailbreak"}}}

To get more details on the LLM calls that were executed, including the raw responses:

    rails.generate(messages=messages, options={
        "log": {
            "llm_calls": True
        }
    })

    # {..., log: {"llm_calls": [...]}}

"""
from typing import List, Optional, Union

from pydantic import BaseModel, Field

from nemoguardrails.logging.explain import LLMCallInfo


class GenerationLogOptions(BaseModel):
    """Options for what should be included in the generation log."""

    triggered_rails: bool = Field(
        default=False,
        description="Include the name of the rails that were triggered during generation.",
    )
    llm_calls: bool = Field(
        default=False,
        description="Include information about all the LLM calls that were made. "
        "This includes: prompt, completion, token usage, raw response, etc.",
    )
    internal_events: bool = Field(
        default=False,
        description="Include the array of internal generated events.",
    )
    colang_history: bool = Field(
        default=False,
        description="Include the history of the conversation in Colang format.",
    )


class GenerationRailsOptions(BaseModel):
    """Options for what rails should be used during the generation."""

    input: Union[bool, List[str]] = Field(
        default=True,
        description="Whether the input rails are enabled or not. "
        "If a list of names is specified, then only the specified input rails will be applied.",
    )
    output: Union[bool, List[str]] = Field(
        default=True,
        description="Whether the output rails are enabled or not. "
        "If a list of names is specified, then only the specified output rails will be applied.",
    )
    retrieval: Union[bool, List[str]] = Field(
        default=True,
        description="Whether the retrieval rails are enabled or not. "
        "If a list of names is specified, then only the specified retrieval rails will be applied.",
    )
    dialog: bool = Field(
        default=True,
        description="Whether the dialog rails are enabled or not.",
    )


class GenerationOptions(BaseModel):
    """A set of options that should be applied during a generation.

    The GenerationOptions control various things such as what rails are enabled,
    additional parameters for the main LLM, whether the rails should be enforced or
    ran in parallel, what to be included in the generation log, etc.
    """

    rails: GenerationRailsOptions = Field(
        default_factory=GenerationRailsOptions,
        description="Options for which rails should be applied for the generation. "
        "By default, all rails are enabled.",
    )
    llm_params: Optional[dict] = Field(
        default=None,
        description="Additional parameters that should be used for the LLM call",
    )
    output_vars: Optional[Union[bool, List[str]]] = Field(
        default=None,
        description="Whether additional context information should be returned. "
        "When True is specified, the whole context is returned. "
        "Otherwise, a list of key names can be specified.",
    )
    enforce: Optional[bool] = Field(
        default=True,
        description="Whether the rails configuration should be enforced. "
        "When set to False, the raw LLM call is made in parallel with running the input rails "
        "on the user input. Also, the output rails are applied to the output of the raw",
    )
    log: GenerationLogOptions = Field(
        default_factory=GenerationLogOptions,
        description="Options about what to include in the log. By default, nothing is included. ",
    )


class GenerationLog(BaseModel):
    """Contains additional logging information associated with a generation call."""

    triggered_rails: Optional[List[dict]] = Field(
        default=None,
        description="The list of rails that were triggered.",
    )
    llm_calls: Optional[List[LLMCallInfo]] = Field(
        default=None,
        description="The list of LLM calls that have been made to fulfill the generation request. "
        "Includes information about the prompt, completion, duration and token usage.",
    )
    internal_events: Optional[List[dict]] = Field(
        default=None, description="The complete sequence of internal events generated."
    )
    colang_history: Optional[str] = Field(
        default=None, description="The Colang history associated with the generation."
    )


class GenerationResponse(BaseModel):
    messages: List[dict] = Field(description="The list of the generated messages.")
    output_data: Optional[dict] = Field(
        default=None,
        description="The output data, i.e. a dict with the values corresponding to the `output_vars`.",
    )
    log: Optional[GenerationLog] = Field(
        default=None, description="Additional logging information."
    )


if __name__ == "__main__":
    print(GenerationOptions(**{"rails": {"input": False}}))
