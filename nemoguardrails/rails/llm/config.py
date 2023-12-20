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

"""Module for the configuration of rails."""
import os
import random
from typing import Any, Dict, List, Optional, Union

import yaml
from pydantic import BaseModel, ValidationError, root_validator
from pydantic.fields import Field

from nemoguardrails.language.coyml_parser import parse_flow_elements
from nemoguardrails.language.parser import parse_colang_file


class Model(BaseModel):
    """Configuration of a model used by the rails engine.

    Typically, the main model is configured e.g.:
    {
        "type": "main",
        "engine": "openai",
        "model": "text-davinci-003"
    }
    """

    type: str
    engine: str
    model: Optional[str] = Field(
        default=None,
        description="The name of the model. If not specified, it should be specified through the parameters attribute.",
    )
    parameters: Dict[str, Any] = Field(default_factory=dict)


class Instruction(BaseModel):
    """Configuration for instructions in natural language that should be passed to the LLM."""

    type: str
    content: str


class Document(BaseModel):
    """Configuration for documents that should be used for question answering."""

    format: str
    content: str


class MessageTemplate(BaseModel):
    """Template for a message structure."""

    type: str = Field(
        description="The type of message, e.g., 'assistant', 'user', 'system'."
    )
    content: str = Field(description="The content of the message.")


class TaskPrompt(BaseModel):
    """Configuration for prompts that will be used for a specific task."""

    task: str = Field(description="The id of the task associated with this prompt.")
    content: Optional[str] = Field(
        default=None, description="The content of the prompt, if it's a string."
    )
    messages: Optional[List[Union[MessageTemplate, str]]] = Field(
        default=None,
        description="The list of messages included in the prompt. Used for chat models.",
    )
    models: Optional[List[str]] = Field(
        default=None,
        description="If specified, the prompt will be used only for the given LLM engines/models. "
        "The format is a list of strings with the format: <engine> or <engine>/<model>.",
    )
    output_parser: Optional[str] = Field(
        default=None,
        description="The name of the output parser to use for this prompt.",
    )

    @root_validator(pre=True, allow_reuse=True)
    def check_fields(cls, values):
        if not values.get("content") and not values.get("messages"):
            raise ValidationError("One of `content` or `messages` must be provided.")

        if values.get("content") and values.get("messages"):
            raise ValidationError(
                "Only one of `content` or `messages` must be provided."
            )

        return values


# Load the default config values from the file
with open(os.path.join(os.path.dirname(__file__), "default_config.yml")) as _fc:
    _default_config = yaml.safe_load(_fc)


def _join_config(dest_config: dict, additional_config: dict):
    """Helper to join two configuration."""

    dest_config["user_messages"] = {
        **dest_config.get("user_messages", {}),
        **additional_config.get("user_messages", {}),
    }

    dest_config["bot_messages"] = {
        **dest_config.get("bot_messages", {}),
        **additional_config.get("bot_messages", {}),
    }

    dest_config["instructions"] = dest_config.get(
        "instructions", []
    ) + additional_config.get("instructions", [])

    dest_config["flows"] = dest_config.get("flows", []) + additional_config.get(
        "flows", []
    )

    dest_config["models"] = dest_config.get("models", []) + additional_config.get(
        "models", []
    )

    dest_config["prompts"] = dest_config.get("prompts", []) + additional_config.get(
        "prompts", []
    )

    dest_config["docs"] = dest_config.get("docs", []) + additional_config.get(
        "docs", []
    )

    dest_config["actions_server_url"] = dest_config.get(
        "actions_server_url", None
    ) or additional_config.get("actions_server_url", None)

    additional_fields = [
        "sample_conversation",
        "lowest_temperature",
        "enable_multi_step_generation",
    ]

    for field in additional_fields:
        if additional_config.get(field):
            dest_config[field] = additional_config[field]


class RailsConfig(BaseModel):
    """Configuration object for the models and the rails.

    TODO: add typed config for user_messages, bot_messages, and flows.
    """

    models: List[Model] = Field(
        description="The list of models used by the rails configuration."
    )

    user_messages: Dict[str, List[str]] = Field(
        default_factory=dict,
        description="The list of user messages that should be used for the rails.",
    )

    bot_messages: Dict[str, List[str]] = Field(
        default_factory=dict,
        description="The list of bot messages that should be used for the rails.",
    )

    flows: List[Dict] = Field(
        default_factory=list,
        description="The list of flows that should be used for the rails.",
    )

    instructions: Optional[List[Instruction]] = Field(
        default=[Instruction.parse_obj(obj) for obj in _default_config["instructions"]],
        description="List of instructions in natural language that the LLM should use.",
    )

    docs: Optional[List[Document]] = Field(
        default=None,
        description="List of documents that should be used for question answering.",
    )

    actions_server_url: Optional[str] = Field(
        default=None,
        description="The URL of the actions server that should be used for the rails.",
    )

    sample_conversation: Optional[str] = Field(
        default=_default_config["sample_conversation"],
        description="The sample conversation that should be used inside the prompts.",
    )

    prompts: Optional[List[TaskPrompt]] = Field(
        default=None,
        description="The prompts that should be used for the various LLM tasks.",
    )

    config_path: Optional[str] = Field(
        default=None, description="The path from which the configuration was loaded."
    )

    # Some tasks need to be as deterministic as possible. The lowest possible temperature
    # will be used for those tasks. Models like dolly don't allow for a temperature of 0.0,
    # for example, in which case a custom one can be set.
    lowest_temperature: Optional[float] = Field(
        default=0.0,
        description="The lowest temperature that should be used for the LLM.",
    )

    # This should only be enabled for highly capable LLMs i.e. ~text-davinci-003.
    enable_multi_step_generation: Optional[bool] = Field(
        default=False,
        description="Whether to enable multi-step generation for the LLM.",
    )

    @staticmethod
    def from_path(
        config_path: str,
        test_set_percentage: Optional[float] = 0.0,
        test_set: Optional[Dict[str, List]] = {},
        max_samples_per_intent: Optional[int] = 0,
    ):
        """Loads a configuration from a given path.

        Supports loading a from a single file, or from a directory.

        Also used for testing Guardrails apps, in which case the test_set is
        randomly created from the intent samples in the config files.
        In this situation test_set_percentage should be larger than 0.

        If we want to limit the number of samples for an intent, set the
        max_samples_per_intent to a positive number. It is useful for testing apps, but
        also for limiting the number of samples for an intent in some scenarios.
        The chosen samples are selected randomly for each intent.
        """
        # If the config path is a file, we load the YAML content.
        # Otherwise, if it's a folder, we iterate through all files.
        if config_path.endswith(".yaml") or config_path.endswith(".yml"):
            with open(config_path) as f:
                raw_config = yaml.safe_load(f.read())

        elif os.path.isdir(config_path):
            # Iterate all .yml files and join them
            raw_config = {}

            for root, dirs, files in os.walk(config_path):
                for file in files:
                    # This is the raw configuration that will be loaded from the file.
                    _raw_config = {}

                    # Extract the full path for the file and compute relative path
                    full_path = os.path.join(root, file)
                    rel_path = os.path.relpath(full_path, config_path)

                    # If it's a file in the `kb` folder we need to append it to the docs
                    if rel_path.startswith("kb"):
                        _raw_config = {"docs": []}
                        if rel_path.endswith(".md"):
                            with open(full_path, encoding="utf-8") as f:
                                _raw_config["docs"].append(
                                    {"format": "md", "content": f.read()}
                                )

                    elif file.endswith(".yml") or file.endswith(".yaml"):
                        with open(full_path, "r", encoding="utf-8") as f:
                            _raw_config = yaml.safe_load(f.read())

                    elif file.endswith(".co"):
                        with open(full_path, "r", encoding="utf-8") as f:
                            _raw_config = parse_colang_file(file, content=f.read())

                    # Extract test set if needed before adding the _raw_config to the app config in raw_config
                    if "user_messages" in _raw_config and test_set_percentage > 0:
                        for intent, samples in _raw_config["user_messages"].items():
                            # We need at least 2 samples to create a test split
                            if len(samples) > 1:
                                random.shuffle(samples)
                                num_test_elements = int(
                                    len(samples) * test_set_percentage
                                )
                                test_set[intent] = samples[:num_test_elements]
                                _raw_config["user_messages"][intent] = samples[
                                    num_test_elements:
                                ]
                                # Limit the number of samples per intent if specified
                                if (
                                    0
                                    < max_samples_per_intent
                                    < len(_raw_config["user_messages"][intent])
                                ):
                                    _raw_config["user_messages"][intent] = _raw_config[
                                        "user_messages"
                                    ][intent][:max_samples_per_intent]

                    _join_config(raw_config, _raw_config)
        else:
            raise ValueError(f"Invalid config path {config_path}.")

        # If there are no instructions, we use the default ones.
        if len(raw_config.get("instructions", [])) == 0:
            raw_config["instructions"] = _default_config["instructions"]

        raw_config["config_path"] = config_path

        return RailsConfig.parse_object(raw_config)

    @staticmethod
    def from_content(
        colang_content: Optional[str] = None, yaml_content: Optional[str] = None
    ):
        """Loads a configuration from the provided colang/YAML content."""
        raw_config = {}

        if colang_content:
            _join_config(
                raw_config, parse_colang_file("main.co", content=colang_content)
            )

        if yaml_content:
            _join_config(raw_config, yaml.safe_load(yaml_content))

        # If there are no instructions, we use the default ones.
        if len(raw_config.get("instructions", [])) == 0:
            raw_config["instructions"] = _default_config["instructions"]

        return RailsConfig.parse_object(raw_config)

    @classmethod
    def parse_object(cls, obj):
        """Parses a configuration object from a given dictionary."""
        # If we have flows, we need to process them further from CoYML to CIL.
        for flow_data in obj.get("flows", []):
            # If the first element in the flow does not have a "_type", we need to convert
            if flow_data.get("elements") and not flow_data["elements"][0].get("_type"):
                flow_data["elements"] = parse_flow_elements(flow_data["elements"])

        return RailsConfig.parse_obj(obj)
