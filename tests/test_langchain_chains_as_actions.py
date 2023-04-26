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

from langchain.chains import ConstitutionalChain
from langchain.chains.constitutional_ai.models import ConstitutionalPrinciple

from nemoguardrails import RailsConfig
from nemoguardrails.rails.llm.context_var_chain import ContextVarChain
from tests.utils import TestChat

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


def test_chains_as_actions():
    """Test registering chains directly as actions."""
    config = RailsConfig.from_content(COLANG_CONFIG)
    chat = TestChat(
        config,
        llm_completions=[
            "  request service status",
            '  "The service is up and running smoothly."',
            "Not good",
            "The service is working smoothly.",
        ],
    )

    constitutional_chain = ConstitutionalChain.from_llm(
        llm=chat.llm,
        chain=ContextVarChain(var_name="last_bot_message"),
        constitutional_principles=[
            ConstitutionalPrinciple(
                critique_request="Tell if this answer is good.",
                revision_request="Give a better answer.",
            )
        ],
    )

    chat.app.register_action(constitutional_chain, name="check_if_constitutional")

    chat >> "Tell me if the service is up"
    chat << "The service is working smoothly."
