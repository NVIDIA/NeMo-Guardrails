# Experimental rail on integrating a custom_llm load from disk and custom knowledge base (kb) support

This is an experimental rail which demonstrates the following integration:

- **load a custom_llm from disk and with multiGPUs support**
 The custom_llm model we downloaded from (huggingface model TheBloke/Wizard-13B)[https://huggingface.co/TheBloke/Wizard-Vicuna-13B-Uncensored-HF/tree/main]

- **a custom retrieve_relevant_chunks function which supports custom vector databases plugin**
 We demonstrate how to plug in another vectorstore ( in this case , faiss vectorstore )
 the ingestion of the raw data, no longer needs to be in markdown format, we scrapped (wikipedia titanic film page)[https://en.wikipedia.org/wiki/Titanic_(1997_film)] and dump the text into a .txt file and we will use it as knowledge base.

- **add citing and source referral in context update**
 adding context update and enable the possibility for the custom_llm to include into the response
 note: the inclusion of the citing and souce reference did not always included in the bot response via the custom_llm plug in, 
 we suspect that more promot engineering is necessary in both config.yaml , general.co and factcheck.co

## install additional python packages
 depending on the way you initiated the environment, some additional package might need to be installed manually, such as einops, accelearte, bitsandbytes ..etc, please refer to config.py in this directory to view all essential python packages and install them.

## datasets
    you can use any dataset in .txt format, one can preprocess by simply provide path to the folder containing .txt file in (this line) [./config.py¤146]
    and provide an (output path in this line)[./config.py#47] to where you would like to stored the vectorized database.
    
**Important** : This rail is experimental, use it at your own risk.