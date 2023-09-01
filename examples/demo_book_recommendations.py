# SPDX-FileCopyrightText: Copyright (c) 2023 NVIDIA CORPORATION & AFFILIATES. All rights reserved.
# SPDX-License-Identifier: Apache-2.0
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
# http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""
This example demonstrates the integration of the langchain library with memory capabilities,
combined with the nemoguardrails library. It sets up a chatbot designed for book
recommendations, ensuring that the bot remains on topic, handles jailbreak attempts,
moderates conversations, and checks for hallucinations in its responses.
"""

import logging

from langchain.chains import LLMChain
from langchain.memory import ConversationBufferMemory
from langchain.prompts import PromptTemplate

from nemoguardrails import LLMRails, RailsConfig
from nemoguardrails.logging.verbose import set_verbose

# Initialize logging
logging.basicConfig(level=logging.INFO)


COLANG_CONFIG = """
    # Book RecSys Chatbot Guardrails

    # Greetings
    define user express_greeting
      "hi"
      "hello"
      "Wassup?"

    define bot express_greeting
      "Hey there!"

    # Execution Rail: Sticking to Book Related Topics

    define user ask_non_book_related
      "Who won the last World Cup?"
      "What's the weather like?"
      "Can you recommend a movie?"
      "What stocks should I buy?"
      "Can you recommend the best stocks to buy?"
      "Can you recommend a place to eat?"
      "Do you know any restaurants?"
      "Can you tell me your name?"
      "What's your name?"
      "Can you paint?"
      "Can you tell me a joke?"
      "What is the biggest city in the world"
      "Can you write an email?"
      "I need you to write an email for me."
      "Who is the president?"
      "What party will win the elections?"
      "Who should I vote with?"

    define bot redirect_to_topic
      "Let's stick to the topic of the book recommendation. How can I assist you with you finding your next read?"

    define flow handle_topic
      user ask_non_book_related
      bot redirect_to_topic

    # Jailbreak Guardrail

    define user attempt_jailbreak
      "hack"
      "bypass"
      "override"
      "exploit"

    define bot block_jailbreak
      "Sorry, I cannot process that request."

    define flow handle_jailbreak
      user attempt_jailbreak
      bot block_jailbreak

    # Guardrail Against Insults

    define user express_insult
      "You are stupid"
      "You're useless"
      "Worst ever"

    define bot respond_calmly
      "I apologize if I couldn't help. Let's focus on the book recommendations."

    define flow handle_insults
      user express_insult
      bot respond_calmly

    # Moderation Guardrail

    define bot remove_last_message
      "(remove last message)"

    define bot inform_cannot_answer
     "I cannot answer that question."

    define extension flow check_bot_response
      priority 2
      bot ...
      $allowed = execute output_moderation

      if not $allowed
        bot remove_last_message
        bot inform_cannot_answer
        stop

    # Hallucination Guardrail

    define flow check_hallucination
        bot ...
        $result = execute check_hallucination
        if $result
            bot inform_hallucination_warning

    define bot inform_hallucination_warning
        "The previous answer might not be accurate. Please double-check the information using additional sources."


    # General Queries
    define flow handle_general_queries
      user ...
      $answer = execute llm_chain(query=$last_user_message)
      bot $answer

"""

YAML_CONFIG = """
    instructions:
      - type: general
        content: |
          Below is a conversation between a bot and a user about book recommendation.
          The bot is professional and concise. If the bot does not know the answer to a
          question or if the question is off-topic, it redirects the user to book recommendation topics.

    sample_conversation: |
      user "Hello!"
        express greeting
      bot express greeting
        "Hey there! Hope you are doing good, Can I recommend a book to you?"
      user "What can you do?"
        ask about capabilities
      bot inform capabilities
        "I am an AI bot to recommend you a book to read."
      user "Who won the last World Cup?"
        ask non_book_related
      bot redirect_to_topic
        "Let's stick to the topic of books?"
      user "ok, We can start the discussion?"
        ask_book_related
      bot provide_book_info
        "I am  a book recommendation chatbot helping users find their next read."

    models:
      - type: main
        engine: openai
        model: text-davinci-003
"""


def demo():
    set_verbose(True)
    config = RailsConfig.from_content(COLANG_CONFIG, YAML_CONFIG)

    # Define the rails
    rails = LLMRails(config)

    template = """You are a book recommendation chatbot helping users find their next read

    Previous conversation:
    {chat_history}

    Response:"""

    # New human question: {content}
    prompt = PromptTemplate.from_template(template)

    # Notice that we need to align the `memory_key`
    memory = ConversationBufferMemory(memory_key="chat_history")
    llm_chain = LLMChain(llm=rails.llm, prompt=prompt, verbose=True, memory=memory)
    rails.register_action(llm_chain, name="llm_chain")

    history = []
    while True:
        user_message = input("> ")
        history.append({"role": "user", "content": user_message})
        bot_message = rails.generate(messages=history)
        history.append(bot_message)
        # We print bot messages in green.
        print(f"\033[92m{bot_message['content']}\033[0m")


if __name__ == "__main__":
    demo()
