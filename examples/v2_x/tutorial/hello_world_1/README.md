# Hello World

This examples shows how to create a main flow that instructs the bot to respond with "Hello World!" whenever the user says "hi".

NOTE: in this example, the exact string "hi" must be used. Anything else will be ignored. The `hello_world_2` example will add more flexibility.

## Example Session

```
$ nemoguardrails chat --config=examples/v2_x/tutorial/hello_world_1
Starting the chat (Press Ctrl + C twice to quit) ...

> hi

Hello World!

> something else is ignored

>
```
