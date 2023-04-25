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

from typer.testing import CliRunner

from nemoguardrails.cli import app

runner = CliRunner()


def test_app():
    result = runner.invoke(
        app,
        [
            "chat",
            "--config=examples/rails/benefits_co/config.yml",
            "--config=examples/rails/benefits_co/general.co",
        ],
    )
    assert result.exit_code == 1
    assert "not supported" in result.stdout
    assert "Please provide a single" in result.stdout
