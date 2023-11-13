# Installation Guide

**⚠️THIS SECTION IS WORK IN PROGRESS. ⚠️**

This guide will walk you through installing NeMo Guardrails, and it will cover:

1. Setting up a fresh virtual environment.
2. Installing using `pip` or `conda`.
3. Installing from Source Code.
4. Optional dependencies.

## Prerequisites

Python 3.8+.

NeMo Guardrails uses [annoy](https://github.com/spotify/annoy), which is a C++ library with Python bindings. To be able to install it, you need ...

**⚠️TODO: figure out the exact dependencies for Unix-based, Mac and Windows.**
- `apt-get install gcc g++` ?
- Windows: Visual Studio Build Tools with "Desktop development with C++"?

## Setting up a virtual environment

If you want to experiment with NeMo Guardrails from scratch, we recommend using a fresh virtual environment. Otherwise, you can skip to the following subsection.

1. First, create a folder for your project, e.g., `my_assistant.`

 ```bash
 > mkdir my_assistant
 > cd my_assistant
 ```

2. Create a virtual environment.

 ```bash
 > python3 -m venv venv
 ```

3. Activate the virtual environment.

 ```bash
 > source venv/bin/activate
 ```

## Installation using `pip`

To install NeMo Guardrails using pip:

 ```bash
 > pip install nemoguardrails
 ```

To install NeMo Guardrails using Conda:

**TODO: enable conda installation***
```bash
# conda install nemoguardrails -c conda-forge
```

## Installing from source code

NeMo Guardrails is under active development and the main branch will always contain the latest development version. To install from source, you first need to clone the repository:

```
git clone https://github.com/NVIDIA/NeMo-Guardrails.git
```

Next, you need to install the package locally:

```
cd NeMo-Guardrails
pip install -e .
```

## Optional dependencies

If you want to use OpenAI, also install the `openai` package. And make sure that you have the `OPENAI_API_KEY` environment variable set.

 ```bash
 > pip install openai
 > export OPENAI_API_KEY=...
 ```

**⚠️TODO: add information about the extras.**

## What's next?

* Check out the `hello-world` [example](../getting_started/hello-world.md).
* Explore more examples in `nemoguardrails/examples` folder.
* Review the [user guide](../README.md#user-guide)!
