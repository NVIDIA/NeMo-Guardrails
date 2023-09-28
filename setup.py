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


"""Install, build and package the `nemoguardrails` package."""

from setuptools import find_packages, setup

setup(
    name="nemoguardrails",
    version="0.5.0",
    packages=find_packages(),
    author="NVIDIA",
    author_email="nemoguardrails@nvidia.com",
    description="NeMo Guardrails is an open-source toolkit for easily adding "
    "programmable guardrails to LLM-based conversational systems.",
    long_description="""NeMo Guardrails is an open-source toolkit for easily adding
    programmable guardrails to LLM-based conversational systems.
    Guardrails (or "rails" for short) are specific ways of controlling the output of an LLM,
    e.g., not talking about politics, responding in a particular way to specific user
    requests, following a predefined dialog path, using a particular language style,
    extracting structured data, etc.""",
    long_description_content_type="text/markdown",
    url="https://github.com/NVIDIA/NeMo-Guardrails",
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: Apache Software License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
    ],
    entry_points={
        "console_scripts": ["nemoguardrails=nemoguardrails.__main__:app"],
    },
    package_data={
        "nemoguardrails": [
            "**/*.yml",
            "**/*.co",
            "**/*.txt",
            "**/*.json",
            "../examples/**/*",
            "../chat-ui/**/*",
            "eval/data/**/*",
        ],
    },
    install_requires=[
        "pydantic~=1.10.6",
        "aiohttp>=3.8.5",
        "langchain>=0.0.251",
        "requests>=2.31.0",
        "typer>=0.7.0",
        "PyYAML~=6.0",
        "setuptools~=65.5.1",
        "annoy>=1.17.3",
        "sentence-transformers>=2.2.2",
        "fastapi>=0.96.0",
        "starlette>=0.27.0",
        "uvicorn>=0.22.0",
        "httpx>=0.23.3",
        "simpleeval>=0.9.13",
        "typing-extensions>=4.5.0",
        "Jinja2>=3.1.2",
        "nest-asyncio>=1.5.6",
    ],
    extras_require={
        "eval": ["tqdm~=4.65", "numpy~=1.24"],
    },
)
