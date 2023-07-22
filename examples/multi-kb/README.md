# Experimental rail on integrating a custom_llm load from disk and custom knowledge base (kb) support

This is an experimental rail which demonstrates the following integration:

## Install additional python packages
 depending on the way you initiated the environment, some additional package might need to be installed manually, such as einops, accelearte, bitsandbytes ..etc, please refer to requirements.txt in this directory to view all essential python packages and install them.

## Datasets
 Datasets for the vectorDB can be provided in .txt format. To preprocess, provide the path to the folder containing the .txt file in (this line) [./config.py¤146] and provide an (output path in this line)[./config.py#47] to where you would like to stored the vectorized database.
 The titanic.csv file can be found in varying sources, for example : (source 1)[https://github.com/datasciencedojo/datasets/blob/master/titanic.csv] and (source_2)[https://www.kaggle.com/c/titanic/data]
    
**Important** : This rail is experimental, use it at your own risk.

- **Load a custom LLM from disk and with multiGPU support**
 The custom_llm model we downloaded from (huggingface model TheBloke/Wizard-13B)[https://huggingface.co/TheBloke/Wizard-Vicuna-13B-Uncensored-HF/tree/main]
 For tabular data QA model, please refer to this repo (gpt4pandas)[https://github.com/ParisNeo/gpt4pandas] and follow the instruction to download the model checkpoint.

- **A custom retrieve_relevant_chunks function which supports custom vector database plugins**
 We demonstrate how to plug in another vector store (in this case, the faiss vector store).
 The ingestion of the raw data no longer needs to be in markdown format. We scraped the (wikipedia titanic film page)[https://en.wikipedia.org/wiki/Titanic_(1997_film)] and dumped the text into a .txt file and we will use it as a knowledge base.

- **A custom tabular QnA function which supports answering queries against pandas processed dataframe**
 We utilize the (gpt4pandas)[https://github.com/ParisNeo/gpt4pandas] to cover queries against tabular dataset leveraging pandas data frame for data preprocessing.

- **add citing and source referral in context update**
Whenever a user query triggers vector database with similarity search, and return top k results. The citing of the paragraphs, as well as the source document referrals, will be logged in system print-out in CLI mode, not yet integrated into the UI.