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
    """
    Retrieves relevant chunks of information from the knowledge base and adds them to the context.

    Args:
        context (Optional[dict], optional): A dictionary containing relevant context information.
            Defaults to None.
        kb (Optional[KnowledgeBase], optional): An instance of the KnowledgeBase. Defaults to None.

    Returns:
        ActionResult: An ActionResult containing relevant chunks of information in the context_updates.

    Note:
        This action retrieves relevant chunks of information from the knowledge base based on the user's message.
        It then adds these chunks to the context, making them available for further interactions.

    Example:
        ```python
        user_message = "Tell me about climate change."
        kb = KnowledgeBase()

        result = await retrieve_relevant_chunks({"last_user_message": user_message}, kb)

        # The result will contain relevant chunks of information in the context_updates.
        ```
    """    
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
