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


from __future__ import annotations

from typing import Optional, Type

from . import fastembed, nim, openai, sentence_transformers, ollama
from .base import EmbeddingModel
from .registry import EmbeddingProviderRegistry

import inspect

# This is the executor that will be used for computing the embeddings.
# Currently, we leave this as None, to use the default executor from asyncio.
# In the future, we might want to customize.

embeddings_executor = None


def register_embedding_provider(
    model: Type[EmbeddingModel], engine_name: Optional[str] = None
):
    """Register an embedding provider.

    Args:
        model (Type[EmbeddingModel]): The embedding model class.
        engine_name (str): The name of the embedding engine.

    Raises:
        ValueError: If the engine name is not provided and the model does not have an engine name.
        TypeError: If the model is not an instance of `EmbeddingModel`.
        ValueError: If the model does not have 'encode' or 'encode_async' methods.
    """

    if not engine_name:
        engine_name = model.engine_name

    if not engine_name:
        raise ValueError(
            "The engine name must be provided either in the model or as an argument."
        )

    registry = EmbeddingProviderRegistry()
    registry.add(engine_name, model)
    print(f"\n**************AM i Here  {engine_name}***********")


# The cache for embedding models, to make sure they are singleton.
_embedding_model_cache = {}


# Add all the implemented embedding providers to the registry.
# As we are not using the `Registered` class, we need to manually register the providers.

register_embedding_provider(fastembed.FastEmbedEmbeddingModel)
register_embedding_provider(openai.OpenAIEmbeddingModel)
register_embedding_provider(sentence_transformers.SentenceTransformerEmbeddingModel)
register_embedding_provider(nim.NIMEmbeddingModel)
register_embedding_provider(nim.NVIDIAAIEndpointsEmbeddingModel)
register_embedding_provider(ollama.OllamaEmbeddingModel)

def init_embedding_model(embedding_model: str, embedding_engine: str, base_url: str) -> EmbeddingModel:
    """Initialize the embedding model.

    Args:
        embedding_model (str): The path or name of the embedding model.
        embedding_engine (str): The name of the embedding engine.
        base_url (str): Base url the model is hosted under.

    Returns:
        EmbeddingModel: An instance of the initialized embedding model.

    Raises:
        ValueError: If the embedding engine is invalid.
    """

    model_key = f"{embedding_engine}-{embedding_model}"

    if model_key not in _embedding_model_cache:

        embedding_engine = EmbeddingProviderRegistry().get(embedding_engine)

        if "base_url" in inspect.signature(embedding_engine.__init__).parameters:
            model = embedding_engine(embedding_model, base_url)
        else:
            model = embedding_engine(embedding_model)

        _embedding_model_cache[model_key] = model

    return _embedding_model_cache[model_key]
