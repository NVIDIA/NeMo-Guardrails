# syntax=docker/dockerfile:experimental

# Copyright (c) 2019, NVIDIA CORPORATION. All rights reserved.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

FROM python:3.10

# Install git
RUN apt-get update && apt-get install -y git

# Install gcc/g++ for annoy
RUN apt-get install -y gcc g++

# We install this separately to speed up the rebuilding of images when dependencies change.
# This installs pytorch and co.
RUN pip install sentence-transformers==2.2.2

# Copy and install NeMo Guardrails
WORKDIR /nemoguardrails
COPY . /nemoguardrails
RUN pip install -e .[all]

# https://stackoverflow.com/questions/77290003/segmentation-fault-when-using-sentencetransformer-inside-docker-container
# Workaround for a bug when running on Apple M1/M2
RUN pip install torch==2.0.*

# Make port 800 available to the world outside this container
EXPOSE 8000

# Run app.py when the container launches
WORKDIR /nemoguardrails

# Link the default configs to the /config folder
RUN ln -s /nemoguardrails/examples/configs/_deprecated /config

# Download the transformer model
RUN python -c "from sentence_transformers import SentenceTransformer; model = SentenceTransformer('all-MiniLM-L6-v2')"

# Run this so that everything is initialized
RUN nemoguardrails --help

ENTRYPOINT ["/usr/local/bin/nemoguardrails"]
CMD ["server", "--verbose", "--config=/config"]
