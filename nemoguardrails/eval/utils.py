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
from time import time
from typing import Any, Dict, List, Union

import yaml

from nemoguardrails.utils import CustomDumper


def load_dict_from_file(file_path: str) -> Dict[str, Any]:
    """Helper to load a dict from a file based on its extension."""
    filename, file_extension = os.path.splitext(file_path)

    _obj = {}
    if file_extension == ".yaml" or file_extension == ".yml":
        with open(file_path) as f:
            _obj = yaml.safe_load(f)
    elif file_extension == ".json":
        with open(file_path) as f:
            _obj = json.load(f)

    return _obj


def load_dict_from_path(path: str) -> Dict[str, Any]:
    """Load a dict from a path.

    It recursively loads all .json and .yaml files in the given path.
    Top level arrays are joined.
    """
    obj = {}

    for root, _, files in os.walk(path, followlinks=True):
        for file in files:
            full_path = os.path.join(root, file)
            _obj = load_dict_from_file(full_path)

            # Join the config object by extending the top level arrays if that's the case.
            for k, v in _obj.items():
                if k not in obj:
                    obj[k] = v
                else:
                    assert isinstance(obj[k], list) and isinstance(v, list)
                    obj[k].extend(v)

    return obj


def update_dict_at_path(path: str, d: dict):
    """Updates a dictionary at the specified path.

    It recursively looks at all .json and .yaml files in the given path.
    for every file that contains a top level key found in `d`, it is updated.
    """
    for root, _, files in os.walk(path, followlinks=True):
        for file in files:
            full_path = os.path.join(root, file)
            _obj = load_dict_from_file(full_path)

            changed = False
            for k in d:
                if k in _obj:
                    _obj[k] = d[k]
                    changed = True

            if changed:
                save_dict_to_file(_obj, full_path)


def save_dict_to_file(val: Any, output_path: str, output_format: str = "yaml"):
    """Helper to write data to a file in the chosen format."""
    _, ext = os.path.splitext(output_path)
    if ext:
        output_format = ext[1:]

    if output_format == "yaml" or output_format == "yml":
        if not output_path.endswith(".yaml") and not output_path.endswith(".yml"):
            output_path += ".yaml"

        with open(output_path, "w") as output_file:
            output_file.write(
                yaml.dump(
                    val,
                    sort_keys=False,
                    Dumper=CustomDumper,
                    width=1000,
                )
            )
    elif output_format == "json":
        if not output_path.endswith(".json"):
            output_path += ".json"

        with open(output_path, "w") as output_file:
            output_file.write(json.dumps(val, indent=True))


def save_eval_output(
    eval_output: "EvalOutput", output_path: str, output_format: str = "yaml"
):
    """Writes the evaluation output to a folder."""
    data = eval_output.dict()

    save_dict_to_file(
        {"results": data["results"]},
        os.path.join(output_path, "results"),
        output_format,
    )
    save_dict_to_file(
        {"logs": data["logs"]}, os.path.join(output_path, "logs"), output_format
    )


def collect_interaction_metrics(
    interaction_outputs: List["InteractionOutput"],
) -> Dict[str, Union[int, float]]:
    """Collects and aggregates the metrics from all the interactions."""
    metrics = {}
    counters = {}
    for interaction_output in interaction_outputs:
        for metric in interaction_output.resource_usage:
            metrics[metric] = (
                metrics.get(metric, 0) + interaction_output.resource_usage[metric]
            )
            counters[metric] = counters.get(metric, 0) + 1

        for metric in interaction_output.latencies:
            metrics[metric] = (
                metrics.get(metric, 0) + interaction_output.latencies[metric]
            )
            counters[metric] = counters.get(metric, 0) + 1

    # For the avg metrics, we need to average them
    for metric in counters:
        if metric.endswith("_avg"):
            metrics[metric] = metrics[metric] / counters[metric]

    return metrics


def get_output_paths() -> List[str]:
    """Helper to return the output paths from the current dir."""
    base_path = os.getcwd()
    return [
        os.path.join(base_path, folder)
        for folder in os.listdir(base_path)
        if folder != "config" and folder[0] != "."
    ]


def update_results(eval_data: "EvalData"):
    """Helper to save changes to the evaluation results."""
    t0 = time()
    results = [
        r.dict() for r in eval_data.eval_outputs[eval_data.selected_output_path].results
    ]
    update_dict_at_path(eval_data.selected_output_path, {"results": results})
    print(f"Updating output results took {time() - t0:.2f} seconds.")


def update_results_and_logs(eval_output: "EvalOutput", output_path: str):
    """Helper to save changes to the evaluation results."""
    t0 = time()
    results = [r.dict() for r in eval_output.results]
    logs = [r.dict() for r in eval_output.logs]
    update_dict_at_path(output_path, {"results": results, "logs": logs})
    print(f"Updating output results took {time() - t0:.2f} seconds.")
