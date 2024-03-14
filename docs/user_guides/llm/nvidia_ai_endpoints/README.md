# ABC Bot with LangChain-NVIDIA AI Endpoints

This user guide will help you set up and use the ABC Bot with LangChain-NVIDIA AI Endpoints, following the configuration of the bot defined for the [RAG example](../../../getting_started/7_rag/).

```bash
rm -r config
mkdir config
cp -r ../../../../examples/bots/abc/* ./config
```

## Prerequisites

Before you begin, ensure you have the following prerequisites in place:

1. The [langchain-nvidia-ai-endpoints](https://github.com/langchain-ai/langchain-nvidia/tree/main/libs/ai-endpoints) package installed:

```bash
pip install -U langchain-nvidia-ai-endpoints
```

2. An NVIDIA NGC account to access AI Foundation Models. Create a free account at the [NVIDIA NGC website](https://ngc.nvidia.com/) to access AI Foundation Models.

3. An API key from NVIDIA AI Foundation Endpoints:
    -  Generate an API key by navigating to the AI Foundation Models section on the NVIDIA NGC website, selecting a model with an API endpoint, and generating an API key.
    -  Export the NVIDIA API key as an environment variable:

!export NVIDIA_API_KEY=nvapi-XXXXXXXXXXXXXXXXXXXXXXXXXX # Replace with your own key

4. Alternatively, set the environment variable within your Python script:

```python
import os
os.environ["NVIDIA_API_KEY"] = "nvapi-XXXXXXXXXXXXXXXXXXXXXXXXXX" # Replace with your own key
```

5. If you're running this inside a notebook, patch the AsyncIO loop.

```python
import nest_asyncio

nest_asyncio.apply()
```

## Existing Guardrails Configuration

The configuration for the ABC bot is set up to utilize OpenAI's models through the OpenAI engine.

```bash
awk '/^models:/{flag=1; next} /^[a-zA-Z]+:/{flag=0} flag' ./config/config.yml
```

```
  - type: main
    engine: openai
    model: gpt-3.5-turbo-instruct

```

## Changing the Model and the Engine in `config.yml`

To change the model used by the bot, update the `model` variable within the models section of the `config.yml` file to the desired model supported by NVIDIA AI Foundation Endpoints.

```yaml
models:
  - type: main
    engine: nvidia_ai_endpoints
    model: playground_mixtral_8x7b
```

## Registering ChatNVIDIA as a New Provider

To change the engine used by the bot, you need to register the new provider within the NeMo Guardrails framework. This is done using the `register_llm_provider` function, which maps the `nvidia_ai_endpoints` identifier to the `ChatNVIDIA` class. As a result, the ABC Bot can call upon `ChatNVIDIA` when it needs to interact with NVIDIA AI Foundation Endpoints and access the models.

```python
from nemoguardrails import LLMRails, RailsConfig

config = RailsConfig.from_path("./config")
rails = LLMRails(config)
```

## Testing the Bot

Start an interactive chat session with the bot using the following command, ensuring the correct path to your configuration file is specified:

```python
response = rails.generate(messages=[
{
    "role": "user",
    "content": "How many vacation days do I have per year?"
}])
print(response['content'])
```

```
The ABC Company provides eligible employees with 20 days of paid vacation time per year, accrued monthly. However, I would need to access your specific information to provide an exact number of days you have taken or accrued. Please refer to the employee handbook for more information.
```
