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
from abc import ABC, abstractmethod
from pathlib import Path

# NOTE: on KeyGenerator
# The benefit of this approach is that it allows us to incorporate preprocessing logic directly into the caching layer.
# For instance, we can handle variations in input such as "adding programmable guardrails" and "adding    programmable guardrails" in a consistent manner.
# Alternatively, instead of using a class, we could simplify the design by passing a callable function directly to the caching layer.


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


def cache_embeddings(func):
    """
    Decorator to cache the embeddings.

    This decorator caches the embeddings in the cache store.
    It uses the key generator to generate the key for the cache.

    If the class does not have a `key_generator` attribute, it will use the `MD5KeyGenerator`.
    If the class does not have a `cache_store` attribute, it will use the `FilesystemCacheStore`.

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

        if not hasattr(self, "key_generator"):
            self.key_generator = MD5KeyGenerator()
        if not hasattr(self, "cache_store"):
            self.cache_store = FilesystemCacheStore()

        for text in texts:
            key = self.key_generator.generate_key(text)
            result = self.cache_store.get(key)
            if result is None:
                print("Does not exist in the cache")
                result = func(self, text)
                self.cache_store.set(key, result)
            else:
                print("Fetching from the cache")
            results.append(result[0])
        return results

    return wrapper_decorator
