<!-- markdownlint-disable -->

<a href="../../nemoguardrails/rails/llm/config.py#L0"><img align="right" style="float:right;" src="https://img.shields.io/badge/-source-cccccc?style=flat-square" /></a>

# <kbd>module</kbd> `nemoguardrails.rails.llm.config`
Module for the configuration of rails.



---

<a href="../../nemoguardrails/rails/llm/config.py#L29"><img align="right" style="float:right;" src="https://img.shields.io/badge/-source-cccccc?style=flat-square" /></a>

## <kbd>class</kbd> `Model`
Configuration of a model used by the rails engine.

Typically, the main model is configured e.g.: {  "type": "main",  "engine": "openai",  "model": "text-davinci-003" }





---

<a href="../../nemoguardrails/rails/llm/config.py#L49"><img align="right" style="float:right;" src="https://img.shields.io/badge/-source-cccccc?style=flat-square" /></a>

## <kbd>class</kbd> `Instruction`
Configuration for instructions in natural language that should be passed to the LLM.





---

<a href="../../nemoguardrails/rails/llm/config.py#L56"><img align="right" style="float:right;" src="https://img.shields.io/badge/-source-cccccc?style=flat-square" /></a>

## <kbd>class</kbd> `Document`
Configuration for documents that should be used for question answering.





---

<a href="../../nemoguardrails/rails/llm/config.py#L63"><img align="right" style="float:right;" src="https://img.shields.io/badge/-source-cccccc?style=flat-square" /></a>

## <kbd>class</kbd> `MessageTemplate`
Template for a message structure.





---

<a href="../../nemoguardrails/rails/llm/config.py#L72"><img align="right" style="float:right;" src="https://img.shields.io/badge/-source-cccccc?style=flat-square" /></a>

## <kbd>class</kbd> `TaskPrompt`
Configuration for prompts that will be used for a specific task.




---

<a href="../../nemoguardrails/rails/llm/config.py#L93"><img align="right" style="float:right;" src="https://img.shields.io/badge/-source-cccccc?style=flat-square" /></a>

### <kbd>classmethod</kbd> `TaskPrompt.check_fields`

```python
check_fields(values)
```






---

<a href="../../nemoguardrails/rails/llm/config.py#L159"><img align="right" style="float:right;" src="https://img.shields.io/badge/-source-cccccc?style=flat-square" /></a>

## <kbd>class</kbd> `RailsConfig`
Configuration object for the models and the rails.

TODO: add typed config for user_messages, bot_messages, and flows.




---

<a href="../../nemoguardrails/rails/llm/config.py#L318"><img align="right" style="float:right;" src="https://img.shields.io/badge/-source-cccccc?style=flat-square" /></a>

### <kbd>method</kbd> `RailsConfig.from_content`

```python
from_content(
    colang_content: Optional[str] = None,
    yaml_content: Optional[str] = None
)
```

Loads a configuration from the provided colang/YAML content.

---

<a href="../../nemoguardrails/rails/llm/config.py#L227"><img align="right" style="float:right;" src="https://img.shields.io/badge/-source-cccccc?style=flat-square" /></a>

### <kbd>method</kbd> `RailsConfig.from_path`

```python
from_path(
    config_path: str,
    test_set_percentage: Optional[float] = 0.0,
    test_set: Optional[Dict[str, List]] = {},
    max_samples_per_intent: Optional[int] = 0
)
```

Loads a configuration from a given path.

Supports loading a from a single file, or from a directory.

Also used for testing Guardrails apps, in which case the test_set is randomly created from the intent samples in the config files. In this situation test_set_percentage should be larger than 0.

If we want to limit the number of samples for an intent, set the max_samples_per_intent to a positive number. It is useful for testing apps, but also for limiting the number of samples for an intent in some scenarios. The chosen samples are selected randomly for each intent.

---

<a href="../../nemoguardrails/rails/llm/config.py#L339"><img align="right" style="float:right;" src="https://img.shields.io/badge/-source-cccccc?style=flat-square" /></a>

### <kbd>classmethod</kbd> `RailsConfig.parse_object`

```python
parse_object(obj)
```

Parses a configuration object from a given dictionary.
