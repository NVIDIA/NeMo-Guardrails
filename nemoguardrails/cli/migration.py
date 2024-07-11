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

import logging
import os
import re
from pathlib import Path

import yaml

from nemoguardrails import utils
from nemoguardrails.colang import parse_colang_file


def convert_co_file_syntax(file_path):
    """Converts a co file from v1 format to v2.

    Args:
        file_path (str): The path to the file to convert.
    Returns:
        bool: True if the file was successfully converted, False otherwise.
    """

    logging.info(f"Converting file: {file_path}")

    new_lines = []
    prev_line = None
    stats = {"lines": 0, "changes": 0}

    try:
        with open(file_path, "r") as file:
            lines = file.readlines()
    except Exception as e:
        logging.error(f"Failed to read file: {file_path}. Error: {str(e)}")
        return new_lines

    for i, line in enumerate(lines):
        stats["lines"] += 1
        # stripped_line = line.strip()
        stripped_line = line
        original_line = line
        stripped_line = _globalize_variable_assignment(stripped_line)

        # Get the next line if it exists
        next_line = lines[i + 1] if i + 1 < len(lines) else None

        # Reset prev_line if a new block is reached
        if stripped_line.lstrip().startswith("define "):
            prev_line = None
        # We convert "define flow" to "flow"
        stripped_line = re.sub(r"define flow", "flow", stripped_line)

        # We convert "define subflow" to "flow"
        stripped_line = re.sub(r"define subflow", "flow", stripped_line)

        if _is_anonymous_flow(stripped_line):
            logging.info(
                "Using of anonymous flow is deprecated in colang v2.0. We add a unique name to the anonymous flow., but for better readability, please provide a name to the flow."
            )
            stripped_line = _revise_anonymous_flow(stripped_line, next_line) + "\n"

        # We convert "define bot" to "flow bot" and set the flag
        if "define bot" in stripped_line:
            stripped_line = re.sub(r"define bot", "flow bot", stripped_line)
            prev_line = "bot"

        # we conver "define user" to "flow user" and set the flag
        elif "define user" in stripped_line:
            stripped_line = re.sub(r"define user", "flow user", stripped_line)
            prev_line = "user"

        # if _is_flow(stripped_line):
        #     stripped_line = re.sub(r"[-+*/]", "", stripped_line)
        #
        # Replace "when/or when" with "when/else when"
        stripped_line = re.sub(r"else when", "or when", stripped_line)
        # converting "execute" to "await"
        stripped_line = re.sub(r"execute", "await", stripped_line)

        # convert snake_case after "await" to CamelCase only if it's a single word, i.e., it is an action not a flow.
        match = re.search(r"await (.*)", stripped_line)
        if match:
            action_name = match.group(1)

            if "_" in action_name:
                snake_case = action_name
                camel_case = utils.snake_to_camelcase(snake_case)
                if not camel_case.endswith("Action"):
                    camel_case += "Action"
                stripped_line = stripped_line.replace(action_name, camel_case)

            elif " " in action_name:
                snake_case = action_name.replace(" ", "_")
                camel_case = utils.snake_to_camelcase(snake_case)
                if not camel_case.endswith("Action"):
                    camel_case += "Action"
                stripped_line = stripped_line.replace(action_name, camel_case)

        # Convert "stop" to "abort"
        stripped_line = re.sub(r"stop", "abort", stripped_line)

        # Convert quoted strings after "bot" to "bot say" or "or bot say" based on the flag
        if prev_line == "bot" and re.search(r"\"(.+?)\"", stripped_line):
            stripped_line = re.sub(r"\"(.+?)\"", r'bot say "\1"', stripped_line)
            prev_line = "bot say"
        elif prev_line == "bot say" and re.search(r"\"(.+?)\"", stripped_line):
            stripped_line = re.sub(r"\"(.+?)\"", r'or bot say "\1"', stripped_line)

        # Convert quoted strings after "user" to "user said" or "or user said" based on the flag
        if prev_line == "user" and re.search(r"\"(.+?)\"", stripped_line):
            stripped_line = re.sub(r"\"(.+?)\"", r'user said "\1"', stripped_line)
            prev_line = "user said"
        elif prev_line == "user said" and re.search(r"\"(.+?)\"", stripped_line):
            stripped_line = re.sub(r"\"(.+?)\"", r'or user said "\1"', stripped_line)

        new_lines.append(stripped_line)

        if original_line != stripped_line:
            stats["changes"] += 1

    return new_lines


def _write_transformed_content_and_rename_original(
    file_path, new_lines, v1_extension=".v1.co"
):
    """Writes the transformed content to the file."""

    # set the name of the v1 file
    new_file_path_v1 = os.path.splitext(file_path)[0] + v1_extension

    # rename the original file
    os.rename(file_path, new_file_path_v1)

    # write the transformed content to a new file with the original name
    return _write_to_file(file_path, new_lines)


def _write_to_file(file_path, new_lines):
    """Writes new lines to a file. If the file does not exist, it is created.

    Args:
        file_path (str): The path to the file to write to.
        new_lines (list): The new lines to write to the file.
    """
    try:
        with open(file_path, "w") as file:
            file.writelines(new_lines)
        return True
    except Exception as e:
        logging.error(f"Failed to write to file: {file_path}. Error: {str(e)}")
        return False


def _is_anonymous_flow(flow_content: str) -> bool:
    """Checks if the flow is an anonymous flow.

    an anonymous flow is a flow that does not start with a name. so it only has define flow without a name.

    Args:
        flow_content (str): The content of the flow.
    Returns:
        bool: True if the flow is anonymous, False otherwise.
    Examples:

        flow_content = "flow  "
        is_anonymous_flow(flow_content)
        # True
        flow_content = "flow my_flow"
        is_anonymous_flow(flow_content)
        # False
    """

    return re.match(r"flow\s*$", flow_content) is not None


def _is_flow(line: str) -> bool:
    """Checks if the line is a flow definition. it is a flow definition if it starts with "flow" and other words after flow."""

    return re.match(r"flow\s+\w+", line) is not None


def _globalize_variable_assignment(line):
    # split the line into tokens
    tokens = line.split()

    # here we have local scope variable assignment
    if "await" in line or "execute" in line:
        return line

    # Check if the line is a variable assignment
    if len(tokens) >= 2 and tokens[1] == "=":
        # Get the original indentation
        indentation = len(line) - len(line.lstrip())

        # Prepend the "global" keyword with the original indentation
        return (
            " " * indentation + "global " + tokens[0] + "\n" + " " * indentation + line
        )
    else:
        # If not a variable assignment, return the line as is
        return line


# TODO: (Razvan): modify the heuristic as needed, the limitation of this appraoch is that if the user has a flow with this name already. Appending a uuid might be beneficial.
def _revise_anonymous_flow(flow_content: str, first_message: str) -> str:
    """Revises an anonymous flow by giving it a unique name.
    Args:
        flow_content (str): The content of the anonymous flow.
        first_message (str): The first message in the flow.
    Returns:
        str: The revised flow content with a unique name.
    """

    # remove "bot" or "user" from first_message
    first_message = first_message.replace("bot", "").replace("user", "").strip()
    # Use the first few words from the user's message for the flow name
    first_message_words = first_message.split()

    # TODO: Adjust the number as needed

    flow_name = "_".join(first_message_words[:3])

    return re.sub(r"flow\s*$", f"flow {flow_name}", flow_content)
    # return re.sub(r"flow\s*$", f"flow anonymous_{uuid.uuid4().hex}", flow_content)


def get_flow_ids(content: str) -> list:
    """Returns the flow ids in the content.

    Args:
        content (str): The content to search for flow ids.
    Returns:
        list: A list of flow ids.

    Examples:
    content = "flow my_flow"
    get_flow_ids(content)
    # ['my_flow']
    content = "flow my_flow is better than\nflow another_flow"
    get_flow_ids(content)
    # ['my_flow is better than', 'another_flow']

    # flow user and flow bot are not considered as flow ids
    content = "flow user express greeting"
    get_flow_ids(content)
    # []

    """

    # Match any words (more than one) that comes after "flow " before new line and the first word after flow is not "user" or "bot"

    root_flow_pattern = re.compile(
        r"^flow\s+(?!user|bot)(.*?)$", re.IGNORECASE | re.MULTILINE
    )
    return root_flow_pattern.findall(content)


def get_flow_ids_from_newlines(new_lines: list) -> list:
    """Returns the flow ids in the new lines.
    Args:
        new_lines (list): The new lines to search for flow ids.
    Returns:
        list: A list of flow ids.
    Examples:
    new_lines = ["flow my_flow is better than", "flow another_flow"]
    get_flow_ids_from_newlines(new_lines)
    # ['my_flow is better than', 'another_flow']
    """
    content = "\n".join(new_lines)
    return get_flow_ids(content)


def generate_main_flow(new_lines: list) -> list:
    """Adds a 'main' flow to the new lines that activates all other flows.

    The 'main' flow is added at the beginning of the new lines. It includes an 'activate' command for each flow id found in the new lines.

    Args:
        new_lines (list): The new lines to add the main flow to.

    Returns:
        list: The new lines with the 'main' flow added at the beginning.

    Examples:
    new_lines = ["flow my_flow", "flow another_flow"]
    include_main_flow(new_lines)
    # '''flow main
    #  activate my_flow
    #  activate another_flow
    """
    # Create the 'main' flow
    main_flow = ["flow main"]

    # Add an 'activate' command for each flow id in the new lines
    flow_ids = get_flow_ids_from_newlines(new_lines)
    # one level indentation
    _INDENT = "  "

    activation_commands = [_INDENT + "activate " + flow_id for flow_id in flow_ids]

    # add new line to the last activation command
    activation_commands[-1] += "\n\n"

    main_flow.extend(activation_commands)

    # Add the 'main' flow at the beginning of the new lines
    new_lines.insert(0, "\n".join(main_flow))

    return new_lines


def add_active_decorator(new_lines: list) -> list:
    """Adds an '@active' decorator above each flow id in the new lines.

    Args:
        new_lines (list): The lines to add the decorators to.

    Returns:
        list: The lines with the decorators added.
    """
    decorated_lines = []

    _ACTIVE_DECORATOR = "@active"
    _NEWLINE = "\n"
    root_flow_pattern = re.compile(
        r"^flow\s+(?!user|bot)(.*?)$", re.IGNORECASE | re.MULTILINE
    )

    for line in new_lines:
        # if it is a root flow
        if root_flow_pattern.match(line):
            # Add the '@active' decorator above the flow id
            decorated_lines.append(_ACTIVE_DECORATOR + _NEWLINE)
        decorated_lines.append(line)
    return decorated_lines


def get_raw_config(config_path: str):
    """read the yaml file and get rails key"""

    if config_path.endswith(".yaml") or config_path.endswith(".yml"):
        with open(config_path) as f:
            raw_config = yaml.safe_load(f.read())

    return raw_config


def get_rails_flows(raw_config):
    """Extracts the list of flows from the raw_config dictionary.

    Args:
        raw_config (dict): The raw configuration dictionary.

    Returns:
        list: The list of flows.
    """
    from collections import defaultdict

    flows = defaultdict(list)
    try:
        for key in raw_config["rails"]:
            if "flows" in raw_config["rails"][key]:
                flows[key].extend(raw_config["rails"][key]["flows"])
    except KeyError:
        pass
    return flows


def generate_rails_flows(flows):
    """Generates flow definitions from the list of flows.
    Args:
        flows (dict): The dictionary of flows.
    Returns:
        str: The flow definitions.
    """
    _MAPPING = {
        "input": "flow input rails $input_text",
        "output": "flow output rails $output_text",
    }

    _GUARDRAILS_IMPORT = "import guardrails"
    _LIBRARY_IMPORT = "import nemoguardrails.library"

    flow_definitions = []
    _INDENT = "    "  # 4 spaces for indentation
    _NEWLINE = "\n"

    for key, value in flows.items():
        flow_definitions.append(_MAPPING[key] + _NEWLINE)
        for v in value:
            flow_definitions.append(_INDENT + v + _NEWLINE)
        flow_definitions.append(_NEWLINE)  # Add an empty line after each flow

    if flow_definitions:
        flow_definitions.insert(0, _GUARDRAILS_IMPORT + _NEWLINE)
        flow_definitions.insert(1, _LIBRARY_IMPORT + _NEWLINE * 2)

    return flow_definitions


def _write_rails_flows_to_file(file_path, rails_flows):
    """Writes the rails flows to a file.
    Args:
        file_path (str): The path to the file to write to.
        rails_flows (list): The rails flows to write to the file.
    """
    try:
        with open(file_path, "w") as file:
            file.writelines(rails_flows)
        return True
    except Exception as e:
        logging.error(f"Failed to write to file: {file_path}. Error: {str(e)}")
        return False


def _remove_rails_flows_from_config(raw_config):
    del raw_config["rails"]
    return raw_config


def migrate(
    path,
    include_main_flow=False,
    use_active_decorator: bool = True,
    validate: bool = True,
):
    """Migrates all .co files in a directory from the old format to the new format.

    Args:
        path (str): The path to the directory containing the files to migrate.
        include_main_flow (bool): Whether to add main flow to the files.
        validate (bool): Whether to validate the files.
    """
    logging.info(f"Starting migration for path: {path}")

    if include_main_flow and use_active_decorator:
        raise ValueError(
            "Cannot use both main flow and active decorator at the same time."
        )

    total_files_changed = 0
    total__config_files_changed = 0

    # Check if path is a file or a directory
    if os.path.isfile(path) and path.endswith(".co"):
        co_files_to_process = [path]
    else:
        co_files_to_process = []
        for root, dirs, files in os.walk(path):
            for file in files:
                if file.endswith(".co"):
                    # Split the filename at the first period
                    base_file = file.split(".", 1)[0]
                    v1_file = os.path.join(root, base_file + ".v1.co")
                    # we do not migrate twice
                    if not os.path.exists(v1_file):
                        co_file = os.path.join(root, file)
                        co_files_to_process.append(co_file)

    config_files_to_process = [
        os.path.join(root, file)
        for root, dirs, files in os.walk(path)
        for file in files
        if file.endswith(".yaml") or file.endswith(".yml")
    ]

    logging.info("Starting migration for colang files.")

    for file_path in co_files_to_process:
        logging.info(f"Converting colang files in path: {file_path}")

        new_lines = convert_co_file_syntax(file_path)
        if new_lines:
            if include_main_flow:
                new_lines = generate_main_flow(new_lines)
            if validate:
                try:
                    parse_colang_file(
                        filename=file_path, content="\n".join(new_lines), version="2.x"
                    )
                except Exception as e:
                    raise Exception(
                        f"Validation failed for file: {file_path}. Error: {str(e)}"
                    )
                    # continue
            if use_active_decorator:
                new_lines = add_active_decorator(new_lines)

            if _write_transformed_content_and_rename_original(file_path, new_lines):
                total_files_changed += 1

    logging.info("Starting migration for config files.")

    for file_path in config_files_to_process:
        logging.info(f"Converting config files in path: {file_path}")
        raw_config = get_raw_config(file_path)

        rails_flows = generate_rails_flows(get_rails_flows(raw_config))

        if rails_flows:
            # at same level as config file we generate a _rails.co file
            # _rails.co file is the file that contains the rails flows
            _rails_co_file_path = Path(file_path).parent / "_rails.co"

            if _write_rails_flows_to_file(_rails_co_file_path, rails_flows):
                total__config_files_changed += 1

            raw_config = _remove_rails_flows_from_config(raw_config)

            # NOTE: we are overwriting the original config file. It ruins the order of the keys in the yaml file.
            with open(file_path, "w") as f:
                yaml.dump(raw_config, f)

    logging.info(
        f"Finished migration for path: {path}. Total files changed: {total_files_changed}"
    )
