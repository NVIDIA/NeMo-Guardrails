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

"""Demo script."""
import logging

from langchain.chains import ConstitutionalChain
from langchain.chains.constitutional_ai.models import ConstitutionalPrinciple

from nemoguardrails import LLMRails, RailsConfig
from nemoguardrails.rails.llm.context_var_chain import ContextVarChain

logging.basicConfig(level=logging.INFO)

COLANG_CONFIG = """
define user express greeting
  "hi"

define bot remove last message
  "(remove last message)"

define flow
  user ...
  bot respond
  $updated_msg = execute check_if_constitutional
  if $updated_msg != $last_bot_message
    bot remove last message
    bot $updated_msg
"""

YAML_CONFIG = """
models:
  - type: main
    engine: openai
    model: gpt-3.5-turbo-instruct
"""


def demo():
    """Demo of using a chain as a custom action."""
    config = RailsConfig.from_content(COLANG_CONFIG, YAML_CONFIG)

    app = LLMRails(config)

    constitutional_chain = ConstitutionalChain.from_llm(
        llm=app.llm,
        chain=ContextVarChain(var_name="last_bot_message"),
        constitutional_principles=[
            ConstitutionalPrinciple(
                critique_request="Tell if this answer is good.",
                revision_request="Give a better answer.",
            )
        ],
    )

    app.register_action(constitutional_chain, name="check_if_constitutional")

    history = [{"role": "user", "content": "Tell me if the service is up"}]
    result = app.generate(messages=history)
    print(result)


if __name__ == "__main__":
    demo()
