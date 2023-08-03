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

# Execution Rails

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

## Security Best Practices

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

## Building the bot
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

### General Configuration for the Bot

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

### Managing conversation

For building this bot, developers need to work with `messages`, `flows`, and
`actions`. We write `messages` & `flows` in their [canonical forms](../../docs/getting_started/hello-world.md#hello-world-example). Let's
examine them individually.

**Note:** Think of messages as generic intents and flows as pseudo-code
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
  "I am an AI assistant that helps answer mathematical questions. My core mathematical skills are powered by wolfram alpha."
```

Therefore, we define a bot message. At this point, a natural question a
developer might ask is, "Do I have to define every type of user & bot behavior?".
The short answer is, it depends on how much determinism is required
for the application. For situations where a flow or a message isn't defines,
the underlying large language model comes up with the next step for the bot or with
an appropriate canonical form. It may or may not leverage the existing rails
to do so, but the mechanism of flows and messages ensures that the LLM can come
up with appropriate responses. Refer to the [colang runtime description guide](../../docs/architecture/README.md#canonical-user-messages) for more information on the same.

#### Using Flows

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

### Linking the Bot with Wolfram|Alpha

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
The Wolfram|Alpha action comes with the library ([found here](../../nemoguardrails/actions/math.py)). Let's take a look at the key elements in the implementation of the action.
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

#### Writing custom actions

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

## Launching the bot

With a basic understanding of building topic rails, the next step is to try out
the bot! You can interact with the bot with an API, a command line interface
with the server, or with a UI.

Before launching the bot, make sure to set your Wolfram|Alpha API KEY.
* **With Linux:**
Run the command ```export WOLFRAM_ALPHA_APP_ID=<your API key>```
* **With Windows:**
Run the command ```set WOLFRAM_ALPHA_APP_ID=<your API key>```


### API

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
Refer to [Python API Documentation](../../docs/user_guide/interface-guide.md#python-api) for more information.
### UI
Guardrails allows users to interact with the server with a stock UI. To launch the
server and access the UI to interact with this example, the following steps are
recommended:
* Launch the server with the command: `nemoguardrails server`
* Once the server is launched, you can go to: `http://localhost:8000` to access
the UI
* Click "New Chat" on the top left corner of the screen and then proceed to
pick `execution_rail` from the drop-down menu.

Refer to [Guardrails Server Documentation](../../docs/user_guide/interface-guide.md#guardrails-server) for more information.
### Command Line Chat

To chat with the bot with a command line interface simply use the following
command while you are in this folder.
```
nemoguardrails chat --config=sample_rails
```
Refer to [Guardrails CLI Documentation](../../docs/user_guide/interface-guide.md#guardrails-cli) for more information.

Wondering what to talk to your bot about?
* Write your own action!
* Try connecting your existing Machine Learning Pipeline via an action!
* [Explore more examples](../README.md#examples) to help steer your bot!
