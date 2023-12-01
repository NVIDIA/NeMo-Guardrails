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

import unittest
from unittest.mock import Mock, patch

from nemoguardrails.embeddings.cache import (
    FilesystemCacheStore,
    MD5KeyGenerator,
    cache_embeddings,
)


class TestCacheEmbeddings(unittest.TestCase):
    def setUp(self):
        self.mock_func = Mock(return_value=[[0.1, 0.2, 0.3]])
        self.decorated_func = cache_embeddings(self.mock_func)

    @patch.object(FilesystemCacheStore, "get", return_value=None)
    @patch.object(FilesystemCacheStore, "set")
    @patch.object(MD5KeyGenerator, "generate_key", return_value="key")
    def test_cache_miss(self, mock_generate_key, mock_set, mock_get):
        self.decorated_func(self, ["text"])
        mock_generate_key.assert_called_once_with("text")
        mock_get.assert_called_once_with("key")
        self.mock_func.assert_called_once_with(self, "text")
        mock_set.assert_called_once_with("key", [[0.1, 0.2, 0.3]])

    @patch.object(FilesystemCacheStore, "get", return_value=[[0.1, 0.2, 0.3]])
    @patch.object(FilesystemCacheStore, "set")
    @patch.object(MD5KeyGenerator, "generate_key", return_value="key")
    def test_cache_hit(self, mock_generate_key, mock_set, mock_get):
        self.decorated_func(self, ["text"])
        mock_generate_key.assert_called_once_with("text")
        mock_get.assert_called_once_with("key")
        self.mock_func.assert_not_called()
        mock_set.assert_not_called()
