# Threads

This is a sample server config folder with server-side threads enabled.

To enable server-side threads, you must register a `DataStore` inside the `config.py` file, which should be placed at the root of the folder containing the rails configurations.

```python
from nemoguardrails.server.api import register_datastore
from nemoguardrails.server.datastore.memory_store import MemoryStore

register_datastore(MemoryStore())
```

## Rails Configurations

For demo purposes, this configuration uses a single dialog rail, which makes the bot respond slightly differently when the user greets the bot the second time in a row.

```colang
define user express greeting
  "hi"

define bot express greeting
  "Hello!"

define bot express greeting again
  "Hello again!"

define flow
  user express greeting
  bot express greeting
  user express greeting
  bot express greeting again
```

## Running the server

To run the server, use the following command from the root of the project:

```bash
nemoguardrails server --config=examples/configs/threads
```

## Testing

When sending "hi" to the server without a thread ID, it always responds with "Hello!"

```bash
curl -X POST -H "Content-Type: application/json" -d '{"config_id": "config_1", "messages": [{"content": "hi", "role": "user"}]}' http://localhost:8000/v1/chat/completions
```

```
{"messages":[{"role":"assistant","content":"Hello!"}]}
```

```bash
curl -X POST -H "Content-Type: application/json" -d '{"config_id": "config_1", "messages": [{"content": "hi", "role": "user"}]}' http://localhost:8000/v1/chat/completions
```

```
{"messages":[{"role":"assistant","content":"Hello!"}]}
```

If you use a `thread_id`, then the conversation gets stored on the server side, and the second time we get the response "Hello again!".

```bash
curl -X POST -H "Content-Type: application/json" -d '{"config_id": "config_1", "thread_id": "1231231231231231", "messages": [{"content": "hi", "role": "user"}]}' http://localhost:8000/v1/chat/completions
```

```
{"messages":[{"role":"assistant","content":"Hello!"}]}
```

```bash
curl -X POST -H "Content-Type: application/json" -d '{"config_id": "config_1", "thread_id": "1231231231231231", "messages": [{"content": "hi", "role": "user"}]}' http://localhost:8000/v1/chat/completions
```

```
{"messages":[{"role":"assistant","content":"Hello again!"}]}
```
