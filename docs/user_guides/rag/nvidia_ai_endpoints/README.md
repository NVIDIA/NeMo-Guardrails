# Using Embeddings Models hosted on NVIDIA AI Playground

This is a guide on using embedding models hosted on the NVIDIA AI Playground for the retrieval step in retrieval-augmented generation. It starts with the [ABC Bot configuration](../../../../examples/bots/abc) and modifies it to use the NVIDIA `nvolveqa-40k` model to retrieve embeddings.

## Prerequisites

1. Install the [langchain-nvidia-ai-endpoints](https://github.com/langchain-ai/langchain-nvidia/tree/main/libs/ai-endpoints) package:

```bash
pip install -U --quiet langchain-nvidia-ai-endpoints
```

2. An NVIDIA NGC account to access AI Foundation Models. To create a free account go to [NVIDIA NGC website](https://ngc.nvidia.com/).

3. An API key from NVIDIA AI Catalog:
    - Generate an API key by navigating to the AI Foundation Models section on the NVIDIA NGC website, selecting a model with an API endpoint, and generating an API key.
    - Export the NVIDIA API key as an environment variable:

```python
import os
os.environ["NVIDIA_API_KEY"] = "<nvapi-your-key>"
```

4. If you're running this inside a notebook, patch the AsyncIO loop.

```python
import nest_asyncio

nest_asyncio.apply()
```

## Configuration

To get started, copy the ABC bot configuration into a subdirectory called `config`:

```bash
cp -r ../../../../examples/bots/abc config
```

Update the `models` section of the `config.yml` as follows. Here we update the model used for generation (with `type: main` to `ai-mixtral-8x7b-instruct`) and

```yaml
...
models:
  - type: main
    engine: nvidia_ai_endpoints
    model: ai-mixtral-8x7b-instruct
  - type: embeddings
    engine: nvidia_ai_endpoints
    model: nvolveqa_40k
...
```

## Usage

Load the guardrails configuration:

```python
from nemoguardrails import LLMRails, RailsConfig

config = RailsConfig.from_path("./config")
rails = LLMRails(config)
```

Test response generation:

```python
response = rails.generate(
    messages=[{"role": "user", "content": "What holidays do I have this year?"}]
)
print(response["content"])
```

```
The ABC Company observes the following paid holidays each year: New Year'
```

To verify the model and engine used for creating embeddings for retrieval, log internal events when generating a response:

```python
response = rails.generate(
    messages=[{"role": "user", "content": "What holidays do I have this year?"}],
    options={
        "log": {
            "llm_calls": True,
            "internal_events": True,
        }
    }
)
print("Response: ", response.response[0]["content"])
print("Retrieval event info: ")
retrieval_events = [e for e in response.log.internal_events if "data" in e and "relevant_chunks" in e["data"]]
from pprint import pprint
pprint(retrieval_events)
```

```
Response:  The ABC Company observes the following paid holidays each year: New Year'
Retrieval event info:
[{'data': {'embedding_engine': 'nvidia_ai_endpoints',
           'embedding_model': 'nvolveqa_40k',
           'relevant_chunks': 'Violations of this code of conduct may result '
                              'in disciplinary action up to and including '
                              'termination.\n'
                              'Employees must provide reasonable notice for '
                              'time off, whenever possible. Unused vacation '
                              'and sick leave will be paid out upon '
                              'termination.\n'
                              '\n'
                              'Employees are expected to maintain a healthy '
                              'work-life balance and are encouraged to use '
                              'their time off when needed.\n'
                              'ABC Company works a standard 40-hour workweek, '
                              'Monday through Friday, 9:00 AM to 5:00 PM, with '
                              'one hour for lunch.\n'
                              '\n'
                              'Employees are eligible for the following time '
                              'off:\n'
                              '\n'
                              '* Vacation: 20 days per year, accrued monthly.\n'
                              '* Sick leave: 15 days per year, accrued '
                              'monthly.\n'
                              '* Personal days: 5 days per year, accrued '
                              'monthly.\n'
                              "* Paid holidays: New Year's Day, Memorial Day, "
                              'Independence Day, Thanksgiving Day, Christmas '
                              'Day.\n'
                              '* Bereavement leave: 3 days paid leave for '
                              'immediate family members, 1 day for '
                              'non-immediate family members.',
           'relevant_chunks_sep': ['Violations of this code of conduct may '
                                   'result in disciplinary action up to and '
                                   'including termination.',
                                   'Employees must provide reasonable notice '
                                   'for time off, whenever possible. Unused '
                                   'vacation and sick leave will be paid out '
                                   'upon termination.\n'
                                   '\n'
                                   'Employees are expected to maintain a '
                                   'healthy work-life balance and are '
                                   'encouraged to use their time off when '
                                   'needed.',
                                   'ABC Company works a standard 40-hour '
                                   'workweek, Monday through Friday, 9:00 AM '
                                   'to 5:00 PM, with one hour for lunch.\n'
                                   '\n'
                                   'Employees are eligible for the following '
                                   'time off:\n'
                                   '\n'
                                   '* Vacation: 20 days per year, accrued '
                                   'monthly.\n'
                                   '* Sick leave: 15 days per year, accrued '
                                   'monthly.\n'
                                   '* Personal days: 5 days per year, accrued '
                                   'monthly.\n'
                                   "* Paid holidays: New Year's Day, Memorial "
                                   'Day, Independence Day, Thanksgiving Day, '
                                   'Christmas Day.\n'
                                   '* Bereavement leave: 3 days paid leave for '
                                   'immediate family members, 1 day for '
                                   'non-immediate family members.'],
           'retrieved_for': 'What holidays do I have this year?'},
  'event_created_at': '2024-04-18T21:17:17.251374+00:00',
  'source_uid': 'NeMoGuardrails',
  'type': 'ContextUpdate',
  'uid': '1c5428f1-87db-4fc0-a902-2755c81900fe'}]
```
