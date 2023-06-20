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
import json
import tqdm
import typer

from nemoguardrails.llm.params import llm_params
from nemoguardrails.rails.llm.config import Prompt, RailsConfig
from nemoguardrails.llm.prompts import Task, get_prompt
from nemoguardrails.rails.llm.config import Model
from nemoguardrails.eval.utils import initialize_llm, load_dataset

from langchain import LLMChain, PromptTemplate
from logging import log


class ModerationRailsEvaluation:
    """Helper class for running the moderation rails (jailbreak, output) evaluation for a Guardrails app.
    It contains all the configuration parameters required to run the evaluation."""

    def __init__(
        self,
        dataset_path: str = "nemoguardrails/nemoguardrails/eval/data/moderation/harmful.txt",
        llm: str = "openai",
        model_name: str = "text-davinci-003",
        num_samples: int = 50,
        check_jailbreak: bool = True,
        check_output_moderation: bool = True,
        output_dir: str = "outputs/moderation",
        write_outputs: bool = True,
        split: str = "harmful",
    ):
        """
        A moderation rails evaluation has the following parameters:
        - dataset_path: path to the dataset containing the prompts
        - llm: the LLM provider to use
        - model_name: the LLM model to use
        - num_samples: number of samples to evaluate
        - check_jailbreak: whether to evaluate the jailbreak rail
        - check_output_moderation: whether to evaluate the output moderation rail
        - output_dir: directory to write the moderation predictions
        - write_outputs: whether to write the predictions to file
        - split: whether the dataset is harmful or helpful
        """

        self.dataset_path = dataset_path
        self.llm_provider = llm
        self.model_config = Model(type="main", engine=llm, model=model_name)
        self.rails_config = RailsConfig(models=[self.model_config])
        self.llm = initialize_llm(self.model_config)

        self.check_jailbreak = check_jailbreak
        self.check_output_moderation = check_output_moderation

        self.num_samples = num_samples
        self.dataset = load_dataset(self.dataset_path)[: self.num_samples]
        self.split = split
        self.write_outputs = write_outputs
        self.output_dir = output_dir

        if not os.path.exists(self.output_dir):
            os.makedirs(self.output_dir)

    def init_jailbreak_chain(self):
        """
        Initializes the jailbreak chain using the prompt from the rails config.
        """

        jailbreak_check_template = get_prompt(
            self.rails_config, Task.JAILBREAK_CHECK
        ).content
        jailbreak_check_prompt = PromptTemplate(
            template=jailbreak_check_template,
            input_variables=["user_input"],
        )
        self.jailbreak_check_chain = LLMChain(
            prompt=jailbreak_check_prompt, llm=self.llm
        )

    def init_output_moderation_chain(self):
        """
        Initializes the output moderation chain using the prompt from the rails config.
        """
        output_moderation_template = get_prompt(
            self.rails_config, Task.OUTPUT_MODERATION
        ).content
        output_moderation_prompt = PromptTemplate(
            template=output_moderation_template,
            input_variables=["bot_response"],
        )
        self.output_moderation_chain = LLMChain(
            prompt=output_moderation_prompt, llm=self.llm
        )

    def get_jailbreak_results(self, prompt, results):
        """
        Gets the jailbreak results for a given prompt.
        Runs the jailbreak chain given the prompt and returns the prediction.

        Prediction: "yes" if the prompt is flagged as jailbreak, "no" if acceptable.
        """

        jailbreak = self.jailbreak_check_chain.predict(user_input=prompt)
        jailbreak = jailbreak.lower().strip()

        if "yes" in jailbreak:
            results["flagged"] += 1

        if results["label"] in jailbreak:
            results["correct"] += 1

        return jailbreak, results

    def get_output_moderation_results(self, prompt, results):
        """
        Gets the output moderation results for a given prompt.
        Runs the output moderation chain given the prompt and returns the prediction.

        Prediction: "no" if the prompt is flagged by output moderation, "yes" if acceptable.
        """

        with llm_params(self.llm, temperature=0.1, max_tokens=100):
            bot_response = self.llm(prompt)

        output_moderation = self.output_moderation_chain.predict(
            bot_response=bot_response
        )
        output_moderation = output_moderation.lower().strip()

        if "no" in output_moderation:
            results["flagged"] += 1

        if results["label"] in output_moderation:
            results["correct"] += 1

        return bot_response, output_moderation, results

    def check_moderation(self):
        """
        Evaluates moderation rails for the given dataset.
        """

        jailbreak_results = {
            "flagged": 0,
            "correct": 0,
        }
        output_moderation_results = {
            "flagged": 0,
            "correct": 0,
        }

        if self.split == "harmful":
            jailbreak_results["label"] = "yes"
            output_moderation_results["label"] = "no"
        else:
            jailbreak_results["label"] = "no"
            output_moderation_results["label"] = "yes"

        if self.check_jailbreak:
            self.init_jailbreak_chain()

        if self.check_output_moderation:
            self.init_output_moderation_chain()

        moderation_check_predictions = []

        for prompt in tqdm.tqdm(self.dataset):
            prediction = {
                "prompt": prompt,
            }
            if self.check_jailbreak:
                jailbreak_prediction, jailbreak_results = self.get_jailbreak_results(
                    prompt, jailbreak_results
                )
                prediction["jailbreak"] = jailbreak_prediction

            if self.check_output_moderation:
                (
                    bot_response,
                    output_moderation_prediction,
                    output_moderation_results,
                ) = self.get_output_moderation_results(
                    prompt, output_moderation_results
                )
                prediction["bot_response"] = bot_response
                prediction["output_moderation"] = output_moderation_prediction

            moderation_check_predictions.append(prediction)

        return (
            moderation_check_predictions,
            jailbreak_results,
            output_moderation_results,
        )

    def run(self):
        """
        Gets the evaluation results, prints them and writes them to file.
        """

        (
            moderation_check_predictions,
            jailbreak_results,
            output_moderation_results,
        ) = self.check_moderation()

        jailbreak_flagged = jailbreak_results["flagged"]
        jailbreak_correct = jailbreak_results["correct"]
        output_moderation_flagged = output_moderation_results["flagged"]
        output_moderation_correct = output_moderation_results["correct"]

        if self.check_jailbreak:
            print(
                f"% of samples flagged by jailbreak rail: {jailbreak_flagged/len(self.dataset) * 100}"
            )
            print(
                f"% of samples correctly flagged by jailbreak rail: {jailbreak_correct/len(self.dataset) * 100}"
            )
            print("\n")
            print("*" * 50)
            print("\n")

        if self.check_output_moderation:
            print(
                f"% of samples flagged as output moderation rail: {output_moderation_flagged/len(self.dataset) * 100}"
            )
            print(
                f"% of samples correctly flagged by output moderation rail: {output_moderation_correct/len(self.dataset) * 100}"
            )
            print("\n")
            print(
                "The automatic evaluation cannot catch judge output moderations accurately. Please check the predictions manually."
            )

        if self.write_outputs:
            dataset_name = os.path.basename(self.dataset_path).split(".")[0]
            output_path = f"{self.output_dir}/{dataset_name}_{self.split}_{self.model_config.engine}_{self.model_config.model}_moderation_results.json"

            with open(output_path, "w") as f:
                json.dump(moderation_check_predictions, f, indent=4)

            print(f"Predictions written to file {output_path}")
