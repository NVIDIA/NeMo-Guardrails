# Guardrails Only

Some LLM guardrail scenarios require invoking a guardrail configuration to check only the input or the output (which was generated through other methods). In other words, the interaction with the LLM will not happen **through** the guardrails layer but rather externally, and the guardrails layer is only invoked to check the input/output.

> NOTE: Version `0.8.0` added support in the Python API to invoke only the input/output rails. The patterns below are deprecated.

To invoke only the input rails, you can use the following pattern in your `config.yml`/`config.co`:

```yaml
rails:
  input:
    flows:
      - dummy input rail
      # ... other input rails can go in here
      - allow input
```

```colang
define bot allow
  "ALLOW"

define bot deny
  "DENY"

define subflow dummy input rail
  """A dummy input rail which checks if the word "dummy" is included in the text."""
  if "dummy" in $user_message
    bot deny
    stop

define subflow allow input
  bot allow
  stop
```

To invoke only the output rails, you can use the following pattern in your `config.yml`/`config.co`:

```yaml
rails:
  output:
    flows:
      - dummy output rail

      # ... other output rails go in here

      # The last output rail will rewrite the message to "ALLOW" if it was not blocked
      # up to this point.
      - allow output

  dialog:
    # We need this setting so that the LLM is not used to compute the user intent.
    # Because there is only one canonical form `user input`, everything will fit into that
    # and the flow that returns the $llm_output is used.
    user_messages:
      embeddings_only: True
```

```colang
define user input
  "..."

define flow
  user input
  bot $llm_output

define bot allow
  "ALLOW"

define bot deny
  "DENY"

define subflow dummy output rail
  """A dummy input rail which checks if the word "dummy" is included in the text."""
  if "dummy" in $bot_message
    bot deny
    stop

define subflow allow output
  bot allow
  stop
```

For a complete example, check out the [demo script](./demo.py) and the example [input](./input) and [output](./output) configurations.
