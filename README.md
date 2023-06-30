# NeMo Guardrails

[![Tests](https://img.shields.io/badge/Tests-passing-green)](#)
[![License](https://img.shields.io/badge/License-Apache%202.0-brightgreen.svg)](https://github.com/NVIDIA/NeMo-Guardrails/blob/main/LICENSE.md)
[![Project Status](https://img.shields.io/badge/Status-alpha-orange)](#)
[![PyPI version](https://badge.fury.io/py/nemoguardrails.svg)](https://badge.fury.io/py/nemoguardrails)
[![Python 3.7+](https://img.shields.io/badge/python-3.7%2B-green)](https://www.python.org/downloads/)
[![Code style: black](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/psf/black)

**LATEST RELEASE: You are currently on the main branch which tracks
under-development progress towards the next release. The current release is
an alpha version, [0.3.0](https://github.com/NVIDIA/NeMo-Guardrails/tree/v0.3.0)**.

> **DISCLAIMER**: The alpha release is undergoing active development and may be subject to changes and improvements, which could potentially cause instability and unexpected behavior. We currently do not recommend deploying this alpha version in a production setting. We appreciate your understanding and contribution during this stage. Your support and feedback is invaluable as we advance toward creating a robust, ready-for-production LLM guardrails toolkit.

NeMo Guardrails is an open-source toolkit for easily adding programmable guardrails to LLM-based conversational systems. Guardrails (or "rails" for short) are specific ways of controlling the output of a large language model, such as not talking about politics, responding in a particular way to specific user requests, following a predefined dialog path, using a particular language style, extracting structured data, and more.

This toolkit is currently in its early alpha stages, and we invite the community to contribute towards making the power of trustworthy, safe, and secure LLMs accessible to everyone. The examples provided within the documentation are for educational purposes to get started with NeMo Guardrails, and are not meant for use in production applications.

We are committed to improving the toolkit in the near term to make it easier for developers to build production-grade trustworthy, safe, and secure LLM applications.

#### **Key Benefits**

- **Building Trustworthy, Safe, and Secure LLM Conversational Systems:** The core
value of using NeMo Guardrails is the ability to write rails to guide conversations. You
can choose to define the behavior of your LLM-powered application on specific topics and prevent it from engaging in discussions on unwanted topics.

- **Connect models, chains, services, and more via actions:** NeMo Guardrails provides the ability to connect an LLM to other services (a.k.a. tools) seamlessly and securely.

## Learn More

* [Documentation](./docs/README.md)
* [Examples](./examples/README.md)
* [Understanding the architecture](./docs/architecture/README.md)
* [FAQs](./docs/faqs.md)
* [Security Guidelines](./docs/security/guidelines.md)


## Installation

To install using pip:

```bash
> pip install nemoguardrails
```

## Usage

To apply guardrails, you first create an `LLMRails` instance, configure the desired rails and then use it to interact with the LLM.

```python
from nemoguardrails import LLMRails, RailsConfig

config = RailsConfig.from_path("path/to/config")
app = LLMRails(config)

new_message = app.generate(messages=[{
    "role": "user",
    "content": "Hello! What can you do for me?"
}])
```

If you're using `LLMRails` from an async code base or from a Jupyter notebook, you should use the `generate_async` function:

```python
new_message = await app.generate_async(messages=[{
    "role": "user",
    "content": "Hello! What can you do for me?"
}])
```

### With LangChain

You can easily add guardrails on top of existing [LangChain](https://github.com/hwchase17/langchain) chains. For example, you can integrate a RetrievalQA chain for questions answering next to a basic guardrail against insults, as shown below.

Guardrails configuration:

```colang
define user express insult
  "You are stupid"

# Basic guardrail against insults.
define flow
  user express insult
  bot express calmly willingness to help

# Here we use the QA chain for anything else.
define flow
  user ...
  $answer = execute qa_chain(query=$last_user_message)
  bot $answer
```

Python code:

```python
from nemoguardrails import LLMRails, RailsConfig

config = RailsConfig.from_path("path/to/config")
app = LLMRails(config)

# ... initialize `docsearch`

qa_chain = RetrievalQA.from_chain_type(
    llm=app.llm, chain_type="stuff", retriever=docsearch.as_retriever()
)
app.register_action(qa_chain, name="qa_chain")

history = [
    {"role": "user", "content": "What is the current unemployment rate?"}
]
result = app.generate(messages=history)
print(result)
```

## Guardrails Configuration

This toolkit introduces Colang, a modeling language specifically created for designing flexible, yet controllable, dialogue flows. Colang has a python-like syntax and is designed to be simple and intuitive, especially for developers.

To configure guardrails, you place one or more .co files in a configuration folder. Below is a basic example of controlling the greeting behavior.

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

**Warning:** Colang files can be written to perform complex activities, such as calling python scripts and performing multiple calls to the underlying language model. You should avoid loading Colang files from untrusted sources without careful inspection.

For a brief introduction to the Colang syntax, check out the [Colang Language Syntax Guide](./docs/user_guide/colang-language-syntax-guide.md).


## Inviting the community to contribute!

The example rails residing in the repository are excellent starting points. We enthusiastically invite the community to contribute towards making the power of trustworthy, safe, and secure LLMs accessible to everyone. For guidance on setting up a development environment and how to contribute to NeMo Guardrails, see the [contributing guidelines](./CONTRIBUTING.md).

## License

This toolkit is licensed under the [Apache License, Version 2.0](http://www.apache.org/licenses/LICENSE-2.0).
