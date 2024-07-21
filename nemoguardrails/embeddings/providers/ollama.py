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

from .base import EmbeddingModel


def get_executor():
    from . import embeddings_executor

    return embeddings_executor


class OllamaEmbeddingModel(EmbeddingModel):
    """Embedding model using Ollama.

    This class represents an embedding model that utilizes the Ollama
    for generating sentence embeddings.

    Args:
        embedding_model (str): The name of Ollama model pulled for embeddings.

    Attributes:
        model: The Ollama model used for encoding sentences.
        embedding_size: The dimensionality of the sentence embeddings generated by the model.
    """

    engine_name = "OllamaEmbed"

    def __init__(self,  embedding_model: str, base_url: str):
        try:
            from langchain_community.embeddings import OllamaEmbeddings
        except ImportError:
            raise ImportError(
                "Could not import langchain_community, please install it with "
                "`pip install langchain_community`."
            )

        self.model = OllamaEmbeddings( model=embedding_model, base_url=base_url )
        self.response = self.model.embed_query( 'The sky is blue because of rayleigh scattering')
        # Get the embedding dimension of the model
        self.embedding_size = len(self.response)

    async def encode_async(self, documents: List[str]) -> List[List[float]]:
        """Encode a list of documents into their corresponding sentence embeddings.

        Args:
            documents (List[str]): The list of documents to be encoded.

        Returns:
            List[List[float]]: The list of sentence embeddings, where each embedding is a list of floats.
        """
        loop = asyncio.get_running_loop()
        result = await loop.run_in_executor(
            get_executor(), self.model.embed_documents, documents
        )

        return result

    def encode(self, documents: List[str]) -> List[List[float]]:
        """Encode a list of documents into their corresponding sentence embeddings.

        Args:
            documents (List[str]): The list of documents to be encoded.

        Returns:
            List[List[float]]: The list of sentence embeddings, where each embedding is a list of floats.
        """
        return self.model.embed_documents(documents)
