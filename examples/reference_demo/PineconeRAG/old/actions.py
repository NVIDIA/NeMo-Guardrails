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
from typing import Optional
from urllib import parse

import aiohttp

from nemoguardrails.actions import action
from nemoguardrails.actions.actions import ActionResult
from nemoguardrails.utils import new_event_dict
from datetime import datetime


from tqdm.auto import tqdm
from pprint import pprint
import fitz
import os
import tiktoken
from langchain.text_splitter import RecursiveCharacterTextSplitter
from uuid import uuid4
import pinecone
from langchain.embeddings.openai import OpenAIEmbeddings
from langchain.vectorstores import Pinecone
from langchain.chat_models import ChatOpenAI
from langchain.chains import RetrievalQA
from datasets import Dataset
from langchain.text_splitter import RecursiveCharacterTextSplitter
from tqdm.auto import tqdm
from langchain.vectorstores import Pinecone
from langchain.chat_models import ChatOpenAI
from langchain.chains import RetrievalQA
from langchain.chains import RetrievalQAWithSourcesChain


LOG_FILENAME = datetime.now().strftime('logs/mylogfile_%H_%M_%d_%m_%Y.log')
log = logging.getLogger(__name__)
logging.basicConfig(filename=LOG_FILENAME,level=logging.DEBUG)
print(logging.getLoggerClass().root.handlers[0].baseFilename)

import json

data = {}

@action(name="extract_and_save_data")
async def extract_and_save_data(
    query: Optional[str] = None, context: Optional[dict] = None
):
    """Saves the inputs received from the user
    
    :param context: The context for the execution of the action.
    :param query: The query for execution
    """
    print(" ** In extract_and_save_data ** " * 3)
    # If we don't have an explicit query, we take the last user message
    if query is None and context is not None:
        query = context.get("last_user_message") or "Example First Name"

    if query is None:
        raise Exception("No input name was provided.")

    log.info(f"Received following query: {query}")
    log.info(f"Received following context: {context}")
    print("****" * 3)
    data = {}
    log.info(f"Found the following relevant data:")
    if "firstname" in context and "firstname" not in data:
        print("Firstname is -> ", context["firstname"])
        data["firstname"] = context["firstname"]
    if "lastname" in context and "lastname" not in data:
        print("Last name is -> ", context["lastname"])
        data["lastname"] = context["lastname"]
    if "user_id" in context and "user_id" not in data:
        print("User id is -> ", context["user_id"])
        data["user_id"] = context["user_id"]
        
    print(data)

@action(name="authenticate_user")
async def authenticate_user(user_id, firstname, lastname):
    """loads the ground truth database for authentication and compares against the inputs received from the user
    """
    print(" ** In authenticate_user ** " * 3)
    print(user_id, firstname, lastname)
    
    with open("ground_truth.json", "r") as infile:
        ground_truth = json.load(infile)
    
    print(ground_truth)
    
    if user_id in ground_truth:
        print("success till here")
        #match against first and last name
        if firstname.lower() == ground_truth[user_id]["firstname"].lower() and lastname.lower() == ground_truth[user_id]["lastname"].lower():
            return True
        else:
            return False
    else:
        return False


#####################################
#### not a defined action ###
#####################################

def load_paths_from_dir(path):
    local_urls = []
    for x in tqdm(os.listdir(path)):
        if x.endswith(".pdf"):
            print(x)
            local_urls.append(path + x)
    return local_urls


def parse_text_from_pdf(local_urls, starting_id=0):
    data_local = {}
    local_articles = []
    for local_url in local_urls:
        doc = fitz.open(local_url)
        text = ""
        for page in doc:
            text+=page.get_text()
        local_articles.append(text)
    data_local = {"id": [starting_id + i for i in range(len(local_urls))] ,"text": [local_articles[i] for i in range(0,len(local_urls))],"url": [local_urls[i] for i in range(0,len(local_urls))]}
    if pr=="y":
        pprint(data_local.items())
    return data_local

#####################################
#### not a defined action ###
#####################################
def merge_dictionary(dict_1, dict_2):
   dict_3 = {**dict_1, **dict_2}
   for key, value in dict_3.items():
       if key in dict_1 and key in dict_2:
               #dict_3[key] = value.append(dict_1[key])
               dict_3[key] = [value, dict_1[key]]

   return dict_3

def load_data_dir():
    data = parse_text_from_pdf(load_paths_from_dir("data/"))
    #data = mergeDictionary(data1, data2)
    # Create a Hugging Face dataset
    our_dataset = Dataset.from_dict(data)
    #use the already loaded hugging face dataset for whatever else
    print(our_dataset)
    # Save the dataset in Hugging Face dataset format
    our_dataset.save_to_disk("stuff_hf_data")

# create the length function
def tiktoken_len(text):
    import tiktoken
    tiktoken.encoding_for_model('gpt-4')
    tokenizer = tiktoken.get_encoding('cl100k_base')
    tokens = tokenizer.encode(
        text,
        disallowed_special=()
    )
    return len(tokens)


text_splitter = RecursiveCharacterTextSplitter(
    chunk_size=400,
    chunk_overlap=20,
    length_function=tiktoken_len,
    separators=["\n\n", "\n", " ", ""])

def create_embedding(texts):
    from langchain.embeddings.openai import OpenAIEmbeddings
    model_name = 'text-embedding-ada-002'
    embed = OpenAIEmbeddings(model=model_name,openai_api_key=OPENAI_API_KEY)
    return embed.embed_documents(texts)


def pinecone_init():
    index_name = 'starterindex'
    import pinecone
    PINECONE_API_KEY = '73f910f7-f8dd-4bc0-a176-fe3e49184e12'
    PINECONE_ENVIRONMENT = 'gcp-starter'
    pinecone.init(api_key=PINECONE_API_KEY,environment=PINECONE_ENVIRONMENT)
    if index_name not in pinecone.list_indexes():
        pinecone.create_index(
            name=index_name,
            metric='cosine',
            dimension=len(res[0])  # 1536 dim of text-embedding-ada-002
        )
    index = pinecone.GRPCIndex(index_name)
    print(index.describe_index_stats())

def pinecone_indexing(index, our_dataset):
    batch_limit = 10
    texts = []
    metadatas = []
    for i, record in enumerate(tqdm(our_dataset)):
        # first get metadata fields for this record
        metadata = {
            'id': str(record['id']),
            'source': record['url']
        }
    # now we create chunks from the record text
    record_texts = text_splitter.split_text(record['text'])
    # create individual metadata dicts for each chunk
    record_metadatas = [{
        "chunk": j, "text": text, **metadata
    } for j, text in enumerate(record_texts)]
    # append these to current batches
    texts.extend(record_texts)
    metadatas.extend(record_metadatas)
    # if we have reached the batch_limit we can add texts
    if len(texts) >= batch_limit:
        ids = [str(uuid4()) for _ in range(len(texts))]
        embeds = embed.embed_documents(texts)
        index.upsert(vectors=zip(ids, embeds, metadatas))
        texts = []
        metadatas = []

    if len(texts) > 0:
        ids = [str(uuid4()) for _ in range(len(texts))]
        embeds = embed.embed_documents(texts)
        index.upsert(vectors=zip(ids, embeds, metadatas))

    print(index.describe_index_stats())
    
def create_vector_store():
    pinecone_init()
    pinecone_indexing(index, our_dataset)
    text_field = "text"
    # switch back to normal index for langchain
    index = pinecone.Index(index_name)
    
    vectorstore = Pinecone(
        index, embed.embed_query, text_field
    )

def run_query(query):
    # completion llm
    llm = ChatOpenAI(
        openai_api_key=OPENAI_API_KEY,
        model_name='gpt-3.5-turbo',
        temperature=0.0
    )
    qa_with_sources = RetrievalQAWithSourcesChain.from_chain_type(
        llm=llm,
        chain_type="stuff",
        retriever=vectorstore.as_retriever()
    )
    return qa_with_sources(query)
