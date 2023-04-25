# Interface guide
There are three interfaces with which developers can interact with NeMo Guardrails:
* [CLI](#guardrails-cli): The CLI interface is best for development and
debugging as it provides access to detailed logs.
* [Guardrails Server](#guardrails-server): The Server is best suited to share
a playground to try the rails. Developers can also use it as a fulfillment
backend.
* [Python API](#python-api): Python API is best suited to add Guardrails to an
application in a server-less manner.
## Guardrails CLI
For testing purposes, the Guardrails toolkit provides a command line chat that can be used to interact with the LLM.
```
> nemoguardrails chat --config examples/ [--verbose]
```
#### Options
- `--config`: The configuration that should be used. Can be a folder or a .co/.yml file.
- `--verbose`: In verbose mode, debugging information is also shown. This includes the entire prompt that is sent to the bot, the flow that is executed, the generated canonical form and the response that is received.

__Warning:__ Colang files can be written to perform complex activities, such as calling python scripts and performing multiple calls to the underlying language model. You should avoid loading Colang files from untrusted sources without careful inspection.

## Guardrails Server

The Guardrails toolkit also supports using a server with a chat UI to interact with the bot. The server is developed using [FastAPI](https://fastapi.tiangolo.com/) and the interface is based on the [chatbot-ui](https://github.com/mckaywrigley/chatbot-ui) project.

### Running the server

```
> nemoguardrails server --port [port]

INFO:     Started server process
INFO:     Waiting for application startup.
INFO:     Application startup complete.
INFO:     Uvicorn running on http://0.0.0.0:8000 (Press CTRL+C to quit)
```

#### Options

- ```--port```: The port on which the server should be run. By default, this is set to ```8000```.

### Endpoints

By default, the server exposes multiple endpoints based on the rail configurations in the examples folder. The chat UI can be accessed at ```http://localhost:8000```.

The server exposes the following endpoints:

- List of rail configurations:

```
GET /v1/rails/configs
```

Sample response based on the default examples

```
[
  {"id":"execution_rails"},
  {"id":"grounding_rail"},
  {"id":"jailbreak_check"},
  {"id":"moderation_rail"}
  {"id":"topical_rail"}
]

```

- The bot response for a given rail configuration and user input:

```
POST /v1/chat/completions
```
```config_id``` is used to specify the rails configuration. ```role``` can be ```user``` or ```bot```. ```content``` is the message that was sent by the user or the bot.

Sample request

```
{
    "config_id": "topical_rails",
    "messages": [{
      "role":"user",
      "content":"Hello! What can you do for me?"
    }]
}
```

Sample response

```
[{
  "role": "bot",
  "content":   "I am an AI assistant which helps answer questions based on a given knowledge base. For this
  interaction, I can answer question based on the job report published by US Bureau of Labor Statistics."

}]
```

The OpenAPI specification for the server is available at ```http://localhost:8000/redoc``` or ```http://localhost:8000/docs```.

## Python API

The NeMo Guardrails toolkit also supports using a Python API to interact with the bot. We first need to create a ```LLMRails``` object, initialize it with the desired rails configuration and then use it to interact with the bot.

```
from nemoguardrails.rails import LLMRails, RailsConfig

# In practice, a folder will be used with the config split across multiple files.
config = RailsConfig.from_path("path/to/config")
rails = LLMRails(config)

# For chat
new_message = rails.generate(messages=[{
    "role": "user",
    "content": "Hello! What can you do for me?"
}])
```

The ```new_message``` variable will contain the response from the bot.

```
{"role": "assistant", "content": "I am an AI assistant to help you get started with NeMo Guardrails" }
```

### Methods

- ```LLMRails(config, llm, verbose)``` - Initializes the LLMRails object.
  - ```config: RailsConfig```: The rails configuration that should be used.
  - ```llm: BaseLLM = None```: The LLM that should be used. If not provided, the default LLM will be used.
  - ```verbose: bool = False```: In verbose mode, debugging information is also shown. This includes the entire prompt that is sent to the bot, the flow that is executed, the generated canonical form and the response that is received. By default, this is set to ```False```.

- ```generate(messages)``` - Generates a response from the bot.
  - ```messages: List[dict] = None```: The messages that have been exchanged between the user and the bot so far. This is a list of dictionaries with the following keys:
    - ```role```: The role of the message. Can be ```user``` or ```bot```.
    - ```content```: The content of the message.

- ```register_action(action, name)``` - Registers a custom action for use with the bot.
  - ```action: callable```: The action that should be registered.
  - ```name: str```: The name of the action. This is the name that will be used in the configuration to invoke the action and obtain the result.
