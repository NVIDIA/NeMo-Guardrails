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
from langchain.chains import RetrievalQAWithSourcesChain
from langchain.vectorstores import Chroma
from nemoguardrails import LLMRails
from nemoguardrails.actions import action
from nemoguardrails.actions.actions import ActionResult
from langchain.text_splitter import CharacterTextSplitter
from langchain.document_loaders import TextLoader
from functools import lru_cache
import faiss
from langchain import HuggingFacePipeline
from nemoguardrails.llm.helpers import get_llm_instance_wrapper
from nemoguardrails.llm.providers import register_llm_provider
import torch
from langchain import HuggingFacePipeline
from langchain.base_language import BaseLanguageModel
from langchain.embeddings import HuggingFaceEmbeddings
from langchain.vectorstores import FAISS
from langchain.chains.qa_with_sources import load_qa_with_sources_chain
import pickle
import transformers
from langchain import HuggingFacePipeline
from langchain.base_language import BaseLanguageModel
from transformers import AutoTokenizer, pipeline
from pathlib import Path


def _make_chromadb(data_path,embeddings):

    # load the document and split it into chunks
    loader = TextLoader(data_path)
    documents = loader.load()

    # split it into chunks
    text_splitter = CharacterTextSplitter(chunk_size=100, chunk_overlap=0)
    docs = text_splitter.split_documents(documents)
    db = Chroma.from_documents(docs, embeddings ,persist_directory="/workspace/Experiment/SE")
    return db

def _make_faiss_gpu(data_path,embeddings):
    # Here we load in the data in the format that Notion exports it in.
    ps = list(Path("/workspace/ckpt/data/").glob('**/*.txt'))
    print(ps)
    data = []
    sources = []
    for p in ps:
        with open(p) as f:
            data.append(f.read())
        sources.append(p)

    # We do this due to the context limits of the LLMs.
    # Here we split the documents, as needed, into smaller chunks.
    # We do this due to the context limits of the LLMs.
    text_splitter = CharacterTextSplitter(chunk_size=200, separator="\n")
    docs = []
    metadatas = []
    for i, d in enumerate(data):
        splits = text_splitter.split_text(d)
        docs.extend(splits)
        metadatas.extend([{"source": sources[i]}] * len(splits))

    # Here we create a vector store from the documents and save it to disk.
    store = FAISS.from_texts(docs, embeddings, metadatas=metadatas)
    faiss.write_index(store.index, "/workspace/Experiment/docs.index")
    store.index = None
    with open("/workspace/Experiment/faiss_store.pkl", "wb") as f:
        pickle.dump(store, f)
    return store

def _get_qa_chain_with_sources():
    # extract embeddings
    model_name = "sentence-transformers/all-mpnet-base-v2"
    model_kwargs = {"device": "cuda"}

    hf_embedding = HuggingFaceEmbeddings(model_name=model_name, model_kwargs=model_kwargs)
    using_vectorstore='faiss'
    if using_vectorstore=='faiss':
        vectorestore_path =  "/workspace/Experiment/"
        if vectorestore_path is not None:
            index = faiss.read_index(vectorestore_path+'docs.index')
            with open(vectorestore_path+"faiss_store.pkl", "rb") as f:
                vectordb = pickle.load(f)
            vectordb.index = index
        else:
            data_path=input("pleaes input the absolute path to the folder of many xxx.txt files for processing into vectorstore : ")
            vectordb = _make_faiss_gpu(data_path,hf_embedding)
    return vectordb


vectordb = _get_qa_chain_with_sources()


@action(is_system_action=True)
async def retrieve_relevant_chunks(
    context: Optional[dict] = None,
):
    """Retrieve relevant chunks from the knowledge base and add them to the context."""
    user_message = context.get("last_user_message")
    #hf_llm=retriver_llm()
    chain = load_qa_with_sources_chain(hf_llm, chain_type="stuff", verbose=True)
    docs = vectordb.similarity_search(user_message)
    result=chain({"input_documents": docs, "question": user_message}, return_only_outputs=False)
    """qa = RetrievalQAWithSourcesChain(
            combine_documents_chain=chain, 
            retriever=vectordb.as_retriever(),
            reduce_k_below_max_tokens=True,
      )"""
    # TODO: query one or multiple KBs
    #result = await qa_chain_with_sources.acall(inputs={"question": user_message})
    #result =await qa.acall({"question": user_message}, return_only_outputs=True)

    # TODO: make call to an additional KB (one that understands table data?)

    context_updates = {
        "relevant_chunks": f"""
            Question: {user_message}
            Answer: {result['output_text']}
    """ }

    return ActionResult(
        return_value=context_updates["relevant_chunks"],
        context_updates=context_updates,
    )

def init(llm_rails: LLMRails):
    llm_rails.register_action(retrieve_relevant_chunks, "retrieve_relevant_chunks")

def get_mosaic_7b_llm():
    name = "mosaicml/mpt-7b-instruct"
    config = transformers.AutoConfig.from_pretrained(name, trust_remote_code=True)
    config.init_device = "cuda:0"  # For fast initialization directly on GPU!
    config.max_seq_len = 4096
    #tokenizer = AutoTokenizer.from_pretrained("EleutherAI/gpt-neox-20b")
    model = transformers.AutoModelForCausalLM.from_pretrained(
        name,
        config=config,
        torch_dtype=torch.bfloat16,  # Load model weights in bfloat16
        trust_remote_code=True,
    )
    tokenizer = AutoTokenizer.from_pretrained("EleutherAI/gpt-neox-20b")


    pipe = pipeline(
        "text-generation",
        model=model,
        tokenizer=tokenizer,
        device="cuda:0",
        max_new_tokens=100,
        do_sample=True,
        use_cache=True,
    )

    hf_llm = HuggingFacePipeline(pipeline=pipe)
    return hf_llm

hf_llm=get_mosaic_7b_llm()
HFPipelineMosaic = get_llm_instance_wrapper(llm_instance=get_mosaic_7b_llm(), llm_type="hf_pipeline_mosaic")
register_llm_provider("hf_pipeline_mosaic", HFPipelineMosaic)