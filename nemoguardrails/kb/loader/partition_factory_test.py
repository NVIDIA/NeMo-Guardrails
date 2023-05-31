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

import tempfile
from unittest.mock import Mock

import pytest

from .partition_factory import (
    FileExtensionNotFoundError,
    FileTypeNotFoundError,
    PartitionFactory,
    partition_html,
)
from .typing import FileType

# Assuming 'mock_partition_function' is a mock function.
mock_partition_function = Mock()


def test_get_partition_function_by_filetype():
    partition_func = PartitionFactory.get(FileType.HTML)
    assert partition_func == partition_html


def test_get_partition_function_by_filepath():
    # Create a temporary file with a .html extension
    temp_file = tempfile.NamedTemporaryFile(prefix="test", suffix=".html", delete=True)
    file_path = temp_file.name
    partition_func = PartitionFactory.get(file_path)

    assert partition_func == partition_html


def test_get_partition_function_by_file_extension():
    partition_func = PartitionFactory.get(".html")
    assert partition_func == partition_html


def test_get_partition_function_invalid_identifier():
    with pytest.raises(ValueError):
        PartitionFactory.get(12345)  # Not a valid file identifier.


def test_register_partition_function():
    PartitionFactory.register(FileType.JSON, mock_partition_function)
    assert (
        PartitionFactory._PARTITION_FUNCTIONS[FileType.JSON] == mock_partition_function
    )  # noqa: E501


def test_unrecognized_file_type():
    with pytest.raises(FileTypeNotFoundError):
        temp_file = tempfile.NamedTemporaryFile(
            prefix="test", suffix=".jpg", delete=True
        )
        file_path = temp_file.name
        PartitionFactory.get(file_path)


def test_unrecognized_file_extension():
    with pytest.raises(FileExtensionNotFoundError):
        PartitionFactory.get(".unrecognized_extension")
