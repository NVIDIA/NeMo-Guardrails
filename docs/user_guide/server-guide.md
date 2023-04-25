# Server Guide

The NeMo Guardrails toolkit enables you to create guardrails configurations and deploy them in a scalable and secure way using a **guardrails server** and an **actions server**.

## Guardrails Server

The Guardrails Server loads a predefined set of guardrails configurations at startup and exposes an HTTP API to use them. The server is developed using [FastAPI](https://fastapi.tiangolo.com/) and the interface is based on the [chatbot-ui](https://github.com/mckaywrigley/chatbot-ui) project. This server is best suited to provide a visual interface/ playground to interact with the bot and try out the rails.

To launch the server:

```
> nemoguardrails server [--config PATH/TO/CONFIGS] [--port PORT]
```

If no `--config` option is specified, the server will try to load the configurations from the `config` folder in the current directory. If no configurations are found, it will load all the example guardrails configurations.

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

## Actions Server

The Actions Server enables you to run the actions invoked from the guardrails in a more secure way (see [Security Guidelines](../security/guidelines.md) for more details). The action server should be deployed in a separate environment.

**Note**: Even though highly recommended for production deployments, the use of an *actions server* is optional, and it's configured per guardrails configuration. If no actions server is specified in a guardrails configuration, the actions will run in the same process as the guardrails server. To launch the server:

```
> nemoguardrails actions-server [--port PORT]
```

On startup, the actions server will automatically register all predefined actions and all the actions included in the current folder (including sub-folders).

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
