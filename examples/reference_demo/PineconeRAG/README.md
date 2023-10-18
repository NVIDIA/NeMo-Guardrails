# [Part 2] Reference Demo

In order to run this component of the reference demo, you will need to obtain a Pinecone API. The Pinecone vector database has the following Wikipedia pages [Nvidia](), [Mango]().

This part enables Nemo Guardrails to talk to Pinecone for which we will be extending or overriding certain functionalities in the Simple Embedding Search Provider API that is provided within Nemo Guardrails core. The Simple Embedding Search Provider has three atomic functions: 
- The initialisation 
- The ability to add one or more items 
- Running a search against the items which returns a list of relevant chunks

In each of these we add code that Pinecone requires. For example in the Simple Embedding Search Provider initialization, we add code to initialize the Pinecone database and add a vectorstore. We can optionally ensure that the vectorstore is not empty so the data has already been uploaded or choose to upload the data. This can also be done in the `add_items` functionality of the Simple Embedding Search Provider. Finally in the `search` functionality, we can add Pinecone and Langchain powered search. Once all these are developed the output will look like this: 

```
> what type of a tree is mango


Event UtteranceUserActionFinished {'final_transcript': 'what type of a tree is mango'}
Event StartInternalSystemAction {'uid': '41b303d6-3fca-4169-be88-f9f413d41aa4', 'event_created_at': '2023-10-15T11:22:11.978966+00:00', 'source_uid': 'NeMoGuardrails', 'action_name': 'generate_user_intent', 'action_params': {}, 'action_result_key': None, 'action_uid': '0d4f0d4d-2b46-4bf5-9776-8c98929f12b8', 'is_system_action': True}
Executing action generate_user_intent
{'question': 'what type of a tree is mango', 'answer': 'The mango tree is a type of tree that produces mangoes. It is scientifically known as Mangifera indica and is believed to have originated in southern Asia, particularly in eastern India, Bangladesh, and the Andaman Islands. There are several hundred cultivars of mango worldwide, with variations in size, shape, sweetness, skin color, and flesh color. The mango is the national fruit of India, Pakistan, and the Philippines, and the mango tree is the national tree of Bangladesh. The English word "mango" originated from the Portuguese word "manga," which came from the Malay word "mangga" and ultimately from the Tamil words for "mango tree" and "fruit." Mango trees can grow up to 30-40 meters tall and are long-lived. They have a crown radius of 10-15 meters and can still bear fruit after 300 years. The ripe fruit varies in size, shape, color, sweetness, and eating quality, with colors ranging from yellow, orange, red, to green. The fruit has a single flat, oblong pit that can be fibrous or hairy on the surface and does not separate easily from the pulp. The fruit takes four to five months from flowering to ripening. \n', 'sources': '/nemoguardrails/examples/reference_demo/PineconeRAG/kb/mango.pdf'}

```

Note a fallacy in this solution, we receive out-of-the-box answers along with citations that are made available to the users but Guardrails is not able to act on them because this is not there result of embedding search providers and instead is simply passed on from Pine cone output. The more elegant and streamlined way of doing this instead would be to let the search function in the simple embedding search provider return relevant chunks from Pine Cone to Nemo guardrails and then let Nemo guardrails control the dialogue flow and Management. When we do something like this the results instead look as follows: 
TBD
