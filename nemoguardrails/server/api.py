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
import time
from typing import List, Optional

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from starlette import status
from starlette.responses import JSONResponse, StreamingResponse
from starlette.staticfiles import StaticFiles

from nemoguardrails import LLMRails, RailsConfig
from nemoguardrails.streaming import StreamingHandler

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
app.rails_config_path = os.path.join(
    os.path.dirname(__file__), "..", "..", "examples", "bots"
)

# Weather the chat UI is enabled or not.
app.disable_chat_ui = False

# auto reload flag
app.auto_reload = False

# stop signal for observer
app.stop_signal = False


class RequestBody(BaseModel):
    config_id: str = Field(description="The id of the configuration to be used.")
    messages: List[dict] = Field(
        default=None, description="The list of messages in the current conversation."
    )
    context: Optional[dict] = Field(
        default=None,
        description="Additional context data to be added to the conversation.",
    )
    stream: Optional[bool] = Field(
        default=False,
        description="If set, partial message deltas will be sent, like in ChatGPT. "
        "Tokens will be sent as data-only server-sent events as they become "
        "available, with the stream terminated by a data: [DONE] message.",
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
llm_rails_events_history_cache = {}


def _get_rails(config_id: str) -> LLMRails:
    """Returns the rails instance for the given config id."""

    if config_id in llm_rails_instances:
        return llm_rails_instances[config_id]

    rails_config = RailsConfig.from_path(os.path.join(app.rails_config_path, config_id))
    llm_rails = LLMRails(config=rails_config, verbose=True)
    llm_rails_instances[config_id] = llm_rails

    # If we have a cache for the events, we restore it
    llm_rails.events_history_cache = llm_rails_events_history_cache.get(config_id, {})

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
        messages = body.messages
        if body.context:
            messages.insert(0, {"role": "context", "content": body.context})

        if (
            body.stream
            and llm_rails.config.streaming_supported
            and llm_rails.main_llm_supports_streaming
        ):
            # Create the streaming handler instance
            streaming_handler = StreamingHandler()

            # Start the generation
            asyncio.create_task(
                llm_rails.generate_async(
                    messages=messages, streaming_handler=streaming_handler
                )
            )

            return StreamingResponse(streaming_handler)
        else:
            bot_message = await llm_rails.generate_async(messages=messages)
            return {"messages": [bot_message]}

    except Exception as ex:
        log.exception(ex)
        return {
            "messages": [{"role": "assistant", "content": "Internal server error."}]
        }


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

    if app.auto_reload:
        app.loop = asyncio.get_running_loop()
        app.task = app.loop.run_in_executor(None, start_auto_reload_monitoring)


def register_logger(logger: callable):
    """Register an additional logger"""
    registered_loggers.append(logger)


@app.on_event("shutdown")
def shutdown_observer():
    if app.auto_reload:
        app.stop_signal = True
        if hasattr(app, "task"):
            app.task.cancel()
        log.info("Shutting down file observer")
    else:
        pass


def start_auto_reload_monitoring():
    """Start a thread that monitors the config folder for changes."""
    try:
        from watchdog.events import FileSystemEventHandler
        from watchdog.observers import Observer

        class Handler(FileSystemEventHandler):
            @staticmethod
            def on_any_event(event):
                if event.is_directory:
                    return None

                elif event.event_type == "created" or event.event_type == "modified":
                    log.info(
                        f"Watchdog received {event.event_type} event for file {event.src_path}"
                    )

                    # Compute the relative path
                    rel_path = os.path.relpath(event.src_path, app.rails_config_path)

                    # The config_id is the first component
                    parts = rel_path.split(os.path.sep)
                    config_id = parts[0]

                    if (
                        not parts[-1].startswith(".")
                        and ".ipynb_checkpoints" not in parts
                        and os.path.isfile(event.src_path)
                    ):
                        # We just remove the config from the cache so that a new one is used next time
                        if config_id in llm_rails_instances:
                            instance = llm_rails_instances[config_id]
                            del llm_rails_instances[config_id]
                            if instance:
                                # We save the events history cache, to restore it on the new instance
                                llm_rails_events_history_cache[
                                    config_id
                                ] = instance.events_history_cache

                            log.info(
                                f"Configuration {config_id} has changed. Clearing cache."
                            )

        observer = Observer()
        event_handler = Handler()
        observer.schedule(event_handler, app.rails_config_path, recursive=True)
        observer.start()
        try:
            while not app.stop_signal:
                time.sleep(5)
        finally:
            observer.stop()
            observer.join()

    except ImportError:
        # Since this is running in a separate thread, we just print the error.
        print(
            "The auto-reload feature requires `watchdog`. "
            "Please install using `pip install watchdog`."
        )
        # Force close everything.
        os._exit(-1)


# Register a nicer error message for 422 error
def register_exception(app: FastAPI):
    @app.exception_handler(RequestValidationError)
    async def validation_exception_handler(
        request: Request, exc: RequestValidationError
    ):
        exc_str = f"{exc}".replace("\n", " ").replace("   ", " ")
        # or logger.error(f'{exc}')
        log.error(request, exc_str)
        content = {"status_code": 10422, "message": exc_str, "data": None}
        return JSONResponse(
            content=content, status_code=status.HTTP_422_UNPROCESSABLE_ENTITY
        )


register_exception(app)
