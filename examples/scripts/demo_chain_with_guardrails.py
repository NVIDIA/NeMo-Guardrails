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

"""Example of using a QnA chain with guardrails."""
import logging
import os

from langchain.chains import RetrievalQA
from langchain.document_loaders import TextLoader
from langchain.embeddings import OpenAIEmbeddings
from langchain.text_splitter import CharacterTextSplitter
from langchain.vectorstores import Chroma

from nemoguardrails import LLMRails, RailsConfig

logging.basicConfig(level=logging.INFO)

COLANG_CONFIG = """
define user express greeting
  "hi"

define user express insult
  "You are stupid"

# Basic guardrail against insults.
define flow
  user express insult
  bot express calmly willingness to help

# Here we use the QA chain for anything else.
define flow
  user ...
  $answer = execute qa_chain(query=$last_user_message)
  bot $answer

"""

YAML_CONFIG = """
models:
  - type: main
    engine: openai
    model: gpt-3.5-turbo-instruct
"""


def _get_qa_chain(llm):
    """Initializes a QA chain using the jobs report.

    It uses OpenAI embeddings.
    """
    loader = TextLoader(
        os.path.join(
            os.path.dirname(__file__),
            "../..",
            "examples/bots/abc/kb/employee-handbook.md",
        )
    )
    docs = loader.load()
    text_splitter = CharacterTextSplitter(chunk_size=1000, chunk_overlap=0)
    texts = text_splitter.split_documents(docs)

    embeddings = OpenAIEmbeddings()
    docsearch = Chroma.from_documents(texts, embeddings)

    qa_chain = RetrievalQA.from_chain_type(
        llm=llm, chain_type="stuff", retriever=docsearch.as_retriever()
    )

    return qa_chain


def demo():
    """Demo of using a chain as a custom action."""
    config = RailsConfig.from_content(COLANG_CONFIG, YAML_CONFIG)
    app = LLMRails(config)

    # Create and register the chain directly as an action.
    qa_chain = _get_qa_chain(app.llm)
    app.register_action(qa_chain, name="qa_chain")

    # Change to mode here to experiment with the multiple ways of using the chain

    # mode = "chain"
    mode = "chain_with_guardrails"
    # mode = "chat_with_guardrails"

    if mode == "chain":
        query = "How many vacation days do I get?"
        result = qa_chain.run(query)

        print(result)

    elif mode == "chain_with_guardrails":
        history = [{"role": "user", "content": "How many vacation days do I get?"}]
        result = app.generate(messages=history)
        print(result)

    elif mode == "chat_with_guardrails":
        history = []
        while True:
            user_message = input("> ")

            history.append({"role": "user", "content": user_message})
            bot_message = app.generate(messages=history)
            history.append(bot_message)

            # We print bot messages in green.
            print(f"\033[92m{bot_message['content']}\033[0m")


if __name__ == "__main__":
    demo()
