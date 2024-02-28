# CLI

**NOTE: THIS SECTION IS WORK IN PROGRESS.**

## Guardrails CLI
For testing purposes, the Guardrails toolkit provides a command line chat that can be used to interact with the LLM.
```
> nemoguardrails chat --config examples/ [--verbose] [--verbose-llm-calls]
```
#### Options
- `--config`: The configuration that should be used. Can be a folder or a .co/.yml file.
- `--verbose`: In verbose mode, detailed debugging information is also shown.
- `--verbose-llm-calls`: In verbose LLM calls mode, the debugging information includes the entire prompt that is sent to the LLM and the completion.


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
  --verbose / --no-verbose  If the chat should be verbose and output detailed logging information. [default: no-verbose]
  --verbose-llm-calls    --no-verbose-llm-calls          If the chat should be verbose and include the prompts and responses for the LLM calls. [default: no-verbose-llm-calls]
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
