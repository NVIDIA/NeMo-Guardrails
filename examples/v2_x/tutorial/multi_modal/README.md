# Multi-modal Example

Example that shows a simple multimodal 'hello world'.

To trigger the bot response type in `hi`, `hello` or simulate a user greeting gesture by typing `/GestureUserActionFinished(gesture="Greeting gesture")`.

```
$ nemoguardrails chat --config=examples/v2_x/tutorial/hello_world_3
Starting the chat (Press Ctrl + C twice to quit) ...

> hi

Welcome!

Gesture: Smile and wave with one hand.

> /GestureUserActionFinished(gesture="Greeting gesture")

Hi there!

Gesture: Smile and wave with one hand.

```
