# HuggingFace Pipeline with llama2 models

This configuration uses the HuggingFace Pipeline LLM with various llama2 models, including 7B and 13B, e.g. [meta-llama/Llama-2-13b-chat-hf](https://huggingface.co/meta-llama/Llama-2-13b-chat-hf).

Note that in order to use community models such as llama2, one will need to first go to [huggingface-llama2](https://huggingface.co/meta-llama).
After receiving access to general llama2 models, one still needs to go to the specific model page on Huggingface, e.g. [meta-llama/Llama-2-13b-chat-hf](https://huggingface.co/meta-llama/Llama-2-13b-chat-hf), to be granted access on HF to that specific model.

Before running this rail, you need to set the environment via export HF_TOKEN="Your_HuggingFace_Access_Token" , [read more on access token](https://huggingface.co/docs/hub/security-tokens).

Please install additional package via :

`pip install accelerate transformers==4.33.1 --upgrade`


The `meta-llama/Llama-2-13b-chat-hf` LLM model has been tested on the topical rails evaluation sets, results are available [here](../../../../nemoguardrails/eval/README.md).
We have also tested the factchecking rail for the same model with good results.
There are examples on how to use the models with a HF repo id or from a local path.

In this folder, the guardrails application is very basic, but anyone can change it with any other more complex configuration.

**Disclaimer**: The `meta-llama/Llama-2-13b-chat-hf` LLM on tested on basic usage combining a toy example of a knowledge base, further experiments of prompt engineering needs to be done on [fact-checking](config.yml#L133-142) for more complex queries as this model may not work correctly. Thorough testing and optimizations are needed before considering a production deployment.
