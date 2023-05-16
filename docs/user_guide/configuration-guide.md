# Configuration Guide

To set up a bot, we need the configuration to include the following:

- **General Options** - which LM to use, general instructions (similar to system prompts), and sample conversation
- **Guardrails Definitions** - files in Colang that define the dialog flows and guardrails
- **Knowledge Base Documents**[Optional] - documents that can be used to provide context for bot responses

These files are typically included in a folder (let's call it `config`) which can be referenced either when initializing a `RailsConfig` instance or when starting the CLI Chat or Server.

```
.
├── config
│   ├── file_1.co
│   ├── file_2.co
│   ├── ...
│   └── config.yml
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

You can use any LLM provider that is supported by LangChain.

Supported values are: `ai21`, `aleph_alpha`, `anthropic`, `anyscale`, `azure`, `bananadev`, `cerebriumai`, `cohere`, `deepinfra`, `forefrontai`, `google_palm`, `gooseai`, `gpt4all`, `huggingface_endpoint`, `huggingface_hub`, `huggingface_pipeline`, `huggingface_textgen_inference`, `human-input`, `llamacpp`, `modal`, `nlpcloud`, `openai`, `petals`, `pipelineai`, `replicate`, `rwkv`, `sagemaker_endpoint`, `self_hosted`, `self_hosted_hugging_face`, `stochasticai`.

**NOTE**: to use any of the providers you will need to install additional packages; when you first try to use a configuration with a new provider, you will typically receive an error from LangChain that will instruct you on what package should be installed.

**IMPORTANT**: while from a technical perspective, you can instantiate any of the LLM providers above, depending on the capabilities of the model, some will work better than others with the NeMo Guardrails toolkit. The toolkit includes prompts that have been optimized for certain types of models (e.g. openai). For others, you can optimize the prompts yourself see [...](#) section.


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
