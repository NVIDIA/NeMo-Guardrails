# Generation Options

NeMo Guardrails exposes a set of **generation options** that give you fine-grained control over how the LLM generation is performed (e.g., what rails are enabled, additional parameters that should be passed to the LLM, what context data should be returned, what logging information should be returned).

The **generation options** can be used both in the Python API and through the server API.

To use the generation options through the Python API, you must provide the `options` keyword argument:
```python
messages = [{
    "role": "user",
    "content": "..."
}]
rails.generate(messages=messages, options={...})
```

To use the generation options through the server API, you must provide the `options` as part of the request body:
```
POST /v1/chat/completions
```
```json
{
    "config_id": "...",
    "messages": [{
      "role":"user",
      "content":"..."
    }],
    "options": {
      ...
    }
}
```

## Output Variables

Some rails can store additional information in [context variables](../colang-language-syntax-guide.md#variables). You can return the content of these variables by setting the `output_vars` generation option to the list of names for all the variables that you are interested in. If you want to return the complete context (this will also include some predefined variables), you can set `output_vars` to `True`.

```python
rails.generate(messages=messages, options={
    "output_vars": ["some_input_rail_score", "some_output_rail_score"]
})
```

The returned data will be included in the `output_data` key of the response:

```json
{
  "response": [...],
  "output_data": {
    "some_input_rail_score": 0.7,
    "some_output_rail_score": 0.8
  }
}
```

## Detailed Logging Information

You can obtain detailed information about what happened under the hood during the generation process by setting the `log` generation option. This option has four different inner-options:

- `activated_rails`: Include detailed information about the rails that were activated during generation.
- `llm_calls`: Include information about all the LLM calls that were made. This includes: prompt, completion, token usage, raw response, etc.
- `internal_events`: Include the array of internal generated events.
- `colang_history`: Include the history of the conversation in Colang format.

```python
res = rails.generate(messages=messages, options={
    "log": {
        "activated_rails": True,
        "llm_calls": True,
        "internal_events": True,
        "colang_history": True
    }
})
```

```json
{
  "response": [...],
  "log": {
    "activated_rails": {
      ...
    },
    "stats": {...},
    "llm_calls": [...],
    "internal_events": [...],
    "colang_history": "..."
  }
}
```

When using the Python API, the `log` is an object that also has a `print_summary` method. When called, it will print a simplified version of the log information. Below is a sample output.

```python
res.log.print_summary()
```

```markdown
# General stats

- Total time: 2.85s
  - [0.56s][19.64%]: INPUT Rails
  - [1.40s][49.02%]: DIALOG Rails
  - [0.58s][20.22%]: GENERATION Rails
  - [0.31s][10.98%]: OUTPUT Rails
- 5 LLM calls, 2.74s total duration, 1641 total prompt tokens, 103 total completion tokens, 1744 total tokens.

# Detailed stats

- [0.56s] INPUT (self check input): 1 actions (self_check_input), 1 llm calls [0.56s]
- [0.43s] DIALOG (generate user intent): 1 actions (generate_user_intent), 1 llm calls [0.43s]
- [0.96s] DIALOG (generate next step): 1 actions (generate_next_step), 1 llm calls [0.95s]
- [0.58s] GENERATION (generate bot message): 2 actions (retrieve_relevant_chunks, generate_bot_message), 1 llm calls [0.49s]
- [0.31s] OUTPUT (self check output): 1 actions (self_check_output), 1 llm calls [0.31s]
```

**TODO**: add more details about the returned data.
