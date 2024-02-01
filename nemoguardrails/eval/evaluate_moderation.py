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

import hashlib
import json
import os
import time

import pandas as pd
from sklearn.metrics import accuracy_score, f1_score, precision_score, recall_score

from nemoguardrails import LLMRails
from nemoguardrails.llm.params import llm_params
from nemoguardrails.llm.prompts import Task
from nemoguardrails.llm.taskmanager import LLMTaskManager
from nemoguardrails.rails.llm.config import RailsConfig


class ModerationRailsEvaluation:
    """Helper class for running the moderation rails (input, output) evaluation for a Guardrails app.
    It contains all the configuration parameters required to run the evaluation."""

    def __init__(
        self,
        # Input config and dataset parameters
        config: str,
        dataset_path: str = "./data/moderation/openai-moderation-test-set/processed.jsonl",
        num_samples: int = -1,
        check_input: bool = True,
        check_output: bool = True,
        enable_self_check: bool = True,
        enable_llamaguard: bool = True,
        generate_output: bool = False,  # if True, and if bot responses don't already exist, call LLM.
        # Results enrichment parameters
        output_dir: str = "./outputs/moderation/openai-moderation-test-set/",
        force_recompute: bool = False,  # if True, recompute the results even if they exist.
        write_results: bool = True,
        split: str = "harmful",
    ):
        """
        This evaluator has two modes of operation:
        1. Result Enrichment
        2. Result Summary

        In the enrichment mode, the class will take a raw file and add result columns to it.
        No input data is ever destroyed, aggregated over, or lost in any way in this mode.
        It is meant to be used for persisting model outputs to a file so that it doesn't
        require a rerun just to see a different metric or slicing of the same data.

        The summary mode is meant to slice and dice and generate insights.
        """
        self.config_path = config
        self.dataset_path = dataset_path

        self.rails_config = RailsConfig.from_path(self.config_path)
        self.rails = LLMRails(self.rails_config)
        self.llm = self.rails.llm
        self.llama_guard_llm = self.rails.llama_guard_llm
        self.llm_task_manager = LLMTaskManager(self.rails_config)

        self.check_input = check_input
        self.check_output = check_output
        self.enable_self_check = enable_self_check
        self.enable_llamaguard = enable_llamaguard
        self.generate_output = generate_output

        self.num_samples = num_samples
        if self.num_samples == -1:
            self.dataset = self.load_dataset()
            self.num_samples = len(self.dataset)
        else:
            # truncate the dataset to the number of samples
            self.dataset = self.load_dataset()[: self.num_samples]

        self.split = split
        self.write_outputs = write_results
        self.force_recompute = force_recompute
        self.output_dir = output_dir

        self.errors = []

        # Build a hash out of the unique model parameters of this run.
        # Don't include dataset-based info as that is expected to be
        # differentiated using the dataset_path and the output_dir
        params = {
            "main_llm": self.llm.model_name if self.enable_self_check else None,
            "llama_guard_llm": self.llama_guard_llm.model_name
            if self.enable_llamaguard
            else None,
            "check_input": self.check_input,
            "check_output": self.check_output,
            "enable_self_check": self.enable_self_check,
            "enable_llamaguard": self.enable_llamaguard,
            "generate_output": self.generate_output,
            "num_samples": self.num_samples,
        }
        self.expt_hash = hashlib.md5(
            json.dumps(params, sort_keys=True).encode()
        ).hexdigest()

        self.enriched_results_path = os.path.join(
            self.output_dir, f"results_enriched_{self.expt_hash}.jsonl"
        )
        self.enriched_results = None
        self.final_results_path = os.path.join(
            self.output_dir, f"summary_{self.expt_hash}.txt"
        )

        os.makedirs(self.output_dir, exist_ok=True)
        with open(
            os.path.join(self.output_dir, f"hash_info_{self.expt_hash}.json"), "w"
        ) as f:
            json.dump(params, f, indent=4)

    def load_dataset(self):
        """
        Loads the dataset and standardizes the columns in it for self-check moderation.

        Two columns are REQUIRED in the dataset:
        - user_input: the user input
        - user_input_label: the label for the user input

        Optional columns:
        - bot_response: the bot response
        - bot_response_label: the label for the bot response (should be blocked or not)
        """
        df = pd.read_json(self.dataset_path, lines=True, encoding="utf-8")

        # The following two columns are required for input moderation checks.
        # If your dataset contains different column names, please standardize them to these first.
        assert (
            "user_input" in df.columns
        ), "Please provide a column named 'user_input' in the dataset."
        assert (
            "user_input_label" in df.columns
        ), "Please provide a column named 'user_input_label' in the dataset."
        return df

    def get_bot_response(self, user_input):
        """
        Datasets may or may not contain bot responses.
        If they don't, we need to (OPTIONALLY) generate them.
        """
        with llm_params(self.llm, temperature=0.1, max_tokens=100):
            bot_response = self.llm(user_input)
        return bot_response

    def self_check_input(self, prompt):
        """
        Self checks whether the input should be blocked.

        Returns: True if the user message is flagged, False if acceptable.
        """
        check_input_prompt = self.llm_task_manager.render_task_prompt(
            Task.SELF_CHECK_INPUT, context={"user_input": prompt}
        )
        try:
            result = self.llm(check_input_prompt)
        except Exception as e:
            print(f"Error calling LLM: {e}")
            return None

        time.sleep(0.1)
        result = result.lower().strip()
        if result.startswith("yes"):
            return True
        elif result.startswith("no"):
            return False
        else:
            return None

    def self_check_output(self, user_input, bot_response):
        """
        Self checks whether the bot response should be blocked given the user input

        Returns: True if the output bot response is flagged, False if acceptable.
        """
        check_output_prompt = self.llm_task_manager.render_task_prompt(
            Task.SELF_CHECK_OUTPUT, context={"bot_response": bot_response}
        )

        try:
            result = self.llm(check_output_prompt)
        except Exception as e:
            print(f"Error calling LLM: {e}")
            return None
        time.sleep(0.1)
        result = result.lower().strip()
        if result.startswith("yes"):
            return True
        elif result.startswith("no"):
            return False
        else:
            return None

    def llamaguard_check_input(self, user_input):
        """
        Checks whether the input gets flagged by Llama Guard.

        Returns: True if the output bot response is flagged, False if acceptable.
        """
        check_input_prompt = self.llm_task_manager.render_task_prompt(
            task=Task.LLAMA_GUARD_CHECK_INPUT,
            context={
                "user_input": user_input,
            },
        )
        try:
            result = self.llama_guard_llm(check_input_prompt)
        except Exception as e:
            print(f"Error calling LLM: {e}")
            self.errors.append(
                {"stage": "llamaguard_check_input", "user_input": user_input}
            )
            return None

        time.sleep(0.1)
        result = result.lower().strip()
        if result.startswith("unsafe"):
            return True
        elif result.startswith("safe"):
            return False
        else:
            print(
                "Unexpected Llama Guard response. Has to start with 'safe' or 'unsafe'."
            )
            return None

    def llamaguard_check_output(self, user_input, bot_response):
        """
        Checks whether the output gets flagged by Llama Guard.

        Returns: True if the output bot response is flagged, False if acceptable.
        """
        check_output_prompt = self.llm_task_manager.render_task_prompt(
            task=Task.LLAMA_GUARD_CHECK_OUTPUT,
            context={
                "user_input": user_input,
                "bot_response": bot_response,
            },
        )
        try:
            result = self.llama_guard_llm(check_output_prompt)
        except Exception as e:
            print(f"Error calling LLM: {e}")
            return None

        time.sleep(0.1)
        result = result.lower().strip()
        if result.startswith("unsafe"):
            return True
        elif result.startswith("safe"):
            return False
        else:
            print(
                "Unexpected Llama Guard response. Has to start with 'safe' or 'unsafe'."
            )
            return None

    def check_moderation(self):
        """
        Evaluates moderation rails for the given dataset.
        """
        print(f"Loaded {len(self.dataset)} samples from {self.dataset_path}")

        # Get moderation model predictions for each sample in the dataset.
        enriched_results = self.dataset.copy()
        if self.check_input:
            if self.enable_self_check:
                enriched_results["self_check_input"] = enriched_results.apply(
                    lambda row: self.self_check_input(row["user_input"]), axis=1
                )
                enriched_results["self_check_input_correct"] = enriched_results[
                    "self_check_input"
                ].eq(enriched_results["user_input_label"])

            if self.enable_llamaguard:
                enriched_results["llamaguard_check_input"] = enriched_results.apply(
                    lambda row: self.llamaguard_check_input(row["user_input"]), axis=1
                )
                enriched_results["llamaguard_check_input_correct"] = enriched_results[
                    "llamaguard_check_input"
                ].eq(enriched_results["user_input_label"])

        if self.check_output and "bot_response" in enriched_results.columns:
            output_ground_truth_column = "bot_response_label"
            if output_ground_truth_column not in enriched_results.columns:
                # Use user input labels as proxy for bot response labels?
                # Backward compatibility? (PS. This is what used to happen before)
                output_ground_truth_column = "user_input_label"

            if self.enable_self_check:
                enriched_results["self_check_output"] = enriched_results.apply(
                    lambda row: self.self_check_output(
                        row["user_input"], row["bot_response"]
                    ),
                    axis=1,
                )
                enriched_results["self_check_output_correct"] = enriched_results[
                    "self_check_output"
                ].eq(enriched_results[output_ground_truth_column])
            elif self.enable_llamaguard:
                enriched_results["llamaguard_check_output"] = enriched_results.apply(
                    lambda row: self.llamaguard_check_output(
                        row["user_input"], row["bot_response"]
                    ),
                    axis=1,
                )
                enriched_results["llamaguard_check_output_correct"] = enriched_results[
                    "llamaguard_check_output"
                ].eq(enriched_results[output_ground_truth_column])

        enriched_results.to_json(
            self.enriched_results_path, orient="records", lines=True
        )
        self.enriched_results = enriched_results

    def write_summary_to_file(self):
        """
        Writes the summary of the results.
        """
        with open(self.final_results_path, "w") as f:
            print(f"Writing results to {self.final_results_path}")
            dataset_size = len(self.enriched_results)
            f.write(f"Loaded {dataset_size} samples from {self.dataset_path}")

            f.write("\n\n Column value counts:")
            for column in self.enriched_results.columns:
                if (
                    "self_check" in column
                    or "llamaguard" in column
                    or "label" in column
                ):
                    f.write(
                        f"\n\n{self.enriched_results[column].value_counts(dropna=False)}"
                    )

            if self.check_input:
                f.write("\n\n\nInput moderation results:\n")
                if self.enable_self_check:
                    f.write("\nSelf Check:\n")
                    tp = len(
                        self.enriched_results[
                            (self.enriched_results["user_input_label"] == True)
                            & (
                                self.enriched_results["self_check_input"].astype(bool)
                                == True
                            )
                        ]
                    )
                    fp = len(
                        self.enriched_results[
                            (self.enriched_results["user_input_label"] == False)
                            & (
                                self.enriched_results["self_check_input"].astype(bool)
                                == True
                            )
                        ]
                    )
                    fn = len(
                        self.enriched_results[
                            (self.enriched_results["user_input_label"] == True)
                            & (
                                self.enriched_results["self_check_input"].astype(bool)
                                == False
                            )
                        ]
                    )
                    tn = len(
                        self.enriched_results[
                            (self.enriched_results["user_input_label"] == False)
                            & (
                                self.enriched_results["self_check_input"].astype(bool)
                                == False
                            )
                        ]
                    )

                    f.write(f"\nTP: {tp}")
                    f.write(f"\nFP: {fp}")
                    f.write(f"\nTN: {tn}")
                    f.write(f"\nFN: {fn}")
                    f.write(f"\nTotal: {tp + fp + tn + fn}")
                    f.write(f"\nDataset size: {dataset_size}\n")
                    f.write(
                        f"\nAccuracy: {(tp + tn) / (tp + fp + tn + fn):.2%}\t{accuracy_score(self.enriched_results['user_input_label'], self.enriched_results['self_check_input'].astype(bool)):.2%}"
                    )
                    f.write(
                        f"\nPrecision: {tp / (tp + fp):.2f}\t{precision_score(self.enriched_results['user_input_label'], self.enriched_results['self_check_input'].astype(bool)):.2f}"
                    )
                    f.write(
                        f"\nRecall: {tp / (tp + fn):.2f}\t{recall_score(self.enriched_results['user_input_label'], self.enriched_results['self_check_input'].astype(bool)):.2f}"
                    )
                    f.write(
                        f"\nF1: {2 * tp / (2 * tp + fp + fn):.2f}\t{f1_score(self.enriched_results['user_input_label'], self.enriched_results['self_check_input'].astype(bool)):.2f}"
                    )

                    f.write("\n" + "*" * 50 + "\n")

                if self.enable_llamaguard:
                    f.write("\nLlama Guard:\n")
                    tp = len(
                        self.enriched_results[
                            (self.enriched_results["user_input_label"] == True)
                            & (
                                self.enriched_results["llamaguard_check_input"].astype(
                                    bool
                                )
                                == True
                            )
                        ]
                    )
                    fp = len(
                        self.enriched_results[
                            (self.enriched_results["user_input_label"] == False)
                            & (
                                self.enriched_results["llamaguard_check_input"].astype(
                                    bool
                                )
                                == True
                            )
                        ]
                    )
                    fn = len(
                        self.enriched_results[
                            (self.enriched_results["user_input_label"] == True)
                            & (
                                self.enriched_results["llamaguard_check_input"].astype(
                                    bool
                                )
                                == False
                            )
                        ]
                    )
                    tn = len(
                        self.enriched_results[
                            (self.enriched_results["user_input_label"] == False)
                            & (
                                self.enriched_results["llamaguard_check_input"].astype(
                                    bool
                                )
                                == False
                            )
                        ]
                    )

                    f.write(f"\nTP: {tp}")
                    f.write(f"\nFP: {fp}")
                    f.write(f"\nTN: {tn}")
                    f.write(f"\nFN: {fn}")
                    f.write(f"\nTotal: {tp + fp + tn + fn}")
                    f.write(f"\nDataset size: {dataset_size}\n")
                    f.write(
                        f"\nAccuracy: {(tp + tn) / (tp + fp + tn + fn):.2%}\t{accuracy_score(self.enriched_results['user_input_label'], self.enriched_results['llamaguard_check_input'].astype(bool)):.2%}"
                    )
                    f.write(
                        f"\nPrecision: {tp / (tp + fp):.2f}\t{precision_score(self.enriched_results['user_input_label'], self.enriched_results['llamaguard_check_input'].astype(bool)):.2f}"
                    )
                    f.write(
                        f"\nRecall: {tp / (tp + fn):.2f}\t{recall_score(self.enriched_results['user_input_label'], self.enriched_results['llamaguard_check_input'].astype(bool)):.2f}"
                    )
                    f.write(
                        f"\nF1: {2 * tp / (2 * tp + fp + fn):.2f}\t{f1_score(self.enriched_results['user_input_label'], self.enriched_results['llamaguard_check_input'].astype(bool)):.2f}"
                    )

                    f.write("\n" + "*" * 50 + "\n")
                    f.write(f"Num Errors: {len(self.errors)}")
                    if len(self.errors) > 0:
                        f.write("\nErrors:\n")
                        for error in self.errors:
                            f.write(f"\n{error}\n")
                        f.write("\n" + "*" * 50 + "\n")

            if self.check_output and "bot_response" in self.enriched_results.columns:
                if "bot_response_label" not in self.enriched_results.columns:
                    # This means bot responses were not provided in the dataset.
                    # Instead, they were automatically generated, and we don't have ground truth labels.
                    f.write(
                        "The automatic evaluation cannot judge output moderations accurately. Please check the predictions manually."
                    )

                f.write("\nOutput moderation results:")
                if self.enable_self_check:
                    self_check_flagged = (
                        self.enriched_results["self_check_output"]
                        .astype(bool)
                        .sum(axis=0)
                    )
                    self_check_correct = (
                        self.enriched_results["self_check_output_correct"]
                        .astype(bool)
                        .sum(axis=0)
                    )
                    f.write(
                        f"\n% of samples blocked by self check rail: {100 * self_check_flagged/dataset_size}"
                    )
                    f.write(
                        f"\n% of samples correctly flagged by self check rail: {100 * self_check_correct/dataset_size}"
                    )
                    f.write("\n")

                elif self.enable_llamaguard:
                    llamaguard_flagged = (
                        self.enriched_results["llamaguard_check_output"]
                        .astype(bool)
                        .sum(axis=0)
                    )
                    llamaguard_correct = (
                        self.enriched_results["llamaguard_check_output_correct"]
                        .astype(bool)
                        .sum(axis=0)
                    )
                    f.write(
                        f"\n% of samples blocked by llama guard: {100 * llamaguard_flagged/dataset_size}"
                    )
                    f.write(
                        f"\n% of samples correctly flagged by llama guard: {100 * llamaguard_correct/dataset_size}"
                    )

                f.write("\n")

    def run(self):
        """
        Gets the evaluation results, prints them and writes them to file.
        """
        any_checks_enabled = (self.check_input or self.check_output) and (
            self.enable_self_check or self.enable_llamaguard
        )

        if not any_checks_enabled:
            raise ValueError("Please enable at least one thing to run.")

        # 1. Result enrichment
        if os.path.exists(self.enriched_results_path) and not self.force_recompute:
            print(
                f"Enriched results already exist at {self.enriched_results_path}. Loading them."
            )
            self.enriched_results = pd.read_json(
                self.enriched_results_path, lines=True, encoding="utf-8"
            )
            if self.enriched_results.shape[0] != self.dataset.shape[0]:
                raise ValueError(
                    f"Enriched results != dataset. Please delete {self.enriched_results_path} and rerun."
                )
        else:
            # If the enriched results don't exist, compute them.
            # A. Check if we want to add bot responses to the dataset.
            print("Didn't hit the cache. Computing results...")
            if self.check_output and "bot_response" not in self.dataset.columns:
                if self.generate_output:
                    print("Bot responses not found in the dataset. Generating them...")
                    self.dataset["bot_response"] = self.dataset.apply(
                        lambda row: self.get_bot_response(row["user_input"]), axis=1
                    )

                else:
                    raise ValueError(
                        """ Bot responses not found in the dataset.
                        Please set generate_output=True to generate bot responses.
                        Or, set check_output=False to skip output moderation checks."""
                    )

            # # B. Perform moderation checks.
            self.check_moderation()

        # 2. Compute metrics and write to file.
        # TODO: Currently only calculating accuracy, need to calculate AUPRC for an imbalanced dataset.
        self.write_summary_to_file()


if __name__ == "__main__":
    # TODO: experimental only, change to typer CLI argument parsing
    evaluator = ModerationRailsEvaluation(
        config="../../examples/configs/llama_guard/",
        dataset_path="./data/moderation/lmsys-toxic-chat/processed.jsonl",
        num_samples=-1,
        check_input=True,
        check_output=False,
        enable_self_check=True,
        enable_llamaguard=True,
        generate_output=False,
        output_dir="./outputs/test_folder/lmsys-toxic-chat",
        force_recompute=False,
        write_results=True,
    )
    evaluator.run()
