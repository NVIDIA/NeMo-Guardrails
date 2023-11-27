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

import hashlib
import logging
import os
from time import time
from typing import Callable, List, Optional, cast

from annoy import AnnoyIndex

from nemoguardrails.embeddings.index import EmbeddingsIndex, IndexItem
from nemoguardrails.kb.utils import split_markdown_in_topic_chunks
from nemoguardrails.rails.llm.config import EmbeddingSearchProvider, KnowledgeBaseConfig

log = logging.getLogger(__name__)

CACHE_FOLDER = os.path.join(os.getcwd(), ".cache")


class KnowledgeBase:
    """
    Basic implementation of a knowledge base.

    This class allows you to initialize, build, and search for relevant chunks of information
    within a collection of documents.

    Usage:
    ```python
    kb = KnowledgeBase(documents, config, get_embedding_search_provider_instance)
    kb.init()  # Initialize the knowledge base
    await kb.build()  # Build the knowledge base index
    results = await kb.search_relevant_chunks(query_text, max_results)
    ```

    Args:
    - documents (List[str]): A list of documents in markdown format.
    - config (KnowledgeBaseConfig): Configuration for the knowledge base.
    - get_embedding_search_provider_instance (Callable): A function to get an instance of
      the embedding search provider.

    Attributes:
    - documents (List[str]): The list of documents.
    - chunks (List[dict]): The topic chunks extracted from the documents.
    - index: The knowledge base index.
    - config (KnowledgeBaseConfig): Configuration for the knowledge base.
    - _get_embeddings_search_instance (Callable): Function to get the embedding search provider instance.

    Methods:
    - init(): Initialize the knowledge base by splitting documents into topic chunks.
    - build(): Build the knowledge base index.
    - search_relevant_chunks(text, max_results): Search for relevant chunks based on a query text.

    Note: This is a simplified implementation and may not cover all use cases.
    """

    def __init__(
        self,
        documents: List[str],
        config: KnowledgeBaseConfig,
        get_embedding_search_provider_instance: Callable[
            [Optional[EmbeddingSearchProvider]], EmbeddingsIndex
        ],
    ):
        self.documents = documents
        self.chunks = []
        self.index = None
        self.config = config
        self._get_embeddings_search_instance = get_embedding_search_provider_instance

    def init(self):
        """Initialize the knowledge base.

        The initial data is loaded from the `$kb_docs` context key. The key is populated when
        the model is loaded. Currently, only markdown format is supported.
        """
        if not self.documents:
            return

        # Start splitting every doc into topic chunks

        for doc in self.documents:
            chunks = split_markdown_in_topic_chunks(doc)
            self.chunks.extend(chunks)

    async def build(self):
        """Builds the knowledge base index."""
        t0 = time()
        index_items = []
        all_text_items = []
        for chunk in self.chunks:
            text = f"# {chunk['title']}\n\n{chunk['body'].strip()}"
            all_text_items.append(text)

            index_items.append(IndexItem(text=text, meta=chunk))

        # Stop if there are no items
        if not index_items:
            return

        # We compute the md5
        md5_hash = hashlib.md5("".join(all_text_items).encode("utf-8")).hexdigest()
        cache_file = os.path.join(CACHE_FOLDER, f"{md5_hash}.ann")
        embedding_size_file = os.path.join(CACHE_FOLDER, f"{md5_hash}.esize")

        # If we have already computed this before, we use it
        if (
            self.config.embedding_search_provider.name == "default"
            and os.path.exists(cache_file)
            and os.path.exists(embedding_size_file)
        ):
            from nemoguardrails.embeddings.basic import BasicEmbeddingsIndex

            log.info(cache_file)
            self.index = cast(
                BasicEmbeddingsIndex,
                self._get_embeddings_search_instance(
                    self.config.embedding_search_provider
                ),
            )

            with open(embedding_size_file, "r") as f:
                embedding_size = int(f.read())

            ann_index = AnnoyIndex(embedding_size, "angular")
            ann_index.load(cache_file)

            self.index.embeddings_index = ann_index

            await self.index.add_items(index_items)
        else:
            self.index = self._get_embeddings_search_instance(
                self.config.embedding_search_provider
            )
            await self.index.add_items(index_items)
            await self.index.build()

            # For the default Embedding Search provider, which uses annoy, we also
            # persist the index after it's computed.
            if self.config.embedding_search_provider.name == "default":
                from nemoguardrails.embeddings.basic import BasicEmbeddingsIndex

                # We also save the file for future use
                os.makedirs(CACHE_FOLDER, exist_ok=True)
                basic_index = cast(BasicEmbeddingsIndex, self.index)
                basic_index.embeddings_index.save(cache_file)

                # And, explicitly save the size as we need it when we reload
                with open(embedding_size_file, "w") as f:
                    f.write(str(basic_index.embedding_size))

        log.info(f"Building the Knowledge Base index took {time() - t0} seconds.")

    async def search_relevant_chunks(self, text, max_results: int = 3):
        """Search the index for the most relevant chunks."""
        if self.index is None:
            return []

        results = await self.index.search(text, max_results=max_results)

        # Return the chunks directly
        return [result.meta for result in results]
