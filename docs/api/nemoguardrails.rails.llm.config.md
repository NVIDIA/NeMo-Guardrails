<!-- markdownlint-disable -->

<a href="../../nemoguardrails/rails/llm/config.py#L0"><img align="right" style="float:right;" src="https://img.shields.io/badge/-source-cccccc?style=flat-square" /></a>

# <kbd>module</kbd> `nemoguardrails.rails.llm.config`
Module for the configuration of rails.



---

<a href="../../nemoguardrails/rails/llm/config.py#L33"><img align="right" style="float:right;" src="https://img.shields.io/badge/-source-cccccc?style=flat-square" /></a>

## <kbd>class</kbd> `Model`
Configuration of a model used by the rails engine.

Typically, the main model is configured e.g.: {  "type": "main",  "engine": "openai",  "model": "gpt-3.5-turbo-instruct" }





---

<a href="../../nemoguardrails/rails/llm/config.py#L53"><img align="right" style="float:right;" src="https://img.shields.io/badge/-source-cccccc?style=flat-square" /></a>

## <kbd>class</kbd> `Instruction`
Configuration for instructions in natural language that should be passed to the LLM.





---

<a href="../../nemoguardrails/rails/llm/config.py#L60"><img align="right" style="float:right;" src="https://img.shields.io/badge/-source-cccccc?style=flat-square" /></a>

## <kbd>class</kbd> `Document`
Configuration for documents that should be used for question answering.





---

<a href="../../nemoguardrails/rails/llm/config.py#L67"><img align="right" style="float:right;" src="https://img.shields.io/badge/-source-cccccc?style=flat-square" /></a>

## <kbd>class</kbd> `SensitiveDataDetectionOptions`








---

<a href="../../nemoguardrails/rails/llm/config.py#L81"><img align="right" style="float:right;" src="https://img.shields.io/badge/-source-cccccc?style=flat-square" /></a>

## <kbd>class</kbd> `SensitiveDataDetection`
Configuration of what sensitive data should be detected.





---

<a href="../../nemoguardrails/rails/llm/config.py#L103"><img align="right" style="float:right;" src="https://img.shields.io/badge/-source-cccccc?style=flat-square" /></a>

## <kbd>class</kbd> `MessageTemplate`
Template for a message structure.





---

<a href="../../nemoguardrails/rails/llm/config.py#L112"><img align="right" style="float:right;" src="https://img.shields.io/badge/-source-cccccc?style=flat-square" /></a>

## <kbd>class</kbd> `TaskPrompt`
Configuration for prompts that will be used for a specific task.




---

<a href="../../nemoguardrails/rails/llm/config.py#L141"><img align="right" style="float:right;" src="https://img.shields.io/badge/-source-cccccc?style=flat-square" /></a>

### <kbd>classmethod</kbd> `TaskPrompt.check_fields`

```python
check_fields(values)
```






---

<a href="../../nemoguardrails/rails/llm/config.py#L154"><img align="right" style="float:right;" src="https://img.shields.io/badge/-source-cccccc?style=flat-square" /></a>

## <kbd>class</kbd> `EmbeddingSearchProvider`
Configuration of a embedding search provider.





---

<a href="../../nemoguardrails/rails/llm/config.py#L164"><img align="right" style="float:right;" src="https://img.shields.io/badge/-source-cccccc?style=flat-square" /></a>

## <kbd>class</kbd> `KnowledgeBaseConfig`








---

<a href="../../nemoguardrails/rails/llm/config.py#L175"><img align="right" style="float:right;" src="https://img.shields.io/badge/-source-cccccc?style=flat-square" /></a>

## <kbd>class</kbd> `CoreConfig`
Settings for core internal mechanics.





---

<a href="../../nemoguardrails/rails/llm/config.py#L184"><img align="right" style="float:right;" src="https://img.shields.io/badge/-source-cccccc?style=flat-square" /></a>

## <kbd>class</kbd> `InputRails`
Configuration of input rails.





---

<a href="../../nemoguardrails/rails/llm/config.py#L193"><img align="right" style="float:right;" src="https://img.shields.io/badge/-source-cccccc?style=flat-square" /></a>

## <kbd>class</kbd> `OutputRails`
Configuration of output rails.





---

<a href="../../nemoguardrails/rails/llm/config.py#L202"><img align="right" style="float:right;" src="https://img.shields.io/badge/-source-cccccc?style=flat-square" /></a>

## <kbd>class</kbd> `RetrievalRails`
Configuration of retrieval rails.





---

<a href="../../nemoguardrails/rails/llm/config.py#L211"><img align="right" style="float:right;" src="https://img.shields.io/badge/-source-cccccc?style=flat-square" /></a>

## <kbd>class</kbd> `SingleCallConfig`
Configuration for the single LLM call option for topical rails.





---

<a href="../../nemoguardrails/rails/llm/config.py#L221"><img align="right" style="float:right;" src="https://img.shields.io/badge/-source-cccccc?style=flat-square" /></a>

## <kbd>class</kbd> `UserMessagesConfig`
Configuration for how the user messages are interpreted.





---

<a href="../../nemoguardrails/rails/llm/config.py#L230"><img align="right" style="float:right;" src="https://img.shields.io/badge/-source-cccccc?style=flat-square" /></a>

## <kbd>class</kbd> `DialogRails`
Configuration of topical rails.





---

<a href="../../nemoguardrails/rails/llm/config.py#L243"><img align="right" style="float:right;" src="https://img.shields.io/badge/-source-cccccc?style=flat-square" /></a>

## <kbd>class</kbd> `FactCheckingRailConfig`
Configuration data for the fact-checking rail.





---

<a href="../../nemoguardrails/rails/llm/config.py#L257"><img align="right" style="float:right;" src="https://img.shields.io/badge/-source-cccccc?style=flat-square" /></a>

## <kbd>class</kbd> `RailsConfigData`
Configuration data for specific rails that are supported out-of-the-box.





---

<a href="../../nemoguardrails/rails/llm/config.py#L271"><img align="right" style="float:right;" src="https://img.shields.io/badge/-source-cccccc?style=flat-square" /></a>

## <kbd>class</kbd> `Rails`
Configuration of specific rails.





---

<a href="../../nemoguardrails/rails/llm/config.py#L361"><img align="right" style="float:right;" src="https://img.shields.io/badge/-source-cccccc?style=flat-square" /></a>

## <kbd>class</kbd> `RailsConfig`
Configuration object for the models and the rails.

TODO: add typed config for user_messages, bot_messages, and flows.


---

#### <kbd>property</kbd> RailsConfig.streaming_supported

Whether the current config supports streaming or not.

Currently, we don't support streaming if there are output rails.



---

<a href="../../nemoguardrails/rails/llm/config.py#L550"><img align="right" style="float:right;" src="https://img.shields.io/badge/-source-cccccc?style=flat-square" /></a>

### <kbd>method</kbd> `RailsConfig.from_content`

```python
from_content(
    colang_content: Optional[str] = None,
    yaml_content: Optional[str] = None,
    config: Optional[dict] = None
)
```

Loads a configuration from the provided colang/YAML content/config dict.

---

<a href="../../nemoguardrails/rails/llm/config.py#L459"><img align="right" style="float:right;" src="https://img.shields.io/badge/-source-cccccc?style=flat-square" /></a>

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

<a href="../../nemoguardrails/rails/llm/config.py#L576"><img align="right" style="float:right;" src="https://img.shields.io/badge/-source-cccccc?style=flat-square" /></a>

### <kbd>classmethod</kbd> `RailsConfig.parse_object`

```python
parse_object(obj)
```

Parses a configuration object from a given dictionary.
