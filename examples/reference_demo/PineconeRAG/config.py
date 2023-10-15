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
from typing import List
from nemoguardrails import LLMRails
from nemoguardrails.embeddings.index import EmbeddingsIndex, IndexItem
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
from langchain.chains import RetrievalQAWithSourcesChain

OPENAI_API_KEY = os.environ.get("OPENAI_API_KEY")
PINECONE_API_KEY = os.environ.get("PINECONE_API_KEY")
PINECONE_ENVIRONMENT = os.environ.get("PINECONE_ENVIRONMENT")
index_name = 'starterindex'
model_name = 'text-embedding-ada-002'

# import warnings
# warnings.filterwarnings("ignore")

class SimpleEmbeddingSearchProvider(EmbeddingsIndex):
    """Connecting to Pinecone"""

    @property
    def embedding_size(self):
        return 0
    
    def load_data_from_pdfs(self, path):
        data_local = {}
        local_urls = []
        for x in tqdm(os.listdir(path)):
            ### extend later on to read all types of text files 
            if x.endswith(".pdf"):
                print(x)
                local_urls.append(path + x)
        local_articles = []
        for local_url in local_urls:
            doc = fitz.open(local_url)
            text = ""
            for page in doc:
                text += page.get_text()
            local_articles.append(text)
        data_local = {"id": [0 + i for i in range(len(local_urls))], "text": [local_articles[i] for i in range(
            0, len(local_urls))], "url": [local_urls[i] for i in range(0, len(local_urls))]}
        print("----- reading dataset from local directory")
        return data_local


    def create_hf_data(self, path):
        data = self.load_data_from_pdfs(path)
        # data = mergeDictionary(data1, data2)
        # Create a Hugging Face dataset
        our_dataset = Dataset.from_dict(data)
        # use the already loaded hugging face dataset for whatever else
        print(our_dataset)
        # Save the dataset in Hugging Face dataset format
        our_dataset.save_to_disk(path)
        print("------- saved huggingface dataset to -> ", path)
        return our_dataset


    def tiktoken_len(self, text):
        tiktoken.encoding_for_model('gpt-4')
        tokenizer = tiktoken.get_encoding('cl100k_base')
        tokens = tokenizer.encode(
            text,
            disallowed_special=()
        )
        print("----- finalizing lengths for tiktoken")
        return len(tokens)



    def split_text_into_chunks(self, dataset):
        # create the length function
        #dataset variable is the hugging face format of dataset
        text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=400,
            chunk_overlap=20,
            length_function=self.tiktoken_len,
            separators=["\n\n", "\n", " ", ""]
        )
        chunks = text_splitter.split_text(dataset)
        print("----- splitting texts into chunks")
        return chunks

 
 
 
 
    def create_embeddings(self, texts):
        model_name = 'text-embedding-ada-002'
        embed = OpenAIEmbeddings(
            model=model_name,
            openai_api_key=OPENAI_API_KEY
        )
        # get text from all the pdf?
        res = embed.embed_documents(texts)
        print(len(res), len(res[0]),
              "shape and size of the generated embeddings")
        print("----- Embeddings being created")
        return res

    
    
    def create_pinecone_index(self, index_name):
        """ will create a pinecone empty template with the size of the data you want to upload"""
        if index_name not in pinecone.list_indexes():
            # we create a new index
            pinecone.create_index(
                name=index_name,
                metric='cosine',
                # 1536 dim of text-embedding-ada-002
                dimension=1536
            )
        index = pinecone.Index(index_name)
        print("----- Pinecone Index being created")
        index.describe_index_stats()
        return index


    def upload_data_to_pinecone_index(self, our_dataset, index):
        from tqdm.auto import tqdm
        from uuid import uuid4
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
            # record_texts = text_splitter.split_text(record['text'])
            record_texts = self.split_text_into_chunks(record['text'])
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
                # embeds = embed.embed_documents(texts)
                embeds = self.create_embeddings(texts)
                index.upsert(vectors=zip(ids, embeds, metadatas))
                texts = []
                metadatas = []

        if len(texts) > 0:
            ids = [str(uuid4()) for _ in range(len(texts))]
            embeds = self.create_embeddings(texts)  # embed.embed_documents(texts)
            index.upsert(vectors=zip(ids, embeds, metadatas))
        print("---------------- data has been uploaded to pinecone index")
        print(index.describe_index_stats())


    def create_vectorstore(self, index_name):
        text_field = "text"
        # switch back to normal index for langchain
        embed = OpenAIEmbeddings(
            model=model_name,
            openai_api_key=OPENAI_API_KEY
        )
        self.vectorstore = Pinecone(
            pinecone.Index(index_name), embed.embed_query, text_field
        )
        
    def __init__(self):
        #first do pinecone initialization 
        pinecone.init(
            api_key=PINECONE_API_KEY,
            environment=PINECONE_ENVIRONMENT
        )
        
        
        if index_name not in pinecone.list_indexes():
            #need to make sure pinecone index exists and has data
            #path to index data from
            path = "/home/sganju/gitlab_stuff/nemoguardrails/examples/reference_demo/PineconeRAG/kb"
            #create hugging face format of dataset
            our_dataset = self.create_hf_data(path)
            #upload data to pinecone
            #make sure pinecone index exists
            self.index = self.create_pinecone_index(index_name)
            self.upload_data_to_pinecone_index(our_dataset, self.index)
        else:
            #index already exists, print out its stats
            self.index = pinecone.Index(index_name)
            print("----- Pinecone Index already exists")
            print(self.index.describe_index_stats())

        #create vector store
        self.create_vectorstore(index_name)
        print("-------- pinecone database and langchain vector store have been created")

    
       
    async def add_items(self,  items: List[IndexItem]):
        """Adds multiple items to the index."""
        # In the init function we have already indexed items into pinecone, so here we can check that pinecone db is full
        print("from add items function of nemo guardrails core")
        print(self.index.describe_index_stats())

    async def search(self, query: str, max_results: int) -> List[IndexItem]:
        """Searches the index for the closes matches to the provided text."""
        # needs to instead call pinecone search
        print(self.retreival_qa_with_sources(query))


    

    def standard_query(self, query):
        #query = "what is nemoguardrails ?"
        result = self.vectorstore.similarity_search(
            query,  # our search query
            k=3  # return 3 most relevant docs
        )
        return result 

    def retreival_qa(self, query):
        # completion llm
        llm = ChatOpenAI(
            openai_api_key=OPENAI_API_KEY,
            model_name='gpt-3.5-turbo',
            temperature=0.0
        )
        qa = RetrievalQA.from_chain_type(
            llm=llm,
            chain_type="stuff",
            retriever=self.vectorstore.as_retriever()
        )
        return qa(query)

    def retreival_qa_with_sources(self, query):
        llm = ChatOpenAI(
            openai_api_key=OPENAI_API_KEY,
            model_name='gpt-3.5-turbo',
            temperature=0.0
        )
        qa_with_sources = RetrievalQAWithSourcesChain.from_chain_type(
            llm=llm,
            chain_type="stuff",
            retriever=self.vectorstore.as_retriever()
        )
        return qa_with_sources(query)


def init(app: LLMRails):
    app.register_embedding_search_provider(
        "simple", SimpleEmbeddingSearchProvider)
