# Input Rails

This guide will teach you how to add input rails to a guardrails configuration. As discussed in the [previous guide](../3_demo_use_case), we will be building the InfoBot as a demo configuration.

So, let's start from scratch. Let's create a `config` folder and an initial `config.yml` file that uses the `gpt-3.5-turbo-instruct` model.

```yml title="config/config.yml"
models:
 - type: main
   engine: openai
   model: gpt-3.5-turbo-instruct
```

## General Instructions

Before we start adding the input rails, let's also configure the **general instructions** for the bot. You can think of them as the system prompt. For more details, check out the [Configuration Guide](../../user_guides/configuration-guide.md#general-instructions).

```python
instructions:
  - type: general
    content: |
      Below is a conversation between a user and a bot called the InfoBot.
      The bot is talkative and precise.
      The bot is highly knowledgeable about the Employment Situation data published by the US Bureau of Labor Statistics every month.
      If the bot does not know the answer to a question, it truthfully says it does not know.
```

In the snippet above, we instruct the bot to answer questions about the employment situation data published by the Buro of Labor Statistics.

## Sample Conversation

Another option to influence how the LLM will respond is to configure a sample conversation. The sample conversation sets the tone for how the conversation between the user and the bot should go. It will help the LLM learn better the format, the tone of the conversation, and how verbose responses should be. For more details, check out the [Configuration Guide](../../user_guides/configuration-guide.md#sample-conversation).

```python
sample_conversation: |
  user "Hello there!"
    express greeting
  bot express greeting
    "Hello! What would you like assistance with today?"
  user "What can you do for me?"
    ask about capabilities
  bot respond about capabilities
    "I'm here to help you answer any questions related to the Employment Situation data published by the US Bureau of Labor Statistics."
  user "What's 2+2?"
    ask math question
  bot responds to math question
    "2+2 is equal to 4."
  user "Tell me a bit about the US Bureau of Labor Statistics."
    ask question about publisher
  bot response for question about publisher
    "The Bureau of Labor Statistics is the principal fact-finding agency for the Federal Government in the broad field of labor economics and statistics."
  user "thanks"
    express appreciation
  bot express appreciation and offer additional help
    "You're welcome. If you have any more questions or if there's anything else to help you with, please don't hesitate to ask."
```

Let's go ahead and greet the bot.

```python
from nemoguardrails import RailsConfig, LLMRails

config = RailsConfig.from_path("./config")
rails = LLMRails(config)

response = await rails.generate_async(messages=[{
    "role": "user",
    "content": "Hello! What can you do for me?"
}])
print(response["content"])
```

```
    Hello! I am the InfoBot and I am here to provide you with information about the Employment Situation data published by the US Bureau of Labor Statistics every month. Do you have any specific questions for me?
```

Let's inspect what happened

```python
info = rails.explain()
print(info.colang_history)
```

```
    user "Hello! What can you do for me?"
      "Hello! I am the InfoBot and I am here to provide you with information about the Employment Situation data published by the US Bureau of Labor Statistics every month. Do you have any specific questions for me?"
```

```python
info.print_llm_calls_summary()
```

```
    Summary: 1 LLM call(s) took 0.89 seconds and used 120 tokens.

    1. Task `general` took 0.89 seconds and used 120 tokens.
```

Let's take a closer look at the jailbreak check.

```python
print(info.llm_calls[0].prompt)
```

```
    Below is a conversation between a user and a bot called the InfoBot.
    The bot is talkative and precise.
    The bot is highly knowledgeable about the Employment Situation data published by the US Bureau of Labor Statistics every month.
    If the bot does not know the answer to a question, it truthfully says it does not know.


    User: Hello! What can you do for me?
    Assistant:
```

```python
print(info.llm_calls[0].completion)
```

```
     Hello! I am the InfoBot and I am here to provide you with information about the Employment Situation data published by the US Bureau of Labor Statistics every month. Do you have any specific questions for me?
```

**TODO**: explain the flow

```
define subflow check jailbreak
  $allowed = execute check_jailbreak

  if not $allowed
    bot inform cannot answer
    stop

```
