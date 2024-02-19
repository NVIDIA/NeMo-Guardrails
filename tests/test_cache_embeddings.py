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

import tempfile
import unittest
from typing import List
from unittest.mock import MagicMock, Mock, patch

import pytest

from nemoguardrails.embeddings.cache import (
    CacheStore,
    EmbeddingsCache,
    FilesystemCacheStore,
    HashKeyGenerator,
    InMemoryCacheStore,
    KeyGenerator,
    MD5KeyGenerator,
    RedisCacheStore,
    cache_embeddings,
)
from nemoguardrails.rails.llm.config import EmbeddingsCacheConfig


def test_key_generator_abstract_class():
    with pytest.raises(TypeError):
        KeyGenerator()


def test_cache_store_abstract_class():
    with pytest.raises(TypeError):
        CacheStore()


def test_hash_key_generator():
    key_gen = HashKeyGenerator()
    key = key_gen.generate_key("test")
    assert isinstance(key, str)


def test_md5_key_generator():
    key_gen = MD5KeyGenerator()
    key = key_gen.generate_key("test")
    assert isinstance(key, str)
    assert len(key) == 32  # MD5 hash is 32 characters long


def test_in_memory_cache_store():
    cache = InMemoryCacheStore()
    cache.set("key", "value")
    assert cache.get("key") == "value"
    cache.clear()
    assert cache.get("key") is None


def test_filesystem_cache_store():
    with tempfile.TemporaryDirectory() as temp_dir:
        cache = FilesystemCacheStore(cache_dir=temp_dir)
        cache.set("key", "value")
        assert cache.get("key") == "value"
        cache.clear()
        assert cache.get("key") is None


def test_redis_cache_store():
    pytest.importorskip("redis")
    mock_redis = MagicMock()
    cache = RedisCacheStore()
    cache._redis = mock_redis
    cache.set("key", "value")
    mock_redis.set.assert_called_once_with("key", "value")
    cache.get("key")
    mock_redis.get.assert_called_once_with("key")
    cache.clear()
    mock_redis.flushall.assert_called_once()


class TestEmbeddingsCache(unittest.TestCase):
    def setUp(self):
        self.cache_embeddings = EmbeddingsCache(
            key_generator=MD5KeyGenerator(), cache_store=FilesystemCacheStore()
        )

    @patch.object(FilesystemCacheStore, "set")
    @patch.object(MD5KeyGenerator, "generate_key", return_value="key")
    def test_cache_miss(self, mock_generate_key, mock_set):
        self.cache_embeddings.set("text", [0.1, 0.2, 0.3])
        mock_generate_key.assert_called_once_with("text")
        mock_set.assert_called_once_with("key", [0.1, 0.2, 0.3])

    @patch.object(FilesystemCacheStore, "get", return_value=[0.1, 0.2, 0.3])
    @patch.object(FilesystemCacheStore, "set")
    @patch.object(MD5KeyGenerator, "generate_key", return_value="key")
    def test_cache_hit(self, mock_generate_key, mock_set, mock_get):
        result = self.cache_embeddings.get("text")
        mock_generate_key.assert_called_once_with("text")
        mock_get.assert_called_once_with("key")
        self.assertEqual(result, [0.1, 0.2, 0.3])
        mock_set.assert_not_called()


class MyClass:
    @property
    def cache_config(self):
        return EmbeddingsCacheConfig()

    @cache_embeddings
    def get_embeddings(self, texts: List[str]) -> List[List[float]]:
        return [[float(ord(c)) for c in text] for text in texts]


async def test_cache_embeddings():
    with patch(
        "nemoguardrails.rails.llm.config.EmbeddingsCacheConfig"
    ) as MockConfig, patch(
        "nemoguardrails.embeddings.cache.EmbeddingsCache"
    ) as MockCache:
        mock_config = MockConfig.return_value
        mock_cache = MockCache.return_value
        my_class = MyClass()

        # Test when cache is not enabled
        mock_config.enabled = False
        texts = ["hello", "world"]
        assert await my_class.get_embeddings(texts) == [
            [104.0, 101.0, 108.0, 108.0, 111.0],
            [119.0, 111.0, 114.0, 108.0, 100.0],
        ]
        mock_cache.get.assert_not_called()
        mock_cache.set.assert_not_called()

        # Test when cache is enabled and all texts are cached
        mock_config.enabled = True
        mock_cache.get.return_value = {
            "hello": [104.0, 101.0, 108.0, 108.0, 111.0],
            "world": [119.0, 111.0, 114.0, 108.0, 100.0],
        }
        assert await my_class.get_embeddings(texts) == [
            [104.0, 101.0, 108.0, 108.0, 111.0],
            [119.0, 111.0, 114.0, 108.0, 100.0],
        ]
        mock_cache.get.assert_called_once_with(texts)
        mock_cache.set.assert_not_called()

        # Test when cache is enabled and some texts are not cached
        mock_cache.reset_mock()
        mock_cache.get.return_value = {"hello": [104.0, 101.0, 108.0, 108.0, 111.0]}
        assert await my_class.get_embeddings(texts) == [
            [104.0, 101.0, 108.0, 108.0, 111.0],
            [119.0, 111.0, 114.0, 108.0, 100.0],
        ]
        mock_cache.get.assert_called_once_with(texts)
        mock_cache.set.assert_called_once_with(
            ["world"], [[119.0, 111.0, 114.0, 108.0, 100.0]]
        )

        # Test when cache is enabled and no texts are cached
        mock_cache.reset_mock()
        mock_cache.get.return_value = {}
        assert my_class.get_embeddings(texts) == [
            [104.0, 101.0, 108.0, 108.0, 111.0],
            [119.0, 111.0, 114.0, 108.0, 100.0],
        ]
        mock_cache.set.assert_called_once_with(
            texts,
            [[104.0, 101.0, 108.0, 108.0, 111.0], [119.0, 111.0, 114.0, 108.0, 100.0]],
        )
