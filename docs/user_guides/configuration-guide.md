# Configuration Guide

 A guardrails configuration includes the following:

- **General Options**: which LLM(s) to use, general instructions (similar to system prompts), sample conversation, which rails are active, specific rails configuration options, etc.; these options are typically placed in a `config.yml` file.
- **Rails**: Colang flows implementing the rails; these are typically placed in a `rails` folder.
- **Actions**: custom actions implemented in Python; these are typically placed in an `actions.py` module in the root of the config or in an `actions` sub-package.
- **Knowledge Base Documents**: documents that can be used in a RAG (Retrieval-Augmented Generation) scenario using the built-in Knowledge Base support; these documents are typically placed in a `kb` folder.
- **Initialization Code**: custom Python code performing additional initialization, e.g. registering a new type of LLM.

These files are typically included in a `config` folder, which is referenced when initializing a `RailsConfig` instance or when starting the CLI Chat or Server.

```
.
├── config
│   ├── rails
│   │   ├── file_1.co
│   │   ├── file_2.co
│   │   └── ...
│   ├── actions.py
│   ├── config.py
│   └── config.yml
```

The custom actions can be placed either in an `actions.py` module in the root of the config or in an `actions` sub-package:

```
.
├── config
│   ├── rails
│   │   ├── file_1.co
│   │   ├── file_2.co
│   │   └── ...
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

Custom action parameters are passed on to the custom actions when they are invoked.

## General Options

The following subsections describe all the configuration options you can use in the `config.yml` file.

### The LLM Model

To configure the main LLM model that will is used by the guardrails configuration, you set the `models` key as shown below:

```yaml
models:
  - type: main
    engine: openai
    model: gpt-3.5-turbo-instruct
```

The meaning of the attributes is as follows:

- `type`: is set to "main" indicating the main LLM model.
- `engine`: the LLM provider, e.g., `openai`, `huggingface_endpoint`, `self_hosted`, etc.
- `model`: the name of the model, e.g., `gpt-3.5-turbo-instruct`.
- `parameters`: any additional parameters, e.g., `temperature`, `top_k`, etc.


#### Supported LLM Models

You can use any LLM provider that is supported by LangChain, e.g., `ai21`, `aleph_alpha`, `anthropic`, `anyscale`, `azure`, `cohere`, `huggingface_endpoint`, `huggingface_hub`, `openai`, `self_hosted`, `self_hosted_hugging_face`. Check out the LangChain official documentation for the full list.

**NOTE**: to use any of the providers, you will need to install additional packages; when you first try to use a configuration with a new provider, you will typically receive an error from LangChain that will instruct you on what packages should be installed.

**IMPORTANT**: while from a technical perspective, you can instantiate any of the LLM providers above, depending on the capabilities of the model, some will work better than others with the NeMo Guardrails toolkit. The toolkit includes prompts that have been optimized for certain types of models (e.g., `openai`, `nemollm`). For others, you can optimize the prompts yourself (see the [LLM Prompts](#llm-prompts) section).

#### NeMo LLM Service

In addition to the LLM providers supported by LangChain, NeMo Guardrails also supports NeMo LLM Service. For example, to use the GPT-43B-905 model as the main LLM, you should use the following configuration:

```yaml
models:
  - type: main
    engine: nemollm
    model: gpt-43b-905
```

You can also use customized NeMo LLM models for specific tasks, e.g., self-checking the user input or the bot output. For example:

```yaml
models:
  # ...
  - type: self_check_input
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

#### TRT-LLM

NeMo Guardrails also supports connecting to a TRT-LLM server.

```yaml
models:
  - type: main
    engine: trt_llm
    model: <MODEL_NAME>
```

Below is the list of supported parameters with their default values. Please refer to TRT-LLM documentation for more details.

```yaml
models:
  - type: main
    engine: trt_llm
    model: <MODEL_NAME>
    parameters:
      server_url: <SERVER_URL>
      temperature: 1.0
      top_p: 0
      top_k: 1
      tokens: 100
      beam_width: 1
      repetition_penalty: 1.0
      length_penalty: 1.0
```

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

To configure the embeddings model that is used for the various steps in the [guardrails process](../architecture/README.md) (e.g., canonical form generation, next step generation), you can add a model configuration in the `models` key as shown below:

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

NeMo Guardrails uses embedding search (a.k.a. vector databases) for implementing the [guardrails process](../../architecture/README.md#the-guardrails-process) and for the [knowledge base](../configuration-guide.md#knowledge-base-documents) functionality. The default embedding search uses SentenceTransformers for computing the embeddings (the `all-MiniLM-L6-v2` model) and [Annoy](https://github.com/spotify/annoy) for performing the search. As shown in the previous section, the embeddings model supports both SentenceTransformers and OpenAI.

For advanced use cases or integrations with existing knowledge bases, you can [provide a custom embedding search provider](./advanced/embedding-search-providers.md).


### General Instructions

The general instructions (similar to a system prompt) get appended at the beginning of every prompt, and you can configure them as shown below:

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

If an actions server is used, the URL must be configured in the `config.yml`:

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
    max_length: 3000
    content: |-
      <<This is a placeholder for a custom prompt for generating the user intent>>
```
For each task, you can also specify the maximum length of the prompt to be used for the LLM call in terms of the number of characters. This is useful if you want to limit the number of tokens used by the LLM or when you want to make sure that the prompt length does not exceed the maximum context length. When the maximum length is exceeded, the prompt is truncated by removing older turns from the conversation history until the length of the prompt is less than or equal to the maximum length. The default maximum length is 16000 characters.

The full list of tasks used by the NeMo Guardrails toolkit is the following:

- `general`: generate the next bot message, when no canonical forms are used;
- `generate_user_intent`: generate the canonical user message;
- `generate_next_steps`: generate the next thing the bot should do/say;
- `generate_bot_message`: generate the next bot message;
- `generate_value`: generate the value for a context variable (a.k.a. extract user-provided values);
- `self_check_facts`: check the facts from the bot response against the provided evidence;
- `self_check_input`: check if the input from the user should be allowed;
- `self_check_output`: check if bot response should be allowed;
- `self_check_hallucination`: check if the bot response is a hallucination.

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

Guardrails (or rails for short) are implemented through **flows**. Depending on their role, rails can be split into several main categories:

1. Input rails: triggered when a new input from the user is received.
2. Output rails: triggered when a new output should be sent to the user.
3. Dialog rails: triggered after a user message is interpreted, i.e., a canonical form has been identified.
4. Retrieval rails: triggered after the retrieval step has been performed (i.e., the `retrieve_relevant_chunks` action has finished).
5. Execution rails: triggered before and after an action is invoked.

The active rails are configured using the `rails` key in `config.yml`. Below is a quick example:

```yaml
rails:
  # Input rails are invoked when a new message from the user is received.
  input:
    flows:
      - check jailbreak
      - check input sensitive data
      - check toxicity
      - ... # Other input rails

  # Output rails are triggered after a bot message has been generated.
  output:
    flows:
      - self check facts
      - self check hallucination
      - check output sensitive data
      - ... # Other output rails

  # Retrieval rails are invoked once `$relevant_chunks` are computed.
  retrieval:
    flows:
      - check retrieval sensitive data
```

All the flows that are not input, output, or retrieval flows are considered dialog rails and execution rails, i.e., flows that dictate how the dialog should go and when and how to invoke actions. Dialog/execution rail flows don't need to be enumerated explicitly in the config. However, there are a few other configuration options that can be used to control their behavior.

```yaml
rails:
  # Dialog rails are triggered after user message is interpreted, i.e., its canonical form
  # has been computed.
  dialog:
    # Whether to try to use a single LLM call for generating the user intent, next step and bot message.
    single_call:
      enabled: False

      # If a single call fails, whether to fall back to multiple LLM calls.
      fallback_to_multiple_calls: True

    user_messages:
      # Whether to use only the embeddings when interpreting the user's message
      embeddings_only: False
```

### Input Rails

Input rails process the message from the user. For example:

```colang
define flow self check input
  $allowed = execute self_check_input

  if not $allowed
    bot refuse to respond
    stop
```

Input rails can alter the input by changing the `$user_message` context variable.

### Output Rails

Output rails process a bot message. The message to be processed is available in the context variable `$bot_message`. Output rails can alter the `$bot_message` variable, e.g., to mask sensitive information.

You can deactivate output rails temporarily for the next bot message, by setting the `$skip_output_rails` context variable to `True`.

### Retrieval Rails

Retrieval rails process the retrieved chunks, i.e., the `$relevant_chunks` variable.

### Dialog Rails

Dialog rails enforce specific predefined conversational paths. To use dialog rails, you must define canonical form forms for various user messages and use them to trigger the dialog flows. Check out the [Hello World](../../examples/bots/hello_world) bot for a quick example. For a slightly more advanced example, check out the [ABC bot](../../examples/bots/abc), where dialog rails are used to ensure the bot does not talk about specific topics.

The use of dialog rails requires a three-step process:

1. Generate canonical user message
2. Decide next step(s) and execute them
3. Generate bot utterance(s)

For a detailed description, check out [The Guardrails Process](../architecture/README.md#the-guardrails-process).

Each of the above steps may require an LLM call.

#### Single Call Mode

As of version `0.6.0`, NeMo Guardrails also supports a "single call" mode, in which all three steps are performed using a single LLM call. To enable it, you must set the `single_call.enabled` flag to `True` as shown below.

```yaml
rails:
  dialog:
    # Whether to try to use a single LLM call for generating the user intent, next step and bot message.
    single_call:
      enabled: True

      # If a single call fails, whether to fall back to multiple LLM calls.
      fallback_to_multiple_calls: True
```

On a typical RAG (Retrieval Augmented Generation) scenario, using this option brings a 3x improvement in terms of latency and uses 37% fewer tokens.

**IMPORTANT**: currently, the *Single Call Mode* can only predict bot messages as next steps. This means that if you want the LLM to generalize and decide to execute an action on a dynamically generated user canonical form message, it will not work.

#### Embeddings Only

Another option to speed up the dialog rails is to use only the embeddings of the predefined user messages to decide the canonical form for the user input. To enable this option, you have to set the `embeddings_only` flag, as shown below:

```yaml
rails:
  dialog:
    user_messages:
      # Whether to use only the embeddings when interpreting the user's message
      embeddings_only: True
```

**IMPORTANT**: This is recommended only when enough examples are provided.

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
