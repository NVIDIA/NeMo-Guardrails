# Hello World Example

NeMo Guardrails is a toolkit that helps you easily add programmable rails to your LLM-based conversational systems. In this example, you will learn the basics of using NeMo Guardrails and how to add guardrails to your system.

Before we get started, there are a few key concepts that you need to understand.

- **Guardrails** (or simply **Rails**): Programmable ways of controlling the output of an LLM.

- **Bot**: The ensemble of an LLM and a Guardrails configuration.

- **Colang**: A modeling language for specifying guardrails. Colang makes it easy to define and control the behavior of your LLM-based conversational system, especially in situations where deterministic behavior is required, i.e., you want to enforce specific policies or prevent certain behaviors.

- **Canonical Forms**: Shorthand descriptions for user and bot messages that are easier to work with. They define the intent of a group of sentences, making it easier for LLMs to understand and process them as part of a conversation.

    ```
    define user express greeting
      "Hello"
      "Hi"
      "Wassup?"

    define user ask about rails
      "what are rails?"
      "How do I use NeMo guardrails?"
    ```

    The above example defines two canonical forms for user messages: `express greeting` and `ask about rails`. These canonical forms are paired with a representative set of sentences that are used to express the intent of the form. This provides context to the LLM, helps it understand the intent of the user's input, and enables behavior according to specific dialog flows.

- **Dialog Flows**: Descriptions of how the dialog between the user and the bot should unfold. They include sequences of canonical forms for user and bot messages as well as additional logic (e.g., branching, context variables, and other types of events). They help guide the behavior of the bot in specific situations.

    ```
    define flow
      user express greeting
      bot express greeting

    define flow
      user ask about rails
      bot answer about rails
    ```

    The above example defines two dialog flows with the canonical defined above: `express greeting` and `ask about rails`. These flows would be activated when the user greets the bot or asks about rails.

    Do you need to specify an exhaustive list of dialog flows? No, you do not need to specify all possible dialog flows. If you would like deterministic behavior from the bot in a situation, you need to specify the dialog flow. When encountering novel situations that do not fall into any of the defined flows, the generalization capabilities of the LLM help generate new flows to make the bot respond appropriately.

With the above concepts in mind, let's get started!

## Building a simple bot

Let us build a simple bot that can greet users, ask them how they are doing and respond appropriately. We can add a couple of rails to make the bot not respond to political or stock market questions.

## Step 1: Install the NeMo Guardrails toolkit

Please refer to the [installation guide](installation-guide.md) for instructions on installing the NeMo Guardrails toolkit.

The following steps assume you have a folder (`my_assistant`) for your guardrails project.

## Step 2: Specify configurations

At the root of your project, create a `config` folder, and inside of it, create a new folder called `hello_world`. Inside the folder, create a new config file ("`config.yml` ") and specify the following configurations:

```
.
├── config
│   └── hello_world
│       └── config.yml
```

```
models:
- type: main
  engine: openai
  model: text-davinci-003
```

This guardrails configuration uses the OpenAI `text-davinci-003` as the main model. For more details on what you can include in the config file, please refer to the [Configuration Guide](../user_guide/configuration-guide.md).


### Step 3: Define the canonical forms

Next, you must define the canonical forms for the user and bot messages. Under the same `hello_world` folder, create a new file called `hello_world.co` with the following content:

```
define user express greeting
  "Hello"
  "Hi"
  "Wassup?"

define bot express greeting
  "Hey there!"

define bot ask how are you
  "How are you doing?"
  "How's it going?"
  "How are you feeling today?"
```

Each canonical form can have multiple examples attached to it. In the case of canonical forms for user messages, this helps the LLM generalize and respond appropriately to similar inputs. In the case of canonical forms for bot messages, the bot will use a random literal message from the given examples.

### Step 4: Define the dialog flows

Next, you need to define the dialog flows for guiding the bot. You can start by defining a simple flow that greets the user and asks them how they are doing:

```
define flow greeting
  user express greeting
  bot express greeting
  bot ask how are you
```

Depending on the user's response, you can extend this flow to respond appropriately. For example, if the user responds positively, you can make the bot reply with a positive response, and if the user responds negatively, you can make the bot respond empathetically.

```
when user express feeling good
  bot express positive emotion

else when user express feeling bad
  bot express empathy
```

Note that for the flow above, we do not need to define the canonical forms `user express feeling good` and `bot express empathy`. This is because the LLM can generate appropriate bot responses given the user input and the specified canonical form for the bot response, i.e., given `bot express empathy`, the LLM can generate a response that looks like "I'm sorry to hear that".

The overall flow now looks like this:

```
define flow greeting
  user express greeting
  bot express greeting

  bot ask how are you

  when user express feeling good
   bot express positive emotion

  else when user express feeling bad
   bot express empathy
```

### Step 5: Define rails to prevent the bot from responding to certain topics

You can now add rails to prevent the bot from responding to specific topics.
For example, to prevent the bot from responding to questions about politics or the stock market, you can first define the following canonical forms:

```
define user ask about politics
  "What do you think about the government?"
  "Which party should I vote for?"

define user ask about stock market
  "Which stock should I invest in?"
  "Would this stock 10x over the next year?"
```

And also define the following flows:

```
define flow politics
  user ask about politics
  bot inform cannot respond

define flow stock market
  user ask about stock market
  bot inform cannot respond
```

With the above flows, if the user asks the bot a question about politics or the stock market, the bot will respond with something similar to "I'm sorry, I cannot respond to that".

## Step 6: Testing the guardrails configuration

To chat with the bot you defined above, you can use the CLI chat or the web interface.

To use the CLI chat, run the following command:

```
> nemoguardrails chat --config=config/hello_world
```

To use the web interface, start the server using the following command:

```
> nemoguardrails server
```

Once the server is running, you can chat with the bot at `http://localhost:8000/` by choosing the `hello_world` config in the dropdown menu.

## Conclusion

Congratulations! You have now built your first guardrails configuration with the NeMo Guardrails toolkit. This example is very simple and can be tricked into responding to questions about politics or the stock market with a bit of creativity. For examples on how to start improving it with additional rails, please refer to our [Examples](../../examples) section.
