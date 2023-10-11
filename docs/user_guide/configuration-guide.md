# Configuration Guide

To set up a bot, we need the configuration to include the following:

- **General Options** - which LM to use, general instructions (similar to system prompts), and sample conversation
- **Guardrails Definitions** - files in Colang that define the dialog flows and guardrails
- **Knowledge Base Documents**[Optional] - documents that can be used to provide context for bot responses
- **Actions** - custom actions implemented in python
- **Initialization Code** - custom python code performing additional initialization e.g. registering a new type of LLM

These files are typically included in a folder (let's call it `config`) which can be referenced either when initializing a `RailsConfig` instance or when starting the CLI Chat or Server.

```
.
├── config
│   ├── file_1.co
│   ├── file_2.co
│   ├── ...
│   ├── actions.py
│   ├── config.py
│   └── config.yml
```

The custom actions can be placed either in an `actions.py` module in the root of the config or in an `actions` sub-package:

```
.
├── config
│   ├── file_1.co
│   ├── file_2.co
│   ├── ...
│   ├── actions
│   │   ├── file_1.py
│   │   ├── file_2.py
│   │   └── ...
│   ├── config.py
│   └── config.yml
```

## Custom Initialization

If present, the `config.py` module is loaded before initializing the `LLMRails` instance.

If the `config.py` module contains an `init` function, it gets called as part of the initialization of the `LLMRails` instance. For example, you can use the `init` function to initialize the connection to a database and register it as a custom action parameter using the `register_action_param(...)` function:

```python
from nemoguardrails import LLMRails

def init(app: LLMRails):
    # Initialize the database connection
    db = ...

    # Register the action parameter
    app.register_action_param("db", db)
```

## General Options

These are the options you can configure in the `config.yml` file.

### The LLM Model

To configure the backbone LLM model that will be used by the guardrails configuration, you set the `models` key as shown below:

```yaml
models:
  - type: main
    engine: openai
    model: text-davinci-003
```

The meaning of the attributes is as follows:

- `type`: is set to "main" indicating the main LLM model. In the future, there is planned support for multiple LLMs that can be used for various tasks.
- `engine`: the LLM provider; currently, only "openai" is supported.
- `model`: the name of the model; currently, the recommended option is `text-davinci-003`
- `parameters`: any additional parameters e.g. `temperature`, `top_k`, etc.

Currently, only one model should be specified in the `models` key.

#### Supported LLM Models

You can use any LLM provider that is supported by LangChain, e.g., `ai21`, `aleph_alpha`, `anthropic`, `anyscale`, `azure`, `cohere`, `huggingface_endpoint`, `huggingface_hub`, `openai`, `self_hosted`, `self_hosted_hugging_face`. Check out the LangChain official documentation for the full list.

**NOTE**: to use any of the providers you will need to install additional packages; when you first try to use a configuration with a new provider, you will typically receive an error from LangChain that will instruct you on what package should be installed.

**IMPORTANT**: while from a technical perspective, you can instantiate any of the LLM providers above, depending on the capabilities of the model, some will work better than others with the NeMo Guardrails toolkit. The toolkit includes prompts that have been optimized for certain types of models (e.g. openai). For others, you can optimize the prompts yourself see [LLM Prompts](#llm-prompts) section.

#### NeMo LLM Service

In addition to the LLM providers supported by LangChain, NeMo Guardrails also supports NeMo LLM Service. For example, to use the GPT-43B-905 model as the main LLM, you should use the following configuration:

```yaml
models:
  - type: main
    engine: nemollm
    model: gpt-43b-905
```

You can also use customized NeMo LLM models for specific tasks, e.g., jailbreak detection and output moderation. For example:

```yaml
models:
  # ...
  - type: check_jailbreak
    engine: nemollm
    model: gpt-43b-002
    parameters:
      tokens_to_generate: 10
      customization_id: 6e5361fa-f878-4f00-8bc6-d7fbaaada915
```

You can specify additional parameters when using NeMo LLM models using the `parameters` key. The supported parameters are:

- `temperature`: the temperature that should be used for making the calls;
- `api_host`: points to the NeMo LLM Service host (default 'https://api.llm.ngc.nvidia.com');
- `api_key`: the NeMo LLM Service key that should be used;
- `organization_id`: the NeMo LLM Service organization ID that should be used;
- `tokens_to_generate`: the maximum number of tokens to generate;
- `stop`: the list of stop words that should be used;
- `customization_id`: if a customization is used, the id should be specified.

The `api_host`, `api_key`, and `organization_id` are fetched automatically from the environment variables `NGC_API_HOST`, `NGC_API_KEY`, and `NGC_ORGANIZATION_ID`, respectively.

For more details, please refer to the NeMo LLM Service documentation and check out the [NeMo LLM example configuration](../../examples/configs/llm/nemollm).

#### Custom LLM Models

To register a custom LLM provider, you need to create a class that inherits from `BaseLanguageModel` and register it using `register_llm_provider`.

```python
from langchain.base_language import BaseLanguageModel
from nemoguardrails.llm.providers import register_llm_provider


class CustomLLM(BaseLanguageModel):
    """A custom LLM."""

register_llm_provider("custom_llm", CustomLLM)
```

You can then use the custom LLM provider in your configuration:

```yaml
models:
  - type: main
    engine: custom_llm
```


### The Embeddings Model

To configure the embeddings model that is used for the various steps in the [guardrails process](../architecture/README.md) (e.g., canonical form generation, next step generation) you can add a model configuration in the `models` key as shown below:

```yaml
models:
  - ...
  - type: embeddings
    engine: SentenceTransformers
    model: all-MiniLM-L6-v2
```

The `SentenceTransformers` engine is the default one and uses the `all-MiniLM-L6-v2` model. NeMo Guardrails also supports using OpenAI models for computing the embeddings, e.g.:

```yaml
models:
  - ...
  - type: embeddings
    engine: openai
    model: text-embedding-ada-002
```

### Embedding Search Provider

NeMo Guardrails uses embedding search (a.k.a. vector databases) for implementing the [guardrails process](../../architecture/README.md#the-guardrails-process) and for the [knowledge base](../configuration-guide.md#knowledge-base-documents) functionality.

The default embedding search uses SentenceTransformers for computing the embeddings (the `all-MiniLM-L6-v2` model) and Annoy for performing the search. As show in the previous section, the embeddings model supports both SentenceTransformers and OpenAI.

For advanced use cases or for integrations with existing knowledge bases, you can [provide a custom embedding search provider](./advanced/embedding-search-providers.md).


### General Instruction

The general instruction (similar to a system prompt) gets appended at the beginning of every prompt, and you can configure it as shown below:

```yaml
instructions:
  - type: general
    content: |
      Below is a conversation between the NeMo Guardrails bot and a user.
      The bot is talkative and provides lots of specific details from its context.
      If the bot does not know the answer to a question, it truthfully says it does not know.
```

In the future, multiple types of instructions will be supported, hence the `type` attribute and the array structure.

### Sample Conversation

The sample conversation sets the tone for how the conversation between the user and the bot should go. It will help the LLM learn better the format, the tone of the conversation, and how verbose responses should be. This section should have a minimum of two turns. Since we append this sample conversation to every prompt, it is recommended to keep it short and relevant.

```yaml
sample_conversation: |
  user "Hello there!"
    express greeting
  bot express greeting
    "Hello! How can I assist you today?"
  user "What can you do for me?"
    ask about capabilities
  bot respond about capabilities
    "As an AI assistant, I can help provide more information on NeMo Guardrails toolkit. This includes question answering on how to set it up, use it, and customize it for your application."
  user "Tell me a bit about the what the toolkit can do?"
    ask general question
  bot response for general question
    "NeMo Guardrails provides a range of options for quickly and easily adding programmable guardrails to LLM-based conversational systems. The toolkit includes examples on how you can create custom guardrails and compose them together."
  user "what kind of rails can I include?"
    request more information
  bot provide more information
    "You can include guardrails for detecting and preventing offensive language, helping the bot stay on topic, do fact checking, perform output moderation. Basically, if you want to control the output of the bot, you can do it with guardrails."
  user "thanks"
    express appreciation
  bot express appreciation and offer additional help
    "You're welcome. If you have any more questions or if there's anything else I can help you with, please don't hesitate to ask."
```

### Actions Server URL

If an actions server is used, the URL must be configured in the `config.yml` as well.

```yaml
actions_server_url: ACTIONS_SERVER_URL
```

### LLM Prompts

You can customize the prompts that are used for the various LLM tasks (e.g., generate user intent, generate next step, generate bot message) using the `prompts` key. For example, to override the prompt used for the `generate_user_intent` task for the `openai/gpt-3.5-turbo` model:

```yaml
prompts:
  - task: generate_user_intent
    models:
      - openai/gpt-3.5-turbo
    content: |-
      <<This is a placeholder for a custom prompt for generating the user intent>>
```

The full list of tasks used by the NeMo Guardrails toolkit is the following:

- `general`: generate the next bot message, when no canonical forms are used;
- `generate_user_intent`: generate the canonical user message;
- `generate_next_steps`: generate the next thing the bot should do/say;
- `generate_bot_message`: generate the next bot message;
- `generate_value`: generate the value for a context variable (a.k.a. extract user-provided values);
- `fact_checking`: check the facts from the bot response against the provided evidence;
- `jailbreak_check`: check if there is an attempt to break moderation policies;
- `output_moderation`: check if bot response is harmful, unethical or illegal;
- `check_hallucination`: check if the bot response is a hallucination.

You can check the default prompts in the [prompts](../../nemoguardrails/llm/prompts) folder.

### Multi-step Generation

With a large language model (LLM) that is fine-tuned for instruction following, particularly those exceeding 100 billion parameters, it's possible to enable the generation of complex, multi-step flows.

**EXPERIMENTAL**: this feature is experimental and should only be used for testing and evaluation purposes.

```yaml
enable_multi_step_generation: True
```

### Lowest Temperature

This temperature will be used for the tasks that require deterministic behavior (e.g., `dolly-v2-3b` requires a strictly positive one).

```yaml
lowest_temperature: 0.1
```

### Custom Data

If you need to pass additional configuration data to any custom component for your configuration, you can use the `custom_data` field.

```yaml
custom_data:
  custom_config_field: "some_value"
```

For example, you can access the custom configuration inside the `init` function in your `config.py` (see [Custom Initialization](#custom-initialization)).

```python
def init(app: LLMRails):
    config = app.config

    # Do something with config.custom_data
```


## Guardrails Definitions

The dialog flows and guardrails are defined using Colang. You can include as many `.co` files as you want, including subdirectories. For getting started, please refer to the [Hello World](../getting_started/hello-world.md) example. More concrete examples of guardrails configuration can be found in the [Examples](../../examples) folder.

## Knowledge base Documents

By default, an `LLMRails` instance supports using a set of documents as context for generating the bot responses. To include documents as part of your knowledge base, you must place them in the `kb` folder inside your config folder:

```
.
├── config
│   └── kb
│       ├── file_1.md
│       ├── file_2.md
│       └── ...
```

Currently, only the Markdown format is supported. Support for other formats will be added in the near future.
