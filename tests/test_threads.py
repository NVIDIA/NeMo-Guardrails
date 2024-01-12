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
import os

import pytest
from fastapi.testclient import TestClient

from nemoguardrails.server import api
from nemoguardrails.server.api import register_datastore
from nemoguardrails.server.datastore.memory_store import MemoryStore

register_datastore(MemoryStore())
api.app.rails_config_path = os.path.join(
    os.path.dirname(__file__), "test_configs", "simple_server"
)
client = TestClient(api.app)


def test_get():
    response = client.get("/v1/rails/configs")
    assert response.status_code == 200

    # Check that we have at least one config
    result = response.json()
    assert len(result) > 0


def test_1():
    response = client.post(
        "/v1/chat/completions",
        json={
            "config_id": "config_1",
            "thread_id": "as9d8f7s9d8f7a9s8df79asdf879",
            "messages": [
                {
                    "content": "hi",
                    "role": "user",
                }
            ],
        },
    )
    assert response.status_code == 200
    res = response.json()
    assert len(res["messages"]) == 1
    assert res["messages"][0]["content"] == "Hello!"

    # When making a second call with the same thread_id, the conversations should continue
    # and we should get the "Hello again!" message.
    response = client.post(
        "/v1/chat/completions",
        json={
            "config_id": "config_1",
            "thread_id": "as9d8f7s9d8f7a9s8df79asdf879",
            "messages": [
                {
                    "content": "hi",
                    "role": "user",
                }
            ],
        },
    )
    res = response.json()
    assert res["messages"][0]["content"] == "Hello again!"


def test_invalid_thread_id():
    response = client.post(
        "/v1/chat/completions",
        json={
            "config_id": "config_1",
            "thread_id": "abcd",
            "messages": [
                {
                    "content": "hi",
                    "role": "user",
                }
            ],
        },
    )
    assert response.status_code == 200
    res = response.json()
    assert len(res["messages"]) == 1
    assert "minimum length of 16" in res["messages"][0]["content"]


@pytest.mark.skip(reason="Should only be run locally when Redis is available.")
def test_with_redis():
    from nemoguardrails.server.datastore.redis_store import RedisStore

    register_datastore(RedisStore("redis://localhost/1"))
    response = client.post(
        "/v1/chat/completions",
        json={
            "config_id": "config_1",
            "thread_id": "as9d8f7s9d8f7a9s8df79asdf879",
            "messages": [
                {
                    "content": "hi",
                    "role": "user",
                }
            ],
        },
    )
    assert response.status_code == 200
    res = response.json()
    assert len(res["messages"]) == 1
    assert res["messages"][0]["content"] == "Hello!"

    # Because of an issue with aiohttp and how the TestClient closes the event loop,
    # We have to register this again here to make the test work.
    register_datastore(RedisStore("redis://localhost/1"))

    # When making a second call with the same thread_id, the conversations should continue
    # and we should get the "Hello again!" message.
    response = client.post(
        "/v1/chat/completions",
        json={
            "config_id": "config_1",
            "thread_id": "as9d8f7s9d8f7a9s8df79asdf879",
            "messages": [
                {
                    "content": "hi",
                    "role": "user",
                }
            ],
        },
    )
    res = response.json()
    assert res["messages"][0]["content"] == "Hello again!"
