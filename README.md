# NeMo Guardrails

![Tests](https://img.shields.io/badge/Tests-passing-green)
[![License](https://img.shields.io/badge/License-Apache%202.0-brightgreen.svg)](https://github.com/NVIDIA/NeMo-Guardrails/blob/main/LICENSE.md)
![Project Status](https://img.shields.io/badge/Status-alpha-orange)
[![PyPI version](https://badge.fury.io/py/nemoguardrails.svg)](https://badge.fury.io/py/nemoguardrails)
[![Python 3.7+](https://img.shields.io/badge/python-3.7%2B-green)](https://www.python.org/downloads/)
[![Code style: black](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/psf/black)

NeMo Guardrails is an open-source toolkit for easily adding programmable guardrails to LLM-based conversational systems. Guardrails (or "rails" for short) are specific ways of controlling the output of a large language model, such as not talking about politics, responding in a particular way to specific user requests, following a predefined dialog path, using a particular language style, extracting structured data, and more.

#### **Key Benefits**
- **Building Trustworthy, Safe and Secure LLM Conversational Systems:** The core
value of using NeMo Guardrails is the ability to write rails to guide conversations. Developers
can choose to define the behavior of their LLM-powered bots on certain topics and keep their creativity unencumbered for others!
- **Connect models, chains, services, and more via actions:** LLMs don't need to solve all the challenges. NeMo Guardrails provides the ability to connect your codebase or services to your chatbot seamlessly and securely!

#### **Points of interest**
* [Documentation](./docs/README.md)
* [Understanding the architecture](./docs/architecture/README.md)
* [Examples](./examples/README.md)

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

Guardrails is an open-source toolkit! While the example rails residing in the repository are excellent starting points we enthusiastically invite the community to contribute towards making the power of trustworthy, safe, and secure LLMs accessible to everyone. For guidance on setting up a development environment and how to contribute to NeMo Guardrails, see the [contributing guidelines](./CONTRIBUTING.md).

## License

This toolkit is licensed under the [Apache License, Version 2.0](http://www.apache.org/licenses/LICENSE-2.0).
