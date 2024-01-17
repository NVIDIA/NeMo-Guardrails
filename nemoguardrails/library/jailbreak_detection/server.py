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

import typer
import uvicorn
from fastapi import FastAPI
from pydantic import BaseModel
from heuristics import checks

app = FastAPI()
cli_app = typer.Typer()

device = os.environ.get("JAILBREAK_CHECK_DEVICE", "cpu")


class JailbreakCheckRequest(BaseModel):
    prompt: str  # User utterance to the model
    lp_threshold: float  # threshold for length-perplexity metric


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
    lp_threshold = request.lp_threshold if request.lp_threshold is not None else 89.79
    return checks.check_jb_lp(request.prompt, lp_threshold)


@app.post("/heuristics")
def run_all_heuristics(request: JailbreakCheckRequest):
    # Will add other heuristics as they become available
    lp_threshold = request.lp_threshold if request.lp_threshold is not None else 89.79
    lp_check = checks.check_jb_lp(request.prompt, lp_threshold)
    jailbreak = any([lp_check["jailbreak"]])
    heuristic_checks = {
        "jailbreak": jailbreak,
        "length_perplexity": lp_check["jailbreak"],
    }
    return heuristic_checks


@cli_app.command()
def start(
    port: int = typer.Option(
        default=1337, help="The port that the server should listen on."
    ),
):
    uvicorn.run(app, host="0.0.0.0", port=port)


if __name__ == "__main__":
    cli_app()
