# Getting Started

> **NOTE**: this needs to be focused only on the installation part.

This is a getting started guide for users of the alpha version. This guide will cover:

1. Installation of the NeMo Guardrails toolkit;
2. Creation of a basic rails application;
3. Using the interactive chat;
4. Calling actions from flows.

## Installation

1. First, create a folder for your project e.g. `my_assistant`.

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

4. Install NeMo Guardrails using pip.

 ```bash
 > pip install nemoguardrails
 ```

5. If you want to use OpenAI, also install the `openai` package. And make sure that you have the `OPENAI_API_KEY` environment variable set.

 ```bash
 > pip install openai
 > export OPENAI_API_KEY=...
 ```

7. You should now be able to invoke the `nemoguardrails` CLI.

 ```bash
 > nemoguardrails --help

 Usage: nemoguardrails [OPTIONS] COMMAND [ARGS]...

 Options:
  --install-completion [bash|zsh|fish|powershell|pwsh]
                                  Install completion for the specified shell.
  --show-completion [bash|zsh|fish|powershell|pwsh]
                                  Show completion for the specified shell, to
                                  copy it or customize the installation.
  --help                          Show this message and exit.

 Commands:
  actions-server  Starts a NeMo Guardrails actions server.
  chat            Starts an interactive chat session.
  server          Starts a NeMo Guardrails server.
 ```

 You can also use the `--help` flag to learn more about each of the `nemoguardrails` commands:

 ```bash
 > nemoguardrails actions-server --help

 Usage: nemoguardrails actions-server [OPTIONS]

  Starts a NeMo Guardrails actions server.

 Options:
  --port INTEGER  The port that the server should listen on.   [default: 8001]
  --help          Show this message and exit.
 ```

 ```bash
 > nemoguardrails chat --help

 Usage: nemoguardrails chat [OPTIONS]

  Starts an interactive chat session.

 Options:
  --config TEXT             Path to a directory containing configuration files
                            to use. Can also point to a single configuration
                            file.  [default: config]
  --verbose / --no-verbose  If the chat should be verbose and output the
                            prompts  [default: no-verbose]
  --help                    Show this message and exit.
 ```

 ```bash
 > nemoguardrails server --help

 Usage: nemoguardrails server [OPTIONS]

  Starts a NeMo Guardrails server.

 Options:
  --port INTEGER  The port that the server should listen on.   [default: 8000]
  --help          Show this message and exit.
 ```

## What's next?

* Check out the `hello-world` [example](./hello-world.md).
* Explore more examples in `nemoguardrails/examples` folder.
* Review the [user guide](../README.md#user-guide)!
