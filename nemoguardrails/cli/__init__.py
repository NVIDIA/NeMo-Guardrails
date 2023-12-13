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
import os
from typing import List, Optional

import typer
import uvicorn
from fastapi import FastAPI

from nemoguardrails.actions_server import actions_server
from nemoguardrails.cli.chat import run_chat
from nemoguardrails.eval.cli import evaluate
from nemoguardrails.logging.verbose import set_verbose
from nemoguardrails.server import api

app = typer.Typer()
app.add_typer(evaluate.app, name="evaluate", short_help="Run an evaluation task.")
app.pretty_exceptions_enable = False

logging.getLogger().setLevel(logging.WARNING)


@app.command()
def chat(
    config: List[str] = typer.Option(
        default=["config"],
        exists=True,
        help="Path to a directory containing configuration files to use. Can also point to a single configuration file.",
    ),
    verbose: bool = typer.Option(
        default=False,
        help="If the chat should be verbose and output the prompts",
    ),
    streaming: bool = typer.Option(
        default=False,
        help="If the chat should use the streaming mode, if possible.",
    ),
    server_url: Optional[str] = typer.Option(
        default=None,
        help="If specified, the chat CLI will interact with a server, rather than load the config. "
        "In this case, the --config-id must also be specified.",
    ),
    config_id: Optional[str] = typer.Option(
        default=None, help="The config_id to be used when interacting with the server."
    ),
):
    """Start an interactive chat session."""
    if verbose:
        set_verbose(True)

    if len(config) > 1:
        typer.secho(f"Multiple configurations are not supported.", fg=typer.colors.RED)
        typer.echo("Please provide a single folder.")
        raise typer.Exit(1)

    typer.echo("Starting the chat (Press Ctrl + C to quit) ...")
    run_chat(
        config_path=config[0],
        verbose=verbose,
        streaming=streaming,
        server_url=server_url,
        config_id=config_id,
    )


@app.command()
def server(
    port: int = typer.Option(
        default=8000, help="The port that the server should listen on. "
    ),
    config: List[str] = typer.Option(
        default=[],
        exists=True,
        help="Path to a directory containing multiple configuration sub-folders.",
    ),
    verbose: bool = typer.Option(
        default=False,
        help="If the server should be verbose and output detailed logs including prompts.",
    ),
    disable_chat_ui: bool = typer.Option(
        default=False,
        help="Weather the ChatUI should be disabled",
    ),
    auto_reload: bool = typer.Option(default=False, help="Enable auto reload option."),
    prefix: str = typer.Option(
        default="",
        help="A prefix that should be added to all server paths. Should start with '/'.",
    ),
):
    """Start a NeMo Guardrails server."""
    if config:
        api.app.rails_config_path = config[0]
    else:
        # If we don't have a config, we try to see if there is a local config folder
        local_path = os.getcwd()
        local_configs_path = os.path.join(local_path, "config")

        if os.path.exists(local_configs_path):
            api.app.rails_config_path = local_configs_path

    if verbose:
        logging.getLogger().setLevel(logging.INFO)

    if disable_chat_ui:
        api.app.disable_chat_ui = True

    if auto_reload:
        api.app.auto_reload = True

    if prefix:
        server_app = FastAPI()
        server_app.mount(prefix, api.app)
    else:
        server_app = api.app

    uvicorn.run(server_app, port=port, log_level="info", host="0.0.0.0")


@app.command("actions-server")
def action_server(
    port: int = typer.Option(
        default=8001, help="The port that the server should listen on. "
    ),
):
    """Start a NeMo Guardrails actions server."""

    uvicorn.run(actions_server.app, port=port, log_level="info", host="0.0.0.0")
