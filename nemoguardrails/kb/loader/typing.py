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

from typing import Any, Dict, Optional, Type, Union

from pydantic import BaseModel
from unstructured.documents.elements import (
    Address,
    Element,
    ElementMetadata,
    FigureCaption,
    Image,
    ListItem,
    NarrativeText,
    PageBreak,
    Table,
    Text,
    Title,
)
from unstructured.file_utils.filetype import FileType


class Document(BaseModel):
    content: str
    type: Union[str, Type[Element]]
    format: str
    metadata: Optional[Dict[str, Any]] = None
    uri: Optional[Dict[Any, Any]] = None
    loader: Optional[str] = None



class Topic(BaseModel):
    title: str
    body: str
    metadata: Dict[str, Any] = {}
