# Types of Rails

Guardrails (or rails for short) are implemented through **flows**. Depending on their role, rails can be split into:

1. Input rails: triggered when a new input from the user is received.
2. Output rails: triggered when a new output should be sent to the user.
3. Topical rails: triggered after a user message is interpreted, i.e., a canonical form has been identified.
4. Retrieval rails: triggered after the retrieval step has been performed, i.e., the `retrieve_relevant_chunks` action has finished.

## Input Rails

Input rails process the message from the user. For example:

```colang
define flow some input rail
  $allowed = execute check_jailbreak

  if not $allowed
    bot inform cannot answer
    stop
```

Input rails can alter the input by changing the `$user_message` context variable.

## Output Rails

Output rails process a bot message. The message to be processed is available in the context variable `$bot_message`. Output rails can alter the `$bot_message` variable, e.g., to mask sensitive information.

## Retrieval Rails

Retrieval rails process the retrieved chunks, i.e., the `$relevant_chunks` variable.
