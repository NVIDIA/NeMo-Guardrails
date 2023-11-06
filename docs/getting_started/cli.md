# CLI

**NOTE: THIS SECTION IS WORK IN PROGRESS.**



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
