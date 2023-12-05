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

import functools
import hashlib
import json
import logging
from abc import ABC, abstractmethod
from functools import singledispatchmethod
from pathlib import Path
from typing import List

log = logging.getLogger(__name__)


class KeyGenerator(ABC):
    """Abstract class for key generators."""

    @abstractmethod
    def generate_key(self, text):
        pass


class HashKeyGenerator(KeyGenerator):
    """Hash-based key generator."""

    def generate_key(self, text):
        return hash(text)


class MD5KeyGenerator(KeyGenerator):
    """MD5-based key generator."""

    def generate_key(self, text):
        return hashlib.md5(text.encode("utf-8")).hexdigest()


class CacheStore(ABC):
    """Abstract class for cache stores."""

    @abstractmethod
    def get(self, key):
        """Get a value from the cache."""
        pass

    @abstractmethod
    def set(self, key, value):
        """Set a value in the cache."""
        pass

    @abstractmethod
    def clear(self):
        """Clear the cache."""
        pass


class InMemoryCacheStore(CacheStore):
    """In-memory cache store.

    This cache store keeps the cache in memory. It does not persist the cache between runs.

    Example:
        >>> cache_store = InMemoryCacheStore()
        >>> cache_store.set('key', 'value')
        >>> print(cache_store.get('key'))  # Outputs: 'value'
        value
    """

    def __init__(self):
        self._cache = {}

    def get(self, key):
        return self._cache.get(key)

    def set(self, key, value):
        self._cache[key] = value

    def clear(self):
        self._cache = {}


class FilesystemCacheStore(CacheStore):
    """Filesystem cache store.

    This cache store persists the cache between runs by storing it in the filesystem as JSON files.

    Args:
        cache_dir (str, optional): The directory where the cache files will be stored. Defaults to "./cache".

    Example:
        >>> cache_store = FilesystemCacheStore(cache_dir='./cache')
        >>> cache_store.set('key', 'value')
        >>> print(cache_store.get('key'))
        value
    """

    def __init__(self, cache_dir: str = None):
        self._cache_dir = Path(cache_dir or "./cache")
        self._cache_dir.mkdir(parents=True, exist_ok=True)

    def _get_file_path(self, key):
        return self._cache_dir / str(key)

    def get(self, key):
        file_path = self._get_file_path(key)
        if file_path.exists():
            with open(file_path, "r") as file:
                return json.load(file)
        return None

    def set(self, key, value):
        file_path = self._get_file_path(key)
        with open(file_path, "w") as file:
            json.dump(value, file)

    def clear(self):
        for file_path in self._cache_dir.glob("*"):
            file_path.unlink()


class RedisCacheStore(CacheStore):
    """Redis cache store.

    This cache store keeps the cache in a Redis database. It can be used to share the cache between multiple machines.

    Args:
        redis_client (redis.Redis, optional): The Redis client to use. If not provided, a new client will be created.

    Example:
        >>> redis_client = redis.Redis(host='localhost', port=6379, db=0)
        >>> cache_store = RedisCacheStore(redis_client=redis_client)
        >>> cache_store.set('key', 'value')
        >>> print(cache_store.get('key'))
        value
    """

    def __init__(self, host: str = "localhost", port: int = 6379, db: int = 0):
        import redis

        self._redis = redis.Redis(host=host, port=port, db=db)

    def get(self, key):
        return self._redis.get(key)

    def set(self, key, value):
        self._redis.set(key, value)

    def clear(self):
        self._redis.flushall()


class CacheEmbeddings:
    def __init__(
        self, key_generator: KeyGenerator = None, cache_store: CacheStore = None
    ):
        self._key_generator = key_generator
        self._cache_store = cache_store

    @classmethod
    def from_dict(cls, d):
        key_generator = d.get("key_generator", MD5KeyGenerator())
        cache_store = d.get("cache_store", FilesystemCacheStore())
        return cls(key_generator=key_generator, cache_store=cache_store)

    @classmethod
    def from_config(cls, config):
        # config is of type EmbeddingSearchProvider
        return cls.from_dict(config.parameters)

    @singledispatchmethod
    def get(self, texts):
        raise NotImplementedError

    @get.register
    def _(self, text: str):
        key = self._key_generator.generate_key(text)
        log.info(f"Fetching key {key} for text '{text[:10]}...' from cache")

        result = self._cache_store.get(key)

        return result

    @get.register
    def _(self, texts: list):
        cached = {}

        for text in texts:
            result = self.get(text)
            if result is not None:
                cached[text] = result

        if len(cached) != len(texts):
            log.info(f"Cache hit rate: {len(cached) / len(texts)}")

        return cached

    @singledispatchmethod
    def set(self, texts):
        raise NotImplementedError

    @set.register
    def _(self, text: str, value: List[float]):
        key = self._key_generator.generate_key(text)
        log.info(f"Cache miss for text '{text}'. Storing key {key} in cache.")
        self._cache_store.set(key, value)

    @set.register
    def _(self, texts: list, values: List[List[float]]):
        for text, value in zip(texts, values):
            self.set(text, value)

    def clear(self):
        self._cache_store.clear()


def cache_embeddings(func):
    """
    Decorator to cache the embeddings.

    This decorator caches the embeddings in the cache store.
    It uses the key generator to generate the key for the cache.

    If the class does not have a `key_generator` attribute, it will use the `MD5KeyGenerator`.
    If the class does not have a `cache_store` attribute, it will use the `FilesystemCacheStore`.
    If the class does not have a `use_cache` attribute, it defaults to True.
    This decorator can be applied to any function that accepts a list of strings and returns a list of lists of floats.

    Args:
        func (Callable[[List[str]], List[List[float]]]): The function to decorate.

    Returns:
        Callable[[List[str]], List[List[float]]]: The decorated function.

    Example:
        @cache_embeddings
        def get_embeddings(texts: List[str]) -> List[List[float]]:
            # implementation here
            pass
    """

    @functools.wraps(func)
    def wrapper_decorator(self, texts):
        results = []

        if not (hasattr(self, "cache_embeddings") and self.cache_embeddings):
            self.cache_embeddings = CacheEmbeddings(
                key_generator=MD5KeyGenerator(), cache_store=FilesystemCacheStore()
            )

        if not hasattr(self, "use_cache"):
            self.use_cache = True

        if not self.use_cache:
            # if `use_cache` is False, then compute embeddings for the whole input
            return func(self, texts)

        cached_texts = {}
        uncached_texts = []

        cached_texts = self.cache_embeddings.get(texts)
        uncached_texts = [text for text in texts if text not in cached_texts]

        # Only call func for uncached texts
        if uncached_texts:
            uncached_results = func(self, uncached_texts)
            self.cache_embeddings.set(uncached_texts, uncached_results)

        cached_texts.update(self.cache_embeddings.get(uncached_texts))
        # Reorder results to match the order of the input texts,
        results = [cached_texts.get(text) for text in texts]
        return results

    return wrapper_decorator
