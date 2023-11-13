# Documentation

The documentation is divided into the following sections:

1. [Getting Started](#getting-started)
2. [Examples](#examples)
3. [User Guide](#user-guide)
4. [Evaluation Tools](#evaluation-tools)
5. [Architecture Guide](#architecture-guide)
6. [Security](#security)
7. [API Reference](./api/README.md)

## Getting Started

This section will help you get started quickly with NeMo Guardrails.

* [Installation guide](getting_started/installation-guide.md): This guide walks you through the process of setting up your environment and installing NeMo Guardrails

* [Getting Started guides](./getting_started): A series of guides that will help you understand the core concepts and build your first guardrails configurations. These guides include Jupyter notebooks that you can experiment with.

## Examples

The [`examples` folder](../examples) contains multiple examples that showcase a particular aspect of using NeMo Guardrails.

* [Bots](../examples/bots): This section includes two example configurations.

  * [Hello World Bot](../examples/bots/hello-world): This basic configuration instructs the bot to greet the user using "Hello World!" and to not talk about politics or the stock market.
  * [Info Bot](../examples/bots/info): This more complex configuration includes topical rails, input and output moderation, retrieval augmented generation, fact-checking and hallucination detection.

* [Configs](../examples/configs): These example configurations showcase specific NeMo Guardrails features, e.g., how to use various LLM providers, Retrieval Augmented Generation, streaming, red-teaming, authentication, etc.

* [Notebooks](../examples/notebooks): These notebooks provide additional examples using Jupyter notebooks, e.g., creating a Pincone index that you can use with NeMo Guardrails.

* [Scripts](../examples/scripts): These short scripts showcase various aspects of the main Python API.


> **Note:** These examples are meant to showcase the process of building rails, not as out-of-the-box safety features. Customization and strengthening of the rails is highly recommended.

## User Guides

The user guides cover the core details of the NeMo Guardrails toolkit and how to configure and use different features to make your own rails.

* [Guardrails Configuration Guide](user_guides/configuration-guide.md): The complete guide to all the configuration options available in the `config.yml` file.
* [Guardrails Library](user_guides/guardrails-library.md): An overview of the starter built-in rails that NeMo Guardrails provide.
* [Colang Language Guide](user_guides/colang-language-syntax-guide.md): Learn the syntax and core concepts of Colang.
* [LLM Support for Guardrails](user_guides/llm-support.md): An easy to grasp summary of the current LLM support.
* [Python API](user_guides/python-api.md): Learn about the Python API, e.g., the `RailsConfig` and `LLMRails` classes.
* [CLI](user_guides/cli.md): Learn about the NeMo Guardrails CLI that can help you use the Chat CLI or start a server.
* [Server Guide](user_guides/server-guide.md): Learn how to use the NeMo Guardrails server.
* [Integration with LangChain](user_guides/integration-with-langchain.md): Integrate Guardrails in your existing LangChain-powered app or bring your preferred Chains to Guardrails.

The following guides explain in more details various specific topics:

* [Extract User-provided Values](user_guides/advanced/extract-user-provided-values.md): Learn how to extract user-provided values like a name, a date or a query.
* [Prompt Customization](user_guides/advanced/prompt-customization.md): Learn how to customize the prompts for a new (or existing) type of LLM.
* [Bot Message Instructions](user_guides/advanced/bot-message-instructions.md): Learn how to further tweak the bot messages with specific instructions at runtime.
* [Streaming](user_guides/advanced/streaming.md): Learn about the streaming support in NeMo Guardrails.
* [Embedding Search Providers](user_guides/advanced/embedding-search-providers.md): Learn about the core embedding search interface that NeMo guardrails uses for some of the core features.
* [Event-based API](user_guides/advanced/event-based-api.md): Learn about the generic event-based interface that you can use to process additional information in your guardrails configuration.
* [Nested AsyncIO Loop](user_guides/advanced/nested-async-loop.md): Understand some of the low level issues regarding `asyncio` and how they are handled in NeMo Guardrails.
* [AlignScore deployment](user_guides/advanced/align_score_deployment.md): Learn how to deploy an AlignScore server either directly or using Docker.

## Evaluation Tools

NeMo Guardrails provides a set of CLI evaluation tools and experimental results for topical and execution rails.
There are also detailed guides on how to reproduce results and create datasets for the evaluation of each type of rail.

* [Evaluation Tools and Results](./../nemoguardrails/eval/README.md): General explanation for the CLI evaluation tools and experimental results.
* [Topical Rail Evaluation - Dataset Tools](./../nemoguardrails/eval/data/topical/README.md): Dataset tools and details to run experiments for topical rails.
* [Fact-checking Rail Evaluation - Dataset Tools](./../nemoguardrails/eval/data/factchecking/README.md): Dataset tools and details to run experiments for fact-checking execution rail.
* [Moderation Rail Evaluation - Dataset Tools](./../nemoguardrails/eval/data/moderation/README.md): Dataset tools and details to run experiments for moderation execution rail.

## Architecture Guide

This guide sheds more light on the infrastructure details and the execution flow for a query when the runtime is used:

* [The Guardrails Process](./architecture/README.md#the-guardrails-process): Learn how the Guardrails runtime works under the hood.

* [Server Architecture](./architecture/README.md#server-architecture): Understand the architecture of the Guardrails server.

# Security

* [Security Guidelines](./security/guidelines.md): Learn about some of the best practices for securely integrating an LLM into your application.
* [Red-teaming](./security/red-teaming.md): Learn how you can use the experimental NeMo Guardrails red-teaming interface.

## Other

* [Glossary](./glossary.md)
* [FAQs](./faqs.md)
