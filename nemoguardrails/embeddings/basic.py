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
import asyncio
from typing import List

from annoy import AnnoyIndex
from torch import cuda

from nemoguardrails.embeddings.index import EmbeddingModel, EmbeddingsIndex, IndexItem


class BasicEmbeddingsIndex(EmbeddingsIndex):
    """Basic implementation of an embeddings index.

    It uses the `sentence-transformers/all-MiniLM-L6-v2` model to compute embeddings.
    Annoy is employed for efficient nearest-neighbor search.

    Attributes:
        embedding_model (str): The model for computing embeddings.
        embedding_engine (str): The engine for computing embeddings.
        embeddings_index (AnnoyIndex): The current embedding index.
        embedding_size (int): The size of the embeddings.
        embeddings (List[List[float]]): The computed embeddings.
    """

    def __init__(self, embedding_model=None, embedding_engine=None, index=None):
        """Initialize the BasicEmbeddingsIndex.

        Args:
            embedding_model (str, optional): The model for computing embeddings. Defaults to None.
            embedding_engine (str, optional): The engine for computing embeddings. Defaults to None.
            index (AnnoyIndex, optional): The pre-existing index. Defaults to None.
        """
        self._model = None
        self._items = []
        self._embeddings = []
        self.embedding_model = embedding_model
        self.embedding_engine = embedding_engine
        self._embedding_size = 0

        # When the index is provided, it means it's from the cache.
        self._index = index

        # Data structures for batching embedding requests
        self._req_queue = {}
        self._req_results = {}
        self._req_idx = 0
        self._current_batch_event = None

    @property
    def embeddings_index(self):
        """Get the current embedding index"""
        return self._index

    @property
    def embedding_size(self):
        """Get the size of the embeddings."""
        return self._embedding_size

    @property
    def embeddings(self):
        """Get the computed embeddings."""
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

    async def _get_embeddings(self, texts: List[str]) -> List[List[float]]:
        """Compute embeddings for a list of texts.

        Args:
            texts (List[str]): The list of texts to compute embeddings for.

        Returns:
            List[List[float]]: The computed embeddings.
        """
        if self._model is None:
            self._init_model()

        embeddings = self._model.encode(texts)
        return embeddings

    async def add_item(self, item: IndexItem):
        """Add a single item to the index.

        Args:
            item (IndexItem): The item to add to the index.
        """
        self._items.append(item)

        # If the index is already built, we skip this
        if self._index is None:
            await self._embeddings.append(self._get_embeddings([item.text])[0])

            # Update the embedding if it was not computed up to this point
            self._embedding_size = len(self._embeddings[0])

    async def add_items(self, items: List[IndexItem]):
        """Add multiple items to the index at once.

        Args:
            items (List[IndexItem]): The list of items to add to the index.
        """
        self._items.extend(items)

        # If the index is already built, we skip this
        if self._index is None:
            self._embeddings.extend(
                await self._get_embeddings([item.text for item in items])
            )

            # Update the embedding if it was not computed up to this point
            self._embedding_size = len(self._embeddings[0])

    async def build(self):
        """Builds the Annoy index."""
        self._index = AnnoyIndex(len(self._embeddings[0]), "angular")
        for i in range(len(self._embeddings)):
            self._index.add_item(i, self._embeddings[i])
        self._index.build(10)

    async def _run_batch(self):
        """Runs the current batch of embeddings."""

        # Wait up to 100ms for the batch to fill
        # TODO: add support to also trigger when a certain number of items is reached
        await asyncio.sleep(0.01)

        # Reset the batch event
        batch_event: asyncio.Event = self._current_batch_event
        self._current_batch_event = None

        # Create the actual batch to be send for computing
        batch = []
        batch_ids = list(self._req_queue.keys())
        for req_id in batch_ids:
            batch.append(self._req_queue[req_id])

        # Empty the queue up to this point
        self._req_queue = {}

        print(f"Running batch of length {len(batch)}")

        # Compute the embeddings
        embeddings = await self._get_embeddings(batch)
        for i in range(len(embeddings)):
            self._req_results[batch_ids[i]] = embeddings[i]

        # Signal that the batch has finished processing
        batch_event.set()

    async def _batch_get_embeddings(self, text: str) -> List[float]:
        req_id = self._req_idx
        self._req_idx += 1
        self._req_queue[req_id] = text

        if self._current_batch_event is None:
            self._current_batch_event = asyncio.Event()
            asyncio.ensure_future(self._run_batch())

        # Wait for the batch to finish
        await self._current_batch_event.wait()

        # Remove the result and return it
        result = self._req_results[req_id]
        del self._req_results[req_id]

        return result

    async def search(self, text: str, max_results: int = 20) -> List[IndexItem]:
        """Search the closest `max_results` items.

        Args:
            text (str): The text to search for.
            max_results (int, optional): The maximum number of results to return. Defaults to 20.

        Returns:
            List[IndexItem]: The closest items found.
        """
        _embedding = await self._batch_get_embeddings(text)
        # _embedding = (await self._get_embeddings([text]))[0]

        results = self._index.get_nns_by_vector(
            _embedding,
            max_results,
        )

        return [self._items[i] for i in results]


class SentenceTransformerEmbeddingModel(EmbeddingModel):
    """Embedding model using sentence-transformers.

    This class represents an embedding model that utilizes the sentence-transformers library
    for generating sentence embeddings.

    Args:
        embedding_model (str): The name or path of the pre-trained sentence-transformers model.

    Attributes:
        model: The sentence-transformers model used for encoding sentences.
        embedding_size: The dimensionality of the sentence embeddings generated by the model.
    """

    def __init__(self, embedding_model: str):
        from sentence_transformers import SentenceTransformer

        device = "cuda" if cuda.is_available() else "cpu"
        self.model = SentenceTransformer(embedding_model, device=device)
        # Get the embedding dimension of the model
        self.embedding_size = self.model.get_sentence_embedding_dimension()

    def encode(self, documents: List[str]) -> List[List[float]]:
        """Encode a list of documents into their corresponding sentence embeddings.

        Args:
            documents (List[str]): The list of documents to be encoded.

        Returns:
            List[List[float]]: The list of sentence embeddings, where each embedding is a list of floats.
        """
        return self.model.encode(documents)


class OpenAIEmbeddingModel(EmbeddingModel):
    """Embedding model using OpenAI API.

    Args:
        embedding_model (str): The name of the embedding model.

    Attributes:
        model (str): The name of the embedding model.
        embedding_size (int): The size of the embeddings.

    Methods:
        encode: Encode a list of documents into embeddings.

    """

    def __init__(self, embedding_model: str):
        self.model = embedding_model
        self.embedding_size = len(self.encode(["test"])[0])

    def encode(self, documents: List[str]) -> List[List[float]]:
        """Encode a list of documents into embeddings.

        Args:
            documents (List[str]): The list of documents to be encoded.

        Returns:
            List[List[float]]: The encoded embeddings.

        """
        import openai

        # Make embedding request to OpenAI API
        res = openai.Embedding.create(input=documents, engine=self.model)
        embeddings = [record["embedding"] for record in res["data"]]
        return embeddings


def init_embedding_model(embedding_model: str, embedding_engine: str) -> EmbeddingModel:
    """Initialize the embedding model.

    Args:
        embedding_model (str): The path or name of the embedding model.
        embedding_engine (str): The name of the embedding engine.

    Returns:
        EmbeddingModel: An instance of the initialized embedding model.

    Raises:
        ValueError: If the embedding engine is invalid.
    """
    if embedding_engine == "SentenceTransformers":
        return SentenceTransformerEmbeddingModel(embedding_model)
    elif embedding_engine == "openai":
        return OpenAIEmbeddingModel(embedding_model)
    else:
        raise ValueError(f"Invalid embedding engine: {embedding_engine}")
