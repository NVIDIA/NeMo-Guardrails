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

from alignscore import AlignScore
from flask import Flask, request

app = Flask(__name__)

base_model = AlignScore(
    model="roberta-base",
    batch_size=32,
    device="cuda:0",
    ckpt_path="../AlignScore/AlignScore-base.ckpt",
    evaluation_mode="nli_sp",
)
large_model = AlignScore(
    model="roberta-large",
    batch_size=32,
    device="cuda:0",
    ckpt_path="../AlignScore/AlignScore-large.ckpt",
    evaluation_mode="nli_sp",
)


@app.route("/", methods=["GET"])
def hello_world():
    res_base = base_model.score(
        contexts=["This is an evidence passage."], claims=["This is a claim."]
    )
    res_large = large_model.score(
        contexts=["This is an evidence passage."], claims=["This is a claim."]
    )
    welcome_str = (
        f"This is a development server to host AlignScore models.\n"
        + f"<br>Hit the /alignscore_base or alignscore_large endpoints with a POST request containing evidence and claim.\n"
        + f"<br>Example: curl -X POST -d 'evidence=This is an evidence passage&claim=This is a claim.' http://localhost:5000/alignscore_base\n"
        + f"<br>Sample response from base model = {res_base}\n"
        + f"<br>Sample response from large model = {res_large}\n"
    )
    return welcome_str


def get_alignscore(model, evidence, claim):
    alignscore = model.score(contexts=[evidence], claims=[claim])[0]
    return f"{alignscore:.2f}"


@app.route("/alignscore_base", methods=["POST"])
def alignscore_base():
    data = request.json
    return get_alignscore(base_model, data["evidence"], data["claim"])


@app.route("/alignscore_large", methods=["POST"])
def alignscore_large():
    data = request.json
    return get_alignscore(large_model, data["evidence"], data["claim"])


if __name__ == "__main__":
    app.run(debug=True)
