# [Part 2] Reference Demo

In order to run this component of the reference demo, you will need to obtain a Pinecone API key. The Pinecone vector database has the following Wikipedia pages [Nvidia](https://en.wikipedia.org/wiki/Nvidia), [Mango](https://en.wikipedia.org/wiki/Mango).

This part enables Nemo Guardrails to talk to Pinecone. It first sends the query to Pinecone via Langchain. Pinecone and Langchain run a similarity search on the vector store and generate an answer which is returned back to Nemo Guardrails. Nemo Guardrails then presents this answer as is to the user. Note that, `relevant_chunks` should contain the text information used by the model as context to answer the question. While the user sees the final answer, the returned `relevant_chunks` are used by the fact-checking and hallucination detection output rails. Rails can be additionally applied by default on anything that is presented to the user before it is presented. Following is an example that is returned back by Pinecone:

```
  {'query': 'str',
    'result': 'str',
    'source_documents': [Document(page_content='...', 
    metadata={'chunk': int, 'id': 'int', 'source': '/path/to/file.pdf'}),
    ]
    }

```