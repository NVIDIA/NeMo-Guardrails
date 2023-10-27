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
import os
import time
from datetime import datetime
from typing import Optional

import pinecone
from langchain.chains import RetrievalQA
from langchain.embeddings.openai import OpenAIEmbeddings
from langchain.llms import BaseLLM
from langchain.vectorstores import Pinecone
from nemoguardrails import LLMRails
from nemoguardrails.actions import action
from nemoguardrails.actions.actions import ActionResult
from nemoguardrails.llm.taskmanager import LLMTaskManager

OPENAI_API_KEY = os.environ.get("OPENAI_API_KEY")
PINECONE_API_KEY = os.environ.get("PINECONE_API_KEY")
PINECONE_ENVIRONMENT = os.environ.get("PINECONE_ENVIRONMENT")
index_name = "nemoguardrailsindex"

LOG_FILENAME = datetime.now().strftime("logs/mylogfile_%H_%M_%d_%m_%Y.log")
log = logging.getLogger(__name__)
logging.basicConfig(filename=LOG_FILENAME, level=logging.DEBUG)


@action(is_system_action=True)
async def answer_question_with_sources(
    llm_task_manager: LLMTaskManager,
    context: Optional[dict] = None,
    llm: Optional[BaseLLM] = None
):
    """Retrieve relevant chunks from the knowledge base and add them to the context."""
    user_message = context.get("last_user_message")
    text_field = "text"
    embed = OpenAIEmbeddings(model=[model.model for model in llm_task_manager.config.models if model.type == "embeddings"][0], 
                             openai_api_key=OPENAI_API_KEY)
    vectorstore = Pinecone(pinecone.Index(index_name),
                           embed.embed_query, text_field)
    qa_with_sources = RetrievalQA.from_chain_type(
        llm=llm, chain_type="stuff",
        retriever=vectorstore.as_retriever(
            search_type="mmr", search_kwargs={'fetch_k': 30}),
        return_source_documents=True)

    start_time = time.time()
    result = qa_with_sources(user_message)
    print(
        "Getting the answer back from pinecone took: ",
        time.time() - start_time,
        " seconds!",
    )
    answer = result["result"]
    source_ref = str(result["source_documents"])
    '''
    Note: Relevant chunks are stored in source_ref with the following format, 
    and urls are already contained inside the metadata tag of source_ref
    {'query': '',
    'result': '',
    'source_documents': [Document(page_content='...', 
    metadata={'chunk': int, 'id': 'int', 'source': '/path/to/file.pdf'}),
    ]
    }
    '''
    context_updates = {
        "relevant_chunks": source_ref,
        "user_question": user_message,
        "bot_response": answer,
    }
    return ActionResult(
        return_value=context_updates["relevant_chunks"],
        context_updates=context_updates,
    )
def init(app: LLMRails):
    app.register_action(answer_question_with_sources,
                        "answer_question_with_sources")
