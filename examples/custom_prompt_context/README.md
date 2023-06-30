# Custom Prompt Context

This example shows how you can include custom data in your custom prompt.

A common use case is to let the LLM know the current date and time so that it can respond appropriately to user queries involving a time component, e.g., "What day is today?". To achieve this, you need to:

1. Register an additional [prompt context variable](../../docs/user_guide/advanced/prompt-customization.md#prompt-variables) (i.e., an additional variable that will be available when the prompts are rendered). This can be achieved using the `register_prompt_context(name, value_or_fn)`.

2. Change the desired prompts to include the new variable(s).

Check out the `config.py` and `config.yml` files for a proof-of-concept.

You can test this configuration with `nemoguardrails chat --config=examples/custom_prompt_context`.
