# Interaction Loop

Unknown user inputs will be tried to be matched to an existing user intent or alternatively caught by the `unhandled user intent` case in the main loop. If the user does not answer within 12 seconds, the bot will proactively remind the user that she can ask anything.

## Example Session

```
$ nemoguardrails chat --config=examples/v2_x/tutorial/interaction_loop/
Starting the chat (Press Ctrl + C twice to quit) ...

> hi
Posture: Thinking, idle.

Hi there!

You can ask me anything!


> what can you do
Posture: Thinking, idle.
Posture: Thinking, idle.

I can assist you with answering questions, providing information, and following instructions. Is there something specific you would like help with?
```
