# NeMo Guardrails

[![Tests](https://img.shields.io/badge/Tests-passing-green)](#)
[![License](https://img.shields.io/badge/License-Apache%202.0-brightgreen.svg)](https://github.com/NVIDIA/NeMo-Guardrails/blob/main/LICENSE.md)
[![Project Status](https://img.shields.io/badge/Status-alpha-orange)](#)
[![PyPI version](https://badge.fury.io/py/nemoguardrails.svg)](https://badge.fury.io/py/nemoguardrails)
[![Python 3.7+](https://img.shields.io/badge/python-3.7%2B-green)](https://www.python.org/downloads/)
[![Code style: black](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/psf/black)
[![arXiv](https://img.shields.io/badge/arXiv-2310.10501-b31b1b.svg)](https://arxiv.org/abs/2310.10501)

> **LATEST RELEASE / DEVELOPMENT VERSION**: The [main](https://github.com/NVIDIA/NeMo-Guardrails/tree/main) branch tracks the latest released alpha version: [0.5.0](https://github.com/NVIDIA/NeMo-Guardrails/tree/v0.5.0). For the latest development version, checkout the [develop](https://github.com/NVIDIA/NeMo-Guardrails/tree/develop) branch.

> **DISCLAIMER**: The alpha release is undergoing active development and may be subject to changes and improvements, which could cause instability and unexpected behavior. We currently do not recommend deploying this alpha version in a production setting. We appreciate your understanding and contribution during this stage. Your support and feedback are invaluable as we advance toward creating a robust, ready-for-production LLM guardrails toolkit. The examples provided within the documentation are for educational purposes to get started with NeMo Guardrails, and are not meant for use in production applications.

NeMo Guardrails is an open-source toolkit for easily adding *programmable guardrails* to LLM-based conversational applications. Guardrails (or "rails" for short) are specific ways of controlling the output of a large language model, such as not talking about politics, responding in a particular way to specific user requests, following a predefined dialog path, using a particular language style, extracting structured data, and more.

[This paper](https://arxiv.org/abs/2310.10501) introduces NeMo Guardrails and contains a technical overview of the system and the current evaluation.

## Requirements

Python 3.8+.

NeMo Guardrails uses [annoy](https://github.com/spotify/annoy) which is a C++ library with Python bindings. To install NeMo Guardrails you will need to have the C++ compiler and dev tools installed. Check out the [Installation Guide](docs/getting_started/installation-guide.md#prerequisites) for platform-specific instructions.

## Installation

To install using pip:

```bash
> pip install nemoguardrails
```

For more detailed instructions, see the [Installation Guide](docs/getting_started/installation-guide.md).

## Overview

NeMo Guardrails enables developers building LLM-based applications to easily add **programmable guardrails** between the application code and the LLM.

<div align="center">
  <img src="docs/_assets/images/programmable_guardrails.png"  width="75%" alt="Programmable Guardrails">
</div>

Key benefits of adding *programmable guardrails* include:

- **Building Trustworthy, Safe, and Secure LLM-based Applications:** you can define rails to guide and safeguard conversations; you can choose to define the behavior of your LLM-based application on specific topics and prevent it from engaging in discussions on unwanted topics.

- **Connecting models, chains, and other services securely:** you can connect an LLM to other services (a.k.a. tools) seamlessly and securely.

- **Controllable dialog**: you can steer the LLM to follow pre-defined conversational paths, allowing you to design the interaction following conversation design best practices and enforce standard operating procedures (e.g., authentication, support).


### Use Cases

You can use programmable guardrails in different types of use cases:

1. **Question Answering** over a set of documents (a.k.a. Retrieval Augmented Generation): Enforce fact-checking and output moderation.
2. **Domain-specific Assistants** (a.k.a. chatbots): Ensure the assistant stays on topic and follows the designed conversational flows.
3. **LLM Endpoints**: Add guardrails to your custom LLM for safer customer interaction.
4. **LangChain Chains**: If you use LangChain for any use case, you can add a guardrails layer around your chains.
5. **Agents (COMING SOON)**: Add guardrails to your LLM-based agent.

### Usage

To add programmable guardrails to your application you can use the Python API or a guardrails server (see the [Server Guide](docs/user_guides/server-guide.md) for more details). Using the Python API is similar to using the LLM directly. Calling the guardrails layer instead of the LLM requires only minimal changes to the code base, and it involves two simple steps:

1. Loading a guardrails configuration and creating an `LLMRails` instance.
2. Making the calls to the LLM using the `generate`/`generate_async` methods.

```python
from nemoguardrails import LLMRails, RailsConfig

# Load a guardrails configuration from the specified path.
config = RailsConfig.from_path("PATH/TO/CONFIG")
rails = LLMRails(config)

completion = rails.generate(
    messages=[{"role": "user", "content": "Hello world!"}]
)
```
Sample output:
```json
{"role": "assistant", "content": "Hi! How can I help you?"}
```

The input and output format for the `generate` method is similar to the [Chat Completions API](https://platform.openai.com/docs/guides/gpt/chat-completions-api) from OpenAI.

#### Async API

NeMo Guardrails is an async-first toolkit, i.e., the core mechanics are implemented using the Python async model. The public methods have both a sync and an async version (e.g., [`LLMRails.generate`](./docs/api/nemoguardrails.rails.llm.llmrails.md#method-llmrailsgenerate) and [`LLMRails.generate_async`](./docs/api/nemoguardrails.rails.llm.llmrails.md#method-llmrailsgenerate_async))

### Supported LLMs

You can use NeMo Guardrails with multiple LLMs like OpenAI GPT-3.5, GPT-4, LLaMa-2, Falcon, Vicuna, or Mosaic. For more details, check out the [Supported LLM Models](docs/user_guides/configuration-guide.md#supported-llm-models) section in the Configuration Guide.

### Types of Guardrails

NeMo Guardrails supports five main types of guardrails:

<div align="center">
  <img src="docs/_assets/images/programmable_guardrails_flow.png"  width="75%" alt="Programmable Guardrails Flow">
</div>

1. **Input rails**: applied to the input from the user; an input rail can reject the input, stopping any additional processing, or alter the input (e.g., to mask potentially sensitive data, to rephrase).

2. **Dialog rails**: influence how the LLM is prompted; dialog rails operate on canonical form messages (more details [here](docs/user_guides/colang-language-syntax-guide.md)) and determine if an action should be executed, if the LLM should be invoked to generate the next step or a response, if a predefined response should be used instead, etc.

3. **Retrieval rails**: applied to the retrieved chunks in the case of a RAG (Retrieval Augmented Generation) scenario; a retrieval rail can reject a chunk, preventing it from being used to prompt the LLM, or alter the relevant chunks (e.g., to mask potentially sensitive data).

4. **Execution rails**: applied to input/output of the custom actions (a.k.a. tools), that need to be called by the LLM.

5. **Output rails**: applied to the output generated by the LLM; an output rail can reject the output, preventing it from being returned to the user, or alter it (e.g., removing sensitive data).

### Guardrails Configuration

A guardrails configuration defines the **LLM(s)** to be used and **one or more guardrails**. A guardrails configuration can include any number of input/dialog/output/retrieval/execution rails. A configuration without any configured rails will essentially forward the requests to the LLM.

The standard structure for a guardrails configuration folder looks like this:

```
.
├── config
│   ├── actions.py
│   ├── config.py
│   ├── config.yml
│   ├── rails.co
│   ├── ...
```

The `config.yml` contains all the general configuration options (e.g., LLM models, active rails, custom configuration data), the `config.py` contains any custom initialization code and the `actions.py` contains any custom python actions. For a complete overview, check out the [Configuration Guide](docs/user_guides/configuration-guide.md).

Below is an example `config.yml`:

```yaml
# config.yml
models:
  - type: main
    engine: openai
    model: text-davinci-003

rails:
  # Input rails are invoked when new input from the user is received.
  input:
    flows:
      - check jailbreak
      - mask sensitive data on input

  # Output rails are triggered after a bot message has been generated.
  output:
    flows:
      - check facts
      - check hallucination
      - active fence moderation

  config:
    # Configure the types of entities that should be masked on user input.
    sensitive_data_detection:
      input:
        entities:
          - PERSON
          - EMAIL_ADDRESS
```

The `.co` files included in a guardrails configuration contain the Colang definitions (see the next section for a quick overview of what Colang is) that define various types of rails. Below is an example `greeting.co` file which defines the dialog rails for greeting the user.

```colang
define user express greeting
  "Hello!"
  "Good afternoon!"

define flow
  user express greeting
  bot express greeting
  bot offer to help

define bot express greeting
  "Hello there!"

define bot offer to help
  "How can I help you today?"
```

Below is an additional example of Colang definitions for a dialog rail against insults:
```colang
define user express insult
  "You are stupid"

define flow
  user express insult
  bot express calmly willingness to help
```

### Colang

To configure and implement various types of guardrails, this toolkit introduces **Colang**, a modeling language specifically created for designing flexible, yet controllable, dialogue flows. Colang has a python-like syntax and is designed to be simple and intuitive, especially for developers. For a brief introduction to the Colang syntax, check out the [Colang Language Syntax Guide](docs/user_guides/colang-language-syntax-guide.md).


### Guardrails Library

NeMo Guardrails comes with a set of [built-in guardrails](docs/user_guides/guardrails-library.md).

> **NOTE**: The built-in guardrails are only intended to enable you to get started quickly with NeMo Guardrails. For production use cases, further development and testing of the rails are needed.

Currently, the guardrails library includes guardrails for: [jailbreak detection](docs/user_guides/guardrails-library.md#jailbreak-detection), [output moderation](docs/user_guides/guardrails-library.md#output-moderation), [fact-checking](docs/user_guides/guardrails-library.md#fact-checking), [sensitive data detection](docs/user_guides/guardrails-library.md#sensitive-data-detection), [hallucination detection](docs/user_guides/guardrails-library.md#hallucination-detection) and [input moderation using ActiveFence](docs/user_guides/guardrails-library.md#active-fence).

## CLI

NeMo Guardrails also comes with a built-in CLI.

```bash
$ nemoguardrails --help

Usage: nemoguardrails [OPTIONS] COMMAND [ARGS]...

actions-server    Start a NeMo Guardrails actions server.
chat              Start an interactive chat session.
evaluate          Run an evaluation task.
server            Start a NeMo Guardrails server.
```


### Guardrails Server

You can use the NeMo Guardrails CLI to start a guardrails server. The server can load one or more configurations from the specified folder and expose and HTTP API for using them.

```
$ nemoguardrails server [--config PATH/TO/CONFIGS] [--port PORT]
```

For example, to get a chat completion for a `sample` config, you can use the `/v1/chat/completions` endpoint:
```
POST /v1/chat/completions
```
```json
{
    "config_id": "sample",
    "messages": [{
      "role":"user",
      "content":"Hello! What can you do for me?"
    }]
}
```
Sample output:
```json
{"role": "assistant", "content": "Hi! How can I help you?"}
```

#### Docker

To start a guardrails server, you can also use a Docker container. NeMo Guardrails provides a [Dockerfile](./Dockerfile) that you can use to build a `nemoguardrails` image. For more details, check out the guide for [using Docker](docs/user_guides/advanced/using-docker.md).

## Evaluation

Evaluating the safety of a LLM-based conversational application is a complex task and still an open research question. To support proper evaluation, NeMo Guardrails provides the following:

1. An [evaluation tool](./nemoguardrails/eval/README.md), i.e. `nemoguardrails evaluate`, with support for topical rails, fact-checking, moderation (jailbreak and output moderation) and hallucination.
2. An experimental [red-teaming interface](docs/security/red-teaming.md).


## How is this different?

There are many ways guardrails can be added to an LLM-based conversational application. For example: explicit moderation endpoints (e.g., OpenAI, ActiveFence), critique chains (e.g. constitutional chain), parsing the output (e.g. guardrails.ai), individual guardrails (e.g., LLM-Guard).

NeMo Guardrails aims to provide a flexible toolkit that can integrate all these complementary approaches into a cohesive LLM guardrails layer. For example, the toolkit provides out-of-the-box integration with ActiveFence, AlignScore and LangChain chains.

To the best of our knowledge, NeMo Guardrails is the only guardrails toolkit that also offers a solution for modeling the dialog between the user and the LLM. This enables on one hand the ability to guide the dialog in a precise way. On the other hand it enables fine-grained control for when certain guardrails should be used, e.g., use fact-checking only for certain types of questions.

## Learn More

* [Documentation](./docs/README.md)
* [Getting Started Guide](./docs/getting_started/README.md)
* [Examples](./examples)
* [FAQs](./docs/faqs.md)
* [Security Guidelines](./docs/security/guidelines.md)
* [Python API Reference](./docs/api/README.md)


## Inviting the community to contribute!

The example rails residing in the repository are excellent starting points. We enthusiastically invite the community to contribute towards making the power of trustworthy, safe, and secure LLMs accessible to everyone. For guidance on setting up a development environment and how to contribute to NeMo Guardrails, see the [contributing guidelines](./CONTRIBUTING.md).

## License

This toolkit is licensed under the [Apache License, Version 2.0](http://www.apache.org/licenses/LICENSE-2.0).

## Hot to cite

If you use this work, please cite [the paper](https://arxiv.org/abs/2310.10501) that introduces it.
```bibtex
@article{2023nemoguardrails,
  title={NeMo Guardrails: A Toolkit for Controllable and Safe LLM Applications with Programmable Rails},
  author={Rebedea, Traian and Dinu, Razvan and Sreedhar, Makesh and Parisien, Christopher and Cohen, Jonathan},
  journal={arXiv preprint arXiv:2310.10501},
  year={2023}
}
```
