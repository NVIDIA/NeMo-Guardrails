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

from dataclasses import dataclass, field
from typing import Dict, List


@dataclass
class IndexItem:
    """
    Represents an item in the embeddings index.

    Attributes:
        text (str): The text content of the item.
        meta (Dict, optional): Additional metadata for the item. Defaults to an empty dictionary.

    Example:
        ```python
        # Create an IndexItem with text and metadata
        item = IndexItem(text="Example text", meta={"key": "value"})
        ```
    """

    text: str
    meta: Dict = field(default_factory=dict)


class EmbeddingsIndex:
    """
    The embeddings index is responsible for computing and searching a set of embeddings.

    Note:
        This class defines the interface for an embeddings index, which is responsible for managing
        and searching a collection of embeddings.

    Example:
        ```python
        # Create a custom EmbeddingsIndex implementation
        class MyEmbeddingsIndex(EmbeddingsIndex):
            # Implement the required methods
            ...

        # Instantiate the custom index
        index = MyEmbeddingsIndex()
        ```
    """

    @property
    def embedding_size(self):
        """
        Get the size of the embeddings.

        Returns:
            int: The size of the embeddings.

        Raises:
            NotImplementedError: This method should be implemented in subclasses.
        """
        raise NotImplementedError

    async def add_item(self, item: IndexItem):
        """
        Adds a new item to the index.

        Args:
            item (IndexItem): The item to add to the index.

        Raises:
            NotImplementedError: This method should be implemented in subclasses.
        """
        raise NotImplementedError()

    async def add_items(self, items: List[IndexItem]):
        """
        Adds multiple items to the index.

        Args:
            items (List[IndexItem]): The list of items to add to the index.

        Raises:
            NotImplementedError: This method should be implemented in subclasses.
        """
        raise NotImplementedError()

    async def build(self):
        """
        Build the index after adding items.

        This method is optional and might not be needed for all implementations.

        Raises:
            NotImplementedError: This method should be implemented in subclasses if needed.
        """
        pass

    async def search(self, text: str, max_results: int) -> List[IndexItem]:
        """
        Searches the index for the closest matches to the provided text.

        Args:
            text (str): The text to search for.
            max_results (int): The maximum number of results to return.

        Returns:
            List[IndexItem]: A list of IndexItem objects representing the closest matches.

        Raises:
            NotImplementedError: This method should be implemented in subclasses.
        """
        raise NotImplementedError()


class EmbeddingModel:
    """
    The embedding model is responsible for creating embeddings from text documents.

    Note:
        This class defines the interface for an embedding model, which is responsible for encoding
        text documents into embeddings.

    Example:
        ```python
        # Create a custom EmbeddingModel implementation
        class MyEmbeddingModel(EmbeddingModel):
            # Implement the required methods
            ...

        # Instantiate the custom embedding model
        model = MyEmbeddingModel()
        ```
    """

    def encode(self, documents: List[str]) -> List[List[float]]:
        """
        Encode a list of text documents into embeddings.

        Args:
            documents (List[str]): The list of text documents to encode.

        Returns:
            List[List[float]]: A list of lists, where each inner list represents the embedding of a document.

        Raises:
            NotImplementedError: This method should be implemented in subclasses.
        """
        raise NotImplementedError()
