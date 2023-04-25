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

import logging
import os.path
from typing import List

from fastapi import FastAPI
from pydantic import BaseModel, Field
from starlette.staticfiles import StaticFiles

from nemoguardrails import LLMRails, RailsConfig

logging.basicConfig(level=logging.INFO)
log = logging.getLogger(__name__)

api_description = """Guardrails Sever API."""


app = FastAPI(
    title="Guardrails Server API",
    description=api_description,
    version="0.1.0",
    license_info={"name": "Apache License, Version 2.0"},
)


# By default, we use the rails in the examples folder
app.rails_config_path = os.path.join(os.path.dirname(__file__), "..", "..", "examples")


class RequestBody(BaseModel):
    config_id: str = Field(description="The id of the configuration to be used.")
    messages: List[dict] = Field(
        default=None, description="The list of messages in the current conversation."
    )


class ResponseBody(BaseModel):
    messages: List[dict] = Field(
        default=None, description="The new messages in the conversation"
    )


@app.get(
    "/v1/rails/configs",
    summary="Get List of available rails configurations.",
)
def get_rails_configs():
    """Returns the list of available rails configurations."""

    # We extract all folder names as config names
    config_ids = [
        f
        for f in os.listdir(app.rails_config_path)
        if os.path.isdir(os.path.join(app.rails_config_path, f))
        and f[0] != "."
        and f[0] != "_"
    ]

    return [{"id": config_id} for config_id in config_ids]


# One instance of LLMRails per config id
llm_rails_instances = {}


def _get_rails(config_id: str) -> LLMRails:
    """Returns the rails instance for the given config id."""
    if config_id in llm_rails_instances:
        return llm_rails_instances[config_id]

    rails_config = RailsConfig.from_path(os.path.join(app.rails_config_path, config_id))
    llm_rails = LLMRails(config=rails_config, verbose=True)
    llm_rails_instances[config_id] = llm_rails

    return llm_rails


@app.post(
    "/v1/chat/completions",
    response_model=ResponseBody,
)
async def chat_completion(body: RequestBody):
    """Chat completion for the provided conversation.

    TODO: add support for explicit state object.
    """
    log.info("Got request for config %s", body.config_id)

    config_id = body.config_id
    try:
        llm_rails = _get_rails(config_id)
    except ValueError:
        return {
            "messages": [
                {"role": "assistant", "content": "Invalid guardrails configuration."}
            ]
        }

    try:
        bot_message = await llm_rails.generate_async(messages=body.messages)
    except Exception as ex:
        log.exception(ex)
        return {
            "messages": [{"role": "assistant", "content": "Internal server error."}]
        }

    return {"messages": [bot_message]}


# Finally, we register the static frontend UI serving

FRONTEND_DIR = os.path.join(
    os.path.dirname(__file__), "..", "..", "chat-ui", "frontend"
)

app.mount(
    "/",
    StaticFiles(
        directory=FRONTEND_DIR,
        html=True,
    ),
    name="chat",
)
