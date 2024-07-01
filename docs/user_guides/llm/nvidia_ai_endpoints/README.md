# Using LLMs hosted on NVIDIA API Catalog

This guide teaches you how to use NeMo Guardrails with LLMs hosted on NVIDIA API Catalog. It uses the [ABC Bot configuration](../../../../examples/bots/abc) and changes the model to `ai-mixtral-8x7b-instruct`.

## Prerequisites

Before you begin, ensure you have the following prerequisites in place:

1. Install the [langchain-nvidia-ai-endpoints](https://github.com/langchain-ai/langchain-nvidia/tree/main/libs/ai-endpoints) package:

```bash
pip install -U --quiet langchain-nvidia-ai-endpoints
```

2. An NVIDIA NGC account to access AI Foundation Models. To create a free account go to [NVIDIA NGC website](https://ngc.nvidia.com/).

3. An API key from NVIDIA API Catalog:
    - Generate an API key by navigating to the AI Foundation Models section on the NVIDIA NGC website, selecting a model with an API endpoint, and generating an API key. You can use this API key for all mdoels available in the NVIDIA API Catalog.
    - Export the NVIDIA API key as an environment variable:

```bash
export NVIDIA_API_KEY=$NVIDIA_API_KEY # Replace with your own key
```

> **Note**: The API key is used to access the models hosted on NVIDIA API Catalog. If you are using self-hosted models with NVIDIA NIM, you can skip this step.

4. If you're running this inside a notebook, patch the AsyncIO loop.

```python
import nest_asyncio

nest_asyncio.apply()
```

## Configuration

To get started, copy the ABC bot configuration into a subdirectory called `config`:

if you are running this inside a notebook, you can use the following code:

```python
from nemoguardrails.utils import get_examples_data_path
!cp -r {get_examples_data_path("bots/abc")} config
```

otherwise, you can use the following command:

```bash
cp -r $(python -c 'from nemoguardrails.utils import get_examples_data_path; print(get_examples_data_path("bots/abc"))') config
```

### Working with NVIDIA API Catalog

If you have obtained the NVIDIA API key, you can use it to access the models hosted on NVIDIA API Catalog. Then update the `config.yml` with the following configuration:

```yaml
...
models:
  - type: main
    engine: nvidia_ai_endpoints
    model: ai-mixtral-8x7b-instruct
...
```

> **Note**: The `ai-mixtral-8x7b-instruct` model is hosted on NVIDIA API Catalog. You can replace it with any other model available in the NVIDIA API Catalog.

### Working with NVIDIA NIMs

When ready to deploy, you can self-host models with NVIDIA NIM—which is included with the NVIDIA AI Enterprise software license—and run them anywhere, giving you ownership of your customizations and full control of your intellectual property (IP) and AI applications.

[Learn more about NIMs](https://developer.nvidia.com/blog/nvidia-nim-offers-optimized-inference-microservices-for-deploying-ai-models-at-scale/)

```yaml
...
  - type: main
    engine: nvidia_ai_endpoints
    model: ai-mixtral-8x7b-instruct
    parameters:
      base_url: http://localhost:8000/v1
...
```

## Usage

Load the guardrails configuration:

```python
from nemoguardrails import LLMRails, RailsConfig

config = RailsConfig.from_path("./config")
rails = LLMRails(config)
```

```
Fetching 7 files:   0%|          | 0/7 [00:00<?, ?it/s]
```

Test that it works:

```python
response = rails.generate(messages=[
{
    "role": "user",
    "content": "How many vacation days do I have per year?"
}])
print(response['content'])
```

```
The ABC Company provides eligible employees with 20 days of paid vacation time
```

You can see that the bot responds correctly.

## Conclusion

In this guide, you learned how to connect a NeMo Guardrails configuration to an NVIDIA API Catalog LLM model. This guide uses `ai-mixtral-8x7b-instruct`, however, you can connect any other model by following the same steps.
