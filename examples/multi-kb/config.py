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

from typing import Optional
from nemoguardrails import LLMRails
from nemoguardrails.actions import action
from nemoguardrails.actions.actions import ActionResult
from langchain.text_splitter import CharacterTextSplitter
import faiss
from langchain import HuggingFacePipeline
from nemoguardrails.llm.helpers import get_llm_instance_wrapper
from nemoguardrails.llm.providers import register_llm_provider
import torch
from langchain import HuggingFacePipeline
from langchain.embeddings import HuggingFaceEmbeddings
from langchain.vectorstores import FAISS
import pickle
from langchain import HuggingFacePipeline
from transformers import AutoTokenizer, pipeline, AutoTokenizer, AutoModelForSeq2SeqLM
from pathlib import Path
from langchain.chains import RetrievalQA
import textwrap
import transformers
import pandas as pd
from langchain import HuggingFacePipeline
from transformers import (
    AutoModelForCausalLM,
    AutoTokenizer,
    pipeline,
)

def load_model(model_name, device, num_gpus, debug=False):
    if device == "cpu":
        kwargs = {}
    elif device == "cuda":
        kwargs = {"torch_dtype": torch.float16}
        if num_gpus == "auto":
            kwargs["device_map"] = "auto"
        else:
            num_gpus = int(num_gpus)
            if num_gpus != 1:
                kwargs.update(
                    {
                        "device_map": "auto",
                        "max_memory": {i: "13GiB" for i in range(num_gpus)},
                    }
                )
    elif device == "mps":
        kwargs = {"torch_dtype": torch.float16}
        # Avoid bugs in mps backend by not using in-place operations.
        print("mps not supported")
    else:
        raise ValueError(f"Invalid device: {device}")

    tokenizer = AutoTokenizer.from_pretrained(model_name, use_fast=False)
    model = AutoModelForCausalLM.from_pretrained(
        model_name, low_cpu_mem_usage=True, **kwargs
    )

    if device == "cuda" and num_gpus == 1:
        model.to(device)

    if debug:
        print(model)

    return model, tokenizer



def _make_faiss_gpu(data_path, out_path, embeddings):
    # Here we process the txt files under the data_path folder.
    ps = list(Path(data_path).glob('**/*.txt'))
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
    faiss.write_index(store.index, out_path+"docs.index")
    store.index = None
    with open(out_path+"faiss_store.pkl", "wb") as f:
        pickle.dump(store, f)
    return store

def wrap_text_preserve_newlines(text, width=110):
    # Split the input text into lines based on newline characters
    lines = text.split('\n')

    # Wrap each line individually
    wrapped_lines = [textwrap.fill(line, width=width) for line in lines]

    # Join the wrapped lines back together using newline characters
    wrapped_text = '\n'.join(wrapped_lines)

    return wrapped_text

def process_llm_response(llm_response):
    print(wrap_text_preserve_newlines(llm_response['result']))
    print('\n\nSources:')
    for source in llm_response["source_documents"]:
        print(source.metadata['source'])


def _get_qa_chain_with_sources():
    # use other embeddings from huggingface
    model_name = "sentence-transformers/all-mpnet-base-v2"
    model_kwargs = {"device": "cuda"}

    hf_embedding = HuggingFaceEmbeddings(model_name=model_name, model_kwargs=model_kwargs)
    using_vectorstore='faiss'
    if using_vectorstore=='faiss':
        vectorestore_path =  "<path_to_already_processd_and_saved_to_disk_vectorstore>"
        if vectorestore_path is not None:
            index = faiss.read_index(vectorestore_path+'docs.index')
            with open(vectorestore_path+"faiss_store.pkl", "rb") as f:
                vectordb = pickle.load(f)
            vectordb.index = index
        else:
            data_path="<path to the folder contain xxx.txt files for processing into vectorstores>"
            out_path="<path to the folder where you would like to save the processed vectorstores>"
            vectordb = _make_faiss_gpu(data_path,out_path, hf_embedding)
    return vectordb


vectordb = _get_qa_chain_with_sources()


@action(is_system_action=True)
async def retrieve_relevant_chunks(
    context: Optional[dict] = None,
):
    """Retrieve relevant chunks from the knowledge base and add them to the context."""
    user_message = context.get("last_user_message")
    # identifying if user would like to query csv data ( i.e tabular data ) instead as an alternative kb
    if ("csv" or "table" or "tabular") in user_message:  
        csv_flag=True    
        tb_tokenizer = AutoTokenizer.from_pretrained("neulab/omnitab-large")
        tb_model = AutoModelForSeq2SeqLM.from_pretrained("neulab/omnitab-large")
        # TODO : find a workflow supporting custom tabular data flatten preprocessing
        # toy example to demonstrate flattened tabular data as KB integration
        data = {
        "count": [136,87,119,80,97,372],
        "class" : ["first class survivied", "middle class survivied","lower class survivied", "first class deceased" ,"middle class deceased", "lower class deceased"]
        }
        table = pd.DataFrame.from_dict(data)
        tb_encoding = tb_tokenizer(table=table, query=user_message, return_tensors="pt")
        tb_outputs = tb_model.generate(**tb_encoding)
        tb_answer=tb_tokenizer.batch_decode(tb_outputs, skip_special_tokens=True)
    else:
        csv_flag=False
    # using faiss vector database , pip install faiss-gpu if you have gpu, otherwise please use faiss-cpu 
    vectordb = _get_qa_chain_with_sources()
    retriever = vectordb.as_retriever(search_type='similarity', search_kwargs={"k": 3})

    qa_chain = RetrievalQA.from_chain_type(llm=hf_llm, 
                                  chain_type="stuff", 
                                  retriever=retriever, 
                                  return_source_documents=True)     

    result = qa_chain(user_message)
    result['source_documents'][0].page_content
    source_ref=str(result['source_documents'][0].metadata['source'])
    # identifying is the user wants to query tabular data instead
    if csv_flag:
        context_updates = {
            "relevant_chunks": f"""
                Question: {user_message}                
                Answer: {tb_answer},
			    Citing : {data},
                Source : {'titanic.csv'}
        """ }
    else:

        context_updates = {
            "relevant_chunks": f"""
                Question: {user_message}
                Answer: {result['result']},
			    Citing : {result['source_documents'][0].page_content},
                Source : {source_ref}
        """ }

    return ActionResult(
        return_value=context_updates["relevant_chunks"],
        context_updates=context_updates,
    )

def init(llm_rails: LLMRails):
    llm_rails.register_action(retrieve_relevant_chunks, "retrieve_relevant_chunks")

def get_bloke_13b_llm():   
    # loading custom llm  from disk with multiGPUs support
    model_name = "< path_to_the_saved_custom_llm_checkpoints >"  # loading model ckpt from disk
    device = "cuda"
    num_gpus = 2  # number of GPUs you have , do nvidia-smi to check 
    model, tokenizer = load_model(model_name, device, num_gpus, debug=False)

	# repo_id="TheBloke/Wizard-Vicuna-13B-Uncensored-HF"
	# pipe = pipeline("text-generation", model=repo_id, device_map={"":"cuda:0"}, max_new_tokens=256, temperature=0.1, do_sample=True,use_cache=True)
    pipe = pipeline(
		"text-generation",
		model=model,
		tokenizer=tokenizer,
		max_new_tokens=256,
		temperature=0.1,
		do_sample=True,
	)
    local_llm = HuggingFacePipeline(pipeline=pipe)
    return local_llm


hf_llm=get_bloke_13b_llm()
HFPipelineBloke = get_llm_instance_wrapper(llm_instance=get_bloke_13b_llm(), llm_type="hf_pipeline_bloke")
register_llm_provider("hf_pipeline_bloke", HFPipelineBloke)