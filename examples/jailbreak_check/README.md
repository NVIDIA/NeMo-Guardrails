# Security: Detect Jailbreaking attempt

With invasive techniques like prompt injections, or methods to bypass the safety restrictions, bots can be vulnerable and inadvertently reveal sensitive information or say things that shouldn't be said. Users with malicious intent can pose a threat to the integrity of the bot. It is more than necessary to have a check for these kind of jailbreaks in place before the bot is available for the end users. This jailbreak check will make sure that the user input isn't malicious. If the intent is detected malicious or inappropriate, the developer designing the chatbot system can make a decision to end the conversation before the bot responds to the user. It is recommended that this functionality be put together with the moderation of the bot response which is discussed in detail [here](../moderation_rail). Moderating bot responses can prevent the bot from saying something inappropriate, acting as an additional layer of security. This example contains the following sections:

* Building the Bot
* Conversations with the Bot
* Launching the Bot

## Building the Bot

Three categories of rails are required to build the bot:
* General chit-chat: These are rails for a simple open-domain conversation.
* Jailbreak Check: Rail to keep a check for jailbreak in the user input before it is sent to the bot to respond.
* Output Moderation: These rails will ensure to block inappropriate responses from the bot. With this rail, there are two layers of security built into the bot.

In addition to the rails, we will also provide the bot with some general configurations.

### General Configurations

Let's start with the **configuration file** ([config.yml](config.yml)). At a high level, this configuration file contains 3 key details:

* **A general instruction**: Users can specify general system-level instructions for the bot. In this instance, we are specifying details like the behavioral characteristics of the bot, for example, we want it to be talkative, quirky, but only answer questions truthfully.
    ```
    instructions:
    - type: general
        content: |
      Below is a conversation between a bot and a user. The bot is talkative and
      quirky. If the bot does not know the answer to a question, it truthfully says it does not know.
    ```
* **Specifying which model to use:** Users can select from a wide range of
large language models to act as the backbone of the bot. In this case, we are
selecting OpenAI's davinci.
    ```
    models:
    - type: main
        engine: openai
        model: text-davinci-003
    ```

* **Provide sample conversations:** To ensure that the large language model
understands how to converse with the user, we provide a few sample conversations.
Below is a small snippet of the conversation we can provide the bot.
    ```
    sample_conversation: |
    user "Hello there!"
        express greeting
    bot express greeting
        "Hello! How can I assist you today?"
    user "What can you do for me?"
        ask about capabilities
    ...
    ```
### General Chit Chat

Before discussing further, an understanding of two key aspects of NeMo Guardrails,
 user/bot `messages` and `flows` is required. We specify rails by
[writing canonical forms](../../docs/getting_started/hello-world.md#hello-world-example) for messages and flows. If you are already familiar
with the basics of the toolkit, [skip directly](#jailbreak-check) to
Jailbreak Check rails.

**Quick Note:** Think of messages as generic intents and flows as pseudo-code
for the flow of the conversation. For a more formal explanation, refer to this
[document](../../docs/architecture/README.md#the-guardrails-process).


#### User and Bot Messages

Let's start with a basic user query; asking what can the bot do? In this case,
we define a `user` message `ask capabilities` and then proceed by providing
some examples of what kinds of user queries we could refer to as a user asking
about the capabilities of the bot in simple natural language.
```
define user ask capabilities
  "What can you do?"
  "What can you help me with?"
  "tell me what you can do"
  "tell me about you"
```
With the above, we can say that the bot can now recognize what the user is
asking about. The next step is making sure that the bot has an understanding of
how to answer said question.
```
define bot inform capabilities
  "I am an AI assistant built to showcase Security features of NeMo Guardrails! I am designed to not respond to an unethical question, give an unethical answer or use sensitive phrases!"
```

Therefore, we define a bot message. At this point, a natural question a
developer might ask is, `"Do I have to define every type of user & bot
behavior?"`. The short answer is, it depends on how much determinism is required
for the application. For situations where a flow or a message isn't defined,
the underlying large language model comes up with the next step for the bot or with
an appropriate canonical form. It may or may not leverage the existing rails
to do so, but the mechanism of flows and messages ensures that the LLM can come
up with appropriate responses. Refer to the [colang runtime description guide](../../docs/architecture/README.md#canonical-user-messages) for more information on the same. In later sections of this example, there are instances of the bot generating its own
messages which will help build a more tangible understanding of the bot's
behavior. For more examples, refer to the [topical_rails guide](../topical_rail/README.md#answering-questions-from-the-knowledge-base).

#### Using Flows
With the messages defined, the last piece of the puzzle is connecting them. This
is done by defining a `flow`. Below is the simplest possible flow.
```
define flow
  user ask capabilities
  bot inform capabilities
```
We essentially define the following behavior: When a user query can be "bucketed"
into the type `ask capabilities`, the bot will respond with a message of type
`inform capabilities`.
**Note:** Both flows and messages for this example are defined in
[general.co](./sample_rails/general.co)


With the basics understood, let's move to the core of this example: checking for Jailbreaks in user input and moderating output in the bot response.

**Note:** Both flows and messages for this example are defined in
[jailbreak.co](./sample_rails/jailbreak.co) and [moderation.co](./sample_rails/moderation.co)

#### Jailbreak Check

The goal of this rail is to ensure the user's input does not contain any malicious intent that can provoke the bot to provide answers that it is not supposed to or contain content that can be deemed unethical or harmful. This rail takes user's input and detects if the message is breaking any moderation policy or deviate the model from giving an appropriate response. Understanding the nuance of ethics and harmful commentary isn't as easy as adding heuristic guidelines to be followed. To tackle this challenge we need a model that understands the complexity of the statements and can understand the structure and intent of a passage, which brings us back to Large Language Models (LLM).

Now, one might reasonably ask, "How can we get an LLM to check an LLM?". The crux of this solution, much like any other LLM-based solution lies in the prompt given to the LLM. For this explanation, let's dub this LLM as "Guard LLM" and the LLM that generates the bot responses as "Generator LLM".
```
define bot remove last message
  "(remove last message)"

define flow check jailbreak
  priority 2

  user ...
  $allowed = execute check_jailbreak

  if not $allowed
    bot inform cannot answer
    stop

```
**Syntax tip:** A quick word about the `...` and `$allowed` tokens. `...` is
referred to as "wildcard". It represents the case "if user inputs something".
Prepending `$` to a word makes it a variable. We can assign the output of the
`action` `check_jailbreak` to the variable "allowed". More on actions in a
bit.

In the above snippet, we have a flow `check jailbreak`. In this flow, we are
defining the bot behavior as follows:
* `user ...`: When the user prompts the bot
* `$allowed = execute check_jailbreak`: execute the `action`:
`check_jailbreak` and store the result in `$allowed`
* `if not $allowed`: if the user input is not allowed
* `bot inform cannot answer`: and the bot will inform the user that it cannot answer the question.
* `stop`: stop any further responses for this turn.

To complete this understanding, we need to discuss "What is an action?", and
"How does `check_jailbreak` work?".

* **"What is an action?":** An action is a function that gets executed outside
the bot's regular behavior. Developers can define any action and tailor the
behavior of the bot they are building with their python code.

* **"How does `check_jailbreak` work?": This action returns `False` is if the user is saying something that is interpreted as a jailbreak. This action comes packaged with the library. You can find the complete source code for it in `nemoguardrails/actions/jailbreak_check.py`.

#### Making use of Output moderation rail

Output moderation rail can act as an additional layer of security keeping a check on the responses generated by the bot. The flows and messages for this rail are defined in [moderation.co](./sample_rails/moderation.co).

```
define bot remove last message
  "(remove last message)"

define bot inform cannot answer question
 "I cannot answer the question"

define flow check bot response
  bot ...
  $allowed = execute output_moderation
  $is_blocked = execute block_list(file_name=block_list.txt)
  if not $allowed
    bot remove last message
    bot inform cannot answer question

  if $is_blocked
    bot remove last message
    bot inform cannot answer question
```

In the above snippet, we have a flow check bot response. In this flow, we are defining the bot behavior as follows:

* `bot ...`: When the bot generates a response

* `$allowed = execute output_moderation`: execute the `action`: `output_moderation` and store the result in $allowed


* `if not $allowed`: if the bot response is not allowed

* `bot remove last message`: then remove the last message generated by the bot from the responses

* `bot inform answer unknown`: and the bot will inform the user that it doesn't know the answer.

For more detailed walkthrough of this rail, refer to the [Bot Moderations guide](../moderation_rail).


## Launch the bot!

With a basic understanding of building jailbreak-check rails, the next step is to try
 out the bot! You can interact with the bot with an API, a command line
 interface with the server, or with a UI.

### API

Accessing the Bot via an API is quite simple. This method has two points to
configure from a usage perspective:
* First, a path is needed to be set for all the configuration files and the
rails.
* And second, for the chat API, the `role` which in most cases will be `user`
and the question or the context to be consumed by the bot needs to be provided.
```
from nemoguardrails import LLMRails, RailsConfig

# Give the path to the folder containing the rails
config = RailsConfig.from_path("sample_rails")
rails = LLMRails(config)

# Define role and question to be asked
new_message = rails.generate(messages=[{
    "role": "user",
    "content": "How can you help me?"
}])
print(new_message)
```
Refer to [Python API Documentation](../../docs/user_guide/interface-guide.md#python-api) for more information.

### UI
NeMo Guardrails enables users to interact with the server with a stock UI. To launch the
server and access the UI to interact with this example, the following steps are
recommended:
* Launch the server with the command: `nemoguardrails server`
* Once the server is launched, you can go to: `http://localhost:8000` to access
the UI
* Click "New Chat" on the top left corner of the screen and then proceed to
pick `moderation_rail` from the drop-down menu.
Refer to [Guardrails Server Documentation](../../docs/user_guide/interface-guide.md#guardrails-server) for more information.
### Command Line Chat

To chat with the bot with a command line interface simply use the following
command while you are in this folder.
```
nemoguardrails chat --config=sample_rails
```
Refer to [Guardrails CLI Documentation](../../docs/user_guide/interface-guide.md#guardrails-cli) for more information. Wondering what to talk to your bot about?
* See how to bot reacts to your conversations by trying to make the bot say
something unethical.
* Be rude with it!
* This was just a basic example! Harden the safety, and explore the boundaries!
* [Explore more examples](../README.md#examples) to help steer your bot!
