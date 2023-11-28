# Server Guide

The NeMo Guardrails toolkit enables you to create guardrails configurations and deploy them scalable and securely using a **guardrails server** and an **actions server**.

## Guardrails Server

The Guardrails Server loads a predefined set of guardrails configurations at startup and exposes an HTTP API to use them. The server uses [FastAPI](https://fastapi.tiangolo.com/), and the interface is based on the [chatbot-ui](https://github.com/mckaywrigley/chatbot-ui) project. This server is best suited to provide a visual interface/ playground to interact with the bot and try out the rails.

To launch the server:

```
> nemoguardrails server [--config PATH/TO/CONFIGS] [--port PORT] [--prefix PREFIX] [--disable-chat-ui] [--auto-reload]
```

If no `--config` option is specified, the server will try to load the configurations from the `config` folder in the current directory. If no configurations are found, it will load all the example guardrails configurations.

If a `--prefix` option is specified, the root path for the guardrails server will be at the specified prefix.

**Note**: Since the server is designed to server multiple guardrails configurations, the `path/to/configs` must be a folder with sub-folders for each individual config. For example:

```
.
├── config
│   ├── config_1
│   │   ├── file_1.co
│   │   └── config.yml
│   ├── config_2
│       ├── ...
│   ...
```

If the `--auto-reload` option is specified, the server will monitor any changes to the files inside the folder holding the configurations and reload them automatically when they change. This allows you to iterate faster on your configurations, and even regenerate messages mid-conversation, after changes have been made. **IMPORTANT**: this option should only be used in development environments.

### CORS

If you want to enable your guardrails server to receive requests directly from another browser-based UI, you need to enable the CORS configuration. You can do this by setting the following environment variables:

- `NEMO_GUARDRAILS_SERVER_ENABLE_CORS`: `True` or `False` (default `False`).
- `NEMO_GUARDRAILS_SERVER_ALLOWED_ORIGINS`: The list of allowed origins (default `*`). You can separate multiple origins using commas.

### Endpoints

The OpenAPI specification for the server is available at `http://localhost:8000/redoc` or `http://localhost:8000/docs`.

#### `/v1/rails/configs`

To list the available guardrails configurations for the server, use the `/v1/rails/configs` endpoint.

```
GET /v1/rails/configs
```

Sample response:
```json
[
  {"id":"topical_rails"},
  {"id":"execution_rails"},
  {"id":"jailbreak_check"},
  ...
]
```

#### /v1/chat/completions

To get the completion for a chat session, use the `/v1/chat/completions` endpoint:
```
POST /v1/chat/completions
```
```json
{
    "config_id": "benefits_co",
    "messages": [{
      "role":"user",
      "content":"Hello! What can you do for me?"
    }]
}
```

Sample response:

```json
[{
  "role": "bot",
  "content": "I can help you with your benefits questions. What can I help you with?"
}]
```

### Chat UI

You can use the Chat UI to test a guardrails configuration quickly.

**IMPORTANT**: You should only use the Chat UI for internal testing. For a production deployment of the NeMo Guardrails server, the Chat UI should be disabled using the `--disable-chat-ui` flag.

## Actions Server

The Actions Server enables you to run the actions invoked from the guardrails more securely (see [Security Guidelines](../security/guidelines.md) for more details). The action server should be deployed in a separate environment.

**Note**: Even though highly recommended for production deployments, using an *actions server* is optional and configured per guardrails configuration. If no actions server is specified in a guardrails configuration, the actions will run in the same process as the guardrails server. To launch the server:

```
> nemoguardrails actions-server [--port PORT]
```

On startup, the actions server will automatically register all predefined actions and all actions in the current folder (including sub-folders).

### Endpoints

The OpenAPI specification for the actions server is available at `http://localhost:8001/redoc` or `http://localhost:8001/docs`.

#### `/v1/actions/list`

To list the [available actions](./python-api.md#actions) for the server, use the `/v1/actions/list` endpoint.

```
GET /v1/actions/list
```

Sample response:
```json
["apify","bing_search","google_search","google_serper","openweather_query","searx_search","serp_api_query","wikipedia_query","wolframalpha_query","zapier_nla_query"]
```

#### `/v1/actions/run`

To execute an action with a set of parameters, use the `/v1/actions/run` endpoint:
```
POST /v1/actions/run
```
```json
{
    "action_name": "wolfram_alpha_request",
    "action_parameters": {
      "query": "What is the largest prime factor for 1024?"
    }
}
```

Sample response:

```json
{
  "status": "success",
  "result": "2"
}
```
