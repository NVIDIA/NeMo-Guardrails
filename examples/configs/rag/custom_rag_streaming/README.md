# Custom RAG with streaming

It is possible to use streaming in custom actions, such as RAG.

This is because the streaming handler is defined and available as a context variable.

```python
import contextvars
streaming_handler_var = contextvars.ContextVar("streaming_handler", default=None)
streaming_handler: StreamingHandler = streaming_handler_var.get()
```

But let's first clarify the folder structure of this example:

- `kb/` - A folder containing our knowledge base to retrieve context from. This folder includes the March 2023 US Jobs
  report in `kb/report.md`.
- `rails/output.co` - A colang file that contains a flow that routes all user messages into our
  custom RAG.
- `config.py` - The config file containing the custom RAG action, the disclaimer action, and the init function that gets
  called as part of the initialization of the LLMRails instance.
- `config.yml` - The config file holding all the configuration options.

The following code samples demonstrate the core of this example in action:

```colang
# output.co

define flow answer report question
  user ...
  $answer = execute rag
  bot $answer
  $disclaimer = execute disclaimer
  bot $disclaimer
```

```python
# config.py

class ContinuousStreamingHandler(StreamingHandler):
    async def _process(self, chunk: str):
        """Processes a chunk of text.

        Stops the stream if the chunk is `""` or `None` (stopping chunks).
        In case you want to keep the stream open, all non-stopping chunks can be piped to a specified handler.
        """
        if chunk is None or chunk == "":
            await self.queue.put(chunk)
            self.streaming_finished_event.set()
            self.top_k_nonempty_lines_event.set()
            return

        await super()._process(chunk)


async def rag(context: dict, llm: BaseLLM, kb: KnowledgeBase) -> ActionResult:

    # ...

    chain = prompt_template | llm | output_parser

    # 💡 Enable streaming
    streaming_handler: StreamingHandler = streaming_handler_var.get()
    local_streaming_handler = ContinuousStreamingHandler()
    local_streaming_handler.set_pipe_to(streaming_handler)

    config = RunnableConfig(callbacks=[local_streaming_handler])
    answer = await chain.ainvoke(input_variables, config)

    return ActionResult(return_value=answer, context_updates=context_updates)
```

Here's what's happening, step by step:

1. We define a custom RAG chain using LangChain's LCEL, but it could be any library. For example, you could call the
   `openai` library directly.
2. We then define a `RunnableConfig` with a local streaming handler as a callback. The local handler is configured to
   pipe the stream to the main streaming handler. The idea behind this is to handle stream-stopping chunks (`""` or
   `None`) only locally, while keeping the main streaming handler running. This enables streaming results from multiple
   actions.
3. We then invoke the chain with the config, which will trigger the streaming handler to be called.
4. Finally, we return the final answer as `ActionResult` which enables downstream processing. In this example, we define
   a `disclaimer` action that just prints a sentence; it could also access the final answer or other context
   variables we define as `context_updates`.

_Note: For simplicity, we re-use the LLM instance configured in [config.yml](./config.yml) as well as the
built-in retrieval via the knowledge base._

## Run the example

```shell
$ export OPENAI_API_KEY='sk-xxx'
$ python -m nemoguardrails.__main__ chat --config /<path_to>/examples/configs/rag/custom_rag_streaming --streaming
```
