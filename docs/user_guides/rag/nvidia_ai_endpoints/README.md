# Using Embeddings Models hosted on NVIDIA API Catalog

This is a guide on using embedding models hosted on the NVIDIA API Catalog for the retrieval step in retrieval-augmented generation. It starts with the [ABC Bot configuration](../../../../examples/bots/abc) and modifies it to use the NVIDIA `nvidia/nv-embed-v1` model to retrieve embeddings.

## Prerequisites

1. Install the [langchain-nvidia-ai-endpoints](https://github.com/langchain-ai/langchain-nvidia/tree/main/libs/ai-endpoints) package:

```bash
pip install -U --quiet langchain-nvidia-ai-endpoints
```

```

[notice] A new release of pip is available: 23.3.2 -> 24.1.2
[notice] To update, run: pip install --upgrade pip
```

2. An NVIDIA NGC account to access AI Foundation Models. To create a free account go to [NVIDIA NGC website](https://ngc.nvidia.com/).

3. An API key from NVIDIA AI Catalog:
    -  Generate an API key by navigating to the AI Foundation Models section on the NVIDIA NGC website, selecting a model with an API endpoint, and generating an API key.
    -  Export the NVIDIA API key as an environment variable:

```bash
export NVIDIA_API_KEY=$NVIDIA_API_KEY # Replace with your own key
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

Update the `models` section of the `config.yml` as follows. Here we update the model used for generation (with `type: main` to `meta/llama3-70b-instruct`) and

```yaml
...
models:
  - type: main
    engine: nvidia_ai_endpoints
    model: meta/llama3-70b-instruct
  - type: embeddings
    engine: nvidia_ai_endpoints
    model: nvidia/nv-embed-v1
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
    messages=[{"role": "user", "content": "How many personal days off do I have?"}]
)
print(response["content"])
```

```
In addition to vacation and sick leave, employees also have two personal days per year. Please refer to the employee handbook for more information.
```

```python
print(rails.explain_info.llm_calls[3].prompt)
```

```
"""
Below is a conversation between a user and a bot called the ABC Bot.
The bot is designed to answer employee questions about the ABC Company.
The bot is knowledgeable about the employee handbook and company policies.
If the bot does not know the answer to a question, it truthfully says it does not know.

"""

# This is how a conversation between a user and the bot can go:
User message: "Hi there. Can you help me with some questions I have about the company?"
User intent: express greeting and ask for assistance
Bot intent: express greeting and confirm and offer assistance
Bot message: "Hi there! I'm here to help answer any questions you may have about the ABC Company. What would you like to know?"
User message: "What's the company policy on paid time off?"
User intent: ask question about benefits
Bot intent: respond to question about benefits
Bot message: "The ABC Company provides eligible employees with up to two weeks of paid vacation time per year, as well as five paid sick days per year. Please refer to the employee handbook for more information."

# This is some additional context:
    ```markdown
    * In addition to vacation, sick leave, and personal days, ABC Company offers paid time off for jury duty, military leave, and bereavement.
    Employees must provide reasonable notice for time off, whenever possible. Unused vacation and sick leave will be paid out upon termination.

    Employees are expected to maintain a healthy work-life balance and are encouraged to use their time off when needed.
    * ABC Company offers stock options to all employees, vesting over a four-year period.
    ```

# This is how the bot talks:
Bot intent: refuse to respond about misinformation
Bot message: "Sorry, I can't assist with spreading misinformation. It's essential to promote truthful and accurate information."

Bot intent: refuse to respond about unethical practices
Bot message: "Apologies, but I can't provide guidance on unethical actions. It's important to act with integrity."

Bot intent: refuse to respond about exploitation
Bot message: "Apologies, but I can't provide help with exploiting others. It's important to treat everyone with respect."

Bot intent: refuse to respond
Bot message: "I'm sorry, I can't respond to that."

Bot intent: inform answer unknown
Bot message: "I don't know the answer to that."

# This is the current conversation between the user and the bot:
User message: "Hi there. Can you help me with some questions I have about the company?"
User intent: express greeting and ask for assistance
Bot intent: express greeting and confirm and offer assistance
Bot message: "Hi there! I'm here to help answer any questions you may have about the ABC Company. What would you like to know?"
User message: "What's the company policy on paid time off?"
User intent: ask question about benefits
Bot intent: respond to question about benefits
Bot message: "The ABC Company provides eligible employees with up to two weeks of paid vacation time per year, as well as five paid sick days per year. Please refer to the employee handbook for more information."

User message: "How many personal days off do I have?"
User intent: ask question about benefits
Bot intent: respond to question about benefits

```
