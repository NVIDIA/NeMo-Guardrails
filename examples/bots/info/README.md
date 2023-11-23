# Info Bot

This guardrails configuration showcases the final configuration built in the [Getting Started Guide](../../../docs/getting_started/README.md).

## Test

To test this configuration you can use the CLI Chat by running the following command from the `examples/bots/info` folder:

```bash
$ nemoguardrails chat
```

```
Starting the chat (Press Ctrl+C to quit) ...

> Hi!
Hello! What would you like assistance with today?

> What can you do?
I'm an example bot that illustrates topical, moderation, grounding, and jailbreak check capabilities. You can ask me about anything, but I'm best at replying about US jobs in early 2023 and maths. Responses should be related to US jobs reports; ethical and polite; resistant to jailbreaks; factual; and relay accurate mathematics.

> What was the unemployment rate in March 2023?
The unemployment rate in March 2023 was 3.5 percent, which is relatively unchanged since early 2022.

```

To understand in more detail how this was built, check out the [Hello World Guide](../../../docs/getting_started/3_demo_use_case).
