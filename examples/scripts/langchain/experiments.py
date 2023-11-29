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

from langchain.chains import LLMMathChain
from langchain.chat_models import ChatOpenAI
from langchain.prompts import ChatPromptTemplate
from langchain_core.tools import Tool
from pydantic import BaseModel, Field

from examples.scripts.langchain.runnable_rails import RunnableRails
from nemoguardrails import LLMRails, RailsConfig

# Set the LangSmith env variables
os.environ["LANGCHAIN_TRACING_V2"] = "true"
os.environ["LANGCHAIN_ENDPOINT"] = "https://api.smith.langchain.com"
# os.environ["LANGCHAIN_API_KEY"] = "***"
# os.environ["LANGCHAIN_PROJECT"] = "***"

YAML_CONTENT = """
models: []
rails:
  input:
    flows:
      - check jailbreak
"""

COLANG_CONTENT = """
define user express greeting
  "hi"
  "hello"

define user ask question
  "What can you do?"
  "Where is Paris?"
  "How tall is mountain Everest?"

define bot express greeting
  "Hello there!"

define flow
  user express greeting
  bot express greeting

define flow
  user ask question
  bot respond
"""

model = ChatOpenAI()


def experiment_1():
    """Basic setup with a prompt and a model."""
    prompt = ChatPromptTemplate.from_template("Write a paragraph about {topic}.")

    # ChatPromptValue -> LLM -> AIMessage
    chain = prompt | model

    for s in chain.stream({"topic": "Paris"}):
        print(s.content, end="", flush=True)


def experiment_2():
    """Basic setup invoking LLM rails directly."""
    rails_config = RailsConfig.from_content(
        yaml_content=YAML_CONTENT, colang_content=COLANG_CONTENT
    )
    rails = LLMRails(config=rails_config, llm=model)

    # print(rails.generate(messages=[{"role": "user", "content": "Hello!"}]))
    print(rails.generate(messages=[{"role": "user", "content": "Who invented chess?"}]))


def experiment_3():
    """Basic setup combining the two above.

    Wraps the model with a rails configuration
    """
    rails_config = RailsConfig.from_content(
        yaml_content=YAML_CONTENT, colang_content=COLANG_CONTENT
    )
    model_with_rails = RunnableRails(config=rails_config, llm=model)

    # Invoke the chain using the model with rails.
    prompt = ChatPromptTemplate.from_template("Write a paragraph about {topic}.")
    chain = prompt | model_with_rails

    # This works
    print(chain.invoke({"topic": "Bucharest"}))

    # This will hit the rail
    print(chain.invoke({"topic": "stealing a car"}))


MATH_COLANG_CONTENT = """

define user ask math question
  "What is the square root of 7?"
  "What is the formula for the area of a circle?"

define flow
  user ask math question
  $result = execute Calculator(tool_input=$user_message)
  bot respond
"""


def experiment_4():
    """Experiment with adding a tool as an action to a RunnableRails instance.

    This is essentially an Agent!
    An Agent is LangChain is a chain + an executor (AgentExecutor).
    - the chain is responsible for predicting the next step
    - the executor is responsible for invoking the tools if needed, and re-invoking the chain

    Since the LLMRails has a built-in executor (the Colang Runtime), the
    same effect can be achieved directly using RunnableRails directly.
    """
    tools = []

    class CalculatorInput(BaseModel):
        question: str = Field()

    llm_math_chain = LLMMathChain(llm=model, verbose=True)
    tools.append(
        Tool.from_function(
            func=llm_math_chain.run,
            name="Calculator",
            description="useful for when you need to answer questions about math",
            args_schema=CalculatorInput,
        )
    )

    rails_config = RailsConfig.from_content(
        yaml_content=YAML_CONTENT, colang_content=COLANG_CONTENT + MATH_COLANG_CONTENT
    )

    # We also add the tools.
    model_with_rails = RunnableRails(config=rails_config, llm=model, tools=tools)

    prompt = ChatPromptTemplate.from_template("{question}")
    chain = prompt | model_with_rails

    print(chain.invoke({"question": "What is 5+5*5/5?"}))


def experiment_5():
    """Other things to support."""
    # rails = RunnableRails(rails_config, model)

    # chain = prompt | rails.input | model
    # chain = prompt | model | rails.output


if __name__ == "__main__":
    # experiment_1()
    # experiment_2()
    # experiment_3()
    experiment_4()
