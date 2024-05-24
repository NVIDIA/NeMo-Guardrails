# Interaction Loop

Unknown user inputs will be tried to be matched to an existing user intent or alternatively caught by the `unhandled user intent` case in the main loop. If the user does not answer within 12 seconds, the bot will proactively remind the user that she can ask anything.

## Example Session

```
$ nemoguardrails chat --config=examples/v2_x/tutorial/interaction_loop/
Starting the chat (Press Ctrl + C twice to quit) ...

> hi

Hi there!

<< pause for 12 seconds >>

You can ask me anything!

> how are you?

I am doing well, thank you for asking! How can I assist you today?
```
