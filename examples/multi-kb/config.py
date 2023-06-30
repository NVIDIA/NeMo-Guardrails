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
from typing import Optional

from langchain import OpenAI
from langchain.chains import RetrievalQAWithSourcesChain
from langchain.embeddings import OpenAIEmbeddings
from langchain.vectorstores import Chroma

from nemoguardrails import LLMRails
from nemoguardrails.actions import action
from nemoguardrails.actions.actions import ActionResult

CHROMA_DB = "xxx"


def _get_qa_chain_with_sources():
    # extract embeddings
    embeddings = OpenAIEmbeddings(openai_api_key=os.environ["OPENAI_API_KEY"])
    collection_name = "langchain"

    # Now we can load the persisted database from disk, and use it as normal.
    vectordb = Chroma(
        persist_directory=CHROMA_DB,
        embedding_function=embeddings,
        collection_name=collection_name,
    )

    qa_chain = RetrievalQAWithSourcesChain.from_chain_type(
        OpenAI(temperature=0),
        chain_type="stuff",
        retriever=vectordb.as_retriever(),
        return_source_documents=True,
    )

    return qa_chain


qa_chain_with_sources = _get_qa_chain_with_sources()


@action(is_system_action=True)
async def retrieve_relevant_chunks(
    context: Optional[dict] = None,
):
    """Retrieve relevant chunks from the knowledge base and add them to the context."""
    user_message = context.get("last_user_message")

    # TODO: query one or multiple KBs
    result = await qa_chain_with_sources.acall(inputs={"question": user_message})

    # TODO: make call to an additional KB (one that understands table data?)

    context_updates = {
        "relevant_chunks": f"""
            Question: {user_message}
            Answer: {result['answer']}
            Sources: {result['sources']}
    """,
        "relevant_sources": result["sources"],
    }

    return ActionResult(
        return_value=context_updates["relevant_chunks"],
        context_updates=context_updates,
    )


def init(llm_rails: LLMRails):
    llm_rails.register_action(retrieve_relevant_chunks, "retrieve_relevant_chunks")
