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
import subprocess
import traceback

EXAMPLES_FOLDER = os.path.join(os.path.dirname(os.path.dirname(__file__)), "examples")


def create_chatter(name, configname, logger):
    """Create a NeMo Guardrails chatter specified with the configuration.

    Args:
        name (str): The name of the chatter.
        configname (str): The name of the configuration.
        logger: The logger object for logging information.

    Returns:
        subprocess.Popen or None: A subprocess representing the chatter or None if creation fails.

    Note:
        This function creates a NeMo Guardrails chatter process based on the specified name and configuration.
        It logs information about the configuration and any errors encountered during the process creation.
    """
    chatter = None
    cwd = os.path.join(EXAMPLES_FOLDER, configname)
    config = os.path.join(EXAMPLES_FOLDER, configname)
    logger.info(f"config: {config}")
    try:
        command = ["nemoguardrails", "chat", f"--config={config}"]
        chatter = subprocess.Popen(
            command,
            cwd=cwd,
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
        )
        if chatter is not None:
            output = chatter.stdout.readline().strip()
            logger.info(f"output: {output}")
            # Is the chatter process ready?
            # assert "Starting the chat" in output
    except subprocess.CalledProcessError as e:
        logger.error("Command execution for config %s failed: %s", name, e)
        logger.error(f"Error message: {e.stderr}")
        logger.error(traceback.format_exc())

    return chatter


def close_chatter(chatter):
    """Close the given chatter.

    Args:
        chatter (subprocess.Popen or None): The chatter subprocess to be closed or None.

    Note:
        This function closes the specified chatter subprocess if it is not None.
    """
    if chatter is not None:
        chatter.communicate()
        chatter.wait()
