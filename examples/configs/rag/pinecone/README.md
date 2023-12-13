# Pinecone RAG

Here we demonstrate Retrieval Augmented Generation (RAG) and NeMo Guardrails.

This part enables Nemo Guardrails to talk to Pinecone. It first sends the query to Pinecone via Langchain. Pinecone and Langchain run a similarity search on the vector store and generate an answer which is returned back to Nemo Guardrails. Additionally, the `relevant_chunks` and the source document URL or path which mentions the chunks from where the answer is derived from is sent back. NeMo Guardrails then presents this answer as is to the user, or one can use the `generate_bot_response` mode of NeMo Guardrails to generate an answer. Note that, `relevant_chunks` should contain the text information used by the model as context to answer the question. While the user sees the final answer, the returned `relevant_chunks` are used by the fact-checking and hallucination detection output rails. Rails are applied by default on anything that is presented to the user before it is presented. One can also add multiple databases and selectively query the database depending on the incoming user question.

In order to run this component of the reference demo, you will need to obtain a [Pinecone API key](https://www.pinecone.io/). The instructions to create a Pinecone database, and uploading a few select PDF files to the database are based on the [official examples](https://github.com/pinecone-io/examples/blob/master/docs/langchain-retrieval-augmentation.ipynb) provided by Pinecone. All the API key values are set in the environment and read from there.

Here is an example run, detailing a few more of the salient features:

```
user:/nemoguardrails/examples/configs/rag/pinecone$ nemoguardrails chat --config=nemoguardrails/examples/configs/rag/pinecone

Starting the chat...

> what does nvidia do
 Nvidia is an American multinational technology company that designs graphics processing units (GPUs), application programming interfaces (APIs) for data science and high-performance computing, system on a chip units (SoCs) for the mobile computing and automotive market, and provides an API called CUDA for creating massively parallel software.
 Cited from: kb/nvidia.pdf
> can you tell me more about it
 Nvidia is a technology company that produces graphics processing units (GPUs), central processing units (CPUs), chipsets, drivers, collaborative software, tablet computers, TV accessories, GPU-chips for laptops, and data processing units. It is deployed in supercomputing sites around the world and has moved into the mobile computing market with Tegra mobile processors for smartphones and tablets, as well as vehicle navigation and entertainment systems. It also makes AI-powered software for audio and video processing.
 Cited from: kb/nvidia.pdf
> what is a gpu
 A GPU (Graphics Processing Unit) is a specialized electronic circuit designed to rapidly process graphical and mathematical operations. It is used in computer graphics and video games to generate high-quality graphics more quickly. Nvidia produces GPUs, as well as other products such as Central Processing Units (CPUs), Chipsets, Drivers, Collaborative Software, Tablet Computers, TV Accessories, GPU-chips for Laptops, and Data Processing Units (DPUs).
 Cited from: kb/nvidia.pdf
> where is the office for nvidia
 The headquarters for Nvidia is located in Santa Clara, California, U.S.
 Cited from: kb/nvidia.pdf
> can you summarize
 Nvidia is a technology company based in Santa Clara, California. It produces Graphics Processing Units (GPUs), Central Processing Units, Chipsets, Drivers, Collaborative Software, Tablet Computers, TV Accessories, GPU-chips for laptops, Data Processing Units, and more. GPUs are specialized electronic circuits that are designed to rapidly process large amounts of data, making them ideal for powering applications like video games and AI-driven software. Nvidia is deployed in supercomputing sites around the world and has recently moved into the mobile computing market. They offer deep learning and accelerated analytics due to their API CUDA, and also have a cloud gaming service called GeForce Now.
```

This example exhibits multi-turn conversations out of the box due to a key element. Note the comment `# Extract the full user query based on previous turns` in the `flow` as defined in [config.co](rails.co). This ensures that if the user question is related to a previous question such as `"can you repeat that?"`, the bot understands the relation and sends the correct question forward.

```
define flow
  user ask question
  # Extract the full user query based on previous turns
  $full_user_query = ...
  $answer = execute answer_question_with_sources(query=$full_user_query)
  bot $answer
```

Within the multi-turn conversations, the NeMo Guardrails bot is able to resolve what `it` refers to based on the previous question. This is being taken care of by the Dialog manager under the hood.

Another salient feature of the [config.co](rails.co) file is that there are two main flows defined. This ensures that the user can start asking questions straightaway without a greeting. Ofcourse, if the user chooses to greet the bot first, then that flow will be run.

If one wants to develop a more complex example, one can choose to extend or override certain functionalities in the `Simple Embedding Search Provider API`` that is provided within NeMo Guardrails core. The Simple Embedding Search Provider has three atomic functions:
- The initialisation
- The ability to add one or more items
- Running a search against the items which returns a list of relevant chunks

In each of these one can add code that Pinecone requires. For example in the Simple Embedding Search Provider initialization, we add code to initialize the Pinecone database and add a vectorstore. We can optionally ensure that the vectorstore is not empty so the data has already been uploaded or choose to upload the data. This can also be done in the `add_items` functionality of the Simple Embedding Search Provider. Finally in the `search` functionality, we can add Pinecone and Langchain powered search. If you choose this route then all the data inside `kb` directory is automatically indexed under the hood and you dont need to index the data separately.
