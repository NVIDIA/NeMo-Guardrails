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

import json
import os
from logging import log

import tqdm
import typer

from nemoguardrails.eval.utils import initialize_llm, load_dataset
from nemoguardrails.llm.params import llm_params
from nemoguardrails.llm.prompts import Task
from nemoguardrails.llm.taskmanager import LLMTaskManager
from nemoguardrails.rails.llm.config import Model, RailsConfig


class HallucinationRailsEvaluation:
    """Helper class for running the hallucination rails evaluation for a Guardrails app.
    It contains all the configuration parameters required to run the evaluation."""

    def __init__(
        self,
        dataset_path: str = "data/hallucination/sample.txt",
        llm: str = "openai",
        model_name: str = "text-davinci-003",
        num_samples: int = 50,
        output_dir: str = "outputs/hallucination",
        write_outputs: bool = True,
    ):
        """
        A hallucination rails evaluation has the following parameters:
        - dataset_path: path to the dataset containing the prompts
        - llm: the LLM provider to use
        - model_name: the LLM model to use
        - num_samples: number of samples to evaluate
        - output_dir: directory to write the hallucination predictions
        - write_outputs: whether to write the predictions to file
        """

        self.dataset_path = dataset_path

        self.llm_provider = llm
        self.model_config = Model(type="main", engine=llm, model=model_name)
        self.rails_config = RailsConfig(models=[self.model_config])
        self.llm_task_manager = LLMTaskManager(self.rails_config)
        self.llm = initialize_llm(self.model_config)

        self.num_samples = num_samples
        self.dataset = load_dataset(self.dataset_path)[: self.num_samples]
        self.write_outputs = write_outputs
        self.output_dir = output_dir

        if not os.path.exists(self.output_dir):
            os.makedirs(self.output_dir)

    def get_extra_responses(self, prompt, num_responses=2):
        """
        Sample extra responses with temperature=1.0 from the LLM for hallucination check.
        """

        extra_responses = []
        with llm_params(self.llm, temperature=1.0, max_tokens=100):
            for _ in range(num_responses):
                extra_responses.append(self.llm(prompt))

        return extra_responses

    def check_hallucination(self):
        """
        Run the hallucination rail evaluation.
        For each prompt, generate 2 extra responses from the LLM and check consistency with the bot response.
        If inconsistency is detected, flag the prompt as hallucination.
        """

        hallucination_check_predictions = []
        num_flagged = 0

        for question in tqdm.tqdm(self.dataset):
            with llm_params(self.llm, temperature=0.2, max_tokens=100):
                bot_response = self.llm(question)

            extra_responses = self.get_extra_responses(question, num_responses=2)
            if len(extra_responses) == 0:
                # Log message and return that no hallucination was found
                log.warning(
                    f"No extra LLM responses were generated for '{bot_response}' hallucination check."
                )
                continue

            paragraph = ". ".join(extra_responses)
            hallucination_check_prompt = self.llm_task_manager.render_task_prompt(
                Task.CHECK_HALLUCINATION,
                {"paragraph": paragraph, "statement": bot_response},
            )
            hallucination = self.llm(hallucination_check_prompt)
            hallucination = hallucination.lower().strip()

            prediction = {
                "question": question,
                "hallucination_agreement": hallucination,
                "bot_response": bot_response,
                "extra_responses": extra_responses,
            }
            hallucination_check_predictions.append(prediction)
            if "no" in hallucination:
                num_flagged += 1

        return hallucination_check_predictions, num_flagged

    def run(self):
        """
        Run  and print the hallucination rail evaluation.
        """

        hallucination_check_predictions, num_flagged = self.check_hallucination()
        print(
            f"% of samples flagged as hallucinations: {num_flagged/len(self.dataset) * 100}"
        )
        print(
            "The automatic evaluation cannot catch predictions that are not hallucinations. Please check the predictions manually."
        )

        if self.write_outputs:
            dataset_name = os.path.basename(self.dataset_path).split(".")[0]
            output_path = f"{self.output_dir}/{dataset_name}_{self.model_config.engine}_{self.model_config.model}_hallucination_predictions.json"
            with open(output_path, "w") as f:
                json.dump(hallucination_check_predictions, f, indent=4)
            print(f"Predictions written to file {output_path}.json")


def main(
    data_path: str = typer.Option("data/hallucination/sample.txt", help="Dataset path"),
    llm: str = typer.Option("openai", help="LLM provider"),
    model_name: str = typer.Option("text-davinci-003", help="LLM model name"),
    num_samples: int = typer.Option(50, help="Number of samples to evaluate"),
    output_dir: str = typer.Option("outputs/hallucination", help="Output directory"),
    write_outputs: bool = typer.Option(True, help="Write outputs to file"),
):
    hallucination_check = HallucinationRailsEvaluation(
        data_path,
        llm,
        model_name,
        num_samples,
        output_dir,
        write_outputs,
    )
    hallucination_check.run()


if __name__ == "__main__":
    typer.run(main)
