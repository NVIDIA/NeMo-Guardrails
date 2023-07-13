<!-- markdownlint-disable -->

<a href="../../nemoguardrails/rails/llm/llmrails.py#L0"><img align="right" style="float:right;" src="https://img.shields.io/badge/-source-cccccc?style=flat-square" /></a>

# <kbd>module</kbd> `nemoguardrails.rails.llm.llmrails`
LLM Rails entry point.



---

<a href="../../nemoguardrails/rails/llm/llmrails.py#L38"><img align="right" style="float:right;" src="https://img.shields.io/badge/-source-cccccc?style=flat-square" /></a>

## <kbd>class</kbd> `LLMRails`
Rails based on a given configuration.

<a href="../../nemoguardrails/rails/llm/llmrails.py#L41"><img align="right" style="float:right;" src="https://img.shields.io/badge/-source-cccccc?style=flat-square" /></a>

### <kbd>method</kbd> `LLMRails.__init__`

```python
__init__(
    config: nemoguardrails.rails.llm.config.RailsConfig,
    llm: Optional[langchain.llms.base.BaseLLM] = None,
    verbose: bool = False
)
```

Initializes the LLMRails instance.



**Args:**

 - <b>`config`</b>:  A rails configuration.
 - <b>`llm`</b>:  An optional LLM engine to use.
 - <b>`verbose`</b>:  Whether the logging should be verbose or not.




---

<a href="../../nemoguardrails/rails/llm/llmrails.py#L256"><img align="right" style="float:right;" src="https://img.shields.io/badge/-source-cccccc?style=flat-square" /></a>

### <kbd>method</kbd> `LLMRails.generate`

```python
generate(prompt: Optional[str] = None, messages: Optional[List[dict]] = None)
```

Synchronous version of generate_async.

---

<a href="../../nemoguardrails/rails/llm/llmrails.py#L185"><img align="right" style="float:right;" src="https://img.shields.io/badge/-source-cccccc?style=flat-square" /></a>

### <kbd>method</kbd> `LLMRails.generate_async`

```python
generate_async(
    prompt: Optional[str] = None,
    messages: Optional[List[dict]] = None
) → Union[str, dict]
```

Generate a completion or a next message.

The format for messages is the following:

```python
     [
         {"role": "context", "content": {"user_name": "John"}},
         {"role": "user", "content": "Hello! How are you?"},
         {"role": "assistant", "content": "I am fine, thank you!"},
         {"role": "event", "event": {"type": "user_silent"}},
         ...
     ]
```



**Args:**

 - <b>`prompt`</b>:  The prompt to be used for completion.
 - <b>`messages`</b>:  The history of messages to be used to generate the next message.



**Returns:**
 The completion (when a prompt is provided) or the next message.

System messages are not yet supported.

---

<a href="../../nemoguardrails/rails/llm/llmrails.py#L310"><img align="right" style="float:right;" src="https://img.shields.io/badge/-source-cccccc?style=flat-square" /></a>

### <kbd>method</kbd> `LLMRails.generate_events`

```python
generate_events(events: List[dict]) → List[dict]
```

Synchronous version of `LLMRails.generate_events_async`.

---

<a href="../../nemoguardrails/rails/llm/llmrails.py#L274"><img align="right" style="float:right;" src="https://img.shields.io/badge/-source-cccccc?style=flat-square" /></a>

### <kbd>method</kbd> `LLMRails.generate_events_async`

```python
generate_events_async(events: List[dict]) → List[dict]
```

Generate the next events based on the provided history.

The format for events is the following:

```python
     [
         {"type": "...", ...},
         ...
     ]
```



**Args:**

 - <b>`events`</b>:  The history of events to be used to generate the next events.



**Returns:**
 The newly generate event(s).

---

<a href="../../nemoguardrails/rails/llm/llmrails.py#L326"><img align="right" style="float:right;" src="https://img.shields.io/badge/-source-cccccc?style=flat-square" /></a>

### <kbd>method</kbd> `LLMRails.register_action`

```python
register_action(
    action: <built-in function callable>,
    name: Optional[str] = None
)
```

Register a custom action for the rails configuration.

---

<a href="../../nemoguardrails/rails/llm/llmrails.py#L330"><img align="right" style="float:right;" src="https://img.shields.io/badge/-source-cccccc?style=flat-square" /></a>

### <kbd>method</kbd> `LLMRails.register_action_param`

```python
register_action_param(name: str, value: Any)
```

Registers a custom action parameter.

---

<a href="../../nemoguardrails/rails/llm/llmrails.py#L334"><img align="right" style="float:right;" src="https://img.shields.io/badge/-source-cccccc?style=flat-square" /></a>

### <kbd>method</kbd> `LLMRails.register_filter`

```python
register_filter(
    filter_fn: <built-in function callable>,
    name: Optional[str] = None
)
```

Register a custom filter for the rails configuration.

---

<a href="../../nemoguardrails/rails/llm/llmrails.py#L338"><img align="right" style="float:right;" src="https://img.shields.io/badge/-source-cccccc?style=flat-square" /></a>

### <kbd>method</kbd> `LLMRails.register_output_parser`

```python
register_output_parser(output_parser: <built-in function callable>, name: str)
```

Register a custom output parser for the rails configuration.

---

<a href="../../nemoguardrails/rails/llm/llmrails.py#L342"><img align="right" style="float:right;" src="https://img.shields.io/badge/-source-cccccc?style=flat-square" /></a>

### <kbd>method</kbd> `LLMRails.register_prompt_context`

```python
register_prompt_context(name: str, value_or_fn: Any)
```

Register a value to be included in the prompt context.

:name: The name of the variable or function that will be used. :value_or_fn: The value or function that will be used to generate the value.
