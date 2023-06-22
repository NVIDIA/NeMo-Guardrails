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

from nemoguardrails.eval.evaluate_factcheck import FactCheckEvaluation
from nemoguardrails.eval.evaluate_hallucination import HallucinationRailsEvaluation
from nemoguardrails.eval.evaluate_moderation import ModerationRailsEvaluation
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
    sim_threshold: float = typer.Option(
        default=0.0,
        help="Minimum similarity score to select the intent when exact match fails.",
    ),
    random_seed: int = typer.Option(
        default=None, help="Random seed used by the evaluation."
    ),
    output_dir: str = typer.Option(
        default=None, help="Output directory for predictions."
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
        max_tests_per_intent=max_tests_intent,
        print_test_results_frequency=results_frequency,
        similarity_threshold=sim_threshold,
        random_seed=random_seed,
        output_dir=output_dir,
    )
    topical_eval.evaluate_topical_rails()


@app.command()
def moderation(
    dataset_path: str = typer.Option(
        "nemoguardrails/eval/data/moderation/harmful.txt",
        help="Path to dataset containing prompts",
    ),
    llm: str = typer.Option("openai", help="LLM provider ex. OpenAI"),
    model_name: str = typer.Option(
        "text-davinci-003", help="LLM model ex. text-davinci-003"
    ),
    num_samples: int = typer.Option(50, help="Number of samples to evaluate"),
    check_jailbreak: bool = typer.Option(True, help="Evaluate jailbreak rail"),
    check_output_moderation: bool = typer.Option(
        True, help="Evaluate output moderation rail"
    ),
    output_dir: str = typer.Option(
        "eval_outputs/moderation", help="Output directory for predictions"
    ),
    write_outputs: bool = typer.Option(True, help="Write outputs to file"),
    split: str = typer.Option("harmful", help="Whether prompts are harmful or helpful"),
):
    """
    Evaluates the performance of the moderation rails defined in a Guardrails application.
    Computes accuracy for jailbreak detection and output moderation.
    """
    moderation_check = ModerationRailsEvaluation(
        dataset_path,
        llm,
        model_name,
        num_samples,
        check_jailbreak,
        check_output_moderation,
        output_dir,
        write_outputs,
        split,
    )
    typer.echo(
        f"Starting the moderation evaluation for data: {dataset_path} using LLM {llm}-{model_name}..."
    )
    moderation_check.run()


@app.command()
def hallucination(
    dataset_path: str = typer.Option(
        "nemoguardrails/eval/data/hallucination/sample.txt", help="Dataset path"
    ),
    llm: str = typer.Option("openai", help="LLM provider"),
    model_name: str = typer.Option("text-davinci-003", help="LLM model name"),
    num_samples: int = typer.Option(50, help="Number of samples to evaluate"),
    output_dir: str = typer.Option(
        "eval_outputs/hallucination", help="Output directory"
    ),
    write_outputs: bool = typer.Option(True, help="Write outputs to file"),
):
    """
    Evaluates the performance of the hallucination rails defined in a Guardrails application.
    Computes accuracy for hallucination detection.
    """
    hallucination_check = HallucinationRailsEvaluation(
        dataset_path,
        llm,
        model_name,
        num_samples,
        output_dir,
        write_outputs,
    )
    typer.echo(
        f"Starting the hallucination evaluation for data: {dataset_path} using LLM {llm}-{model_name}..."
    )
    hallucination_check.run()


@app.command()
def fact_checking(
    dataset_path: str = typer.Option(
        "nemoguardrails/eval/data/factchecking/sample.json",
        help="Path to the folder containing the dataset",
    ),
    llm: str = typer.Option("openai", help="LLM provider to be used for fact checking"),
    model_name: str = typer.Option(
        "text-davinci-003", help="Model name ex. text-davinci-003"
    ),
    num_samples: int = typer.Option(50, help="Number of samples to be evaluated"),
    create_negatives: bool = typer.Argument(
        True, help="create synthetic negative samples"
    ),
    output_dir: str = typer.Option(
        "eval_outputs/factchecking",
        help="Path to the folder where the outputs will be written",
    ),
    write_outputs: bool = typer.Option(
        True, help="Write outputs to the output directory"
    ),
):
    """
    Evaluates the performance of the fact checking rails defined in a Guardrails application.
    Computes accuracy for fact checking.
    Negatives can be created synthetically by an LLM that acts as an adversary and modifies the answer to make it incorrect.
    """
    fact_check = FactCheckEvaluation(
        dataset_path,
        llm,
        model_name,
        num_samples,
        create_negatives,
        output_dir,
        write_outputs,
    )
    typer.echo(
        f"Starting the fact checking evaluation for data: {dataset_path} using LLM {llm}-{model_name}..."
    )
    fact_check.run()
