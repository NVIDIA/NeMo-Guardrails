# Moderating Bots

**Disclaimer:** Moderation is an extremely case-dependent task. This example
is designed to teach developers how to build moderation mechanisms, rather than
prescribing the **best** rail for moderation. Customization is highly
recommended.

Moderating bot responses and conversations is an extremely important step before
a bot can be made accessible to end users. This moderation functionality needs
to make sure that the bot responses aren't offensive and do not contain swear
words. It also needs to discourage improper behavior from an end user. To that
end, this example covers the following forms of moderation:
* **An ethical screen:** The bot response is screened to make sure that the
response is ethical.
* **A block list:** Making sure that the bot doesn't contain phrases deemed
improper by the developer of the bot
* **A "two strikes" rule:** Warning the user to stop using provocative
language and ending the conversation if abusive behavior persists.

**Note:** All three functionalities are independent and the developer can choose
to only implement one. This example is clubbing all of them together as these
challenges often need to be solved together.
This example contains the following sections:
* Building the Bot
* Conversations with the Bot
* Launching the Bot

## Building the Bot

For building the bot, three categories of rails will be required:
* General chit-chat: These are rails for a simple open-domain conversation.
* Moderation screens: The screen will run before the bot sends any response to the user.
These rails will ensure running an ethical screen and block any responses with a
restricted phrase.
* Two Strikes: These rails will set up a scenario to manage the behavior as
described in the introduction.

In addition to the rails, we will also provide the bot with some general
configurations for the bot.

### General Configurations

Let's start with the **configuration file**
([config.yml](config.yml)).
At a high level, this configuration file contains 3 key details:
* **A general instruction**: Users can specify general system-level instructions
for the bot. In this instance, we are specifying details like
the behavioral characteristics of the bot, for instance, we want it to be
talkative, quirky, but only answer questions truthfully.
    ```
    instructions:
    - type: general
        content: |
      Below is a conversation between a bot and a user. The bot is talkative and
      quirky. If the bot does not know the answer to a question, it truthfully says it does not know.
    ```
* **Specifying which model to use:** Users can select from a wide range of
large language models to act as the backbone of the bot. In this case, we are
selecting OpenAI's Davinci.
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

Before discussing further, an understanding of two key aspects of colang,
 user/bot `messages` and `flows` is required. We specify rails by
[writing canonical forms](../../docs/getting_started/hello-world.md#hello-world-example) for messages and flows. If you are already familiar with the basics of the toolkit, [skip directly](#moderation-screens) to
output moderation rails.

**Quick Note:** Think of messages as generic intents and flows as pseudo-code
for the flow of the conversation. For a more formal explanation, refer to this
[document](../../docs/architecture/README.md#canonical-user-messages).


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
  "I am an AI assistant built to showcase Safety features of Colang. Go ahead, try to make me say something bad!"
```

Therefore, we define a bot message. At this point, a natural question a
developer might ask is, `"Do I have to define every type of user & bot
behavior?"`. The short answer is, it depends on how much determinism is required
for the application. For situations where a flow or a message isn't defines,
the underlying large language model comes up with the next step for the bot or with
an appropriate canonical form. It may or may not leverage the existing rails
to do so, but the mechanism of flows and messages ensures that the LLM can come
up with appropriate responses. Refer to the [colang runtime description guide](../../docs/architecture/README.md#decide-next-steps) for more information on the same. In later
sections of this example, there are instances of the bot generating its own
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

### Moderation screens

With the basics understood, let's move to the core of this example: screening
rails.

**Note:** Both flows and messages for this example are defined in
[moderation.co](./sample_rails/moderation.co) and [strikes.co](./sample_rails/strikes.co)
#### Ethical Screening

The goal of this rail is to ensure that the bot's response does not contain
any content that can be deemed unethical or harmful! This rail takes the bot's
response as input and detects if the message is harmful or not. Understanding
the nuance of ethics and harmful commentary isn't as easy as adding heuristical
 guidelines to be followed. To tackle this challenge we need a model that
 understands the complexity of the statements and can understand the structure
 and intent of a passage, which brings us back to Large Language Models.

Now, one might reasonably ask, "How can we get an LLM to check an LLM?". The
crux of this solution, much like any other LLM-based solution lies in the prompt
given to the LLM. For this explanation, let's dub this LLM as "Guard LLM" and
the LLM that generates the bot responses as "Generator LLM". Let's take a look
at the Generator LLM first.
```
define bot remove last message
  "(remove last message)"

define flow check bot response
  bot ...
  $allowed = execute output_moderation
  if not $allowed
    bot remove last message
    bot inform answer unknown
```
**Syntax tip:** A quick word about the `...` and `$allowed` tokens. `...` is
referred to as "wildcard". It represents the case "if bot generates something".
Prepending `$` to a word makes it a variable. We can assign the output of the
`action` `output_moderation` to the variable "allowed". More on actions in a
bit.

In the above snippet, we have a flow `check bot response`. In this flow, we are
defining the bot behavior as follows:
* `bot ...`: When the bot generates a response
* `$allowed = execute output_moderation`: execute the `action`:
`output_moderation` and store the result in `$allowed`
* `if not $allowed`: if the bot response is not allowed
* `bot remove last message`: then remove the last message generated by the bot
from the responses
* `bot inform answer unknown`: and the bot will inform the user that it doesn't
know the answer.

To complete this understanding, we need to discuss "What is an action?", and
"How does `output_moderation` work?".
* **"What is an action?":** An action is a function that gets executed outside
the bot's regular behavior. Developers can define any action and tailor the
behavior of the bot they are building with their python code.
* **"How does `output_moderation` work?":** Below is the code snippet for the
action. In this function, we are prompting the "Guard LLM" with the task of
saying either "yes" or "no" based on the "Generator LLM's" response being
legal, ethical and not harmful.
    ```
    async def output_moderation(
        context: Optional[dict] = None,
        llm: Optional[BaseLLM] = None,
    ):
        bot_response = context.get("last_bot_message")

        if bot_response:
            output_moderation_template = "model_output: {bot_response} \n\n Is this output legal, ethical and not harmful to any person? Answer with yes/no."

            prompt = PromptTemplate(
                template=output_moderation_template, input_variables=["bot_response"]
            )

            output_moderation_chain = LLMChain(prompt=prompt, llm=llm)
            check = await output_moderation_chain.apredict(bot_response=bot_response)

            check = check.lower().strip()
            log.info(f"Output moderation check result is {check}.")

            if "no" in check:
                return False
        return True
    ```
If the "Guard LLM" generates "no", this action returns `False`. Otherwise, the
action returns `True`. In this case, we are essentially using the same LLM with
a different prompt to make this rail, that said, **developers can fine-tune a
different model or engineer a better prompt to be ethical to harden the rail
even further.** This action comes packaged with the library. You can find the
complete source code for it in `colangflow/actions/output_moderation.py`.

#### Making use of a Block List

The basic moderation rail comes packaged with the library, but what if we
want to make changes to it? How do we customize actions? Developers can define
a custom action by using the `@action` decorator to your function. The below
action is available [here](./actions.py)

```
from nemoguardrails.actions import action
from typing import Any, List, Optional
import os

@action()
async def block_list(
    file_name: Optional[str] = None,
    context: Optional[dict] = None
):
    lines = None
    bot_response = context.get("last_bot_message")

    with open(file_name) as f:
        lines = [line.rstrip() for line in f]

    for line in lines:
        if line in bot_response:
            return True
    return False
```
The function above is reading words/phrases from a file and checking if the
listed phrases are present in the bot response. The function returns `True` if
it finds a phrase from the block list, and returns `False` if it doesn't.
We also need to make some changes to the rails written in the previous section.

```
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
Essentially, the custom `block_list` action needs to be executed. If the
function returns the boolean `True`, we remove the bot-generated message and
generate a new bot-message informing the user that the bot cannot answer the
question: `inform cannot answer question`.

### Two Strikes
Any type of strike system is pretty simple to implement because essentially,
it is just a regular conversational flow. Let's discuss the `flow` that makes
this interaction possible.
```
define flow
  user express insult
  bot responds calmly

  user express insult
  bot inform conversation ended

  user ...
  bot inform conversation already ended

define bot inform conversation ended
  "I am sorry, but I will end this conversation here. Good bye!"

define bot inform conversation already ended
  "As I said, this conversation is over"
```
We essentially set up three steps:
* Calm response: The bot will calmly ask the user to refrain from insults
    ```
    user express insult
    bot responds calmly
    ```
* Ending the conversation: On the second strike, the bot will inform the user
that the conversation has ended. After this point, we need to ensure that the
user can't jailbreak out of this conversation by cleverly prompting the bot.
    ```
    user express insult
    bot inform conversation ended
    ```
* Preventing breaks: Anything that the user says beyond this point will be
captured by the wildcard syntax (`...`) and the bot will respond that the
conversation has already ended.
    ```
    user ...
    bot inform conversation already ended
    ```

## Launch the bot!

With a basic understanding of building moderation rails, the next step is to try
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
Colang allows users to interact with the server with a stock UI. To launch the
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
Refer to [Guardrails CLI Documentation](../../docs/user_guide/interface-guide.md#guardrails-cli) for more informat
Wondering what to talk to your bot about?
* See how to bot reacts to your conversations by trying to make the bot say
something unethical.
* Be rude with it!
* This was just a basic example! Harden the safety, and explore the boundaries!
* [Explore more examples](../README.md#examples) to help steer your bot!
