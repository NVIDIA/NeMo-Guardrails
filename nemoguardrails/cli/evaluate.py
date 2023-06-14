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

from nemoguardrails import LLMRails, RailsConfig
from nemoguardrails.actions.llm.utils import (
    get_last_bot_intent_event,
    get_last_bot_utterance_event,
    get_last_user_intent_event,
)


def sync_wrapper(async_func):
    def wrapper(*args, **kwargs):
        loop = asyncio.get_event_loop()
        return loop.run_until_complete(async_func(*args, **kwargs))

    return wrapper


@sync_wrapper
async def run_evaluate(config_path: str, verbose: bool = False):
    """Runs a chat session in the terminal."""

    test_set = {}
    rails_config = RailsConfig.from_path(
        config_path, test_set_percentage=0.3, test_set=test_set
    )

    # TODO: add support for loading a config directly from live playground
    # rails_config = RailsConfig.from_playground(model="...")

    # TODO: add support to register additional actions
    # rails_app.register_action(...)

    rails_app: LLMRails = LLMRails(rails_config, verbose=verbose)

    # Find the intents that do not have a flow that matches them
    intents_with_flows = {}
    for flow in rails_config.flows:
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
        set(test_set.keys()).intersection(intents_with_flows.keys())
    )

    print(
        textwrap.dedent(
            f"""Started processing rails app from path: {config_path}.
            Number of intents: {len(test_set.keys())}.
            Number of flows: {len(rails_config.flows)}.
            Number of intents that have an associated flow: {num_intents_with_flows}.
            Intents without associated flows: {set(test_set.keys()).difference(intents_with_flows.keys())}."""
        )
    )

    # Run all samples in the test set one by one
    processed_samples = 0
    num_user_intent_errors = 0
    num_bot_intent_errors = 0
    num_bot_utterance_errors = 0
    max_tests_per_intent = 3

    for intent, samples in test_set.items():
        # Limit the number of samples per intent
        if len(samples) > max_tests_per_intent:
            samples = samples[:max_tests_per_intent]

        for sample in samples:
            # history = [{"role": "user", "content": sample}]
            # bot_message = rails_app.generate(messages=history)

            history_events = [{"type": "user_said", "content": sample}]
            new_events = await rails_app.runtime.generate_events(history_events)

            generated_user_intent = get_last_user_intent_event(new_events)["intent"]
            if generated_user_intent != intent:
                num_user_intent_errors += 1
                print(
                    f"Error!: Generated intent: {generated_user_intent} <> Expected intent: {intent}"
                )

            generated_bot_intent = get_last_bot_intent_event(new_events)["intent"]
            if generated_bot_intent not in intents_with_flows[intent]:
                num_bot_intent_errors += 1
                print(
                    f"Error!: Generated bot intent: {generated_bot_intent} <> Expected bot intent: {intents_with_flows[intent]}"
                )

            generated_bot_utterance = get_last_bot_utterance_event(new_events)[
                "content"
            ]
            found_utterance = False
            found_bot_message = False
            for bot_intent in intents_with_flows[intent]:
                if bot_intent in rails_config.bot_messages:
                    found_bot_message = True
                    if generated_bot_utterance in rails_config.bot_messages[bot_intent]:
                        found_utterance = True
            if found_bot_message and not found_utterance:
                num_bot_utterance_errors += 1
                print(
                    f"Error!: Generated bot message: {generated_bot_utterance} <> Expected bot message: {rails_config.bot_messages[bot_intent]}"
                )

            processed_samples += 1
            if processed_samples % 10 == 0:
                print(
                    textwrap.dedent(
                        f"Processed {processed_samples} samples! "
                        f"Num intent errors: {num_user_intent_errors}. "
                        f"Num bot intent errors {num_bot_intent_errors}. "
                        f"Num bot message errors {num_bot_utterance_errors}."
                    )
                )

    print(
        textwrap.dedent(
            f"Processed {processed_samples} samples! "
            f"Num intent errors: {num_user_intent_errors}. "
            f"Num bot intent errors {num_bot_intent_errors}. "
            f"Num bot message errors {num_bot_utterance_errors}."
        )
    )
