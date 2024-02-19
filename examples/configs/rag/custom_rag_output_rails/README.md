# Custom RAG Output Rails

This example demonstrates the use of output rails when using a custom RAG.

The structure of the config folder is the following:

- `kb/` - A folder containing our knowledge base to retrieve context from and fact-check against.
  This folder includes the March 2023 US Jobs report in `kb/report.md`.
- `rails/output.co` - A colang file that contains a flow that routes all user messages into our
  custom RAG.
- `config.py` - The config file containing the custom RAG action and the init function that gets
  called as part of the initialization of the LLMRails instance.
- `config.yml` - The config file holding all the configuration options.

Output railing is enabled by setting the **necessary context variables** via the return type
`ActionResult` of our custom RAG.

The system action `self_check_facts` makes use of `relevant_chunks` to check if `bot_message` is
grounded and entailed to them.

Hallucination-checking, however, relies on the presence of `bot_message` and `_last_bot_prompt`.

So, here is what our custom action returns:

```python
return ActionResult(
    return_value=answer,
    context_updates=context_updates
)
```

Besides the `answer`, we return **context updates**, that contain `relevant_chunks` for fact
checking and `_last_bot_prompt` for hallucination checking.

Please refer to [config.py](./config.py) for the whole example. We chose a custom RAG based on
LangChain. We implement a custom prompt that we both store in context and use to generate a custom
answer.

For simplicity, we re-use the LLM instance configured in [config.yml](./config.yml) as well as the
built-in retrieval via the knowledge base.
