# Hello World

This examples shows how to create a main flow that instructs the bot to respond with "Hello World!" whenever the user says "hi" or "hello.

NOTE: in this example, the exact strings "hi"/"hello" must be used. Anything else will be ignored. The `hello_world_3` example will add more flexibility.

## Example Session

```
$ nemoguardrails chat --config=examples/v2_x/tutorial/hello_world_2
Starting the chat (Press Ctrl + C twice to quit) ...

> hi

Hello World!

> hello

Hello World!

> something else is ignored

>
```
