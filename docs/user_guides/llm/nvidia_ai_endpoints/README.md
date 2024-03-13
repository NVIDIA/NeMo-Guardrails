# ABC Bot with Llama2-70b and LangChain-NVIDIA AI Endpoints

This user guide will help you set up and use the ABC Bot with the Llama2-70b model and LangChain-NVIDIA AI Endpoints, following the configuration of the bot defined for the [RAG example](../../../getting_started/7_rag/).

## Prerequisites

Before you begin, ensure you have the following prerequisites in place:

1. The langchain-nvidia-ai-endpoints package installed:

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

## Changing the Model and the Engine in `config.yml`

To change the model used by the bot, update the `model` variable within the models section of the `config.yml` file to the desired model supported by NVIDIA AI Foundation Endpoints.

    ```yaml
models:
  - type: main
    engine: nvidia_ai_endpoints
    model: playground_llama2_70b
    ```

## Registering ChatNVIDIA as a New Provider

To change the engine used by the bot, you need to register the new provider within the NeMo Guardrails framework. This is done using the `register_llm_provider` function, which maps the `nvidia_ai_endpoints` identifier to the `ChatNVIDIA` class. As a result, the ABC Bot can call upon `ChatNVIDIA` when it needs to interact with NVIDIA AI Foundation Endpoints and access the models.

```python
from nemoguardrails import LLMRails, RailsConfig
from nemoguardrails.llm.providers import register_llm_provider
from langchain_nvidia_ai_endpoints import ChatNVIDIA

register_llm_provider("nvidia_ai_endpoints", ChatNVIDIA)

config = RailsConfig.from_path("./config")
rails = LLMRails(config)
```

```
Fetching 7 files:   0%|          | 0/7 [00:00<?, ?it/s]
```

## Testing the Bot

Start an interactive chat session with the bot using the following command, ensuring the correct path to your configuration file is specified:

```python
response = rails.generate(messages=[{
    "role": "context",
    "content": {
        "relevant_chunks": """
            Employees are eligible for the following time off:
              * Vacation: 20 days per year, accrued monthly.
              * Sick leave: 15 days per year, accrued monthly.
              * Personal days: 5 days per year, accrued monthly.
              * Paid holidays: New Year's Day, Memorial Day, Independence Day, Thanksgiving Day, Christmas Day.
              * Bereavement leave: 3 days paid leave for immediate family members, 1 day for non-immediate family members. """
    }
},{
    "role": "user",
    "content": "How many vacation days do I have per year?"
}])
print(response["content"])
```

```
According to the ABC Company's employee handbook, eligible employees are entitled to up to 20 days of paid vacation time per year, accrued monthly. Please note that the exact number of vacation days you have per year may depend on your individual employment contract or collective bargaining agreement, if applicable. It's always best to consult the employee handbook or speak with HR for personalized information regarding your benefits.
```
