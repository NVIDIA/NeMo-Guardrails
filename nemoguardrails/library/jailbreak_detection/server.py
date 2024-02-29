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
from typing import Optional

import typer
import uvicorn
from fastapi import FastAPI
from heuristics import checks
from pydantic import BaseModel

app = FastAPI()
cli_app = typer.Typer()

device = os.environ.get("JAILBREAK_CHECK_DEVICE", "cpu")


class JailbreakCheckRequest(BaseModel):
    """
    prompt (str): User utterance to the model
    lp_threshold (float): Threshold value for length-perplexity heuristic. Default: 89.79
    ps_ppl_threshold (float): Threshold value for prefix/suffix perplexity heuristic. Default: 1845.65
    """

    prompt: str
    lp_threshold: Optional[float] = 89.79
    ps_ppl_threshold: Optional[float] = 1845.65


@app.get("/")
def hello_world():
    welcome_str = (
        "This is a development server for jailbreak detection.\n"
        "Hit the /heuristics endpoint to run all heuristics by sending a POST request with the user prompt.\n"
        "Detailed documentation and all endpoints are included in the README."
    )
    return welcome_str


@app.post("/jailbreak_lp_heuristic")
def lp_heuristic_check(request: JailbreakCheckRequest):
    return checks.check_jailbreak_length_per_perplexity(
        request.prompt, request.lp_threshold
    )


@app.post("/jailbreak_ps_heuristic")
def ps_ppl_heuristic_check(request: JailbreakCheckRequest):
    return checks.check_jailbreak_prefix_suffix_perplexity(
        request.prompt, request.ps_ppl_threshold
    )


@app.post("/heuristics")
def run_all_heuristics(request: JailbreakCheckRequest):
    # Will add other heuristics as they become available
    lp_check = checks.check_jailbreak_length_per_perplexity(
        request.prompt, request.lp_threshold
    )
    ps_ppl_check = checks.check_jailbreak_prefix_suffix_perplexity(
        request.prompt, request.ps_ppl_threshold
    )
    jailbreak = any([lp_check["jailbreak"], ps_ppl_check["jailbreak"]])
    heuristic_checks = {
        "jailbreak": jailbreak,
        "length_per_perplexity": lp_check["jailbreak"],
        "prefix_suffix_perplexity": ps_ppl_check["jailbreak"],
    }
    return heuristic_checks


@cli_app.command()
def start(
    port: int = typer.Option(
        default=1337, help="The port that the server should listen on."
    ),
    host: str = typer.Option(default="0.0.0.0", help="IP address of the host"),
):
    uvicorn.run(app, host=host, port=port)


if __name__ == "__main__":
    cli_app()
