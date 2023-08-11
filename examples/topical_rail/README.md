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


# Topical Rails: Jobs Report

When answering questions, it is best to stick to topics with which one has
familiarity. This policy is doubly true for chatbots. The question is: how do
we make a bot stick to a particular topic? In this example, we will cover:
* Building the bot
* Walking through conversations
* A brief walkthrough of launching a bot with topical rails

## Building the bot

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

### General Configurations

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

### Using a knowledge base

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

### Writing Topical Rails

With the context and knowledge base set, let's dive deep into the core of the
conversation: setting rails. For this discussion, we can make use of two key
aspects of colang, user/bot `messages` and `flows`. We write rails by
[writing canonical forms](../../docs/getting_started/hello-world.md#hello-world-example) for messages and flows.

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
  "I am an AI assistant which helps answer questions based on a given knowledge base. For this interaction, I can answer question based on the job report published by US Bureau of Labor Statistics."
```

Therefore, we define a bot message. At this point, a natural question a
developer might ask is, `"Do I have to define every type of user & bot
behavior?"`. The short answer is, it depends. The underlying large
language model can answer undefined questions. Refer to the
[colang runtime description guide](../../docs/architecture/README.md#canonical-user-messages) for more information on the same. In the
knowledge-base-based questions in the later section, we will see a case where
the bot message is generated rather than defined.

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
[jobs.co](jobs.co)

#### Answering Questions from the Knowledge Base

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
#### Steering away from non-relevant conversations

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


## Launch the bot!

With a basic understanding of building topic rails, the next step is to try out
the bot! You can interact with the bot with an API, a command line interface
with the server, or with a UI.

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
config = RailsConfig.from_path(".")
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
pick `topical_rail` from the drop-down menu.
Refer to [Guardrails Server Documentation](../../docs/user_guide/interface-guide.md#guardrails-server) for more information.
### Command Line Chat

To chat with the bot with a command line interface simply use the following
command while you are in this folder.
```
nemoguardrails chat --config=.
```
Refer to [Guardrails CLI Documentation](../../docs/user_guide/interface-guide.md#guardrails-cli) for more information.
Wondering what to talk to your bot about?
* See how the bot reacts to your conversations about the topics covered in the
 rails
* Go off the rails! Explore what happens if you ask about topics that aren't
covered. Try to write or modify rails for some cases, or simply add more
natural language examples!
* [Explore more examples](../README.md#examples) to help steer your bot!
