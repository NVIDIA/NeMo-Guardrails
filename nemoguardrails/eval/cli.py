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
import logging
import os
import sys
from typing import List

import typer
from langchain_community.cache import SQLiteCache
from langchain_core.globals import set_llm_cache

from nemoguardrails.eval import check
from nemoguardrails.eval.check import LLMJudgeComplianceChecker
from nemoguardrails.eval.eval import run_eval
from nemoguardrails.eval.utils import get_output_paths
from nemoguardrails.evaluate.cli import evaluate
from nemoguardrails.utils import console

app = typer.Typer()
app.add_typer(evaluate.app, name="rail", short_help="Run a rail evaluation task.")

logging.getLogger().setLevel(logging.WARNING)


@app.command()
def run(
    eval_config_path: str = typer.Option(
        default="config",
        exists=True,
        help="Path to a directory containing eval configuration files. "
        "Defaults to the `config` folder in the current folder.",
    ),
    guardrail_config_path: str = typer.Option(
        exists=True,
        help="Path to a directory containing guardrail configuration files.",
    ),
    output_path: str = typer.Option(
        default="",
        help="Output directory for the results. "
        "Defaults to a folder in the current directory with the same name as the guardrail configuration.",
    ),
):
    """Run an evaluation."""
    eval_config_path = os.path.abspath(eval_config_path)
    if output_path == "":
        output_path = os.path.abspath(os.path.basename(guardrail_config_path))

    console.print(f"Loading eval configuration from {eval_config_path}.")
    console.print(f"Starting the evaluation for {guardrail_config_path}.")
    console.print(f"Writing results to {output_path}.")

    run_eval(
        eval_config_path=eval_config_path,
        guardrail_config_path=guardrail_config_path,
        output_path=output_path,
    )


def _launch_ui(script: str, port: int = 8501):
    """Helper to launch a Streamlit UI."""
    try:
        from streamlit.web import cli
    except ImportError:
        console.print("[red]Could not import Streamlit.[/]")
        console.print("Please install using `pip install streamlit`.")
        exit(1)

    base_path = os.path.abspath(os.path.dirname(__file__))

    # Forward the rest of the parameters
    cli.main_run(
        [os.path.join(base_path, "ui", script), "--server.port", str(port), "--"]
        + sys.argv[3:]
    )


@app.command()
def check_compliance(
    eval_config_path: str = typer.Option(
        default="config",
        exists=True,
        help="Path to a directory containing eval configuration files. "
        "Defaults to the `config` folder in the current folder.",
    ),
    output_path: List[str] = typer.Option(
        default=[],
        help="One or more output directories from evaluation runs."
        "Defaults to the list of folders in the current folder, except `config`.",
    ),
    llm_judge: str = typer.Option(
        help="The name of the model to be used as a judge. "
        "The model needs to be configured in the `models` key in the evaluation config.",
    ),
    policy_ids: List[str] = typer.Option(
        default=[],
        help="The ids of all the policies that should be checked. "
        "If no policies are specified, all policies will be checked.",
    ),
    multi_check: bool = typer.Option(
        default=False,
        help="Whether to check compliance for multiple policies in a single LLM call.",
    ),
    verbose: bool = typer.Option(
        default=False,
        help="Whether the output should be verbose or not.",
    ),
    disable_llm_cache: bool = typer.Option(
        default=False,
        help="Whether to disable the LLM caching. By default it's enabled.",
    ),
    force: bool = typer.Option(
        default=False,
        help="Whether to force the compliance check, even if a result exists. Defaults to False.",
    ),
    reset: bool = typer.Option(
        default=False,
        help="Whether to reset the compliance check data. Defaults to False.",
    ),
):
    """Check the policy compliance of the interactions in the `output_path`."""
    output_paths = []
    if not output_path:
        output_paths = get_output_paths()
    else:
        for path in output_path:
            output_paths.extend(path.split(","))

    if disable_llm_cache:
        console.print("[orange]Caching is disabled.[/]")
    else:
        console.print("[green]Caching is enabled.[/]")
        set_llm_cache(SQLiteCache(database_path=".langchain.db"))

    console.print(f"Using eval configuration from {eval_config_path}.")
    console.print(f"Using output paths: {output_path}.")

    compliance_checker = LLMJudgeComplianceChecker(
        eval_config_path=eval_config_path,
        output_paths=output_paths,
        llm_judge_model=llm_judge,
        policy_ids=policy_ids,
        multi_check=multi_check,
        verbose=verbose,
        force=force,
        reset=reset,
    )
    asyncio.run(compliance_checker.run())


@app.command()
def review(
    eval_config_path: str = typer.Option(
        default="config",
        exists=True,
        help="Path to a directory containing eval configuration files. "
        "Defaults to the `config` folder in the current folder.",
    ),
    output_path: List[str] = typer.Option(
        default=[],
        help="One or more output directories from evaluation runs."
        "Defaults to the list of folders in the current folder, except `config`.",
    ),
):
    """Review the interactions included in the evaluation.

    Launches a web Streamlit web UI.
    """
    if not output_path:
        output_path = get_output_paths()

    console.print(f"Using eval configuration from {eval_config_path}.")
    console.print(f"Using output paths: {output_path}.")

    _launch_ui("review.py", port=8501)


@app.command()
def summary(
    eval_config_path: str = typer.Option(
        default="",
        exists=True,
        help="Path to a directory containing eval configuration files.",
    ),
    output_path: List[str] = typer.Option(
        default=[],
        help="One or more output directories from evaluation runs."
        "Defaults to the list of folders in the current folder, except `config`.",
    ),
):
    """Show a summary of the evaluation.

    Launches a web Streamlit web UI.
    """
    if not output_path:
        output_path = get_output_paths()

    console.print(f"Using eval configuration from {eval_config_path}.")
    console.print(f"Using output paths: {output_path}.")

    _launch_ui("summary.py", port=8502)
