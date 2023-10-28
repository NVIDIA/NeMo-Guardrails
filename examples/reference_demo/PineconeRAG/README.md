# [Part 2] Pinecone RAG

Here we demonstrate Retrieval Augmented Generation (RAG) and NeMo Guardrails.

This part enables Nemo Guardrails to talk to Pinecone. It first sends the query to Pinecone via Langchain. Pinecone and Langchain run a similarity search on the vector store and generate an answer which is returned back to Nemo Guardrails. Additionally, the `relevant_chunks` and the source document URL or path which mentions the chunks from where the answer is derived from is sent back. NeMo Guardrails then presents this answer as is to the user, or one can use the `generate_bot_response` mode of NeMo Guardrails to generate an answer. Note that, `relevant_chunks` should contain the text information used by the model as context to answer the question. While the user sees the final answer, the returned `relevant_chunks` are used by the fact-checking and hallucination detection output rails. Rails are applied by default on anything that is presented to the user before it is presented. One can also add multiple databases and selectively query the database depending on the incoming user question. 

In order to run this component of the reference demo, you will need to obtain a [Pinecone API key](https://www.pinecone.io/). The instructions to create a Pinecone database, and uploading a few select PDF files to the database are based on the [official examples](https://github.com/pinecone-io/examples/blob/master/docs/langchain-retrieval-augmentation.ipynb) provided by Pinecone. All the API key values are set in the environment and read from there.

This example exhibits multi-turn conversations out of the box due to a key element. Note the comment `# Extract the full user query based on previous turns` in the `flow` as defined in [config.co](./config.co). This ensures that if the user question is related to a previous question such as `"can you repeat that?"`, the bot understands the relation and sends the correct question forward.

```
define flow
  user ask question
  # Extract the full user query based on previous turns
  $full_user_query = ...
  $answer = execute answer_question_with_sources(query=$full_user_query)
  bot $answer
```

Another salient feature of the [config.co](./config.co) file is that there are two main flows defined. This ensures that the user can start asking questions straightaway without a greeting. Ofcourse, if the user chooses to greet the bot first, then that flow will be run.

If one wants to develop a more complex example, one can choose to extend or override certain functionalities in the `Simple Embedding Search Provider API`` that is provided within NeMo Guardrails core. The Simple Embedding Search Provider has three atomic functions: 
- The initialisation 
- The ability to add one or more items 
- Running a search against the items which returns a list of relevant chunks

In each of these one can add code that Pinecone requires. For example in the Simple Embedding Search Provider initialization, we add code to initialize the Pinecone database and add a vectorstore. We can optionally ensure that the vectorstore is not empty so the data has already been uploaded or choose to upload the data. This can also be done in the `add_items` functionality of the Simple Embedding Search Provider. Finally in the `search` functionality, we can add Pinecone and Langchain powered search. If you choose this route then all the data inside `kb` directory is automatically indexed under the hood and you dont need to index the data separately. 
