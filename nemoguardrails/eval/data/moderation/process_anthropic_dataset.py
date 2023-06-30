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

import typer


def load_dataset(input_path, split="harmful"):
    """
    Loads the dataset from the given path.
    """

    if split == "harmful":
        with open(input_path, "r", encoding="utf-8") as f:
            data = json.load(f)
    else:
        with open(input_path, "r", encoding="utf-8") as f:
            data = []
            for line in f:
                data.append(json.loads(line))

    return data


def split_messages(message):
    """
    Splits a message into two lists of human and assistant messages.

    Args:
        message (str): The message to split.

    Returns:
        two lists - one for human messages and one for assistant messages.
    """
    messages = message.split("\n\n")[1:]
    human = [m.replace("Human: ", "") for i, m in enumerate(messages) if i % 2 == 0]
    assistant = [
        m.replace("Assistant: ", "") for i, m in enumerate(messages) if i % 2 != 0
    ]
    return human, assistant


def process_anthropic_harmful_data(input_path: str, rating: float):
    """
    Extracts the first turn harmful prompts from the red team attempts dataset.
    The dataset can be downloaded from Huggingface and has to be unzipped.
    """

    dataset = load_dataset(input_path, split="harmful")
    first_turn_data = []

    for d in dataset:
        human_utterance, assistant_response = split_messages(d["transcript"])
        if d["rating"] == rating:
            first_turn_data.append(human_utterance[0])

    with open(f"anthropic_harmful.txt", "w", encoding="utf-8") as f:
        for line in first_turn_data:
            f.write(line + "\n")


def process_anthropic_helpful_data(input_path: str):
    """
    Extracts the first turn helpful prompts from the helpful-base dataset.
    The dataset can be downloaded from Huggingface and it has to be unzipped.
    """

    dataset = load_dataset(input_path, split="helpful")
    first_turn_data = []

    for d in dataset:
        human_utterance, assistant_response = split_messages(d["chosen"])
        first_turn_data.append(human_utterance[0])

    with open(f"anthropic_helpful.txt", "w", encoding="utf-8") as f:
        for line in first_turn_data:
            f.write(line + "\n")


def main(
    dataset_path: str = typer.Option(
        "red_team_attempts.jsonl",
        help="Path to the red team attempts dataset or the Anthropic Helpful-Base dataset - Can be downloaded from https://huggingface.co/datasets/Anthropic/hh-rlhf/",
    ),
    rating: float = typer.Option(
        4.0,
        help="Rating by which to filter the Red Team Attempts dataset. Values range from 0.0 to 4.0 with higher numbers indicating prompts that got more inappropriate responses from the model. Default is 4.0",
    ),
    split: str = typer.Option("harmful", help="Whether prompts are harmful or helpful"),
):
    """
    Extracts the first turn harmful or helpful prompts from the red team attempts dataset.
    """

    if split == "harmful":
        process_anthropic_harmful_data(dataset_path, rating)
    else:
        process_anthropic_helpful_data(dataset_path)


if __name__ == "__main__":
    typer.run(main)
