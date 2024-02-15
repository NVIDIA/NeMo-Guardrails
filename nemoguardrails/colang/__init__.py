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
from .v1_0.lang import parser as parser_v1_0
from .v2_x.lang import parser as parser_v2_x


def parse_colang_file(
    filename: str,
    content: str,
    include_source_mapping: bool = True,
    version: str = "1.0",
):
    """Parse the content of a .co file into the CoYML format."""
    if version == "1.0":
        return parser_v1_0.parse_colang_file(filename, content, include_source_mapping)
    elif version == "2.x":
        return parser_v2_x.parse_colang_file(filename, content, include_source_mapping)
    else:
        raise Exception(f"Unsupported colang version {version}")


def parse_flow_elements(items, version: str = "1.0"):
    """Parse the flow elements from CoYML format to CIL."""
    if version == "1.0":
        return parser_v1_0.parse_flow_elements(items)
    elif version == "2.x":
        raise Exception(
            f"Parsing flow elements not supported for colang version {version}"
        )
    else:
        raise Exception(f"Unsupported colang version {version}")
