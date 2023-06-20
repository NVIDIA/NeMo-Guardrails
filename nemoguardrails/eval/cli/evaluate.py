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
from typing import List

import typer

from nemoguardrails.eval.evaluate_topical import TopicalRailsEvaluation
from nemoguardrails.logging.verbose import set_verbose

app = typer.Typer()

logging.getLogger().setLevel(logging.WARNING)


@app.command()
def topical(
    config: List[str] = typer.Option(
        default=[""],
        exists=True,
        help="Path to a directory containing configuration files of the Guardrails application for evaluation. "
        "Can also point to a single configuration file.",
    ),
    verbose: bool = typer.Option(
        default=False,
        help="If the chat should be verbose and output the prompts.",
    ),
    test_percentage: float = typer.Option(
        default=0.3,
        help="Percentage of the samples for an intent to be used as test set.",
    ),
    max_tests_intent: int = typer.Option(
        default=3,
        help="Maximum number of test samples per intent to be used when testing. "
        "If value is 0, no limit is used.",
    ),
    max_samples_intent: int = typer.Option(
        default=0,
        help="Maximum number of samples per intent indexed in vector database. "
        "If value is 0, all samples are used.",
    ),
    results_frequency: int = typer.Option(
        default=10,
        help="Print evaluation intermediate results using this step.",
    ),
):
    """Evaluates the performance of the topical rails defined in a Guardrails application.
    Computes accuracy for canonical form detection, next step generation, and next bot message generation.
    Only a single Guardrails application can be specified in the config option.
    """
    if verbose:
        set_verbose(True)

    if len(config) > 1:
        typer.secho(f"Multiple configurations are not supported.", fg=typer.colors.RED)
        typer.echo("Please provide a single config path (folder or config file).")
        raise typer.Exit(1)

    if config[0] == "":
        typer.echo("Please provide a value for the config path.")
        raise typer.Exit(1)

    typer.echo(f"Starting the evaluation for app: {config[0]}...")

    topical_eval = TopicalRailsEvaluation(
        config_path=config[0],
        verbose=verbose,
        test_set_percentage=test_percentage,
        max_samples_per_intent=max_samples_intent,
        max_tests_intent=max_tests_intent,
        print_test_results_frequency=results_frequency,
    )
    topical_eval.evaluate_topical_rails()
