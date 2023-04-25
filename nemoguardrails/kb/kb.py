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
from typing import List

from annoy import AnnoyIndex

from nemoguardrails.kb.basic import BasicEmbeddingsIndex
from nemoguardrails.kb.index import IndexItem
from nemoguardrails.kb.utils import split_markdown_in_topic_chunks

log = logging.getLogger(__name__)

CACHE_FOLDER = os.path.join(os.getcwd(), ".cache")


class KnowledgeBase:
    """Basic implementation of a knowledge base."""

    def __init__(self, documents: List[str]):
        self.documents = documents
        self.chunks = []
        self.index = None

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

    def build(self):
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

        # If we have already computed this before, we use it
        if os.path.exists(cache_file):
            # TODO: this should not be hardcoded. Currently set for all-MiniLM-L6-v2.
            embedding_size = 384
            ann_index = AnnoyIndex(embedding_size, "angular")
            ann_index.load(cache_file)

            self.index = BasicEmbeddingsIndex(index=ann_index)
            self.index.add_items(index_items)
        else:
            self.index = BasicEmbeddingsIndex()
            self.index.add_items(index_items)
            self.index.build()

            # We also save the file for future use
            os.makedirs(CACHE_FOLDER, exist_ok=True)
            self.index.embeddings_index.save(cache_file)

        log.info(f"Building the Knowledge Base index took {time() - t0} seconds.")

    def search_relevant_chunks(self, text, max_results: int = 3):
        """Search the index for the most relevant chunks."""
        if self.index is None:
            return []

        results = self.index.search(text, max_results=max_results)

        # Return the chunks directly
        return [result.meta for result in results]
