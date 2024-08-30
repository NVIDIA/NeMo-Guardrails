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

from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.pydantic_v1 import BaseModel
from langchain_core.runnables import RunnablePassthrough
from langchain_nvidia_ai_endpoints import ChatNVIDIA
from nemoguardrails import LLMRails, RailsConfig
from nemoguardrails.integrations.langchain.runnable_rails import RunnableRails

from ingest import retriever

llm = ChatNVIDIA(
    model="meta/llama-3.1-70b-instruct",
    temperature=0,
    top_p=0.7,
    max_tokens=1024,
)

prompt_template = """Based on the following context, answer the question in a single, short, and straightforward sentence.
If unsure, respond with 'I don't know.' Avoid jargon and keep the answer as simple as possible.

{context}

Question: {question}

Helpful Answer:"""

prompt = ChatPromptTemplate.from_template(prompt_template)

config = RailsConfig.from_path("./guardrails/llamaguard_config")
llamaguard = RunnableRails(
    config, input_key="question", output_key="answer", passthrough=False
)

chain = (
    {"context": retriever, "question": RunnablePassthrough()}
    | prompt
    | llm
    | StrOutputParser()
)

chain_with_llamaguard = llamaguard | chain


# Add typing for input
class Question(BaseModel):
    __root__: str


chain_with_llamaguard = chain_with_llamaguard.with_types(input_type=Question)

print(
    f"Hello, I am an AI Assistant that can answer any questions on NVIDIA AI Enterprise."
)
question = input("How can I help you today? \n\n")
print("\n")
print(f'{chain_with_llamaguard.invoke({"question": question})["answer"]}')
