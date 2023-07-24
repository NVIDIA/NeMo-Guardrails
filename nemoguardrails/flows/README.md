# Flows

The core abstraction in the NeMo Guardrails toolkit is a **flow**.

## Events

The following is the list of standard events:

- `UtteranceUserActionFinished(final_transcript)`: a new utterance from the user has been received.
- `UserIntent(intent)`: a canonical form for the user utterance has been identified.
- `bot_intent(intent)`: a new bot intent has been decided i.e. what it should say.
- `bot_said(content)`: the utterance for a bot message has been decided.
- `start_action(action_name, is_system_action, action_parameters)`: it has been decided that an action should be started.
- `action_finished(action_name, action_parameters, action_result)`: an action has finished.
- `create_events(events)`: new events need to be created.
- `listen`: there's nothing let to do and the bot should listen for new user input/events.
- `context_update`: the context data has been updated.


## Context Variables

The following is the list of standard context variables:

- `last_user_message`: the last utterance from the user.
- `last_bot_message`: the last utterance from the bot.
- `relevant_chunks`: the relevant chunks of text related to what the user said.
