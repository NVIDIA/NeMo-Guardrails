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
OPENAI_API_KEY = "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"


class SimpleEmbeddingSearchProvider(EmbeddingsIndex):
    """Connecting to Pinecone"""

    @property
    def embedding_size(self):
        return 0

    def create_pinecone_index(self, index_name, texts):
        """ will create a pinecone empty template with the size of the data you want to upload"""
        #index_name = 'starterindex'
        if index_name not in pinecone.list_indexes():
            # we create a new index
            pinecone.create_index(
                name=index_name,
                metric='cosine',
                dimension=len(create_embeddings(texts)[0])  # 1536 dim of text-embedding-ada-002
            )
        index = pinecone.GRPCIndex(index_name)
        index.describe_index_stats()
        return index
    
    def __init__(self):
        #change this or delete on website
        #https://app.pinecone.io/organizations/-NX1GJikDzyct7bwFz-B/projects/asia-southeast1-gcp-free:15a7b1a/indexes/test-our-data-retrieval-augmentation
        import pinecone
        # find API key in console at app.pinecone.io
        PINECONE_API_KEY = '73f910f7-f8dd-4bc0-a176-fe3e49184e12'
        #os.getenv('PINECONE_API_KEY') or 'PINECONE_API_KEY'
        # find ENV (cloud region) next to API key in console
        PINECONE_ENVIRONMENT = 'gcp-starter'
        #os.getenv('PINECONE_ENVIRONMENT') or 'PINECONE_ENVIRONMENT'
        pinecone.init(
            api_key=PINECONE_API_KEY,
            environment=PINECONE_ENVIRONMENT
        )
        self.pinecone_init = create_pinecone_index(self, "starterindex", "something")

    async def add_items(self, items: List[IndexItem]):
        """Adds multiple items to the index."""
        await upload_data_to_pinecone_index(self, our_dataset, index)
        self.items.extend(items)

    async def search(self, text: str, max_results: int) -> List[IndexItem]:
        """Searches the index for the closes matches to the provided text."""
        results = []
        for item in self.items:
            if text in item.text:
                results.append(item)
        return results
    
    async def load_data_from_pdfs(self, path, starting_id=0, pr="y"):
        data_local = {}
        local_urls = []
        for x in tqdm(os.listdir(path)):
            if x.endswith(".pdf"):
                print(x)
                local_urls.append(path + x)
        if pr=="y":
            pprint(local_urls)
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

    async def create_hf_data(self, path):
        from datasets import Dataset
        data = load_data_from_pdfs(path)
        #data = mergeDictionary(data1, data2)
        # Create a Hugging Face dataset
        our_dataset = Dataset.from_dict(data)
        #use the already loaded hugging face dataset for whatever else
        print(our_dataset)
        # Save the dataset in Hugging Face dataset format
        our_dataset.save_to_disk(path)
        return our_dataset
    
    async def split_text_into_chunks(self, dataset):
        import tiktoken
        tiktoken.encoding_for_model('gpt-4')
        tokenizer = tiktoken.get_encoding('cl100k_base')
        # create the length function
        async def tiktoken_len(text):
            tokens = tokenizer.encode(
                text,
                disallowed_special=()
            )
            return len(tokens)
        print(tiktoken_len("hello I am a chunk of text and using the tiktoken_len function "
                    "we can find the length of this chunk of text in tokens"))
        from langchain.text_splitter import RecursiveCharacterTextSplitter

        text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=400,
            chunk_overlap=20,
            length_function=tiktoken_len,
            separators=["\n\n", "\n", " ", ""]
        )
        chunks = text_splitter.split_text(dataset)
        return chunks
    
    async def create_embeddings(self, texts):
        from langchain.embeddings.openai import OpenAIEmbeddings
        model_name = 'text-embedding-ada-002'
        embed = OpenAIEmbeddings(
            model=model_name,
            openai_api_key=OPENAI_API_KEY
        )
        texts = [
            'this is the first chunk of text',
            'then another second chunk of text is here']
        res = embed.embed_documents(texts)
        print(len(res), len(res[0]), "shape and size of the generated embeddings")
        return res
        
    async def list_indexes_in_pinecone(self):
        for index_name in pinecone.list_indexes():
            print(index_name)
    
    
        
    async def upload_data_to_pinecone_index(self, our_dataset, index):
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
            #record_texts = text_splitter.split_text(record['text'])
            record_texts = split_text_into_chunks(record['text'])
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
                #embeds = embed.embed_documents(texts)
                embeds = create_embeddings(texts)
                index.upsert(vectors=zip(ids, embeds, metadatas))
                texts = []
                metadatas = []

        if len(texts) > 0:
            ids = [str(uuid4()) for _ in range(len(texts))]
            embeds = create_embeddings(texts) #embed.embed_documents(texts)
            index.upsert(vectors=zip(ids, embeds, metadatas))
            
        print(index.describe_index_stats())
        
        
    async def vector_store_init(self, index_name):
        from langchain.vectorstores import Pinecone
        text_field = "text"
        # switch back to normal index for langchain
        index = pinecone.Index(index_name)
        embed = OpenAIEmbeddings(
            model=model_name,
            openai_api_key=OPENAI_API_KEY
        )
        vectorstore = Pinecone(
            index, embed.embed_query, text_field
        )
        query = "what is nemoguardrails ?"

        vectorstore.similarity_search(
            query,  # our search query
            k=3  # return 3 most relevant docs
        )


    async def retreival_qa(vectorstore):
        from langchain.chat_models import ChatOpenAI
        from langchain.chains import RetrievalQA

        # completion llm
        llm = ChatOpenAI(
            openai_api_key=OPENAI_API_KEY,
            model_name='gpt-3.5-turbo',
            temperature=0.0
        )
        qa = RetrievalQA.from_chain_type(
        llm=llm,
        chain_type="stuff",
        retriever=vectorstore.as_retriever()
        )
        
    async def retreival_qa_with_sources(vectorstore, query):
        from langchain.chains import RetrievalQAWithSourcesChain
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
    

def init(app: LLMRails):
    app.register_embedding_search_provider("simple", SimpleEmbeddingSearchProvider)