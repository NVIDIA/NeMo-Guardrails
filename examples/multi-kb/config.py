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
import pandas as pd
from gpt4pandas import GPT4Pandas

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

def tabularQnA_gpt4pandas(usr_query):
    # loading titanic csv file
    cut_idx=usr_query.find('based on')
    usr_query=usr_query[:cut_idx]+'?'
    model_path='/workspace/ckpt/gpt4all/ggml-vicuna-13b-4bit-rev1.bin'#<'path to the model file'>
    titanic_csv_path='/workspace/Experiment/titanic.csv' # <path to titanic.csv is downloaded>
    df = pd.read_csv(titanic_csv_path,sep=',')

    # working on the data    
    Embarked_d={'C' : "Cherbourg", 'Q': "Queenstown", 'S' : "Southampton"}
    class_d={1:'first class',2:'second class',3:'third class'}
    df['Class']=df['Pclass'].apply(lambda x : class_d[x])
    # changing the embark port to full name
    n=len(df)
    col_ls=list(df.columns)
    idx=col_ls.index('Embarked')
    ls=[]
    for i in range(n):        
        temp=df.iloc[i,idx]
        if type(temp)==str :
            out=Embarked_d[temp]
            ls.append(out)
        else :
            ls.append('N/A')
            #print(i,temp, type(temp))
    df['port']=ls
    df['Lived']=df['Survived'].apply(lambda x: 'survived' if x ==1 else 'died')
    #dropping duplicated and re-worked column 
    df.drop('Survived', inplace=True, axis=1)
    df.drop('Pclass', inplace=True, axis=1)
    df.drop('Embarked', inplace=True, axis=1)
    grouped_by_cols=[]
    if any(word in usr_query for word in ['first class','second class','third class']) :
        grouped_by_cols.append('Class')
    elif 'port' in usr_query:
        grouped_by_cols.append('port')
    elif any(word in usr_query for word in ['female','male','man','woman','men','women']) :
        grouped_by_cols.append('Sex')
    else:
        pass
    d=df.groupby(grouped_by_cols)['Lived'].value_counts()
    #flatten the groupedby pandas series to flatten dictionary
    d2=d.reset_index(inplace=False)
    gpt = GPT4Pandas(model_path, d2, verbose=False)
    out = gpt.ask(usr_query)
    return out, titanic_csv_path , d2.to_string()
    

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
        vectorestore_path =  '/workspace/Experiment/'#"<path_to_already_processd_and_saved_to_disk_vectorstore>"
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
    if 'csv' in user_message:
        result, file_loc , flattened2string =tabularQnA_gpt4pandas(user_message)
        source_ref= file_loc
        citing_text=flattened2string
    else:
        # using faiss vector database , pip install faiss-gpu if you have gpu, otherwise please use faiss-cpu 
        vectordb = _get_qa_chain_with_sources()
        retriever = vectordb.as_retriever(search_type='similarity', search_kwargs={"k": 3})

        qa_chain = RetrievalQA.from_chain_type(llm=hf_llm, 
                                    chain_type="stuff", 
                                    retriever=retriever, 
                                    return_source_documents=True)     

        out = qa_chain(user_message)
        result=out['result']
        citing_text= out['source_documents'][0].page_content
        source_ref=str(out['source_documents'][0].metadata['source'])   

    context_updates = {
        "relevant_chunks": f"""
            Question: {user_message}
            Answer: {result},
            Citing : {citing_text},
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
    model_name = '/workspace/ckpt/bloke/'#"< path_to_the_saved_custom_llm_checkpoints >"  # loading model ckpt from disk
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