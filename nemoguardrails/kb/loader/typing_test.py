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

from .typing import Document, Topic


def test_document_init():
    # Initialize a Document instance
    document = Document(
        content="test content",
        type="text",
        format="txt",
        metadata={"author": "John Doe"},
        uri={"filename": "/path/to/file"},
        loader="DocumentLoader",
    )

    assert document.content == "test content"
    assert document.type == "text"
    assert document.format == "txt"
    assert document.metadata == {"author": "John Doe"}
    assert document.uri == {"filename": "/path/to/file"}
    assert document.loader == "DocumentLoader"


def test_topic_init():
    # Initialize a Topic instance
    topic = Topic(title="test title", body="test body", metadata={"author": "John Doe"})

    assert topic.title == "test title"
    assert topic.body == "test body"
    assert topic.metadata == {"author": "John Doe"}
