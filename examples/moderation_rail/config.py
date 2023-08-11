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

import uuid
from typing import List
from urllib.parse import urljoin

import requests

from nemoguardrails.kb.index import EmbeddingsIndex, IndexItem
from nemoguardrails.rails.llm.llmrails import LLMRails


class NLPServer(EmbeddingsIndex):
    url: str = "http://localhost:9000/"
    create_store: str = "/nlp/embedding_search/create_store"
    search_path: str = "/nlp/embedding_search/search"

    def __init__(self, model: str = ""):
        self.model = model
        self.uuid: str = f"a{uuid.uuid4()}".replace("-", "")
        print("UUID: ", self.uuid)

    def add_item(self, item: IndexItem):
        """Adds a new item to the index."""

        print("Add item Model Name: ", self.model)

    def add_items(self, item: List[IndexItem]):
        """Adds multiple items to the index."""
        anchors = []
        for i in item:
            # We index on the full body for now
            anchors.append({"text": i.text, "metadata": i.meta})

        request = {
            "anchors": anchors,
            "store_name": self.uuid,
            "model_name": self.model,
        }

        url = urljoin(self.url, self.create_store)
        # print("Add items: ", url)
        try:
            resp = requests.post(f"{url}", json=request)
            # with requests.Session() as session:
            #     # Create store name and generate embeddings for anchors
            #     resp = session.post(
            #         url,
            #         json=request,
            #     )
            #     resp.raise_for_status()
            resp.raise_for_status()

        except Exception as e:
            print(f"Request to {url} failed with exception {e}")

        # print("Add items multiple: ", self.model)
        # print(self.url, self.create_store, self.search_path, self.uuid)

    def build(self):
        """Build the index, after the items are added.

        This is optional, might not be needed for all implementations."""
        print("Build Index and model name : ", self.model)
        pass

    def search(self, text: str, max_results: int) -> List[IndexItem]:
        """Searches the index for the closes matches to the provided text."""
        print("Search items here wooo: ", self.model)
        url = urljoin(self.url, self.search_path)

        request = {
            "query": text,
            "top_k": max_results,
            "embedding_stores": [self.uuid],
            "model_name": self.model,
            "model_version": "",
        }
        try:
            print(f"resp = requests.post({url}, json={request})")
            resp = requests.post(f"{url}", json=request)
            # with requests.Session() as session:
            #     resp = session.post(
            #         url,
            #         json=request,
            #     )
            #     print("Result: ", resp)
            #     response = resp.json()
            # async with aiohttp.ClientSession() as session:
            #     async with session.post(url, json=request) as resp:
            #         response = resp
            #         response_json = await resp.json()
            print(resp)
            print(resp.reason)
        except Exception as e:
            print(f"Request to {url} failed with exception {e}")
            return []

        # if resp.status != 200:
        #     print(f"Request to {url} failed with error {resp.reason}")
        #     return []

        result = []
        for r in resp.get("results", []):
            result.append(IndexItem(text=r.get("text"), meta=r.get("metadata")))
        return result


LLMRails.register_embedding_search_provider("nlp-server", NLPServer)
