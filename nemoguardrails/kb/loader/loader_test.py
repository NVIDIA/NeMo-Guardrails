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

import io
import os
import tempfile
from unittest.mock import Mock, PropertyMock, patch

import PyPDF2
import requests

from nemoguardrails.kb.loader import DocumentLoader

from .loader import PdfLoader
from .partition_factory import partition_pdf
from .typing import Document, ElementMetadata, FigureCaption, Text, Title


@patch("nemoguardrails.kb.loader.PartitionFactory.get")
def test_get_partition_handler(mock_get):
    # Assuming PartitionFactory.get returns a mock object
    mock_get.return_value = partition_pdf
    temp_file = tempfile.NamedTemporaryFile(prefix="test", suffix=".pdf", delete=True)
    filename = temp_file.name

    loader = DocumentLoader(file_path=filename)
    handler = loader.partition_handler

    # check if PartitionFactory.get was called with the correct arguments

    mock_get.assert_called_with(filename)

    # check the return value
    assert handler == partition_pdf


@patch.object(DocumentLoader, "_elements", new_callable=PropertyMock)
def test_load(mock_elements):
    # Assume Element.text, Element.metadata.filetype and Element.metadata.to_dict
    # return some mock values

    metadata = ElementMetadata(filename="fake-file.txt")
    elements = [
        Title(text="a title", metadata=metadata, element_id="0"),
        FigureCaption(text="a caption", metadata=metadata, element_id="1"),
        Text(text="first text", metadata=metadata, element_id="2"),
        Text(text="second text", metadata=metadata, element_id="3"),
    ]

    metadata.filetype = "txt"

    mock_elements.return_value = elements

    temp_file = tempfile.NamedTemporaryFile(
        prefix="fake-file", suffix=".txt", delete=True
    )
    filename = temp_file.name
    loader = DocumentLoader(file_path=filename)

    documents = list(loader.load())

    assert len(documents) == 4
    assert documents[0].content == "a title"
    assert documents[0].type is type(elements[0])
    assert documents[0].metadata == metadata.to_dict()
    assert documents[0].uri == {"filename": filename}
    assert documents[0].loader == "DocumentLoader"


@patch.object(DocumentLoader, "load")
def test_combine_topics(mock_load):
    doc1 = Document(content="mock title", format="md", type=Title, metadata={})
    doc2 = Document(content="mock body", format="md", type=Text, metadata={})
    mock_load.return_value = [doc1, doc2]

    # Create a StringIO object and write the markdown content to it
    file_content = f"# {doc1.content}\n\n{doc2.content}"
    file_obj = io.StringIO(file_content)
    loader = DocumentLoader(file=file_obj)
    topics = loader.combine_topics()

    assert len(topics) == 1
    assert topics[0]["title"] == "mock title"
    assert topics[0]["body"] == "mock body"
    assert topics[0]["metadata"] == {}


# Define a mock PDF page with extractText method
class MockPdfPage:
    def extractText(self):
        return "mock page text"


# Define a mock PDF reader with pages
class MockPdfReader:
    def __init__(self, num_pages):
        self.pages = [MockPdfPage() for _ in range(num_pages)]


@patch.object(PyPDF2, "PdfFileReader")
@patch.object(requests, "get")
def test_load_from_url(mock_get, mock_reader):
    mock_get.return_value = Mock(content=b"mock pdf content")
    mock_reader.return_value = MockPdfReader(num_pages=1)

    loader = PdfLoader(url="http://example.com/sample.pdf")
    documents = list(loader.load())

    assert len(documents) == 1
    assert documents[0].content == "mock page text"
    assert documents[0].type == Text
    assert documents[0].format == "pdf"
    assert documents[0].metadata == {"page_num": 0}
    assert documents[0].uri == {"url": "http://example.com/sample.pdf"}
    assert documents[0].loader == "PdfLoader"


@patch.object(PyPDF2, "PdfFileReader")
def test_load_from_file(mock_reader):
    mock_reader.return_value = MockPdfReader(num_pages=1)

    mock_file = Mock()
    mock_file.read.return_value = b"mock pdf content"

    loader = PdfLoader(file=mock_file)
    documents = list(loader.load())

    assert len(documents) == 1
    # other assertions omitted for brevity


@patch.object(PyPDF2, "PdfFileReader")
def test_load_from_filename(mock_reader):
    mock_reader.return_value = MockPdfReader(num_pages=1)

    # Create a temporary file with some mock PDF content
    with open("mock.pdf", "wb") as f:
        f.write(b"mock pdf content")

    # Use the temporary file path as the filename argument
    loader = PdfLoader(file_path=os.path.abspath("mock.pdf"))
    documents = list(loader.load())

    assert len(documents) == 1

    # Remove the temporary file
    os.remove("mock.pdf")
    # other assertions omitted for brevity


@patch.object(PyPDF2, "PdfFileReader")
def test_load_from_text(mock_reader):
    mock_reader.return_value = MockPdfReader(num_pages=1)

    loader = PdfLoader(text=b"mock pdf content")
    documents = list(loader.load())

    assert len(documents) == 1
    # other assertions omitted for brevity
