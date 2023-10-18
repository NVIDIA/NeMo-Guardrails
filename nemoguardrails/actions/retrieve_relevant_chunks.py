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

import logging
import random
from typing import Optional

from langchain import LLMChain, PromptTemplate
from langchain.llms import BaseLLM

from nemoguardrails.actions.actions import ActionResult, action
from nemoguardrails.kb.kb import KnowledgeBase

log = logging.getLogger(__name__)


@action(is_system_action=True)
async def retrieve_relevant_chunks(
    context: Optional[dict] = None,
    kb: Optional[KnowledgeBase] = None,
):
    """Retrieve relevant chunks from the knowledge base and add them to the context."""
    user_message = context.get("last_user_message")
    context_updates = {}
    context_updates["relevant_chunks"] = ""
    if user_message and kb:
        chunks = await kb.search_relevant_chunks(user_message)
        relevant_chunks = "\n".join([chunk["body"] for chunk in chunks])
        context_updates["relevant_chunks"] = relevant_chunks

    return ActionResult(
        return_value=context_updates["relevant_chunks"],
        context_updates=context_updates,
    )
