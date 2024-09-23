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

To configure the main LLM model that will be used by the guardrails configuration, you set the `models` key as shown below:

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

```{note}
To use any of the providers, you must install additional packages; when you first try to use a configuration with a new provider, you typically receive an error from LangChain that instructs which packages you should install.
```

```{important}
Although you can instantiate any of the previously mentioned LLM providers, depending on the capabilities of the model, the NeMo Guardrails toolkit works better with some providers than others. The toolkit includes prompts that have been optimized for certain types of models, such as `openai` and `nemollm`. For others, you can optimize the prompts yourself following the information in the [LLM Prompts](#llm-prompts) section.
```

#### NIM for LLMs

[NVIDIA NIM](https://docs.nvidia.com/nim/index.html) is a set of easy-to-use microservices designed to accelerate the deployment of generative AI models across the cloud, data center, and workstations.
[NVIDIA NIM for LLMs](https://docs.nvidia.com/nim/large-language-models/latest/introduction.html) brings the power of state-of-the-art LLMs to enterprise applications, providing unmatched natural language processing and understanding capabilities. [Learn more about NIMs](https://developer.nvidia.com/blog/nvidia-nim-offers-optimized-inference-microservices-for-deploying-ai-models-at-scale/).

NeMo Guardrails supports connecting to a NIM as follows:

```yaml
models:
  - type: main
    engine: nim
    model: <MODEL_NAME>
    parameters:
      base_url: <NIM_ENDPOINT_URL>
```

For example, to connect to a locally deployed `meta/llama3-8b-instruct` model, on port 8000, use the following model configuration:

```yaml
models:
  - type: main
    engine: nim
    model: meta/llama3-8b-instruct
    parameters:
      base_url: http://localhost:8000/v1
```

```{important}
To use the `nim` LLM provider, install the `langchain-nvidia-ai-endpoints` package using the command `pip install langchain-nvidia-ai-endpoints`.
```

#### NVIDIA AI Endpoints

[NVIDIA AI Endpoints](https://www.nvidia.com/en-us/ai-data-science/foundation-models/) give users easy access to NVIDIA hosted API endpoints for NVIDIA AI Foundation Models such as Llama 3, Mixtral 8x7B, and Stable Diffusion.
These models, hosted on the [NVIDIA API catalog](https://build.nvidia.com/), are optimized, tested, and hosted on the NVIDIA AI platform, making them fast and easy to evaluate, further customize, and seamlessly run at peak performance on any accelerated stack.

To use an LLM model through the NVIDIA AI Endpoints, use the following model configuration:

```yaml
models:
  - type: main
    engine: nvidia_ai_endpoints
    model: <MODEL_NAME>
```

For example, to use the `llama3-8b-instruct` model, use the following model configuration:

```yaml
models:
  - type: main
    engine: nvidia_ai_endpoints
    model: meta/llama3-8b-instruct
```

```{important}
To use the `nvidia_ai_endpoints` LLM provider, you must install the `langchain-nvidia-ai-endpoints` package using the command `pip install langchain-nvidia-ai-endpoints`, and configure a valid `NVIDIA_API_KEY`.
```

For further information, see the [user guide](./llm/nvidia_ai_endpoints/README.md).

Here's an example configuration for using `llama3` model with [Ollama](https://ollama.com/):

```yaml
models:
  - type: main
    engine: ollama
    model: llama3
    parameters:
      base_url: http://your_base_url
```

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
- `api_host`: points to the NeMo LLM Service host (default '<https://api.llm.ngc.nvidia.com>');
- `api_key`: the NeMo LLM Service key that should be used;
- `organization_id`: the NeMo LLM Service organization ID that should be used;
- `tokens_to_generate`: the maximum number of tokens to generate;
- `stop`: the list of stop words that should be used;
- `customization_id`: if a customization is used, the id should be specified.

The `api_host`, `api_key`, and `organization_id` are fetched automatically from the environment variables `NGC_API_HOST`, `NGC_API_KEY`, and `NGC_ORGANIZATION_ID`, respectively.

For more details, please refer to the NeMo LLM Service documentation and check out the [NeMo LLM example configuration](https://github.com/NVIDIA/NeMo-Guardrails/tree/develop/examples/configs/llm/nemollm/README.md).

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

It is important to implement the following methods:

**Required**:

- `_call`
- `_llm_type`

**Optional**:

- `_acall`
- `_astream`
- `_stream`
- `_identifying_params`

In other words, to create your custom LLM provider, you need to implement the following interface methods: `_call`, `_llm_type`, and optionally `_acall`, `_astream`, `_stream`, and `_identifying_params`. Here's how you can do it:

```python
from typing import Any, Iterator, List, Optional

from langchain.base_language import BaseLanguageModel
from langchain_core.callbacks.manager import (
    CallbackManagerForLLMRun,
    AsyncCallbackManagerForLLMRun,
)
from langchain_core.outputs import GenerationChunk

from nemoguardrails.llm.providers import register_llm_provider


class MyCustomLLM(BaseLanguageModel):

    def _call(
        self,
        prompt: str,
        stop: Optional[List[str]] = None,
        run_manager: Optional[CallbackManagerForLLMRun] = None,
        **kwargs,
    ) -> str:
        pass

    async def _acall(
        self,
        prompt: str,
        stop: Optional[List[str]] = None,
        run_manager: Optional[AsyncCallbackManagerForLLMRun] = None,
        **kwargs,
    ) -> str:
        pass

    def _stream(
        self,
        prompt: str,
        stop: Optional[List[str]] = None,
        run_manager: Optional[CallbackManagerForLLMRun] = None,
        **kwargs: Any,
    ) -> Iterator[GenerationChunk]:
        pass

    # rest of the implementation
    ...

register_llm_provider("custom_llm", MyCustomLLM)
```

You can then use the custom LLM provider in your configuration:

```yaml
models:
  - type: main
    engine: custom_llm
```

### Configuring LLMs per Task

The interaction with the LLM is structured in a task-oriented manner. Each invocation of the LLM is associated with a specific task. These tasks are integral to the guardrail process and include:

1. `generate_user_intent`: This task transforms the raw user utterance into a canonical form. For instance, "Hello there" might be converted to `express greeting`.
2. `generate_next_steps`: This task determines the bot's response or the action to be executed. Examples include `bot express greeting` or `bot respond to question`.
3. `generate_bot_message`: This task decides the exact bot message to be returned.
4. `general`: This task generates the next bot message based on the history of user and bot messages. It is used when there are no dialog rails defined (i.e., no user message canonical forms).

For a comprehensive list of tasks, refer to the [Task type](https://github.com/NVIDIA/NeMo-Guardrails/blob/develop/nemoguardrails/llm/types.py).

You can use different LLM models for specific tasks. For example, you can use a different model for the `self_check_input` and `self_check_output` tasks from various providers. Here's an example configuration:

```yaml

models:
  - type: main
    model: meta/llama-3.1-8b-instruct
    engine: nim
  - type: self_check_input
    model: meta/llama3-8b-instruct
    engine: nim
  - type: self_check_output
    model: meta/llama-3.1-70b-instruct
    engine: nim
```

In the previous example, the `self_check_input` and `self_check_output` tasks use different models. It is even possible to get more granular and use different models for a task like `generate_user_intent`:

```yaml
models:
  - type: main
    model: meta/llama-3.1-8b-instruct
    engine: nim
  - type: self_check_input
    model: meta/llama3-8b-instruct
    engine: nim
  - type: self_check_output
    model: meta/llama-3.1-70b-instruct
    engine: nim
  - type: generate_user_intent
    model: meta/llama-3.1-8b-instruct
    engine: nim
```

> Remember, the best model for your needs will depend on your specific requirements and constraints. It's often a good idea to experiment with different models to see which one works best for your specific use case.

### The Embeddings Model

To configure the embedding model used for the various steps in the [guardrails process](../architecture/README.md), such as canonical form generation and next step generation, add a model configuration in the `models` key as shown in the following configuration file:

```yaml
models:
  - ...
  - type: embeddings
    engine: FastEmbed
    model: all-MiniLM-L6-v2
```

The `FastEmbed` engine is the default one and uses the `all-MiniLM-L6-v2` model. NeMo Guardrails also supports using OpenAI models for computing the embeddings, e.g.:

```yaml
models:
  - ...
  - type: embeddings
    engine: openai
    model: text-embedding-ada-002
```

#### Supported Embedding Providers

The following tables lists the supported embedding providers:

| Provider Name        | `engine_name`          | `model`                            |
|----------------------|------------------------|------------------------------------|
| FastEmbed (default)  | `FastEmbed`            | `all-MiniLM-L6-v2` (default), etc. |
| OpenAI               | `openai`               | `text-embedding-ada-002`, etc.     |
| SentenceTransformers | `SentenceTransformers` | `all-MiniLM-L6-v2`, etc.           |
| NVIDIA AI Endpoints  | `nvidia_ai_endpoints`  | `nv-embed-v1`, etc.                |

```{note}
You can use any of the supported models for any of the supported embedding providers.
The previous table includes an example of a model that can be used.
```

#### Custom Embedding Provider

You can also register a custom embedding provider by using the `LLMRails.register_embedding_provider` function.

To register a custom LLM provider,
create a class that inherits from `EmbeddingModel` and register it in your `config.py`.

```python
from typing import List
from nemoguardrails.embeddings.providers.base import EmbeddingModel
from nemoguardrails import LLMRails


class CustomEmbeddingModel(EmbeddingModel):
    """An implementation of a custom embedding provider."""
    engine_name = "CustomEmbeddingModel"

    def __init__(self, embedding_model: str):
        # Initialize the model
        ...

    async def encode_async(self, documents: List[str]) -> List[List[float]]:
        """Encode the provided documents into embeddings.

        Args:
            documents (List[str]): The list of documents for which embeddings should be created.

        Returns:
            List[List[float]]: The list of embeddings corresponding to the input documents.
        """
        ...

    def encode(self, documents: List[str]) -> List[List[float]]:
        """Encode the provided documents into embeddings.

        Args:
            documents (List[str]): The list of documents for which embeddings should be created.

        Returns:
            List[List[float]]: The list of embeddings corresponding to the input documents.
        """
        ...


def init(app: LLMRails):
    """Initialization function in your config.py."""
    app.register_embedding_provider(CustomEmbeddingModel, "CustomEmbeddingModel")
```

You can then use the custom embedding provider in your configuration:

```yaml
models:
  # ...
  - type: embeddings
    engine: SomeCustomName
    model: SomeModelName      # supported by the provider.
```

### Embedding Search Provider

NeMo Guardrails uses embedding search, also called vector databases, for implementing the [guardrails process](../architecture/README.md#the-guardrails-process) and for the [knowledge base](#knowledge-base-documents) functionality. The default embedding search uses FastEmbed for computing the embeddings (the `all-MiniLM-L6-v2` model) and [Annoy](https://github.com/spotify/annoy) for performing the search. As shown in the previous section, the embeddings model supports both FastEmbed and OpenAI. SentenceTransformers is also supported.

For advanced use cases or integrations with existing knowledge bases, you can [provide a custom embedding search provider](advanced/embedding-search-providers.md).

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
    output_parser: user_intent
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

You can check the default prompts in the [prompts](https://github.com/NVIDIA/NeMo-Guardrails/tree/develop/nemoguardrails/llm/prompts) folder.

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

Dialog rails enforce specific predefined conversational paths. To use dialog rails, you must define canonical form forms for various user messages and use them to trigger the dialog flows. Check out the [Hello World](.https://github.com/NVIDIA/NeMo-Guardrails/tree/develop/examples/bots/hello_world/README.md) bot for a quick example. For a slightly more advanced example, check out the [ABC bot](https://github.com/NVIDIA/NeMo-Guardrails/tree/develop/examples/bots/abc/README.md), where dialog rails are used to ensure the bot does not talk about specific topics.

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
      # Use only the embeddings when the similarity is above the specified threshold.
      embeddings_only_similarity_threshold: 0.75
      # When the fallback is set to None, if the similarity is below the threshold, the user intent is computed normally using the LLM.
      # When it is set to a string value, that string value will be used as the intent.
      embeddings_only_fallback_intent: None
```

**IMPORTANT**: This is recommended only when enough examples are provided. The threshold used here is 0.75, which triggers an LLM call for user intent generation if the similarity is below this value. If you encounter false positives, consider increasing the threshold to 0.8. Note that the threshold is model dependent.

## Exceptions

NeMo Guardrails supports raising exceptions from within flows.
An exception is an event whose name ends with `Exception`, e.g., `InputRailException`.
When an exception is raised, the final output is a message with the role set to `exception` and the content
set to additional information about the exception. For example:

```colang
define flow input rail example
  # ...
  create event InputRailException(message="Input not allowed.")
```

```json
{
  "role": "exception",
  "content": {
    "type": "InputRailException",
    "uid": "45a452fa-588e-49a5-af7a-0bab5234dcc3",
    "event_created_at": "9999-99-99999:24:30.093749+00:00",
    "source_uid": "NeMoGuardrails",
    "message": "Input not allowed."
  }
}
```

### Guardrails Library Exception

By default, all the guardrails included in the [Guardrails Library](./guardrails-library.md) return a predefined message
when a rail is triggered. You can change this behavior by setting the `enable_rails_exceptions` key to `True` in your
`config.yml` file:

```yaml
enable_rails_exceptions: True
```

When this setting is enabled, the rails are triggered, they will return an exception message.
To understand better what is happening under the hood, here's how the `self check input` rail is implemented:

```colang
define flow self check input
  $allowed = execute self_check_input
  if not $allowed
    if $config.enable_rails_exceptions
      create event InputRailException(message="Input not allowed. The input was blocked by the 'self check input' flow.")
    else
      bot refuse to respond
      stop
```

> **Note**: In Colang 2.x, you must change `$config.enable_rails_exceptions` to `$system.config.enable_rails_exceptions` and `create event` to `send`.

When the `self check input` rail is triggered, the following exception is returned.

```json
{
  "role": "exception",
  "content": {
    "type": "InputRailException",
    "uid": "45a452fa-588e-49a5-af7a-0bab5234dcc3",
    "event_created_at": "9999-99-99999:24:30.093749+00:00",
    "source_uid": "NeMoGuardrails",
    "message": "Input not allowed. The input was blocked by the 'self check input' flow."
  }
}
```

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
