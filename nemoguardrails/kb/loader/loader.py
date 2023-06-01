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

from abc import ABC, abstractmethod
from io import BytesIO
from typing import IO, Any, Callable, Iterable, List, Optional

import PyPDF2
import requests

from .partition_factory import PartitionFactory
from .typing import (
    Document,
    Element,
    FigureCaption,
    ListItem,
    NarrativeText,
    Text,
    Title,
    Topic,
)


class BaseDocumentLoader(ABC):
    """Base class for document loaders.

    Documnet loaders are used to load documents from a source.
    The source can be a file_path, file, text, or url.

    :param: file_path: The path to the file to load.
    :param: file: A file-like object using "r" mode --> open(filename, "r").
    :param: text: The string representation of the file to load.
    :param: url: The URL of a webpage to parse. Only for URLs
        that return an HTML document.
    :param: kwargs: Additional keyword arguments to pass to the partition

    """

    def __init__(
        self,
        file_path: Optional[str] = None,
        file: Optional[IO] = None,
        text: Optional[str] = None,
        url: Optional[str] = None,
        **kwargs: Any,
    ):
        # _source is a dictionary that contains the source of the document
        # The source can be a file_path, file, text, or url

        source = {
            "filename": file_path,
            "file": file,
            "text": text,
            "url": url,
        }

        non_none_sources = _remove_none_values(source)
        if len(non_none_sources) != 1:
            raise ValueError(
                "Exactly one of file_path, file, text, or url must be specified."
                f"Received {non_none_sources}"
            )
        self._source = non_none_sources
        print(self._source)
        print("****|||||****" * 10)
        self._kwargs = kwargs

    @abstractmethod
    def load(self) -> Iterable[Document]:
        """Load documents from a source."""
        pass

    @abstractmethod
    def combine_topics(self) -> Iterable[Topic]:
        """Combine multiple documents into topics."""
        pass

    def _combine_topics_by_size(self, topics, topic_size: int) -> Iterable[Topic]:
        """Combine topics to meet a minimum size."""
        pass


class DocumentLoader(BaseDocumentLoader):
    """A builder class for loading documents from a source.

    It loads documents of different types from a source.
    The source can be a file_path, file, text, or url.
    It currently supports the following document types:
    `text`, `html`, `markdown`, `pdf`, `doc`, and `docx`.

    :param: file_path: The path to the file to load.
    :param: file: A file-like object using "r" mode --> open(filename, "r").
    :param: text: The string representation of the file to load.
    :param: url: The URL of a webpage to parse. Only for URLs that
        return an HTML document.
    :param: partition_handler: A partition handler to use for the loader.
    :param: kwargs: Additional keyword arguments to pass to the partition
        handler see  [unstructured.partion](https://github.com/Unstructured-IO/unstructured/tree/main/unstructured/partition).


    Example:
        >>> from nemoguardrails.kb.loader import DocumentLoader
        >>> loader = DocumentLoader(file_path="path/to/file.md")
        >>> for document in loader.load():
        ...     print(document.content)
        ...     print(document.type)
        ...     print(document.format)
        ...     print(document.metadata)
        ...     print(document.file_path)
        ...     print(document.loader)

        >>> file_paths = ["file1.txt", "file2.txt", "file3.txt"]
        >>> loaders = [DocumentLoader(file_path=path) for path in file_paths]
        >>> for loader in loaders:
        ...     documents = loader.load()
        ...     # process the documents for each file here

        >>> loader = DocumentLoader(file_path="Nemo-Guardrails/examples/grounding_rail/kb/report.md")
        >>> topics = loader.combine_topics()
        >>> sized_topics = loader.combine_topics(topic_size=100)
        >>> print(topics)
        >>> print(sized_topics)

    """

    def __init__(
        self,
        file_path: Optional[str] = None,
        file: Optional[IO] = None,
        text: Optional[str] = None,
        url: Optional[str] = None,
        partition_handler: Optional[Callable] = None,
        **kwargs: Any,
    ):
        super().__init__(file_path=file_path, file=file, text=text, url=url, **kwargs)

        self._partition_handler = partition_handler

    @property
    def partition_handler(self):
        """Get the partition handler for the loader."""

        if self._partition_handler is None:
            self._partition_handler = self._get_partition_handler()

        print(self._kwargs)
        # return self._partition_handler(**self._kwargs)
        return self._partition_handler

    def _get_partition_handler(self):
        """Get the partition handler for the loader."""
        # NOTE: PartitionFactory currently only supports file_path
        # TODO: Add support for file, text, and url

        source_value = next(iter(self._source.values()))
        return PartitionFactory.get(source_value)

    @property
    def _elements(self) -> List[Element]:
        """Get the elements from the partition handler."""
        return self.partition_handler(**self._source, **self._kwargs)

    def load(self) -> Iterable[Document]:
        """Load documents from a source."""

        for element in self._elements:
            yield Document(
                content=element.text,
                type=type(element),
                format=element.metadata.filetype,
                metadata=element.metadata.to_dict(),
                source=_remove_none_values(self._source),
                loader=self.__class__.__name__,
            )

    def combine_topics(self, topic_size: Optional[int] = None) -> List[Topic]:
        """Combine multiple documents into topics.

        This method aggregates the body of multiple documents into topics,
        using the title of each document as the title of the corresponding topic.
        The resulting topics are represented as dictionaries
        with keys for `title`, `body`, and `metadata`.

        It's important to note that each file can contain multiple elements,
        which can correspond to multiple documents.
        One of these elements could be a Title.
        The text elements that follow the Title until the next Title is encountered
        are considered to be the body of the current topic,
        with the Title serving as the title of the topic.

        Returns:
            A list of dictionaries, each representing a topic.
        """

        # TODO: is topics a good name for this?

        topics = []
        topic_schema = {
            "title": "",
            "body": "",
            "metadata": {},
        }
        topic = Topic(title="", body="")
        for doc in self.load():
            if doc.type == Title:
                topic.title += doc.content
                continue

            elif doc.type in (Text, ListItem, FigureCaption, NarrativeText):
                # bodies.append(doc.content)
                topic.body += doc.content
                topic.metadata = doc.metadata

            # topic has values other than topic_schema 's default values
            if topic.dict() != topic_schema:
                topics.append(topic.dict())

        if topic_size:
            topics = self._combine_topics_by_size(topics, topic_size)

        return topics

    def _combine_topics_by_size(
        self, topics: List[Topic], topic_size: int
    ) -> List[Topic]:
        """Combine topics to meet a minimum size.

        If the body of a topic is less than the specified size,
        it is combined with the body of the next topic until the combined
        body size is at least the specified size. The titles of the combined
        topics are concatenated to form the title of the new topic.

        :param topics: A list of dictionaries, each representing a topic.
        :param topic_size: The size of the topic body.
        :return: A list of dictionaries, each representing a topic.

        """

        if not isinstance(topic_size, int):
            raise TypeError(f"topic_size must be an integer but receieved{topic_size}")

        if topic_size < 1:
            raise ValueError(
                f"topic_size must be greater than 0 but received {topic_size}"
            )

        new_topics = []
        current_topic = None
        current_topic_size = 0
        current_topic_title_parts = []

        for topic in topics:
            if current_topic is None:
                current_topic = topic
                current_topic_size = len(topic["body"])
                current_topic_title_parts.append(topic["title"])
            else:
                if current_topic_size < topic_size:
                    current_topic_size += len(topic["body"])
                    current_topic["body"] += "\n" + topic["body"]
                    current_topic_title_parts.append(topic["title"])
                else:
                    current_topic["title"] = " - ".join(current_topic_title_parts)
                    new_topics.append(current_topic)
                    current_topic = topic
                    current_topic_size = len(topic["body"])
                    current_topic_title_parts = [topic["title"]]

        if current_topic is not None:
            current_topic["title"] = " - ".join(current_topic_title_parts)
            new_topics.append(current_topic)

        return new_topics


class PdfLoader(BaseDocumentLoader):
    """Load documents from a PDF file."""

    def __init__(
        self,
        file_path: Optional[str] = None,
        file: Optional[IO] = None,
        text: Optional[str] = None,
        url: Optional[str] = None,
        partition_handler: Optional[Callable] = None,
        **kwargs: Any,
    ):
        super().__init__(file_path=file_path, file=file, text=text, url=url, **kwargs)

    def load(self) -> Iterable[Document]:
        """Load documents from a PDF file."""

        if "text" in self._source:
            pdf_file_obj = BytesIO(self._source["text"])

        elif "file" in self._source:
            pdf_file_obj = BytesIO(self._source["file"].read())

        elif "url" in self._source:
            pdf_file_obj = BytesIO(requests.get(self._source["url"]).content)

        elif "filename" in self._source:
            pdf_file_obj = open(self._source["filename"], "rb")

        else:
            raise ValueError(f"Invalid source: {self._source}")

        pdf_reader = PyPDF2.PdfFileReader(pdf_file_obj)

        for page_num, page in enumerate(pdf_reader.pages):
            page_text = page.extractText()
            yield Document(
                content=page_text,
                type=Text,
                format="pdf",
                metadata={"page_num": page_num},
                uri=_remove_none_values(self._source),
                loader=self.__class__.__name__,
            )
            print(Document)

    def combine_topics(self, topic_size: Optional[int] = None) -> List[Topic]:
        """Combine multiple documents into topics.

        Returns:
            A list of dictionaries, each representing a topic.
        """
        topics = []

        for doc in self.load():
            topics.append(
                Topic(
                    title=None,
                    body=doc.content,
                    metadata=doc.metadata,
                )
            )

        return topics


class MarkdownLoader(BaseDocumentLoader):
    """Load documents from a Markdown file."""

    def load(self):
        """Load documents from a Markdown file."""

    def combine_topics(self):
        """Combine multiple documents into topics."""


def _remove_none_values(d: dict) -> dict:
    """Return a new dictionary with only the non-None and non-empty string values."""
    return {k: v for k, v in d.items() if v not in (None, "")}
