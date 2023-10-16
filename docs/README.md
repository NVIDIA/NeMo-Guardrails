# Documentation

The documentation is divided into the following sections:

1. [Getting Started](#getting-started)
2. [Examples](#examples)
3. [User Guide](#user-guide)
4. [Evaluation Tools](#evaluation-tools)
5. [Architecture Guide](#architecture-guide)
6. [Security Guidelines](./security/guidelines.md)
7. [API Reference](./api/README.md)

## Getting Started

The getting started section covers two topics:

* [Installation Guide](./getting_started/installation-guide.md): This guide walks you through the process of setting up an environment to run Guardrails. It also showcases the various ways in which you can interact with the bot.
* [The "Hello World" example](./getting_started/hello-world.md): This example walks you through setting up basic rails along with peeling some layers for the Guardrail runtime to explain how the rails work.

## Examples

Five reference examples are provided as a general demonstration for building different types of rails:

* [Topical Rail](../examples/_deprecated/topical_rail/README.md): Making the bot stick to a specific topic of conversation.
* [Moderation Rail](../examples/_deprecated/moderation_rail/README.md): Moderating a bot's response.
* [Fact Checking and Hallucination Rail](../examples/_deprecated/grounding_rail/README.md): Ensuring factual answers.
* [Secure Execution Rail](../examples/_deprecated/execution_rails/README.md): Executing a third-party service with LLMs.
* [Jailbreaking Rail](../examples/_deprecated/jailbreak_check/README.md): Ensuring safe answers despite malicious intent from the user.

> **Note:** These examples are meant to showcase the process of building rails, not as out-of-the-box safety features. Customization and strengthening of the rails is highly recommended.

## User Guide

The user guide covers the core details of the Guardrails toolkit and how to configure and use different features to make your own rails.

* [Colang Language Guide](./user_guide/colang-language-syntax-guide.md): Learn about Colang, the language at the heart of NeMo Guardrails.
* [Colang Syntax Reference Guide](./user_guide/colang-syntax-reference.md): General keyword ledger.
* [Guardrails Configuration Guide](./user_guide/configuration-guide.md): Learn how to do general configurations such as adding a system prompt.
* [Python API](./user_guide/python-api.md): Explore the Python API for Guardrails!
* [Integration with LangChain](./user_guide/integration-with-langchain.md): Integrate Guardrails in your existing LangChain-powered app or bring your preferred Chains to Guardrails.
* [Server Guide](./user_guide/server-guide.md): General explanation for the Guardrails Servers.
* [Interface Guide](./user_guide/server-guide.md): Learn the different ways in which to interact with the bot.

The following guides explain in more details various specific topics:

* [Extract User Provided Values](./user_guide/advanced/extract-user-provided-values.md): Learn how to extract user-provided values like a name, a date or a query.
* [Prompt Customization](./user_guide/advanced/prompt-customization.md): Learn how to customize the prompts for a new (or existing) type of LLM.
* [Bot Message Instructions](./user_guide/advanced/bot-message-instructions.md): Learn how to further tweak the bot messages with specific instructions at runtime.

## Evaluation Tools

We provide a set of CLI evaluation tools and experimental results for topical and execution rails.
There are also detailed guides on how to reproduce results and create datasets for the evaluation of each type of rail.

* [Evaluation Tools and Results](./../nemoguardrails/eval/README.md): General explanation for the CLI evaluation tools and experimental results.
* [Topical Rail Evaluation - Dataset Tools](./../nemoguardrails/eval/data/topical/README.md): Dataset tools and details to run experiments for topical rails.
* [Fact-checking Rail Evaluation - Dataset Tools](./../nemoguardrails/eval/data/factchecking/README.md): Dataset tools and details to run experiments for fact-checking execution rail.
* [Moderation Rail Evaluation - Dataset Tools](./../nemoguardrails/eval/data/moderation/README.md): Dataset tools and details to run experiments for moderation execution rail.

## Architecture Guide

This guide sheds more light on the infrastructure details and the execution flow for a query when the runtime is used:

* [The Guardrails Process](./architecture/README.md#the-guardrails-process): Learn how the Guardrails runtime works under the hood.

* [Server Architecture](./architecture/README.md#server-architecture): Understand the architecture of the Guardrails server.
