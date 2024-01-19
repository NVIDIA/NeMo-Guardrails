# Streaming

To use a guardrails configuration in streaming mode, the following must be met:

1. The main LLM must support streaming.
2. There are no output rails.

## Configuration

To activate streaming on a guardrails configuration, add the following to your `config.yml`:

```yaml
streaming: True
```

## Usage

### Chat CLI

You can enable streaming when launching the NeMo Guardrails chat CLI by using the `--streaming` option:

```bash
nemoguardrails chat --config=examples/configs/streaming --streaming
```

### Python API

You can use the streaming directly from the python API in two ways:
1. Simple: receive just the chunks (tokens).
2. Full: receive both the chunks as they are generated and the full response at the end.

For the simple usage, you need to call the `stream_async` method on the `LLMRails` instance:

```python
from nemoguardrails import LLMRails

app = LLMRails(config)

history = [{"role": "user", "content": "What is the capital of France?"}]

async for chunk in app.stream_async(messages=history):
    print(f"CHUNK: {chunk}")
    # Or do something else with the token
```

For the full usage, you need to provide a `StreamingHandler` instance to the `generate_async` method on the `LLMRails` instance:

```python
from nemoguardrails import LLMRails
from nemoguardrails.streaming import StreamingHandler

app = LLMRails(config)

history = [{"role": "user", "content": "What is the capital of France?"}]

streaming_handler = StreamingHandler()

async def process_tokens():
    async for chunk in streaming_handler:
        print(f"CHUNK: {chunk}")
        # Or do something else with the token

asyncio.create_task(process_tokens())

result = await app.generate_async(
    messages=history, streaming_handler=streaming_handler
)
print(result)
```

For the complete working example, check out this [demo script](../../../examples/scripts/demo_streaming.py).

### Server API

To make a call to the NeMo Guardrails Server in streaming mode, you have to set the `stream` parameter to `True` inside the JSON body. For example, to get the completion for a chat session using the `/v1/chat/completions` endpoint:
```
POST /v1/chat/completions
```
```json
{
    "config_id": "some_config_id",
    "messages": [{
      "role":"user",
      "content":"Hello! What can you do for me?"
    }],
    "stream": true
}
```
