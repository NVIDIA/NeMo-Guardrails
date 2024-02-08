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
