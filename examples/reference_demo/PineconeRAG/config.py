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
from pprint import pprint
from typing import List, Optional
from uuid import uuid4

import fitz
import pinecone
import tiktoken
from datasets import Dataset
from langchain.chains import RetrievalQA, RetrievalQAWithSourcesChain
from langchain.chat_models import ChatOpenAI
from langchain.embeddings.openai import OpenAIEmbeddings
from langchain.llms import BaseLLM
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain.vectorstores import Pinecone
from tqdm.auto import tqdm

from nemoguardrails import LLMRails
from nemoguardrails.actions import action
from nemoguardrails.actions.actions import ActionResult
from nemoguardrails.embeddings.basic import OpenAIEmbeddingModel
from nemoguardrails.embeddings.index import EmbeddingsIndex, IndexItem

OPENAI_API_KEY = os.environ.get("OPENAI_API_KEY")
PINECONE_API_KEY = os.environ.get("PINECONE_API_KEY")
PINECONE_ENVIRONMENT = os.environ.get("PINECONE_ENVIRONMENT")
index_name = "nemoguardrailsindex"
model_name = "text-embedding-ada-002"
# todo different llm for different tasks
# https://github.com/NVIDIA/NeMo-Guardrails/blob/aa07d889e9437dc687cd1c0acf51678ad435516e/tests/test_configs/with_openai_embeddings/config.yml#L4

# import warnings
# warnings.filterwarnings("ignore")

LOG_FILENAME = datetime.now().strftime("logs/mylogfile_%H_%M_%d_%m_%Y.log")
log = logging.getLogger(__name__)
logging.basicConfig(filename=LOG_FILENAME, level=logging.DEBUG)


@action(is_system_action=True)
async def answer_question_with_sources(
    context: Optional[dict] = None, llm: Optional[BaseLLM] = None
):
    """Retrieve relevant chunks from the knowledge base and add them to the context."""
    user_message = context.get("last_user_message")
    text_field = "text"
    # switch back to normal index for langchain

    embed = OpenAIEmbeddings(model=model_name, openai_api_key=OPENAI_API_KEY)
    vectorstore = Pinecone(pinecone.Index(index_name), embed.embed_query, text_field)
    # vectorstore = Pinecone(pinecone.Index(index_name), OpenAIEmbeddingModel.embed_query, text_field)

    qa_with_sources = RetrievalQAWithSourcesChain.from_chain_type(
        llm=llm, chain_type="stuff", retriever=vectorstore.as_retriever()
    )
    start_time = time.time()
    result = qa_with_sources(context.get("last_user_message"))
    print(
        "Getting the answer back from pinecone took: ",
        time.time() - start_time,
        " seconds!",
    )
    answer = result["answer"]
    source_ref = str(result["sources"])

    context_updates = {
        "relevant_chunks": source_ref,
        "user_question": user_message,
        "bot_response": answer,
    }

    '''
    context_updates = {
        "relevant_chunks": f"""
                Question: {user_message}
                Answer: {answer},
                Citing: {"None--"}
                Source : {source_ref}
        """
    }
    '''

    return ActionResult(
        return_value=context_updates["relevant_chunks"],
        context_updates=context_updates,
    )


def init(app: LLMRails):
    app.register_action(answer_question_with_sources, "answer_question_with_sources")
