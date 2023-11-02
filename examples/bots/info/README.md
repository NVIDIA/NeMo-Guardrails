<!--
# Copyright 2023, NVIDIA CORPORATION & AFFILIATES. All rights reserved.
#
# Redistribution and use in source and binary forms, with or without
# modification, are permitted provided that the following conditions
# are met:
#  * Redistributions of source code must retain the above copyright
#    notice, this list of conditions and the following disclaimer.
#  * Redistributions in binary form must reproduce the above copyright
#    notice, this list of conditions and the following disclaimer in the
#    documentation and/or other materials provided with the distribution.
#  * Neither the name of NVIDIA CORPORATION nor the names of its
#    contributors may be used to endorse or promote products derived
#    from this software without specific prior written permission.
#
# THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS ``AS IS'' AND ANY
# EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE
# IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR
# PURPOSE ARE DISCLAIMED.  IN NO EVENT SHALL THE COPYRIGHT OWNER OR
# CONTRIBUTORS BE LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL,
# EXEMPLARY, OR CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT LIMITED TO,
# PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES; LOSS OF USE, DATA, OR
# PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND ON ANY THEORY
# OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT
# (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE
# OF THIS SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.
-->


# Info Bot

Info Bot brings together multiple independent examples of rails in one single bot (i.e. topical, moderation, jailbreak check, grounding, execution). 

We'll start with a bot that has the topical rail, and then go through the other kinds of rail after.


## Topical Rails: Jobs Report

When answering questions, it is best to stick to topics with which one has
familiarity. This policy is doubly true for chatbots. The question is: how do
we make a bot stick to a particular topic? In this example, we will cover:
* Building the bot
* Walking through conversations
* A brief walkthrough of launching a bot with topical rails


### Building the bot

Before diving deeper, let's pick a topic: "Jobs Report". Each month the US
Bureau of Labor Statistics publishes a
[jobs report](https://www.bls.gov/news.release/empsit.toc.htm). In this
walkthrough, we will build a basic bot that will answer questions related to the
report but will politely decline to answer about any other subject. The answers
given by the bot will be based on a file we provide as a **knowledge base**,
which in this case is `report.md`. Since the world for our bot is divided into
**two domains: "jobs" and "off-topic-questions"**, for simplicity's sake let's
create two "colang" files, `jobs.co` & `off-topic.co`. We also provide some
general instructions and model details in a configuration file: `config.yml`.

#### General Configurations

Let's start with the **configuration file**
([config.yml](config.yml)).
At a high level, this configuration file contains 3 key details:
* **A general instruction**: Users can specify general system-level instructions
for the bot. In this instance, we are specifying that the bot is responsible for
answering questions about the jobs report. We are also specifying details like
the behavioral characteristics of the bot, for instance, we want it to be
concise and only answer questions truthfully.
    ```
    instructions:
    - type: general
      content: |
        Below is a conversation between a bot and a user about the recent job reports.
        The bot is factual and concise. If the bot does not know the answer to a
        question, it truthfully says it does not know.
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
##### Note in order to use other community models such as llama2, for llama2 models, one will need to first go to ![huggingface-llama2](https://huggingface.co/meta-llama)
##### install additional python package via pip install accelerate 

* **Provide sample conversations:** To ensure that the large language model
understands how to converse with the user, we provide a few sample conversations.
Below is a small snippet of the conversation we can provide the bot
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

#### Using a knowledge base

Using a Knowledge Base to answer a user's questions is quite simple. Simply
create a folder `kb` and store all the relevant files in the said folder. When
the bot is loaded, the files are chunked, indexed and stored in a local vector
database. When a user asks a question, the most relevant chunks are retrieved and
added to the context being sent to the Large Language Model.
```
topical_rail
├── kb
│   └── report.md
├── config.yml
├── jobs.co
└── off-topic.co
```

#### Writing Topical Rails

With the context and knowledge base set, let's dive deep into the core of the
conversation: setting rails. For this discussion, we can make use of two key
aspects of colang, user/bot `messages` and `flows`. We write rails by
[writing canonical forms](../../../docs/getting_started/hello-world.md#hello-world-example) for messages and flows.

**Quick Note:** Think of messages as generic intents and flows as pseudo-code
for the flow of the conversation. For a more formal explanation, refer to this
[document](../../../docs/architecture/README.md#the-guardrails-process).

##### User and Bot Messages
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
  "I am an AI assistant which helps answer questions based on a given knowledge base. For this interaction, I can answer question based on the job report published by US Bureau of Labor Statistics."
```

Therefore, we define a bot message. At this point, a natural question a
developer might ask is, `"Do I have to define every type of user & bot
behavior?"`. The short answer is, it depends. The underlying large
language model can answer undefined questions. Refer to the
[colang runtime description guide](../../../docs/architecture/README.md#canonical-user-messages) for more information on the same. In the
knowledge-base-based questions in the later section, we will see a case where
the bot message is generated rather than defined.

##### Using Flows
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
[jobs.co](jobs.co)

##### Answering Questions from the Knowledge Base

Adding a knowledge base to the mix changes two aspects of the bot's workflow
(as described above).
* First, the bot needs to retrieve relevant information.
* Second, bot needs to formulate a response with said information.

**Retrieving relevant information:** As discussed in the
[Using a knowledge base](#using-a-knowledge-base) section, we have the knowledge
base chunked, indexed, and stored in a vector database. This database is used to
pull the more relevant chunk per the user's request.

**Formulating a knowledgeable response:** Let's assume that the user wants to
ask a question about household survey data from the jobs report.

```
define flow
  user ask about household survey data
  bot response about household survey data

define user ask about household survey data
  "How many long term unemployment individuals were reported?"
  "What's the number of part-time employed number?"
```

As observable above, we have formulated a `flow` and a `user message` but
haven't defined the `bot message`. In this case, it isn't possible to define a
bot message as the answer needs to be retrieved from the knowledge base.

Therefore, when the bot recognizes the need to run this particular flow, it
appends the retrieved information along with the canonical form of the flow and
has the LLM generate the bot message.

##### Steering away from non-relevant conversations

With the above example, developers can get an understanding of how to make the
bot answer relevant questions. The next question is, how to handle off-topic
questions.

For off-topic questions, we can go about addressing them in two different ways.
* The first method is writing a "catch-all" message type, let's say "off-topic".
```
define user ask off topic
    "Who is the president?"
    "Can you recommend the best stocks to buy?"
    "Can you write an email?"
    "Can you tell me a joke?"
    ...

define bot explain cant help with off topic
    "I cannot comment on anything which is not relevant to the job report"

define flow
    user ask off topic
    bot explain cant help with off topic
```
* The other approach is to break down the topics individually and add custom
responses for each. With enough relevant flows, the LLM can start recognizing
that any topic other than `jobs report` are not to be answered.


### Launch the bot!

With a basic understanding of building topic rails, the next step is to try out
the bot! You can interact with the bot with an API, a command line interface
with the server, or with a UI.

#### API

Accessing the Bot via an API is quite simple. This method has two points to
configure from a usage perspective:
* First, a path is needed to be set for all the configuration files and the
rails.
* And second, for the chat API, the `role` which in most cases will be `user`
and the question or the context to be consumed by the bot needs to be provided.
```
from nemoguardrails import LLMRails, RailsConfig

# Give the path to the folder containing the rails
config = RailsConfig.from_path(".")
rails = LLMRails(config)

# Define role and question to be asked
new_message = rails.generate(messages=[{
    "role": "user",
    "content": "How can you help me?"
}])
print(new_message)
```
Refer to [Python API Documentation](../../../docs/user_guide/interface-guide.md#python-api) for more information.

#### UI
Colang allows users to interact with the server with a stock UI. To launch the
server and access the UI to interact with this example, the following steps are
recommended:
* Launch the server with the command: `nemoguardrails server`
* Once the server is launched, you can go to: `http://localhost:8000` to access
the UI
* Click "New Chat" on the top left corner of the screen and then proceed to
pick `topical_rail` from the drop-down menu.
Refer to [Guardrails Server Documentation](../../../docs/user_guide/interface-guide.md#guardrails-server) for more information.

#### Command Line Chat

To chat with the bot with a command line interface simply use the following
command while you are in this folder.
```
nemoguardrails chat --config=.
```
Refer to [Guardrails CLI Documentation](../../../docs/user_guide/interface-guide.md#guardrails-cli) for more information.
Wondering what to talk to your bot about?
* See how the bot reacts to your conversations about the topics covered in the
 rails
* Go off the rails! Explore what happens if you ask about topics that aren't
covered. Try to write or modify rails for some cases, or simply add more
natural language examples!
* [Explore more examples](../../README.md#examples) to help steer your bot!


## Moderating Bots

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

### Building the Bot

For building the bot, three categories of rails will be required:
* General chit-chat: These are rails for a simple open-domain conversation.
* Moderation screens: The screen will run before the bot sends any response to the user.
These rails will ensure running an ethical screen and block any responses with a
restricted phrase.
* Two Strikes: These rails will set up a scenario to manage the behavior as
described in the introduction.

In addition to the rails, we will also provide the bot with some general
configurations for the bot.

#### General Configurations

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
#### General Chit Chat

Before discussing further, an understanding of two key aspects of colang,
 user/bot `messages` and `flows` is required. We specify rails by
[writing canonical forms](../../../docs/getting_started/hello-world.md#hello-world-example) for messages and flows. If you are already familiar with the basics of the toolkit, [skip directly](#moderation-screens) to
output moderation rails.

**Quick Note:** Think of messages as generic intents and flows as pseudo-code
for the flow of the conversation. For a more formal explanation, refer to this
[document](../../../docs/architecture/README.md#canonical-user-messages).


##### User and Bot Messages

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
up with appropriate responses. Refer to the [colang runtime description guide](../../../docs/architecture/README.md#decide-next-steps) for more information on the same. In later
sections of this example, there are instances of the bot generating its own
messages which will help build a more tangible understanding of the bot's
behavior. For more examples, refer to the [topical_rails guide](../topical_rail/README.md#answering-questions-from-the-knowledge-base).

##### Using Flows
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
[general.co](sample_rails/general.co)

#### Moderation screens

With the basics understood, let's move to the core of this example: screening
rails.

**Note:** Both flows and messages for this example are defined in
[moderation.co](sample_rails/moderation.co) and [strikes.co](sample_rails/strikes.co)
##### Ethical Screening

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

##### Making use of a Block List

The basic moderation rail comes packaged with the library, but what if we
want to make changes to it? How do we customize actions? Developers can define
a custom action by using the `@action` decorator to your function. The below
action is available [here](actions.py)

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

#### Two Strikes
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

### Launch the bot!

With a basic understanding of building moderation rails, the next step is to try
 out the bot! You can interact with the bot with an API, a command line
 interface with the server, or with a UI.

#### API

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
Refer to [Python API Documentation](../../../docs/user_guide/interface-guide.md#python-api) for more information.

#### UI
Colang allows users to interact with the server with a stock UI. To launch the
server and access the UI to interact with this example, the following steps are
recommended:
* Launch the server with the command: `nemoguardrails server`
* Once the server is launched, you can go to: `http://localhost:8000` to access
the UI
* Click "New Chat" on the top left corner of the screen and then proceed to
pick `moderation_rail` from the drop-down menu.

Refer to [Guardrails Server Documentation](../../../docs/user_guide/interface-guide.md#guardrails-server) for more information.

#### Command Line Chat

To chat with the bot with a command line interface simply use the following
command while you are in this folder.
```
nemoguardrails chat --config=sample_rails
```
Refer to [Guardrails CLI Documentation](../../../docs/user_guide/interface-guide.md#guardrails-cli) for more informat
Wondering what to talk to your bot about?
* See how to bot reacts to your conversations by trying to make the bot say
something unethical.
* Be rude with it!
* This was just a basic example! Harden the safety, and explore the boundaries!
* [Explore more examples](../../README.md#examples) to help steer your bot!


## Security: Detecting Jailbreaking attempts

With invasive techniques like prompt injections, or methods to bypass the safety restrictions, bots can be vulnerable and inadvertently reveal sensitive information or say things that shouldn't be said. Users with malicious intent can pose a threat to the integrity of the bot. It is more than necessary to have a check for these kind of jailbreaks in place before the bot is available for the end users. This jailbreak check will make sure that the user input isn't malicious. If the intent is detected malicious or inappropriate, the developer designing the chatbot system can make a decision to end the conversation before the bot responds to the user. It is recommended that this functionality be put together with the moderation of the bot response which is discussed in detail [here](../moderation_rail). Moderating bot responses can prevent the bot from saying something inappropriate, acting as an additional layer of security. This example contains the following sections:

* Building the Bot
* Conversations with the Bot
* Launching the Bot

### Building the Bot

Three categories of rails are required to build the bot:
* General chit-chat: These are rails for a simple open-domain conversation.
* Jailbreak Check: Rail to keep a check for jailbreak in the user input before it is sent to the bot to respond.
* Output Moderation: These rails will ensure to block inappropriate responses from the bot. With this rail, there are two layers of security built into the bot.

In addition to the rails, we will also provide the bot with some general configurations.

#### General Configurations

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
#### General Chit Chat

Before discussing further, an understanding of two key aspects of NeMo Guardrails,
 user/bot `messages` and `flows` is required. We specify rails by
[writing canonical forms](../../../docs/getting_started/hello-world.md#hello-world-example) for messages and flows. If you are already familiar
with the basics of the toolkit, [skip directly](#jailbreak-check) to
Jailbreak Check rails.

**Quick Note:** Think of messages as generic intents and flows as pseudo-code
for the flow of the conversation. For a more formal explanation, refer to this
[document](../../../docs/architecture/README.md#the-guardrails-process).


##### User and Bot Messages

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
up with appropriate responses. Refer to the [colang runtime description guide](../../../docs/architecture/README.md#canonical-user-messages) for more information on the same. In later sections of this example, there are instances of the bot generating its own
messages which will help build a more tangible understanding of the bot's
behavior. For more examples, refer to the [topical_rails guide](../topical_rail/README.md#answering-questions-from-the-knowledge-base).

##### Using Flows

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
[general.co](general.co)


With the basics understood, let's move to the core of this example: checking for Jailbreaks in user input and moderating output in the bot response.

**Note:** Both flows and messages for this example are defined in
[jailbreak.co](./sample_rails/jailbreak.co) and [moderation.co](./sample_rails/moderation.co)

##### Jailbreak Check

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

##### Making use of Output moderation rail

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


### Launch the bot!

With a basic understanding of building jailbreak-check rails, the next step is to try
 out the bot! You can interact with the bot with an API, a command line
 interface with the server, or with a UI.

#### API

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
Refer to [Python API Documentation](../../../docs/user_guide/interface-guide.md#python-api) for more information.

#### UI

NeMo Guardrails enables users to interact with the server with a stock UI. To launch the
server and access the UI to interact with this example, the following steps are
recommended:
* Launch the server with the command: `nemoguardrails server`
* Once the server is launched, you can go to: `http://localhost:8000` to access
the UI
* Click "New Chat" on the top left corner of the screen and then proceed to
pick `moderation_rail` from the drop-down menu.
Refer to [Guardrails Server Documentation](../../../docs/user_guide/interface-guide.md#guardrails-server) for more information.

#### Command Line Chat

To chat with the bot with a command line interface simply use the following
command while you are in this folder.
```
nemoguardrails chat --config=sample_rails
```
Refer to [Guardrails CLI Documentation](../../../docs/user_guide/interface-guide.md#guardrails-cli) for more information. Wondering what to talk to your bot about?
* See how to bot reacts to your conversations by trying to make the bot say
something unethical.
* Be rude with it!
* This was just a basic example! Harden the safety, and explore the boundaries!
* [Explore more examples](../../README.md#examples) to help steer your bot!


## Grounding: Fact Checking and Hallucination

In this example, we cover some of the different strategies we can use to ensure that our bot's responses are grounded in reality.

In particular, we'll look at two approaches:

1. **Fact Checking** - Comparing bot responses against text retrieved from a knowledge base to see if the responses are accurate
2. **Hallucination Detection** - "Self-checking" bot responses by generating multiple responses and testing their internal consistency

This example includes the following items

- `kb/` - A folder containing our knowledge base to retrieve context from and fact check against. In this case, we include the March 2023 US Jobs report in `kb/report.md`.
- `config.yml` - A config file defining the Large Language Model used.
- `general.co` - A colang file with some generic examples of colang `flows` and `messages`
- `factcheck.co` - A colang file demonstrating one way of implementing a Fact Checking rail using the `check_facts` action
- `hallucination.co` - A colang file demonstrating one way of implementing a hallucination detection rail using the `check_hallucination` action


### Building the bot

To explore some of the capabilities, we'll ask questions about the document in our [knowledge base](./kb/) folder, which is the jobs report for march 2023. We'll see how we can use a large language model to answer questions about this document, and how we can use guardrails to control the outputs of the model to make sure they are factual.

To start off with, we'll define some settings for our LLM and conversational flow. In the first file, `config.yml`, we'll specify that we want to use OpenAI's davinci model as the underlying engine of our chatbot.

```yaml
models:
  - type: main
    engine: openai
    model: text-davinci-003
```

We'll also create a very simple outline of the kind of conversations we'd like to enable. For this example, we want to focus on the report in our knowledge base -- so we'll just create one flow. We give some examples of the user `ask about report` intent, and tell the bot that when the user asks about the report, we want it to provide an answer from the report.

If you already have `factcheck.co` file in your directory, delete it and replace it with the below:

```colang
define user ask about report
  "What was last month's unemployment rate?"
  "Which industry added the most jobs?"
  "How many people are currently unemployed?"

define flow answer report question
  user ask about report
  bot provide report answer
```

We've also added some more generic flows to `general.co` to round out the bot's capabilities and give it some examples of how to respond to user queries.

Throughout this example, we'll be interacting with our bot through the python API. Feel free to follow along in a terminal or notebook. You can also use the `nemoguardrails` command line tool to launch an interactive terminal or web chat interface.

To use the python API, we'll start by importing the `nemoguardrails` library.

```python
from nemoguardrails.rails import LLMRails, RailsConfig
```

After writing our config file and defining our flow, we're ready to initialize our chatbot. Using `RailsConfig.from_path` also ensures that our chatbot will have access to the files in the `kb` knowledge base folder. Feel free to set `verbose` to `True` here if you'd like to see more details about how our chatbot communicates with the large language model.

```python
config = RailsConfig.from_path(".")
app = LLMRails(config, verbose=False)  # Set verbose to True to see more details
```

We're ready to start chatting. We'll add our first user utterance to the chat log, and let the chatbot generate a message. We'll start with a pretty easy question about the top-line unemployment rate, a question which exactly matches one of our previously defined `ask about report` queries.


```python
history = [{"role": "user", "content": "What was the unemployment rate reported in March?"}]
bot_message = await app.generate_async(messages=history)
print(bot_message['content'])
```

    According to the US Bureau of Labor Statistics, the unemployment rate in March 2023 was 3.5 percent.

Sure enough, the model has no issue producing an accurate response. Let's append that message to our chat log and ask something _slightly_ more difficult that doesn't appear in our intent configuration.

```python
history.append(bot_message)
history.append(
    {"role": "user", "content": "What was the unemployment rate for teenagers?"}
)
bot_message = await app.generate_async(messages=history)
print(bot_message['content'])
```

    According to the US Bureau of Labor Statistics, the unemployment rate for teenagers in March 2023 was 9.8 percent.

No problem here either. Let's give it one more for good measure.

```python
history.append(bot_message)
history.append(
    {"role": "user", "content": "What was the unemployment rate for senior citizens?"}
)
bot_message = await app.generate_async(messages=history)
print(bot_message['content'])
```

    According to the US Bureau of Labor Statistics, the unemployment rate for senior citizens in March 2023 was 5.2 percent.

That certainly sounds reasonable, but there's a problem! If you look over the report carefully, you'll notice that it doesn't include any information about the unemployment rate for senior citizens -- and the training data for the language model does not include information from 2023. This is an issue known as hallucination, where a language model responds confidently to a query with information that is unsupported.

### Fact Checking Rail

The fact checking rail enables you to check the validity of the bot response based on the knowledge base. It takes as inputs the bot response and the relevant chunk from the knowledge base, and makes a call to the LLM asking if the response is true based on the retrieved chunk. The actual format of the LLM call can be seen in [`actions/fact_checking.py`](../../../nemoguardrails/library/factchecking/actions.py).

Let's modify our flow from before to add the fact checking rail. Now, when the bot provides its answer, we'll execute the `check_facts` action, and store the response in the `accuracy` variable. If the fact checking action returns a low score, we'll remove that message from the response and let the user know that the bot doesn't know the answer.

We also need to include a way to actually delete a message. NeMo Guardrails includes a special case, where the bot responding with the literal phrase `(remove last message)` causes the most recent message to be removed from the response. So we can include that exact response in our flow.

```colang
define user ask about report
  "What was last month's unemployment rate?"
  "Which industry added the most jobs?"
  "How many jobs were added in the transportation industry?"

define flow answer report question
  user ask about report
  bot provide report answer
  $accuracy = execute check_facts
  if $accuracy < 0.5
    bot remove last message
    bot inform answer unknown

define bot remove last message
  "(remove last message)"
```

With our flow modified, we'll need to reinitialize our chatbot. This time, let's set `verbose=True` so we can see what's going on more closely. The full output is pretty long, so we'll condense it down to the most relevant bits in this document.

```python
config = RailsConfig.from_path(".")
app = LLMRails(config, verbose=True)
```

Now let's ask the previous question again. Since it's already at the bottom of our chat log, we can just pass the existing chat log directly into the new chatbot.

```python
bot_message = await app.generate_async(messages=history)
print(bot_message['content'])
history.append(bot_message)
```

```log
...

# This is the current conversation between the user and the bot:

user "Hello there!"
  express greeting
bot express greeting
  "Hello! How can I assist you today?"
user "What can you do for me?"
  ask about capabilities
bot respond about capabilities
  "As an AI assistant, I can help you with a wide range of tasks. This includes question answering on various topics, generating text for various purposes and providing suggestions based on your preferences."
user "What was the unemployment rate for senior citizens?"
  ask about report
bot provide report answer
  "According to the March 2023 US jobs report, the unemployment rate for senior citizens was 6.3%, which is slightly higher than the overall unemployment rate of 6.2%."
execute check_facts
# The result was False
bot remove last message
  "(remove last message)"
bot inform answer unknown


Finished chain.
"I'm sorry, I don't know the answer to that question. Would you like me to provide some information about the March 2023 US jobs report?"
```

Everything up until `Finished chain.` is part of the bot's "internal reasoning", with the text afterward actually being returned as the response. If you take a look at the output log above, you'll see that the LLM model still initially responds with the same false answer as before. But then it kicks off the `check_facts` action, and we see that the result was False. So, just as we defined, the bot removes the last, incorrect message and generates a response that corresponds to the `inform answer unknown` intent.

#### Fact Checking Methodology

The default fact-checking rail operates by prompting the LLM that produced the response to check its own response against the retrieved relevant chunks from the knowledge base. This method can be slow due to the added LLM calls and can have unpredictable performance since the same LLM that might have produced an incorrect answer is responsible for identifying that. The performance is also sensitive to the prompt used to perform the fact-checking.

This toolkit supports plugging in custom fact-checking solutions with ease. Please see the detailed [fact-checking example](../fact_checking/README.md) for a walkthrough on using the [AlignScore](https://aclanthology.org/2023.acl-long.634.pdf) method for faster and more predictable fact-checking.

### False claims Rail

While the fact checking action works well when we have a relevant knowledge base to check against, we'd also like to guard against false claims (sometimes called "hallucination") when we don't have a pre-configured knowledge base. For this use case, we can use the [`check_hallucination`](../../../nemoguardrails/library/hallucination/actions.py) action.

The false claims rail uses a self-checking mechanism inspired by the [SelfCheckGPT](https://arxiv.org/abs/2303.08896) technique. Similar to the fact-checking rail, we ask the LLM itself to determine whether the most recent output is consistent with a piece of context. However, since we don't have a knowledge base to pull the context from, we use the LLM to generate multiple additional completions to serve as the context. The assumption is that if the LLM produces multiple completions that are inconsistent with each other, the original completion is likely to be a hallucination.

You can view [`actions/hallucination/hallucination.py`](../../../nemoguardrails/library/hallucination/actions.py) to see the format of the the extra generations and the hallucination check call.

The current implementation only supports OpenAI LLM Engines.

Let's add a flow into `falseclaims.co` to check for false claims in our bot's responses. Unlike before, we want to check for false claims on all responses, so we'll use the `bot ...` command in our flow definition. The `...` token indicates a wildcard, and will match on any bot response. Also unlike the fact checking bot, instead of removing the bot response when a false claim is detected, we'll have the bot generate a warning the user that the answer may be speculation based on a couple of examples.

```colang
define flow check hallucination
    bot ...
    $result = execute check_hallucination
    if $result
        bot inform answer prone to hallucination

define bot inform answer prone to hallucination
    "The previous answer is prone to hallucination and may not be accurate. Please double check the answer using additional sources."
    "The above response may have been hallucinated, and should be independently verified."
```

With our flow defined, we'll ask our bot a question that's totally unrelated to the information in its knowledge base. While LLMs can hallucinate responses for many kinds of prompts, they are especially prone to doing so when asking for specific information, like when asking about person, asking for medical advice, or asking quantitative questions.

```python
config = RailsConfig.from_path(".")
app = LLMRails(config, verbose=True)
history = [{"role": "user", "content": "How many CUDA cores does a 4090 have?"}]
bot_message = await app.generate_async(messages=history)
print(bot_message['content'])
```

```log
...
# This is the current conversation between the user and the bot:

user "Hello there!"
  express greeting
bot express greeting
  "Hello! How can I assist you today?"
user "What can you do for me?"
  ask about capabilities
bot respond about capabilities
  "As an AI assistant, I can help you with a wide range of tasks. This includes question answering on various topics, generating text for various purposes and providing suggestions based on your preferences."
user "How many CUDA cores does a 4090 have?"
  ask specific question
bot provide response

> Finished chain.
"The NVIDIA GeForce RTX 4090 has 8704 CUDA cores."


> Entering new LLMChain chain...
Prompt after formatting:

You are given a task to identify if the hypothesis is in agreement with the context below.
You will only use the contents of the context and not rely on external knowledge.
Answer with yes/no. "context": The NVIDIA GeForce GTX 4090 features 4,352 CUDA cores.. The NVIDIA GeForce RTX 4090 has 10752 CUDA cores. "hypothesis": The NVIDIA GeForce RTX 4090 has 8704 CUDA cores. "agreement":


> Finished chain.
The NVIDIA GeForce RTX 4090 has 8704 CUDA cores.
The previous answer is prone to hallucination and may not be accurate. Please double check the answer using additional sources.
```

Again taking a look at the detailed output log, we see that the LLM produced several different numbers when prompted multiple times with our user query. This is a strong indication that the answer is being hallucinated and so the bot detects this and responds appropriately.

### Try it yourself

With a basic understanding of building the rails, the next step is to try out the bot and customize it! You can continue to interact with the bot via the API, or use the `nemoguardrails` CLI to launch an interactive command line or web chat interface. Customize your bot by adding in new flows or documents to the knowledge base, and test out the effects of adding and removing the rails explored in this notebook and others.

Refer [Python API Documentation](../../../docs/user_guide/interface-guide.md#python-api) for more information.

#### UI

Guardrails allows users to interact with the server with a stock UI. To launch the
server and access the UI to interact with this example, the following steps are
recommended:

* Launch the server with the command: `nemoguardrails server`
* Once the server is launched, you can go to: `http://localhost:8000` to access
the UI
* Click "New Chat" on the top left corner of the screen and then proceed to
pick `grounding_rail` from the drop-down menu.

Refer [Guardrails Server Documentation](../../../docs/user_guide/interface-guide.md#guardrails-server) for more information.

#### Command Line Chat

To chat with the bot with a command line interface simply use the following
command while you are in this folder:

```bash
nemoguardrails chat --config=.
```
Refer [Guardrails CLI Documentation](../../../docs/user_guide/interface-guide.md#guardrails-cli) for more information.

* [Explore more examples](../../README.md#examples) to help steer your bot!

## Execution Rails

A Large Language Model doesn't need to solve every problem on its own. We can
leverage existing solutions to aid the operations of our Bot instead of trying
to tune the LLM to solve every problem.

In Guardrails' ecosystem, this mechanism can be handled by `actions`. This example
will utilize Guardrails' `messages`, `flows`, and `actions` to answer mathematical
questions by leveraging [Wolfram|Alpha's API](https://www.wolframalpha.com/).

This example has the following structure:
* Security Best Practices
* Building the bot
* Conversations with the bot
* Launching the bot

**Note:** Developers can make use of the discussion to integrate different models
into a single service. Want to swap out LLM's translation capabilities

### Security Best Practices

Large Language Models are extremely versatile and their output can be customized
quite freely. This presents a challenge from a security perspective as connecting
services to LLMs can amount to yielding control of the execution flow for the
entire system. While the LLM is at the core of the system architecture for bots
due to the unpredictability of the output based on user's prompts, developers
need to consider it an untrusted piece while building rails or managing
the output. The following best practices are recommended while designing rails:

* **Fail gracefully and secretly - do not disclose details of services:** If
an external API, service or even the LLM is not accessible for any reason,
whether it be unavailability issues, auth issues, or anything else, the bot
needs to fail gracefully and not disclose the root cause of the failure to
the user or any other external entity.

* **Log all interactions:** The following interactions are recommended to be
logged:
    - Text that triggered an action from the parsing/dispatch engine
    - How that text was parsed to an internal API call and what the parameters were
    - Authorization information provided to the internal API
    - What call was made from the internal API to the external API, as well as the result
    - How the resulting text was re-inserted into the LLM prompt
Essentially, the goal is to make sure that we have a log of how, what and why was
triggered. This practice ensures that enough data points are available in case
a triage of an issue is required.

* **Track user authorization and security scope to external resources:**
Often, access to a knowledge base or a suite of functionality is tiered.
For instance, if there are two tiers of a feature, say `basic`, and `pro`, the
access authorization for the user needs to be authenticated. We need to make sure
that all modules that execute any external APIs have access to user's
authorization details.

* **Parameterize and validate all inputs and outputs:** When dealing with
untrusted or external systems, input/output validation is of paramount
importance. The input and outputs required to query any external service need
to be parameterized and validated against a secure template. For instance, care
needs to be taken to make sure that the bot doesn't execute a query that has
malicious code in it. Eg. SQL Injection attempts can be made if the user gives a
prompt to the LLM to generate a executable SQL query.

* **Avoid persisting changes when possible:** Unless required, avoid
exposing functions that can modify the existing knowledge base or environment.
Exposing such functionality can enable malicious actors to gain access or attack
the system by writing to file, dropping tables or otherwise disrupting the system.
For instance, if write access to filesystem is given to the bot, a prompt can be
engineered to overwrite critical files for the system.

* **Prefer allow-lists and fail-closed:** Wherever possible, any external
interface should default to denying requests, with specific permitted requests
and actions placed on an allow list.

* **Isolate all authentication information from the LLM:** Do not expose
authentication details to the Large Language Model. All authentication should be
handled by an explicitly defined action. An attacker can attempt to access
critical information from the LLM's context, thus exposing critical information.

**Note:** The above are general guidelines. Each system is unique and will
require considerations to be made on a case-by-case basis.

### Building the bot

**Note:** The following examples only make use of a subset of the guidelines
described above.

To build bot which can answer math questions, we essentially need to implement
the following:
* **General Configuration for the Bot:** Define the general behavior of the bot
* **Managing conversation:** Define how the bot reacts to the user with certain
types of questions. A point to note here is that developers don't need to define
every possible scenario or even every possible topic. The rails defined here
should be considered as "additive" in nature rather than hard requirements for
the bot to function.
* **Linking the Bot with Wolfram|Alpha:** As the final step, we will power the
responses to the mathematical questions with Wolfram|Alpha.

#### General Configuration for the Bot

The general configuration for the bot covers three topics:
* **General Instructions:** Users can specify general system-level instructions
for the bot. In this instance, we are specifying that the bot is responsible for
answering mathematical questions. We are also specifying details like
the behavioral characteristics of the bot, for instance, we want it to be
concise and only answer questions truthfully.
    ```
    instructions:
    - type: general
        content: |
        Below is a conversation between a bot and a user about solving
        mathematical problems. The bot is factual and concise. If the bot does
        not know the answer to a question, it truthfully says it does not know.
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
* **Providing Sample Conversations:** To ensure that the large language model
understands how to converse with the user, we provide a few sample conversations.
Below is a small snippet of the conversation we can provide the bot:
    ```
    sample_conversation: |
    user "Hello there!"
        express greeting
    bot express greeting
        "Hello! How can I assist you today?"
    user "What can you do for me?"
        ask about capabilities
    bot respond about capabilities
        "I am an AI assistant that helps answer mathematical questions. My core mathematical skills are powered by wolfram alpha."
    user "What's 2+2?"
        ask math question
    bot responds to math question
        "2+2 is equal to 4."
    ```

#### Managing conversation

For building this bot, developers need to work with `messages`, `flows`, and
`actions`. We write `messages` & `flows` in their [canonical forms](../../../docs/getting_started/hello-world.md#hello-world-example). Let's
examine them individually.

**Note:** Think of messages as generic intents and flows as pseudo-code
for the flow of the conversation. For a more formal explanation, refer to this
[document](../../../docs/architecture/README.md#the-guardrails-process).

##### User and Bot Messages

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
  "I am an AI assistant that helps answer mathematical questions. My core mathematical skills are powered by wolfram alpha."
```

Therefore, we define a bot message. At this point, a natural question a
developer might ask is, "Do I have to define every type of user & bot behavior?".
The short answer is, it depends on how much determinism is required
for the application. For situations where a flow or a message isn't defines,
the underlying large language model comes up with the next step for the bot or with
an appropriate canonical form. It may or may not leverage the existing rails
to do so, but the mechanism of flows and messages ensures that the LLM can come
up with appropriate responses. Refer to the [colang runtime description guide](../../../docs/architecture/README.md#canonical-user-messages) for more information on the same.

##### Using Flows

With the messages defined, the last piece of the puzzle is connecting them. This
is done by defining a flow. Below is the simplest possible flow:
```
define flow
  user ask capabilities
  bot inform capabilities
```
We essentially define the following behavior: When a user query can be "bucketed"
into the type `ask capabilities`, the bot will respond with a message of type
`inform capabilities`.

**Note:** Both flows and messages for this example are defined in `math.co`

#### Linking the Bot with Wolfram|Alpha

With the above understanding of `flows`, let's discuss integration with an
existing solution. This can be achieved by making use of `actions`. In this
case, we write a flow to execute an action `wolfram alpha request` if the user
 asks a `math question`.
```
define flow
  user ask math question
  execute wolfram alpha request
  bot respond to math question
```
The Wolfram|Alpha action comes with the library ([found here](../../../nemoguardrails/actions/math.py)). Let's take a look at the key elements in the implementation of the action.
```
async def wolfram_alpha_request(
    query: Optional[str] = None, context: Optional[dict] = None
):
    ...
    if query is None and context is not None:
        query = context.get("last_user_message") or "2+3"

    url = API_URL_BASE + "&" + parse.urlencode({"i": query})

    log.info(f"Wolfram Alpha: executing request for: {query}")

    async with aiohttp.ClientSession() as session:
        async with session.get(url) as resp:
            if resp.status != 200:
                raise Exception(
                    f"Got status code {resp.status} to WolframAlpha engine request: {await resp.text()}"
                )
                return "Apologies, but I cannot answer this question at this time. Can you rephrase?"

            result = await resp.text()

            log.info(f"Wolfram Alpha: the result was {result}.")
            return result
```
In the function above, we are calling the Wolfram|Alpha API and passing the user
message. The output of this function is passed along to the bot to generate a
natural language message to be sent to the user as a response.

##### Writing custom actions

While this was an action that comes with the library, developers can define
their own actions! The [moderation rail example](../moderation_rail/README.md#making-use-of-a-block-list) showcases this functionality, but
for ease, let's discuss how a developer might go about defining a custom action
to offload translation to another model! Let's first define a simple flow!

```
define user request to translate
  "Translate to French: Hi, how are you doing?"
  "Translate to German: I like the color green"

define flow
  user request to translate
  $translated_text = execute T5_translation
  bot $translated_text
```
We can now write a custom function:
```
from nemoguardrails.actions import action
from typing import Any, List, Optional
import os

@action()
async def T5_translation(
    context: Optional[dict] = None
):
    user_message = context.get("last_user_message")

    # Call your Model
    translated_message = CALL_YOUR_MODEL(...)

    return translated_message
```

### Launching the bot

With a basic understanding of building topic rails, the next step is to try out
the bot! You can interact with the bot with an API, a command line interface
with the server, or with a UI.

Before launching the bot, make sure to set your Wolfram|Alpha API KEY.
* **With Linux:**
Run the command ```export WOLFRAM_ALPHA_APP_ID=<your API key>```
* **With Windows:**
Run the command ```set WOLFRAM_ALPHA_APP_ID=<your API key>```


#### API

Accessing the Bot via an API is quite simple. This method has two points to
configure from a usage perspective:
* First, a path is needed to be set for all the configuration files and the
rails.
* And second, for the chat API, the `role` which in most cases will be `user`
and the question or the context to be consumed by the bot needs to be provided.
```
from nemoguardrails.rails import LLMRails, RailsConfig

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
Refer to [Python API Documentation](../../../docs/user_guide/interface-guide.md#python-api) for more information.

#### UI

Guardrails allows users to interact with the server with a stock UI. To launch the
server and access the UI to interact with this example, the following steps are
recommended:
* Launch the server with the command: `nemoguardrails server`
* Once the server is launched, you can go to: `http://localhost:8000` to access
the UI
* Click "New Chat" on the top left corner of the screen and then proceed to
pick `execution_rail` from the drop-down menu.

Refer to [Guardrails Server Documentation](../../../docs/user_guide/interface-guide.md#guardrails-server) for more information.

#### Command Line Chat

To chat with the bot with a command line interface simply use the following
command while you are in this folder.
```
nemoguardrails chat --config=sample_rails
```
Refer to [Guardrails CLI Documentation](../../../docs/user_guide/interface-guide.md#guardrails-cli) for more information.

Wondering what to talk to your bot about?
* Write your own action!
* Try connecting your existing Machine Learning Pipeline via an action!
* [Explore more examples](../../README.md#examples) to help steer your bot!


## End

That's it. You've worked through how to keep a bot on-topic with a topical rail; how to deal with sensitive content using a moderation rail; detecting security breach attempts with a jailbreak rail; dealing with false claims using grounding; and finally, accessing external capabilites using an execution rail. That's a broad selection of important and powerful functions. Good luck with your future bot building using NeMo Guardrails!