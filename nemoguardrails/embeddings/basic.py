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

from typing import List

from annoy import AnnoyIndex
from torch import cuda

from nemoguardrails.embeddings.index import EmbeddingModel, EmbeddingsIndex, IndexItem


class BasicEmbeddingsIndex(EmbeddingsIndex):
    """
    Basic implementation of an embeddings index.

    This index uses the `sentence-transformers/all-MiniLM-L6-v2` model to compute embeddings
    and employs Annoy for efficient nearest neighbor search.

    Attributes:
        embedding_model: The name or path of the embedding model to use.
        embedding_engine: The embedding engine to use.
        index: The Annoy index for nearest neighbor search.

    Note:
        This class provides a basic embeddings index implementation. It computes embeddings for text items
        and allows efficient searching for similar items.

    Example:
        ```python
        # Create an instance of BasicEmbeddingsIndex
        index = BasicEmbeddingsIndex(embedding_model="sentence-transformers/all-MiniLM-L6-v2")

        # Add items to the index
        items = [IndexItem(text="Example text 1"), IndexItem(text="Example text 2")]
        await index.add_items(items)

        # Build the index for efficient searching
        await index.build()

        # Search for similar items
        results = await index.search("Query text", max_results=5)
        ```
    """

    def __init__(self, embedding_model=None, embedding_engine=None, index=None):
        self._model = None
        self._items = []
        self._embeddings = []
        self.embedding_model = embedding_model
        self.embedding_engine = embedding_engine
        self._embedding_size = 0

        # When the index is provided, it means it's from the cache.
        self._index = index

    @property
    def embeddings_index(self):
        return self._index

    @property
    def embedding_size(self):
        return self._embedding_size

    @property
    def embeddings(self):
        return self._embeddings

    @embeddings_index.setter
    def embeddings_index(self, index):
        """Setter to allow replacing the index dynamically."""
        self._index = index

    def _init_model(self):
        """Initialize the model used for computing the embeddings."""
        self._model = init_embedding_model(
            embedding_model=self.embedding_model, embedding_engine=self.embedding_engine
        )

    def _get_embeddings(self, texts: List[str]) -> List[List[float]]:
        """Compute embeddings for a list of texts."""
        if self._model is None:
            self._init_model()

        embeddings = self._model.encode(texts)
        return embeddings

    async def add_item(self, item: IndexItem):
        """Add a single item to the index."""
        self._items.append(item)

        # If the index is already built, we skip this
        if self._index is None:
            self._embeddings.append(self._get_embeddings([item.text])[0])

            # Update the embedding if it was not computed up to this point
            self._embedding_size = len(self._embeddings[0])

    async def add_items(self, items: List[IndexItem]):
        """Add multiple items to the index at once."""
        self._items.extend(items)

        # If the index is already built, we skip this
        if self._index is None:
            self._embeddings.extend(self._get_embeddings([item.text for item in items]))

            # Update the embedding if it was not computed up to this point
            self._embedding_size = len(self._embeddings[0])

    async def build(self):
        """Builds the Annoy index."""
        self._index = AnnoyIndex(len(self._embeddings[0]), "angular")
        for i in range(len(self._embeddings)):
            self._index.add_item(i, self._embeddings[i])
        self._index.build(10)

    async def search(self, text: str, max_results: int = 20) -> List[IndexItem]:
        """Search the closest `max_results` items."""
        _embedding = self._get_embeddings([text])[0]
        results = self._index.get_nns_by_vector(
            _embedding,
            max_results,
        )

        return [self._items[i] for i in results]


class SentenceTransformerEmbeddingModel(EmbeddingModel):
    """
    Embedding model using sentence-transformers.

    Attributes:
        embedding_model (str): The name or path of the sentence-transformers model to use.

    Note:
        This class provides an embedding model based on sentence-transformers. It computes embeddings
        for text documents using the specified sentence-transformers model.

    Example:
        ```python
        # Create an instance of SentenceTransformerEmbeddingModel
        model = SentenceTransformerEmbeddingModel(embedding_model="bert-base-uncased")

        # Encode a list of documents into embeddings
        embeddings = model.encode(["Document 1", "Document 2"])
        ```
    """
    def __init__(self, embedding_model: str):
        from sentence_transformers import SentenceTransformer

        device = "cuda" if cuda.is_available() else "cpu"
        self.model = SentenceTransformer(embedding_model, device=device)
        # Get the embedding dimension of the model
        self.embedding_size = self.model.get_sentence_embedding_dimension()

    def encode(self, documents: List[str]) -> List[List[float]]:
        return self.model.encode(documents)


class OpenAIEmbeddingModel(EmbeddingModel):
    """
    Embedding model using OpenAI API.

    Attributes:
        embedding_model (str): The name or path of the OpenAI API model to use.

    Note:
        This class provides an embedding model based on the OpenAI API. It computes embeddings
        for text documents using the specified OpenAI API model.

    Example:
        ```python
        # Create an instance of OpenAIEmbeddingModel
        model = OpenAIEmbeddingModel(embedding_model="gpt-3.5-turbo")

        # Encode a list of documents into embeddings
        embeddings = model.encode(["Document 1", "Document 2"])
        ```
    """


    def __init__(self, embedding_model: str):
        self.model = embedding_model
        self.embedding_size = len(self.encode(["test"])[0])

    def encode(self, documents: List[str]) -> List[List[float]]:
        """Encode a list of documents into embeddings."""
        import openai

        # Make embedding request to OpenAI API
        res = openai.Embedding.create(input=documents, engine=self.model)
        embeddings = [record["embedding"] for record in res["data"]]
        return embeddings


def init_embedding_model(embedding_model: str, embedding_engine: str) -> EmbeddingModel:
    """
    Initialize the embedding model based on the specified engine.

    Args:
        embedding_model (str): The name or path of the embedding model to use.
        embedding_engine (str): The embedding engine to use.

    Returns:
        EmbeddingModel: An instance of the specified embedding model.

    Raises:
        ValueError: If the specified embedding engine is invalid.

    Example:
        ```python
        # Initialize an embedding model based on the engine
        model = init_embedding_model(embedding_model="bert-base-uncased", embedding_engine="SentenceTransformers")
        ```
    """    
    if embedding_engine == "SentenceTransformers":
        return SentenceTransformerEmbeddingModel(embedding_model)
    elif embedding_engine == "openai":
        return OpenAIEmbeddingModel(embedding_model)
    else:
        raise ValueError(f"Invalid embedding engine: {embedding_engine}")
