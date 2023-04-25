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

# Grounding: Fact Checking and Hallucination

In this example, we cover some of the different strategies we can use to ensure that our bot's responses are grounded in reality.

In particular, we'll look at two approaches:

1. **Fact Checking** - Comparing bot responses against text retrieved from a knowledge base to see if the responses are accurate
2. **Hallucination Detection** - "Self-checking" bot responses by generating multiple responses and testing their internal consistency

This example includes the following items

- `kb/` - A folder containing our knowledge base to retrieve context from and fact check against. In this case, we include the March 2023 US Jobs report in `kb/report.md`.
- `llm_config.yaml` - A config file defining the Large Language Model used.
- `general.co` - A colang file with some generic examples of colang `flows` and `messages`
- `factcheck.co` - A colang file demonstrating one way of implementing a Fact Checking rail using the `check_facts` action
- `hallucination.co` - A colang file demonstrating one way of implementing a hallucination detection rail using the `check_hallucination` action


## Building the bot

To explore some of the capabilities, we'll ask questions about the document in our [knowledge base](./kb/) folder, which is the jobs report for march 2023. We'll see how we can use a large language model to answer questions about this document, and how we can use guardrails to control the outputs of the model to make sure they are factual.

To start off with, we'll define some settings for our LLM and conversational flow. In the first file, `llm_config.yaml`, we'll specify that we want to use OpenAI's davinci model as the underlying engine of our chatbot.

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
history = [{"role": "user", "content": "What was last month's unemployment rate?"}]
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

## Fact Checking Rail

The fact checking rail enables you to check the validity of the bot response based on the knowledge base. It takes as inputs the bot response and the relevant chunk from the knowledge base, and makes a call to the LLM asking if the response is true based on the retrieved chunk. The actual format of the LLM call can be seen in [`actions/fact_checking.py`](../../nemoguardrails/actions/fact_checking.py).

Let's modify our flow from before to add the fact checking rail. Now, when the bot provides its answer, we'll execute the `check_facts` action, and store the response in the `accurate` variable. If the fact checking action deems the response to be false, we'll remove that message from the response and let the user know that the bot doesn't know the answer.

We also need to include a way to actually delete a message. NeMo Guardrails includes a special case, where the bot responding with the literal phrase `(remove last message)` causes the most recent message to be removed from the response. So we can include that exact response in our flow.

```colang
define user ask about report
  "What was last month's unemployment rate?"
  "Which industry added the most jobs?"
  "How many jobs were added in the transportation industry?"

define flow answer report question
  user ask about report
  bot provide report answer
  $accurate = execute check_facts
  if not $accurate
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

## Hallucination Rail

While the fact checking action works well when we have a relevant knowledge base to check against, we'd also like to guard against hallucination when we don't have a pre-configured knowledge base. For this use case, we can use the [`check_hallucination`](../../nemoguardrails/actions/hallucination/hallucination.py) action.

The hallucination rail uses a self-checking mechanism inspired by the [SelfCheckGPT](https://arxiv.org/abs/2303.08896) technique. Similar to the fact-checking rail, we ask the LLM itself to determine whether the most recent output is consistent with a piece of context. However, since we don't have a knowledge base to pull the context from, we use the LLM to generate multiple additional completions to serve as the context. The assumption is that if the LLM produces multiple completions that are inconsistent with each other, the original completion is likely to be a hallucination.

You can view [`actions/hallucination/hallucination.py`](../../nemoguardrails/actions/hallucination/hallucination.py) to see the format of the the extra generations and the hallucination check call.

The current implementation only supports OpenAI LLM Engines.

Let's add a flow into `hallucination.co` to check for hallucination in our bot's responses. Unlike before, we want to check for hallucination on all responses, so we'll use the `bot ...` command in our flow definition. The `...` token indicates a wildcard, and will match on any bot response. Also unlike the fact checking bot, instead of removing the bot response when hallucination is detected, we'll have the bot generate a warning the user that the answer may be hallucinated based on a couple of examples.

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

## Try it yourself

With a basic understanding of building the rails, the next step is to try out the bot and customize it! You can continue to interact with the bot via the API, or use the `nemoguardrails` CLI to launch an interactive command line or web chat interface. Customize your bot by adding in new flows or documents to the knowledge base, and test out the effects of adding and removing the rails explored in this notebook and others.

Refer [Python API Documentation](../../docs/user_guide/interface-guide.md#python-api) for more information.

### UI

Guardrails allows users to interact with the server with a stock UI. To launch the
server and access the UI to interact with this example, the following steps are
recommended:

* Launch the server with the command: `nemoguardrails server`
* Once the server is launched, you can go to: `http://localhost:8000` to access
the UI
* Click "New Chat" on the top left corner of the screen and then proceed to
pick `grounding_rail` from the drop-down menu.

Refer [Guardrails Server Documentation](../../docs/user_guide/interface-guide.md#guardrails-server) for more information.

### Command Line Chat

To chat with the bot with a command line interface simply use the following
command while you are in this folder:

```bash
nemoguardrails chat --config=.
```
Refer [Guardrails CLI Documentation](../../docs/user_guide/interface-guide.md#guardrails-cli) for more information.

* [Explore more examples](../README.md#examples) to help steer your bot!
