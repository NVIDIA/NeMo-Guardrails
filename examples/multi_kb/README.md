# Custom LLM and KBs

This is an experimental guardrails configuration on integrating a custom LLM load from disk and custom knowledge bases support.

**Important**: This example is experimental and is not production-ready.

## Install additional python packages

Depending on how you initiated the environment, additional packages might need to be installed manually, such as `einops`, `accelearte`, `bitsandbytes`, etc. Please refer to the `requirements.txt` in this directory to view all essential Python packages and install them.

## Datasets

The datasets for the vector database can be provided in .txt format. To preprocess, provide the path to the folder containing the .txt file in [this line](./config.py#146) and provide an [output path in this line](./config.py#47) to where you would like to store the vectorized database.

The `titanic.csv` file can be found in varying sources, for example [source 1](https://github.com/datasciencedojo/datasets/blob/master/titanic.csv) and [source 2](https://www.kaggle.com/c/titanic/data).


## Integrations

This configuration demonstrates the following:

- **Loading a custom LLM from disk and with multi-GPU support**

The custom LLM model we downloaded is [HuggingFace model TheBloke/Wizard-13B](https://huggingface.co/TheBloke/Wizard-Vicuna-13B-Uncensored-HF/tree/main).
For tabular data QA model, please refer to this repo [gpt4pandas](https://github.com/ParisNeo/gpt4pandas) and follow the instructions to download the model checkpoint.

- **A custom `retrieve_relevant_chunks` function that supports custom vector database plugins**

We show how to plug in another vector store (in this case, the FAISS vector store).
The ingestion of the raw data no longer needs to be in Markdown format. We scraped the [Wikipedia Titanic film page](https://en.wikipedia.org/wiki/Titanic_(1997_film)) and dumped the text into a .txt file, and we used it as a knowledge base.

- **A custom tabular QnA function which supports answering queries against pandas processed data frame**

We utilize the [gpt4pandas](https://github.com/ParisNeo/gpt4pandas) to cover queries against a tabular dataset leveraging pandas data frame for data preprocessing.

- **Adding citing and source referral in context update**

Whenever a user query triggers a vector database with a similarity search, it returns top k results. The citing of the paragraphs and the source document referrals will be logged when using the CLI chat mode (it is not yet integrated into the UI).
