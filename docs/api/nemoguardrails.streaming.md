<!-- markdownlint-disable -->

<a href="../../nemoguardrails/streaming.py#L0"><img align="right" style="float:right;" src="https://img.shields.io/badge/-source-cccccc?style=flat-square" /></a>

# <kbd>module</kbd> `nemoguardrails.streaming`






---

<a href="../../nemoguardrails/streaming.py#L31"><img align="right" style="float:right;" src="https://img.shields.io/badge/-source-cccccc?style=flat-square" /></a>

## <kbd>class</kbd> `StreamingHandler`
Streaming async handler.

Implements the LangChain AsyncCallbackHandler, so it can be notified of new tokens. It also implements the AsyncIterator interface, so it can be used directly to stream back the response.

<a href="../../nemoguardrails/streaming.py#L39"><img align="right" style="float:right;" src="https://img.shields.io/badge/-source-cccccc?style=flat-square" /></a>

### <kbd>method</kbd> `StreamingHandler.__init__`

```python
__init__(enable_print: bool = False, enable_buffer: bool = False)
```






---

#### <kbd>property</kbd> StreamingHandler.ignore_agent

Whether to ignore agent callbacks.

---

#### <kbd>property</kbd> StreamingHandler.ignore_chain

Whether to ignore chain callbacks.

---

#### <kbd>property</kbd> StreamingHandler.ignore_chat_model

Whether to ignore chat model callbacks.

---

#### <kbd>property</kbd> StreamingHandler.ignore_llm

Whether to ignore LLM callbacks.

---

#### <kbd>property</kbd> StreamingHandler.ignore_retriever

Whether to ignore retriever callbacks.

---

#### <kbd>property</kbd> StreamingHandler.ignore_retry

Whether to ignore retry callbacks.



---

<a href="../../nemoguardrails/streaming.py#L121"><img align="right" style="float:right;" src="https://img.shields.io/badge/-source-cccccc?style=flat-square" /></a>

### <kbd>method</kbd> `StreamingHandler.disable_buffering`

```python
disable_buffering()
```

When we disable the buffer, we process the buffer as a chunk.

---

<a href="../../nemoguardrails/streaming.py#L117"><img align="right" style="float:right;" src="https://img.shields.io/badge/-source-cccccc?style=flat-square" /></a>

### <kbd>method</kbd> `StreamingHandler.enable_buffering`

```python
enable_buffering()
```





---

<a href="../../nemoguardrails/streaming.py#L263"><img align="right" style="float:right;" src="https://img.shields.io/badge/-source-cccccc?style=flat-square" /></a>

### <kbd>method</kbd> `StreamingHandler.on_chat_model_start`

```python
on_chat_model_start(
    serialized: Dict[str, Any],
    messages: List[List[langchain.schema.messages.BaseMessage]],
    run_id: uuid.UUID,
    parent_run_id: Optional[uuid.UUID] = None,
    tags: Optional[List[str]] = None,
    metadata: Optional[Dict[str, Any]] = None,
    **kwargs: Any
) → Any
```





---

<a href="../../nemoguardrails/streaming.py#L295"><img align="right" style="float:right;" src="https://img.shields.io/badge/-source-cccccc?style=flat-square" /></a>

### <kbd>method</kbd> `StreamingHandler.on_llm_end`

```python
on_llm_end(
    response: langchain.schema.output.LLMResult,
    run_id: uuid.UUID,
    parent_run_id: Optional[uuid.UUID] = None,
    tags: Optional[List[str]] = None,
    **kwargs: Any
) → None
```

Run when LLM ends running.

---

<a href="../../nemoguardrails/streaming.py#L276"><img align="right" style="float:right;" src="https://img.shields.io/badge/-source-cccccc?style=flat-square" /></a>

### <kbd>method</kbd> `StreamingHandler.on_llm_new_token`

```python
on_llm_new_token(
    token: str,
    chunk: Optional[langchain.schema.output.GenerationChunk, langchain.schema.output.ChatGenerationChunk] = None,
    run_id: uuid.UUID,
    parent_run_id: Optional[uuid.UUID] = None,
    tags: Optional[List[str]] = None,
    **kwargs: Any
) → None
```

Run on new LLM token. Only available when streaming is enabled.

---

<a href="../../nemoguardrails/streaming.py#L186"><img align="right" style="float:right;" src="https://img.shields.io/badge/-source-cccccc?style=flat-square" /></a>

### <kbd>method</kbd> `StreamingHandler.push_chunk`

```python
push_chunk(
    chunk: Optional[str, langchain.schema.output.GenerationChunk, langchain.schema.messages.AIMessageChunk]
)
```

Push a new chunk to the stream.

---

<a href="../../nemoguardrails/streaming.py#L79"><img align="right" style="float:right;" src="https://img.shields.io/badge/-source-cccccc?style=flat-square" /></a>

### <kbd>method</kbd> `StreamingHandler.set_pattern`

```python
set_pattern(prefix: Optional[str] = None, suffix: Optional[str] = None)
```

Sets the patter that is expected.

If a prefix or a suffix are specified, they will be removed from the output.

---

<a href="../../nemoguardrails/streaming.py#L87"><img align="right" style="float:right;" src="https://img.shields.io/badge/-source-cccccc?style=flat-square" /></a>

### <kbd>method</kbd> `StreamingHandler.set_pipe_to`

```python
set_pipe_to(another_handler)
```





---

<a href="../../nemoguardrails/streaming.py#L90"><img align="right" style="float:right;" src="https://img.shields.io/badge/-source-cccccc?style=flat-square" /></a>

### <kbd>method</kbd> `StreamingHandler.wait`

```python
wait()
```

Waits until the stream finishes and returns the full completion.

---

<a href="../../nemoguardrails/streaming.py#L95"><img align="right" style="float:right;" src="https://img.shields.io/badge/-source-cccccc?style=flat-square" /></a>

### <kbd>method</kbd> `StreamingHandler.wait_top_k_nonempty_lines`

```python
wait_top_k_nonempty_lines(k: int)
```

Waits for top k non-empty lines from the LLM.

When k lines have been received (and k+1 has been started) it will return and remove them from the buffer
