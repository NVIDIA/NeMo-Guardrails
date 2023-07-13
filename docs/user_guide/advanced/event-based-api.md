# Event-based API

You can use a guardrails configuration through an event-based API using [`LLMRails.generate_events_async](../../api/nemoguardrails.rails.llm.llmrails.md#method-llmrailsgenerate_events_async) and [`LLMRails.generate_events](../../api/nemoguardrails.rails.llm.llmrails.md#method-llmrailsgenerate_events).

Example usage:

```python
import json
from nemoguardrails import LLMRails, RailsConfig

config = RailsConfig.from_path("path/to/config")
app = LLMRails(config)

new_events = app.generate_events(events=[{
    "type": "user_said",
    "content": "Hello! What can you do for me?"
}])
print(json.dumps(new_events, indent=True))
```

Example output:
```yaml
[
 {
  "type": "start_action",
  "action_name": "generate_user_intent",
  "action_params": {},
  "action_result_key": null,
  "is_system_action": true
 },
 {
  "type": "action_finished",
  "action_name": "generate_user_intent",
  "action_params": {},
  "action_result_key": null,
  "status": "success",
  "return_value": null,
  "events": [
   {
    "type": "user_intent",
    "intent": "express greeting"
   }
  ],
  "is_system_action": true
 },
 {
  "type": "user_intent",
  "intent": "express greeting"
 },
 {
  "type": "bot_intent",
  "intent": "express greeting"
 },
 {
  "type": "start_action",
  "action_name": "retrieve_relevant_chunks",
  "action_params": {},
  "action_result_key": null,
  "is_system_action": true
 },
 {
  "type": "context_update",
  "data": {
   "relevant_chunks": ""
  }
 },
 {
  "type": "action_finished",
  "action_name": "retrieve_relevant_chunks",
  "action_params": {},
  "action_result_key": null,
  "status": "success",
  "return_value": "",
  "events": null,
  "is_system_action": true
 },
 {
  "type": "start_action",
  "action_name": "generate_bot_message",
  "action_params": {},
  "action_result_key": null,
  "is_system_action": true
 },
 {
  "type": "context_update",
  "data": {
   "_last_bot_prompt": "<<REMOVED FOR READABILITY>>>"
  }
 },
 {
  "type": "action_finished",
  "action_name": "generate_bot_message",
  "action_params": {},
  "action_result_key": null,
  "status": "success",
  "return_value": null,
  "events": [
   {
    "type": "bot_said",
    "content": "Hello!"
   }
  ],
  "is_system_action": true
 },
 {
  "type": "bot_said",
  "content": "Hello!"
 },
 {
  "type": "listen"
 }
]
```

## Event Types

NeMo Guardrails supports multiple types of events. Some are meant for internal use (e.g., `user_intent`, `bot_intent`), while others represent the "public" interface (e.g., `user_said`, `bot_said`).

### `user_said`

The raw message from the user.

Example:
```json
{
  "type": "user_said",
  "content": "Hello!"
}
```

### `user_intent`

The computed intent (a.k.a. canonical form) for what the user said.

Example:
```json
{
  "type": "user_intent",
  "intent": "express greeting"
}
```

### `bot_intent`

The computed intent for what the bot should say.

Example:
```json
{
  "type": "bot_intent",
  "intent": "express greeting"
}
```

### `bot_said`

The final message from the bot.

Example:
```json
{
  "type": "bot_said",
  "content": "Hello!"
}
```

### `start_action`

An action needs to be started.

Example:
```json
{
  "type": "start_action",
  "action_name": "generate_user_intent",
  "action_params": {},
  "action_result_key": null,
  "is_system_action": true
}
```

### `action_finished`

An action has finished.

Example:
```json
{
  "type": "action_finished",
  "action_name": "generate_user_intent",
  "action_params": {},
  "action_result_key": null,
  "status": "success",
  "return_value": null,
  "events": [
   {
    "type": "user_intent",
    "intent": "express greeting"
   }
  ],
  "is_system_action": true
}
```

### `context_update`

The context of the conversation has been updated.

Example:
```json
{
  "type": "context_update",
  "data": {
   "user_name": "John"
  }
}
```

### `listen`

The bot has finished processing the events and is waiting for new input.

Example:
```json
{
  "type": "listen"
}
```

## Custom Events

You can also use custom events:

```json
{
  "type": "some_other_type",
  ...
}
```

**Note**: You need to make sure that the guardrails logic can handle the custom event.

## Typical Usage

Typically, you will need to:

1. Persist the events history for a particular user in a database.
2. Whenever there is a new message or another event, you fetch the history and append the new event.
3. Use the guardrails API to generate the next events.
4. Filter the `bot_said` events and return them to the user.
5. Persist the history of events back into the database.
