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
import logging
import os
from typing import Any, Dict, List, Optional, Set, Tuple, Union

import yaml
from pydantic import BaseModel, ValidationError, root_validator
from pydantic.fields import Field

from nemoguardrails.colang import parse_colang_file, parse_flow_elements
from nemoguardrails.colang.v2_x.lang.colang_ast import Flow

log = logging.getLogger(__name__)

# Load the default config values from the file
with open(os.path.join(os.path.dirname(__file__), "default_config.yml")) as _fc:
    _default_config = yaml.safe_load(_fc)


class Model(BaseModel):
    """Configuration of a model used by the rails engine.

    Typically, the main model is configured e.g.:
    {
        "type": "main",
        "engine": "openai",
        "model": "gpt-3.5-turbo-instruct"
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


class SensitiveDataDetectionOptions(BaseModel):
    entities: List[str] = Field(
        default_factory=list,
        description="The list of entities that should be detected. "
        "Check out https://microsoft.github.io/presidio/supported_entities/ for"
        "the list of supported entities.",
    )
    # TODO: this is not currently in use.
    mask_token: str = Field(
        default="*",
        description="The token that should be used to mask the sensitive data.",
    )


class SensitiveDataDetection(BaseModel):
    """Configuration of what sensitive data should be detected."""

    recognizers: List[dict] = Field(
        default_factory=list,
        description="Additional custom recognizers. "
        "Check out https://microsoft.github.io/presidio/tutorial/08_no_code/ for more details.",
    )
    input: SensitiveDataDetectionOptions = Field(
        default_factory=SensitiveDataDetectionOptions,
        description="Configuration of the entities to be detected on the user input.",
    )
    output: SensitiveDataDetectionOptions = Field(
        default_factory=SensitiveDataDetectionOptions,
        description="Configuration of the entities to be detected on the bot output.",
    )
    retrieval: SensitiveDataDetectionOptions = Field(
        default_factory=SensitiveDataDetectionOptions,
        description="Configuration of the entities to be detected on retrieved relevant chunks.",
    )


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
    max_length: Optional[int] = Field(
        default=16000,
        description="The maximum length of the prompt in number of characters.",
    )
    mode: Optional[str] = Field(
        default=_default_config["prompting_mode"],
        description="Corresponds to the `prompting_mode` for which this prompt is fetched. Default is 'standard'.",
    )
    stop: Optional[List[str]] = Field(
        default=None,
        description="If specified, will be configure stop tokens for models that support this.",
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


class EmbeddingsCacheConfig(BaseModel):
    """Configuration for the caching embeddings."""

    enabled: bool = Field(
        default=False,
        description="Whether caching of the embeddings should be enabled or not.",
    )
    key_generator: str = Field(
        default="md5",
        description="The method to use for generating the cache keys.",
    )
    store: str = Field(
        default="filesystem",
        description="What type of store to use for the cached embeddings.",
    )
    store_config: Dict[str, Any] = Field(
        default_factory=dict,
        description="Any additional configuration options required for the store. "
        "For example, path for `filesystem` or `host`/`port`/`db` for redis.",
    )

    def to_dict(self):
        return self.dict()


class EmbeddingSearchProvider(BaseModel):
    """Configuration of a embedding search provider."""

    name: str = Field(
        default="default",
        description="The name of the embedding search provider. If not specified, default is used.",
    )
    parameters: Dict[str, Any] = Field(default_factory=dict)
    cache: EmbeddingsCacheConfig = Field(default_factory=EmbeddingsCacheConfig)


class KnowledgeBaseConfig(BaseModel):
    folder: str = Field(
        default="kb",
        description="The folder from which the documents should be loaded.",
    )
    embedding_search_provider: EmbeddingSearchProvider = Field(
        default_factory=EmbeddingSearchProvider,
        description="The search provider used to search the knowledge base.",
    )


class CoreConfig(BaseModel):
    """Settings for core internal mechanics."""

    embedding_search_provider: EmbeddingSearchProvider = Field(
        default_factory=EmbeddingSearchProvider,
        description="The search provider used to search the most similar canonical forms/flows.",
    )


class InputRails(BaseModel):
    """Configuration of input rails."""

    flows: List[str] = Field(
        default_factory=list,
        description="The names of all the flows that implement input rails.",
    )


class OutputRails(BaseModel):
    """Configuration of output rails."""

    flows: List[str] = Field(
        default_factory=list,
        description="The names of all the flows that implement output rails.",
    )


class RetrievalRails(BaseModel):
    """Configuration of retrieval rails."""

    flows: List[str] = Field(
        default_factory=list,
        description="The names of all the flows that implement retrieval rails.",
    )


class SingleCallConfig(BaseModel):
    """Configuration for the single LLM call option for topical rails."""

    enabled: bool = False
    fallback_to_multiple_calls: bool = Field(
        default=True,
        description="Whether to fall back to multiple calls if a single call is not possible.",
    )


class UserMessagesConfig(BaseModel):
    """Configuration for how the user messages are interpreted."""

    embeddings_only: bool = Field(
        default=False,
        description="Whether to use only embeddings for computing the user canonical form messages.",
    )


class DialogRails(BaseModel):
    """Configuration of topical rails."""

    single_call: SingleCallConfig = Field(
        default_factory=SingleCallConfig,
        description="Configuration for the single LLM call option.",
    )
    user_messages: UserMessagesConfig = Field(
        default_factory=UserMessagesConfig,
        description="Configuration for how the user messages are interpreted.",
    )


class FactCheckingRailConfig(BaseModel):
    """Configuration data for the fact-checking rail."""

    parameters: Dict[str, Any] = Field(default_factory=dict)
    fallback_to_self_check: bool = Field(
        default=False,
        description="Whether to fall back to self-check if another method fail.",
    )


class JailbreakDetectionConfig(BaseModel):
    """Configuration data for jailbreak detection."""

    server_endpoint: Optional[str] = Field(
        default=None,
        description="The endpoint for the jailbreak detection heuristics server.",
    )
    length_per_perplexity_threshold: float = Field(
        default=89.79, description="The length/perplexity threshold."
    )
    prefix_suffix_perplexity_threshold: float = Field(
        default=1845.65, description="The prefix/suffix perplexity threshold."
    )


class RailsConfigData(BaseModel):
    """Configuration data for specific rails that are supported out-of-the-box."""

    fact_checking: FactCheckingRailConfig = Field(
        default_factory=FactCheckingRailConfig,
        description="Configuration data for the fact-checking rail.",
    )

    sensitive_data_detection: Optional[SensitiveDataDetection] = Field(
        default_factory=SensitiveDataDetection,
        description="Configuration for detecting sensitive data.",
    )

    jailbreak_detection: Optional[JailbreakDetectionConfig] = Field(
        default_factory=JailbreakDetectionConfig,
        description="Configuration for jailbreak detection.",
    )


class Rails(BaseModel):
    """Configuration of specific rails."""

    config: RailsConfigData = Field(
        default_factory=RailsConfigData,
        description="Configuration data for specific rails that are supported out-of-the-box.",
    )
    input: InputRails = Field(
        default_factory=InputRails, description="Configuration of the input rails."
    )
    output: OutputRails = Field(
        default_factory=OutputRails, description="Configuration of the output rails."
    )
    retrieval: RetrievalRails = Field(
        default_factory=RetrievalRails,
        description="Configuration of the retrieval rails.",
    )
    dialog: DialogRails = Field(
        default_factory=DialogRails, description="Configuration of the dialog rails."
    )


def merge_two_dicts(dict_1: dict, dict_2: dict, ignore_keys: Set[str]) -> None:
    """Merges the fields of two dictionaries recursively."""
    for key, value in dict_2.items():
        if key not in ignore_keys:
            if key in dict_1:
                if isinstance(dict_1[key], dict) and isinstance(value, dict):
                    merge_two_dicts(dict_1[key], value, set())
                elif dict_1[key] != value:
                    log.warning(
                        "Conflicting fields with same name '%s' in yaml config files detected!",
                        key,
                    )
            else:
                dict_1[key] = value


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

    dest_config["sensitive_data_detection"] = {
        **dest_config.get("sensitive_data_detection", {}),
        **additional_config.get("sensitive_data_detection", {}),
    }

    dest_config["embedding_search_provider"] = dest_config.get(
        "embedding_search_provider", {}
    ) or additional_config.get("embedding_search_provider", {})

    # We join the arrays and keep only unique elements for import paths.
    dest_config["import_paths"] = dest_config.get("import_paths", [])
    for import_path in additional_config.get("import_paths", []):
        if import_path not in dest_config["import_paths"]:
            dest_config["import_paths"].append(import_path)

    additional_fields = [
        "sample_conversation",
        "lowest_temperature",
        "enable_multi_step_generation",
        "colang_version",
        "custom_data",
        "prompting_mode",
        "knowledge_base",
        "core",
        "rails",
        "streaming",
        "passthrough",
        "raw_llm_call_action",
    ]

    for field in additional_fields:
        if additional_config.get(field):
            dest_config[field] = additional_config[field]

    # TODO: Rethink the best way to parse and load yaml config files
    ignore_fields = set(additional_fields).union(
        {
            "user_messages",
            "bot_messages",
            "instructions",
            "flows",
            "models",
            "prompts",
            "docs",
            "actions_server_url",
            "sensitive_data_detection",
            "embedding_search_provider",
        }
    )

    # Reads all the other fields and merges them with the custom_data field
    merge_two_dicts(
        dest_config.get("custom_data", {}), additional_config, ignore_fields
    )


def _load_path(
    config_path: str,
) -> Tuple[dict, List[Tuple[str, str]]]:
    """Load a configuration object from the specified path.

    Args:
        config_path: The path from which to load.

    Returns:
        (raw_config, colang_files) The raw config object and the list of colang files.
    """
    raw_config = {}

    # The names of the colang files.
    colang_files = []

    if not os.path.exists(config_path):
        raise ValueError(f"Could not find config path: {config_path}")

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
                colang_files.append((file, full_path))

            _join_config(raw_config, _raw_config)

    return raw_config, colang_files


def _load_imported_paths(raw_config: dict, colang_files: List[Tuple[str, str]]):
    """Load recursively all the imported path in the specified raw_config.

    Args:
        raw_config: The starting raw configuration (i.e., a dict)
        colang_files: The current set of colang files which will be extended as new
            configurations are loaded.
    """
    imported_paths = []
    while len(imported_paths) != len(raw_config["import_paths"]):
        for import_path in raw_config["import_paths"]:
            if import_path in imported_paths:
                continue

            log.info(f"Loading imported path: {import_path}")

            _raw_config, _colang_files = _load_path(import_path)

            # Join them.
            _join_config(raw_config, _raw_config)
            colang_files.extend(_colang_files)

            # And mark the path as imported.
            imported_paths.append(import_path)


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

    flows: List[Union[Dict, Flow]] = Field(
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
    )  # consider as conflict

    sample_conversation: Optional[str] = Field(
        default=_default_config["sample_conversation"],
        description="The sample conversation that should be used inside the prompts.",
    )

    prompts: Optional[List[TaskPrompt]] = Field(
        default=None,
        description="The prompts that should be used for the various LLM tasks.",
    )

    prompting_mode: Optional[str] = Field(
        default=_default_config["prompting_mode"],
        description="Allows choosing between different prompting strategies.",
    )

    config_path: Optional[str] = Field(
        default=None, description="The path from which the configuration was loaded."
    )

    import_paths: Optional[List[str]] = Field(
        default_factory=list,
        description="A list of additional paths from which configuration elements (colang flows, .yml files, actions)"
        " should be loaded.",
    )

    # Some tasks need to be as deterministic as possible. The lowest possible temperature
    # will be used for those tasks. Models like dolly don't allow for a temperature of 0.0,
    # for example, in which case a custom one can be set.
    lowest_temperature: Optional[float] = Field(
        default=0.0,
        description="The lowest temperature that should be used for the LLM.",
    )

    # This should only be enabled for highly capable LLMs i.e. gpt-3.5-turbo-instruct or similar.
    enable_multi_step_generation: Optional[bool] = Field(
        default=False,
        description="Whether to enable multi-step generation for the LLM.",
    )

    colang_version: str = Field(default="1.0", description="The Colang version to use.")

    custom_data: Dict = Field(
        default_factory=dict,
        description="Any custom configuration data that might be needed.",
    )

    knowledge_base: KnowledgeBaseConfig = Field(
        default_factory=KnowledgeBaseConfig,
        description="Configuration for the built-in knowledge base support.",
    )

    core: CoreConfig = Field(
        default_factory=CoreConfig,
        description="Configuration for core internal mechanics.",
    )

    rails: Rails = Field(
        default_factory=Rails,
        description="Configuration for the various rails (input, output, etc.).",
    )

    streaming: bool = Field(
        default=False,
        description="Whether this configuration should use streaming mode or not.",
    )

    passthrough: bool = Field(
        default=False,
        description="Weather the original prompt should pass through the guardrails configuration as is. "
        "This means it will not be altered in any way. ",
    )

    @root_validator(pre=True, allow_reuse=True)
    def check_prompt_exist_for_self_check_rails(cls, values):
        rails = values.get("rails", {})

        enabled_input_rails = rails.get("input", {}).get("flows", [])
        enabled_output_rails = rails.get("output", {}).get("flows", [])
        provided_task_prompts = [
            prompt.get("task") for prompt in values.get("prompts", [])
        ]

        # Input moderation prompt verification
        if (
            "self check input" in enabled_input_rails
            and "self_check_input" not in provided_task_prompts
        ):
            raise ValueError("You must provide a `self_check_input` prompt template.")
        if (
            "llama guard check input" in enabled_input_rails
            and "llama_guard_check_input" not in provided_task_prompts
        ):
            raise ValueError(
                "You must provide a `llama_guard_check_input` prompt template."
            )

        # Output moderation prompt verification
        if (
            "self check output" in enabled_output_rails
            and "self_check_output" not in provided_task_prompts
        ):
            raise ValueError("You must provide a `self_check_output` prompt template.")
        if (
            "llama guard check output" in enabled_output_rails
            and "llama_guard_check_output" not in provided_task_prompts
        ):
            raise ValueError(
                "You must provide a `llama_guard_check_output` prompt template."
            )

        if (
            "self check facts" in enabled_output_rails
            and "self_check_facts" not in provided_task_prompts
        ):
            raise ValueError("You must provide a `self_check_facts` prompt template.")

        return values

    raw_llm_call_action: Optional[str] = Field(
        default="raw llm call",
        description="The name of the action that would execute the original raw LLM call. ",
    )

    @staticmethod
    def from_path(
        config_path: str,
    ):
        """Loads a configuration from a given path.

        Supports loading a from a single file, or from a directory.
        """
        # If the config path is a file, we load the YAML content.
        # Otherwise, if it's a folder, we iterate through all files.
        if config_path.endswith(".yaml") or config_path.endswith(".yml"):
            with open(config_path) as f:
                raw_config = yaml.safe_load(f.read())

        elif os.path.isdir(config_path):
            raw_config, colang_files = _load_path(config_path)

            # If we have import paths, we also need to load them.
            if raw_config.get("import_paths"):
                _load_imported_paths(raw_config, colang_files)

            # Parse the colang files after we know the colang version
            colang_version = raw_config.get("colang_version", "1.0")

            # To allow overriding of elements from imported paths, we need to process
            # these in reverse order.
            for file, full_path in reversed(colang_files):
                with open(full_path, "r", encoding="utf-8") as f:
                    _raw_config = parse_colang_file(
                        file, content=f.read(), version=colang_version
                    )
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
        colang_content: Optional[str] = None,
        yaml_content: Optional[str] = None,
        config: Optional[dict] = None,
    ):
        """Loads a configuration from the provided colang/YAML content/config dict."""
        raw_config = {}

        if config:
            _join_config(raw_config, config)

        if yaml_content:
            _join_config(raw_config, yaml.safe_load(yaml_content))

        # If we have import paths, we also need to load them.
        colang_files = []
        if raw_config.get("import_paths"):
            _load_imported_paths(raw_config, colang_files)

        # Parse the colang files after we know the colang version
        colang_version = raw_config.get("colang_version", "1.0")

        # To allow overriding of elements from imported paths, we need to process
        # these in reverse order.
        for file, full_path in reversed(colang_files):
            with open(full_path, "r", encoding="utf-8") as f:
                _raw_config = parse_colang_file(
                    file, content=f.read(), version=colang_version
                )
                _join_config(raw_config, _raw_config)

        # Finally, parse the content colang.
        if colang_content:
            _join_config(
                raw_config,
                parse_colang_file(
                    "main.co",
                    content=colang_content,
                    version=colang_version,
                ),
            )

        # If there are no instructions, we use the default ones.
        if len(raw_config.get("instructions", [])) == 0:
            raw_config["instructions"] = _default_config["instructions"]

        return RailsConfig.parse_object(raw_config)

    @classmethod
    def parse_object(cls, obj):
        """Parses a configuration object from a given dictionary."""
        # If we have flows, we need to process them further from CoYML to CIL, but only for
        # version 1.0.

        if obj.get("colang_version", "1.0") == "1.0":
            for flow_data in obj.get("flows", []):
                # If the first element in the flow does not have a "_type", we need to convert
                if flow_data.get("elements") and not flow_data["elements"][0].get(
                    "_type"
                ):
                    flow_data["elements"] = parse_flow_elements(flow_data["elements"])

        return RailsConfig.parse_obj(obj)

    @property
    def streaming_supported(self):
        """Whether the current config supports streaming or not.

        Currently, we don't support streaming if there are output rails.
        """
        if len(self.rails.output.flows) > 0:
            return False

        return True

    def __add__(self, other):
        """Adds two RailsConfig objects."""
        return _join_rails_configs(self, other)


def _join_dict(dict1, dict2):
    """
    Joins two dictionaries recursively.
    - If values are dictionaries, it applies _join_dict recursively.
    - If values are lists, it concatenates them, ensuring unique elements.
    - For other types, values from dict2 overwrite dict1.
    """
    result = dict(dict1)  # Create a copy of dict1 to avoid modifying the original

    for key, value in dict2.items():
        # If key is in both dictionaries and both values are dictionaries, apply _join_dict recursively
        if key in dict1 and isinstance(dict1[key], dict) and isinstance(value, dict):
            result[key] = _join_dict(dict1[key], value)
        # If key is in both dictionaries and both values are lists, concatenate unique elements
        elif key in dict1 and isinstance(dict1[key], list) and isinstance(value, list):
            # Since we want values from dict2 to take precedence, we concatenate dict2 first
            result[key] = _unique_list_concat(value, dict1[key])
        # Otherwise, simply overwrite the value from dict2
        else:
            result[key] = value

    return result


def _unique_list_concat(list1, list2):
    """
    Concatenates two lists ensuring all elements are unique.
    Handles unhashable types like dictionaries.
    """
    result = list(list1)
    for item in list2:
        if item not in result:
            result.append(item)
    return result


def _join_rails_configs(
    base_rails_config: RailsConfig, updated_rails_config: RailsConfig
):
    """Helper to join two rails configuration."""

    config_old_types = {}
    for model_old in base_rails_config.models:
        config_old_types[model_old.type] = model_old

    for model_new in updated_rails_config.models:
        if model_new.type in config_old_types:
            if model_new.engine != config_old_types[model_new.type].engine:
                raise ValueError(
                    "Both config files should have the same engine for the same model type"
                )
            if model_new.model != config_old_types[model_new.type].model:
                raise ValueError(
                    "Both config files should have the same model for the same model type"
                )

    if base_rails_config.actions_server_url != updated_rails_config.actions_server_url:
        raise ValueError("Both config files should have the same actions_server_url")

    combined_rails_config_dict = _join_dict(
        base_rails_config.dict(), updated_rails_config.dict()
    )
    combined_rails_config_dict["config_path"] = ",".join(
        [
            base_rails_config.dict()["config_path"],
            updated_rails_config.dict()["config_path"],
        ]
    )
    combined_rails_config = RailsConfig(**combined_rails_config_dict)
    return combined_rails_config
