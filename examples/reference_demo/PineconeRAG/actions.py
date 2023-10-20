from typing import List
from nemoguardrails import LLMRails
from nemoguardrails.embeddings.index import EmbeddingsIndex, IndexItem
from tqdm.auto import tqdm
from pprint import pprint
import fitz

from typing import Optional
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
from datetime import datetime
import logging
import time

from nemoguardrails.actions import action
from nemoguardrails.actions.actions import ActionResult
from nemoguardrails.utils import new_event_dict


OPENAI_API_KEY = os.environ.get("OPENAI_API_KEY")
model_name = 'text-embedding-ada-002'
index_name = 'nemoguardrailsindex'

LOG_FILENAME = datetime.now().strftime('logs/mylogfile_%H_%M_%d_%m_%Y.log')
log = logging.getLogger(__name__)
logging.basicConfig(filename=LOG_FILENAME,level=logging.DEBUG)
print(logging.getLoggerClass().root.handlers[0].baseFilename)

import json

@action(name="qa_chain_with_sources")
#async def qa_chain_with_sources(query: Optional[str] = None, context: Optional[dict] = None):
async def qa_chain_with_sources(user_question):
    """
    Directly call Pinecone qa with sources as an action and pass the users last message as the query.
    The pinecone db and vector store have already been initilzied and indexed before
    """
    #print(context)
    print(user_question)
    text_field = "text"
    embed = OpenAIEmbeddings(model=model_name,openai_api_key=OPENAI_API_KEY)
    vectorstore = Pinecone(pinecone.Index(index_name), embed.embed_query, text_field)
    
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
    
    start_time = time.time()
    #result = qa_with_sources(context.get("last_user_message"))
    result = qa_with_sources(user_question))
    print("--->>>>> Retrieval from Pinecone took: ", time.time() - start_time)
    print(result)
    print(type(result))
    return result['answer']