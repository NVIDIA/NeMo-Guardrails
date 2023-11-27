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


def create_logger(filename):
    """Create a logger specified by the filename.

    Args:
        filename (str): The name of the log file.

    Returns:
        logging.Logger: A logger instance configured to write log messages to the specified file.

    Note:
        This function creates a logger instance and configures it to log messages to a file with the given filename.
        It sets the logging level to INFO and uses a timestamped format for log entries.
    """
    logger = logging.getLogger(filename)
    logger.setLevel(logging.INFO)

    # Create a file handler
    file_handler = logging.FileHandler(filename, mode="w")

    # Configure the formatter and add it to the file handler
    formatter = logging.Formatter("%(asctime)s - %(levelname)s - %(message)s")
    file_handler.setFormatter(formatter)

    # Add the file handler to the logger
    logger.addHandler(file_handler)

    return logger
