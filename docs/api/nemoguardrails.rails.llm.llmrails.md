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

<a href="../../nemoguardrails/rails/llm/llmrails.py#L202"><img align="right" style="float:right;" src="https://img.shields.io/badge/-source-cccccc?style=flat-square" /></a>

### <kbd>method</kbd> `LLMRails.generate`

```python
generate(prompt: Optional[str] = None, messages: Optional[List[dict]] = None)
```

Synchronous version of generate_async.

---

<a href="../../nemoguardrails/rails/llm/llmrails.py#L141"><img align="right" style="float:right;" src="https://img.shields.io/badge/-source-cccccc?style=flat-square" /></a>

### <kbd>method</kbd> `LLMRails.generate_async`

```python
generate_async(
    prompt: Optional[str] = None,
    messages: Optional[List[dict]] = None
)
```

Generates a completion or a next message.

The format for messages is currently the following: [  {"role": "user", "content": "Hello! How are you?"},  {"role": "assistant", "content": "I am fine, thank you!"}, ] System messages are not yet supported.

---

<a href="../../nemoguardrails/rails/llm/llmrails.py#L220"><img align="right" style="float:right;" src="https://img.shields.io/badge/-source-cccccc?style=flat-square" /></a>

### <kbd>method</kbd> `LLMRails.register_action`

```python
register_action(
    action: <built-in function callable>,
    name: Optional[str] = None
)
```

Register a custom action for the rails configuration.

---

<a href="../../nemoguardrails/rails/llm/llmrails.py#L224"><img align="right" style="float:right;" src="https://img.shields.io/badge/-source-cccccc?style=flat-square" /></a>

### <kbd>method</kbd> `LLMRails.register_action_param`

```python
register_action_param(name: str, value: Any)
```

Registers a custom action parameter.

---

<a href="../../nemoguardrails/rails/llm/llmrails.py#L228"><img align="right" style="float:right;" src="https://img.shields.io/badge/-source-cccccc?style=flat-square" /></a>

### <kbd>method</kbd> `LLMRails.register_filter`

```python
register_filter(
    filter_fn: <built-in function callable>,
    name: Optional[str] = None
)
```

Register a custom filter for the rails configuration.

---

<a href="../../nemoguardrails/rails/llm/llmrails.py#L232"><img align="right" style="float:right;" src="https://img.shields.io/badge/-source-cccccc?style=flat-square" /></a>

### <kbd>method</kbd> `LLMRails.register_output_parser`

```python
register_output_parser(output_parser: <built-in function callable>, name: str)
```

Register a custom output parser for the rails configuration.

---

<a href="../../nemoguardrails/rails/llm/llmrails.py#L236"><img align="right" style="float:right;" src="https://img.shields.io/badge/-source-cccccc?style=flat-square" /></a>

### <kbd>method</kbd> `LLMRails.register_prompt_context`

```python
register_prompt_context(name: str, value_or_fn: Any)
```

Register a value to be included in the prompt context.

:name: The name of the variable or function that will be used. :value_or_fn: The value or function that will be used to generate the value.
