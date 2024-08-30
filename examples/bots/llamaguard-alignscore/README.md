# LlamaGuard-AlignScore-NeMoGuardrails-NIM



## How to run the app

### Start with setting up the llamaguard model

Make sure you have access allowed for the `meta-llama/LlamaGuard-7b` model from here - https://huggingface.co/meta-llama/LlamaGuard-7b

Once you have the access token generated, follow the steps here to setup the vllm for llamaGuard - https://github.com/NVIDIA/NeMo-Guardrails/blob/develop/docs/user_guides/advanced/llama-guard-deployment.md

### Running the app

Setup the environement and install the following libraries

```
pip install langchain_nvidia_ai_endpoints nemoguardrails openai

```

Add the environment variables as follows:

Here NVIDIA NIMs are used for both the embedding model and LLM. You can easily swap the models with your choice

```
export NVIDIA_API_KEY=....
export OPEANI_API_KEY-"dummy"
```
run the `ingest.py` file with whatever pdf as your data. Here the data is based on NVIDIA AI Enterprise user guide and then run `main.py` as follows:

```
python ingest.py
python main.py
```

