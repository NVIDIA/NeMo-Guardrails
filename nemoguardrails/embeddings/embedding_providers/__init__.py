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

# This is the executor that will be used for computing the embeddings.
# Currently, we leave this as None, to use the default executor from asyncio.
# In the future, we might want to customize.
embeddings_executor = None

# The cache for embedding models, to make sure they are singleton.
_embedding_model_cache = {}


class EmbeddingModel:
    """Generic interface for an embedding model.

    The embedding model is responsible for creating the embeddings given a list of
    input texts."""

    async def encode_async(self, documents: List[str]) -> List[List[float]]:
        """Encode the provided documents into embeddings.

        Args:
            documents (List[str]): The list of documents for which embeddings should be created.

        Returns:
            List[List[float]]: The list of embeddings corresponding to the input documents.
        """
        raise NotImplementedError()

    def encode(self, documents: List[str]) -> List[List[float]]:
        """Encode the provided documents into embeddings.

        Args:
            documents (List[str]): The list of documents for which embeddings should be created.

        Returns:
            List[List[float]]: The list of embeddings corresponding to the input documents.
        """
        raise NotImplementedError()


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
    model_key = f"{embedding_engine}-{embedding_model}"

    if model_key not in _embedding_model_cache:
        if embedding_engine == "SentenceTransformers":
            from .sentence_transformers import SentenceTransformerEmbeddingModel

            model = SentenceTransformerEmbeddingModel(embedding_model)

        elif embedding_engine == "FastEmbed":
            from .fastembed import FastEmbedEmbeddingModel

            model = FastEmbedEmbeddingModel(embedding_model)

        elif embedding_engine == "openai":
            from .openai import OpenAIEmbeddingModel

            model = OpenAIEmbeddingModel(embedding_model)

        else:
            raise ValueError(f"Invalid embedding engine: {embedding_engine}")

        _embedding_model_cache[model_key] = model

    return _embedding_model_cache[model_key]
