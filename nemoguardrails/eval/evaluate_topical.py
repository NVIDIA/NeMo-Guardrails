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
import textwrap
from typing import Optional

from nemoguardrails import LLMRails, RailsConfig
from nemoguardrails.actions.llm.utils import (
    get_last_bot_intent_event,
    get_last_bot_utterance_event,
    get_last_user_intent_event,
)


def sync_wrapper(async_func):
    """Wrapper for the evaluate_topical_rails method which is async."""

    def wrapper(*args, **kwargs):
        loop = asyncio.get_event_loop()
        return loop.run_until_complete(async_func(*args, **kwargs))

    return wrapper


class TopicalRailsEvaluation:
    """Helper class for running the topical rails evaluation for a Guardrails app.
    It contains all the configuration parameters required to run the evaluation."""

    def _initialize_rails_app(self):
        self.test_set = {}
        rails_config = RailsConfig.from_path(
            config_path=self.config_path,
            test_set_percentage=self.test_set_percentage,
            max_samples_per_intent=self.max_samples_per_intent,
            test_set=self.test_set,
        )
        """Initializes the Rails app used for evaluation."""

        # TODO: add support to register additional actions
        # rails_app.register_action(...)

        self.rails_app = LLMRails(rails_config, verbose=self.verbose)

    @staticmethod
    def _print_evaluation_results(
        processed_samples,
        total_test_samples,
        num_user_intent_errors,
        num_bot_intent_errors,
        num_bot_utterance_errors,
    ):
        """Prints a summary of the evaluation results."""
        print(
            textwrap.dedent(
                f"Processed {processed_samples}/{total_test_samples} samples! "
                f"Num intent errors: {num_user_intent_errors}. "
                f"Num bot intent errors {num_bot_intent_errors}. "
                f"Num bot message errors {num_bot_utterance_errors}."
            )
        )

    def __init__(
        self,
        config_path: str,
        verbose: Optional[bool] = False,
        test_set_percentage: Optional[float] = 0.3,
        max_tests_per_intent: Optional[int] = 3,
        max_samples_per_intent: Optional[int] = 0,
        print_test_results_frequency: Optional[int] = 10,
    ):
        """A topical rails evaluation has the following parameters:

        - config_path: The Guardrails app to be evaluated.
        - verbose: If the Guardrails app should be run in verbose mode
        - test_set_percentage: Percentage of the samples for an intent to be used as test set
        - max_tests_per_intent: Maximum number of test samples per intent to be used when testing
        (useful to have balanced test data for unbalanced datasets). If the value is 0,
        this parameter is not used.
        - max_samples_per_intent: Maximum number of samples per intent to be used in the
        vector database. If the value is 0, all samples not in test set are used.
        - print_test_results_frequency: If we want to print intermediate results about the
        current evaluation, this is the step.
        """
        self.config_path = config_path
        self.verbose = verbose
        self.test_set_percentage = test_set_percentage
        self.max_tests_per_intent = max_tests_per_intent
        self.max_samples_per_intent = max_samples_per_intent
        self.print_test_results_frequency = print_test_results_frequency
        self._initialize_rails_app()

    @sync_wrapper
    async def evaluate_topical_rails(self):
        """Runs the topical evaluation for the Guardrails app with the current configuration."""

        # Find the intents that do not have a flow that matches them
        intents_with_flows = {}
        for flow in self.rails_app.config.flows:
            intent_next_actions = None
            for event in flow["elements"]:
                if event["_type"] == "user_intent":
                    intent_name = event["intent_name"]
                    if intent_name in intents_with_flows:
                        print(intent_name)
                    intent_next_actions = intents_with_flows.get(intent_name, [])
                    if intent_name not in intents_with_flows:
                        intents_with_flows[intent_name] = intent_next_actions
                elif event["_type"] == "run_action" and event["action_name"] == "utter":
                    if intent_next_actions is not None:
                        intent_next_actions.append(event["action_params"]["value"])

        num_intents_with_flows = len(
            set(self.test_set.keys()).intersection(intents_with_flows.keys())
        )

        # Limit the number of test samples per intent, if we want to have a balanced test set
        total_test_samples = 0
        for intent, samples in self.test_set.items():
            if 0 < self.max_tests_per_intent < len(samples):
                samples = samples[: self.max_tests_per_intent]
            total_test_samples += len(samples)

        print(
            textwrap.dedent(
                f"""Started processing rails app from path: {self.config_path}.
                Number of intents: {len(self.test_set.keys())}.
                Number of flows: {len(self.rails_app.config.flows)}.
                Number of test samples: {total_test_samples}.
                Number of intents that have an associated flow: {num_intents_with_flows}.
                Intents without associated flows: {set(self.test_set.keys()).difference(intents_with_flows.keys())}."""
            )
        )

        # Run evaluation experiment, for each test sample start a new conversation
        processed_samples = 0
        num_user_intent_errors = 0
        num_bot_intent_errors = 0
        num_bot_utterance_errors = 0

        for intent, samples in self.test_set.items():
            for sample in samples:
                history_events = [{"type": "user_said", "content": sample}]
                new_events = await self.rails_app.runtime.generate_events(
                    history_events
                )

                generated_user_intent = get_last_user_intent_event(new_events)["intent"]
                if generated_user_intent != intent:
                    num_user_intent_errors += 1
                    print(
                        f"Error!: Generated intent: {generated_user_intent} <> "
                        f"Expected intent: {intent}"
                    )

                generated_bot_intent = get_last_bot_intent_event(new_events)["intent"]
                if generated_bot_intent not in intents_with_flows[intent]:
                    num_bot_intent_errors += 1
                    print(
                        f"Error!: Generated bot intent: {generated_bot_intent} <> "
                        f"Expected bot intent: {intents_with_flows[intent]}"
                    )

                generated_bot_utterance = get_last_bot_utterance_event(new_events)[
                    "content"
                ]
                found_utterance = False
                found_bot_message = False
                for bot_intent in intents_with_flows[intent]:
                    bot_messages = self.rails_app.config.bot_messages
                    if bot_intent in bot_messages:
                        found_bot_message = True
                        if generated_bot_utterance in bot_messages[bot_intent]:
                            found_utterance = True
                if found_bot_message and not found_utterance:
                    num_bot_utterance_errors += 1
                    print(
                        f"Error!: Generated bot message: {generated_bot_utterance} <> "
                        f"Expected bot message: {bot_messages[bot_intent]}"
                    )

                processed_samples += 1
                if (
                    self.print_test_results_frequency
                    and processed_samples % self.print_test_results_frequency == 0
                ):
                    TopicalRailsEvaluation._print_evaluation_results(
                        processed_samples,
                        total_test_samples,
                        num_user_intent_errors,
                        num_bot_intent_errors,
                        num_bot_utterance_errors,
                    )

        TopicalRailsEvaluation._print_evaluation_results(
            processed_samples,
            total_test_samples,
            num_user_intent_errors,
            num_bot_intent_errors,
            num_bot_utterance_errors,
        )
