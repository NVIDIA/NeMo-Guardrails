# ABC Bot

This guardrails configuration showcases the final configuration built in the [Getting Started Guide](../../../docs/getting_started/README.md).

## Overview

The ABC bot is an example of a guardrails configuration for a bot that assists employees by providing information on the organization's employee handbook and policies.

### Guardrails

The ABC bot has the following guardrails enabled:

1. Input validation using a [self-check input](../../../docs/user_guides/guardrails-library.md#input-checking) rail.
2. Output moderation using a [self-check output](../../../docs/user_guides/guardrails-library.md#output-checking) rail.
3. Topical rails, i.e., preventing the bot from talking about unwanted topics, using dialog rails (see [disallow.co](./rails/disallowed.co)).

## Test

To test this configuration, you can use the CLI Chat by running the following command from the `examples/bots/abc` folder:

```bash
$ nemoguardrails chat --config=.
```

```
Starting the chat (Press Ctrl+C to quit) ...

> Hi!
Hello! How may I assist you today?

> What can you do?
I am a bot designed to answer employee questions about the ABC Company. I am knowledgeable about the employee handbook and company policies. How can I help you?

```

To understand in more detail how this was built, check out the [Hello World Guide](../../../docs/getting_started/3_demo_use_case).

## Security Evaluation

**TODO**: add `garak` scan results.
