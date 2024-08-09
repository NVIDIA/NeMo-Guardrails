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

import argparse
import os
import random
from concurrent.futures import ThreadPoolExecutor
from time import time
from typing import Dict, List, Optional

import streamlit as st
from pydantic import BaseModel

from nemoguardrails.eval.models import EvalConfig, EvalOutput
from nemoguardrails.eval.utils import get_output_paths, update_dict_at_path


class EvalData(BaseModel):
    """Data relation to an evaluation, relevant for the UI."""

    eval_config_path: str
    eval_config: EvalConfig
    output_paths: List[str]
    selected_output_path: Optional[str] = None
    eval_outputs: Dict[str, EvalOutput]

    def update_results(self):
        """Updates back the evaluation results."""
        t0 = time()
        results = [
            r.dict() for r in self.eval_outputs[self.selected_output_path].results
        ]
        update_dict_at_path(self.selected_output_path, {"results": results})
        print(f"Updating output results took {time() - t0:.2f} seconds.")

    def update_results_and_logs(self, output_path: str):
        """Update back the results and the logs."""
        t0 = time()
        results = [r.dict() for r in self.eval_outputs[output_path].results]
        logs = [r.dict() for r in self.eval_outputs[output_path].logs]
        update_dict_at_path(output_path, {"results": results, "logs": logs})
        print(f"Updating output results took {time() - t0:.2f} seconds.")

    def update_config_latencies(self):
        """Update back the expected latencies."""
        t0 = time()
        update_dict_at_path(
            self.eval_config_path,
            {"expected_latencies": self.eval_config.expected_latencies},
        )
        print(f"Updating expected latencies took {time() - t0:.2f} seconds.")


@st.cache_resource
def get_span_colors(_eval_output: EvalOutput):
    """Helper to get colors for the spans."""
    random.seed(4)
    colors = {}
    for log in _eval_output.logs:
        for span in reversed(log.trace):
            if span.name not in colors:
                colors[span.name] = "#" + "".join(
                    [random.choice("0123456789ABCDEF") for _ in range(6)]
                )
    return colors


@st.cache_resource
def load_eval_data():
    """Loads the evaluation data"""
    # Setup argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--eval-config-path", type=str, default="")
    parser.add_argument("--output-path", nargs="+", type=str, default=[])

    # Parse arguments
    args = parser.parse_args()

    # Load the evaluation configuration
    eval_config_path = os.path.abspath(args.eval_config_path)
    eval_config = EvalConfig.from_path(eval_config_path)

    # If no explicit output paths are provided, load all the output
    # dirs from the current folder
    if not args.output_path:
        args.output_path = get_output_paths()

    eval_outputs = {}
    for output_path in args.output_path:
        # We use relative paths to CWD to have them shorter in the UI
        output_path = os.path.relpath(output_path, os.getcwd())

        if os.path.basename(output_path).startswith("."):
            continue

        # Load the output
        eval_output = EvalOutput.from_path(output_path)
        eval_outputs[output_path] = eval_output

    return EvalData(
        eval_config_path=eval_config_path,
        output_paths=args.output_path,
        eval_config=eval_config,
        eval_outputs=eval_outputs,
    )
