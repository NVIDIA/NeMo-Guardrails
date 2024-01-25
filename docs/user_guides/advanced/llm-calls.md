# LLM Calls

This guide explains when the LLM is called based on various options in a guardrails configuration.

## Types of calls


- Main LLM Call:
- Rail LLM Calls:
  - input checking, output checking, moderation, value extraction, user intent, bot message, next step
  - potentially other types of tasks (query expansion for RAG; full query for multi-turn queries)


- passthrough mode vs. rails mode
- potentially no llm calls when using `embeddings_only` with pre-defined flows
  - or when an input rail which does not use the LLM flags the message
-

## Latency

- `embeddings_only`
- `rails.dialog.single_call.enabled` = `True`
- parallelism for input/output rails (to come)

## Different LLMs for different tasks
