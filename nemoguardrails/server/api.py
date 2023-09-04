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
import contextvars
import importlib.util
import json
import logging
import os.path
from typing import List

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from starlette.staticfiles import StaticFiles

from nemoguardrails import LLMRails, RailsConfig

logging.basicConfig(level=logging.INFO)
log = logging.getLogger(__name__)

# The list of registered loggers. Can be used to send logs to various
# backends and storage engines.
registered_loggers = []

api_description = """Guardrails Sever API."""

# The headers for each request
api_request_headers = contextvars.ContextVar("headers")


app = FastAPI(
    title="Guardrails Server API",
    description=api_description,
    version="0.1.0",
    license_info={"name": "Apache License, Version 2.0"},
)

ENABLE_CORS = os.getenv("NEMO_GUARDRAILS_SERVER_ENABLE_CORS", "false").lower() == "true"
ALLOWED_ORIGINS = os.getenv("NEMO_GUARDRAILS_SERVER_ALLOWED_ORIGINS", "*")

if ENABLE_CORS:
    # Split origins by comma
    origins = ALLOWED_ORIGINS.split(",")

    log.info(f"CORS enabled with the following origins: {origins}")

    app.add_middleware(
        CORSMiddleware,
        allow_origins=origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

# By default, we use the rails in the examples folder
app.rails_config_path = os.path.join(os.path.dirname(__file__), "..", "..", "examples")

# Weather the chat UI is enabled or not.
app.disable_chat_ui = False


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
async def get_rails_configs():
    """Returns the list of available rails configurations."""

    # We extract all folder names as config names
    config_ids = [
        f
        for f in os.listdir(app.rails_config_path)
        if os.path.isdir(os.path.join(app.rails_config_path, f))
        and f[0] != "."
        and f[0] != "_"
        # We filter out all the configs for which there is no `config.yml` file.
        and (
            os.path.exists(os.path.join(app.rails_config_path, f, "config.yml"))
            or os.path.exists(os.path.join(app.rails_config_path, f, "config.yaml"))
        )
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
async def chat_completion(body: RequestBody, request: Request):
    """Chat completion for the provided conversation.

    TODO: add support for explicit state object.
    """
    log.info("Got request for config %s", body.config_id)
    for logger in registered_loggers:
        asyncio.get_event_loop().create_task(
            logger({"endpoint": "/v1/chat/completions", "body": body.json()})
        )

    # Save the request headers in a context variable.
    api_request_headers.set(request.headers)

    config_id = body.config_id
    try:
        llm_rails = _get_rails(config_id)
    except ValueError as ex:
        return {
            "messages": [
                {
                    "role": "assistant",
                    "content": f"Could not load the {config_id} guardrails configuration: {str(ex)}",
                }
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


# By default, there are no challenges
challenges = []


def register_challenges(additional_challenges: List[dict]):
    """Register additional challenges

    Args:
        additional_challenges: The new challenges to be registered.
    """
    challenges.extend(additional_challenges)


@app.get(
    "/v1/challenges",
    summary="Get list of available challenges.",
)
async def get_challenges():
    """Returns the list of available challenges for red teaming."""

    return challenges


@app.on_event("startup")
async def startup_event():
    """Register any additional challenges, if available at startup."""
    challenges_files = os.path.join(app.rails_config_path, "challenges.json")

    if os.path.exists(challenges_files):
        with open(challenges_files) as f:
            register_challenges(json.load(f))

    # Finally, check if we have a config.py for the server configuration
    filepath = os.path.join(app.rails_config_path, "config.py")
    if os.path.exists(filepath):
        filename = os.path.basename(filepath)
        spec = importlib.util.spec_from_file_location(filename, filepath)
        config_module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(config_module)

    # Finally, we register the static frontend UI serving

    if not app.disable_chat_ui:
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
    else:

        @app.get("/")
        async def root_handler():
            return {"status": "ok"}


def register_logger(logger: callable):
    """Register an additional logger"""
    registered_loggers.append(logger)
