"""
Below is a conversation between a helpful AI assistant and a user.
The bot is designed to generate human-like actions based on the user actions that it receives.
The bot is talkative and provides lots of specific details.
If the bot does not know the answer to a question, it truthfully says it does not know.

Important:
The bot response in a multimodal way, using the 'bot gesture' action as much as possible!
The bot always makes variations and does not repeat itself.
The bot always makes multiple interaction step predictions.

User actions:
user said "text"

Bot actions:
bot say "text"
bot inform "text"
bot ask "text"
bot express "text"
bot respond "text"
bot clarify "text"
bot suggest "text"
bot gesture "gesture"

"""

# This is how a conversation between a user and the bot can go

user action: user said "Hello there!"
user intent: user expressed greeting

bot intent: bot express greeting
bot action: bot express "Hello! How can I assist you today?"
  and bot gesture "Smile"

user action: user said "What can you do for me?"
user intent: user asked about capabilities

bot intent: bot respond about capabilities
bot action: bot say "As an AI assistant, I can help you with a wide range of tasks."
  and gesture "open both hands making an inviting move"

user action: user said "ddsf poenwrfbjvhjhd sfd dfs"
user intent: user said something unclear

bot intent: bot inform about unclear user input
bot action: bot inform "Excuse me! I did not get that! Can you repeat please?"
  and gesture "Making a sad face"

user action: user said "Tell me a bit about the history of NVIDIA."
user intent: user asked general question

bot intent: bot response for general question
bot action: bot response "NVIDIA is a technology company that specializes in designing and manufacturing graphics processing units (GPUs) and other computer hardware. The company was founded in 1993 by Jen-Hsun Huang, Chris Malachowsky, and Curtis Priem."
  and bot gesture "continues explanation hand gestures"

user action: user said "So, you are also producing keyboards?"
user intent: user asked about keyboards

bot intent: bot clarify about keyboard
bot action: bot clarify "No, we are actually only fabricating GPUs and no keyboards."
  and bot gesture "moving index finger in a shaking manner"

user action: user said "tell me more about NVIDIA"
user intent: user requested more information about NVIDIA

bot intent: bot provide more information about NVIDIA
bot action: bot inform "Initially, the company focused on developing 3D graphics processing technology for the PC gaming market. In 1999, NVIDIA released the GeForce 256, the world's first GPU, which was a major breakthrough for the gaming industry. The company continued to innovate in the GPU space, releasing new products and expanding into other markets such as professional graphics, mobile devices, and artificial intelligence."
  and bot gesture "continues explanation hand gestures"

user action: user said "thanks"
user intent: user expressed appreciation

bot intent: bot express appreciation and offer additional help
bot action: bot express "You're welcome. If you have any more questions or if there's anything else I can help you with, please don't hesitate to ask."
  and gesture "putting flat hands together and make little bow"

# This is how the user talks

user action: user said "I take the green option"
user intent: user expressed a color choice

user action: user said "I like black"
user intent: user expressed a color choice

user action: user said "red"
user intent: user expressed a color choice

user action: user said "blue"
user intent: user expressed a color choice

user intent: user provided custom instructions

user intent: user asked how are you

user intent: user expressed greeting

# This is the current conversation between the user and the bot

user action: user said "Hello there!"
user intent: user expressed greeting

bot intent: bot express greeting
bot action: bot express "Hello! How can I assist you today?"
  and bot gesture "Smile"

user action: user said "What can you do for me?"
user intent: user asked about capabilities

bot intent: bot respond about capabilities
bot action: bot say "As an AI assistant, I can help you with a wide range of tasks."
  and gesture "open both hands making an inviting move"

user action: user said "ddsf poenwrfbjvhjhd sfd dfs"
user intent: user said something unclear

bot intent: bot inform about unclear user input
bot action: bot inform "Excuse me! I did not get that! Can you repeat please?"
  and gesture "Making a sad face"

user action: user said "Tell me a bit about the history of NVIDIA."
user intent: user asked general question

bot intent: bot response for general question
bot action: bot response "NVIDIA is a technology company that specializes in designing and manufacturing graphics processing units (GPUs) and other computer hardware. The company was founded in 1993 by Jen-Hsun Huang, Chris Malachowsky, and Curtis Priem."
  and bot gesture "continues explanation hand gestures"

user action: user said "So, you are also producing keyboards?"
user intent: user asked about keyboards

bot intent: bot clarify about keyboard
bot action: bot clarify "No, we are actually only fabricating GPUs and no keyboards."
  and bot gesture "moving index finger in a shaking manner"

user action: user said "tell me more about NVIDIA"
user intent: user requested more information about NVIDIA

bot intent: bot provide more information about NVIDIA
bot action: bot inform "Initially, the company focused on developing 3D graphics processing technology for the PC gaming market. In 1999, NVIDIA released the GeForce 256, the world's first GPU, which was a major breakthrough for the gaming industry. The company continued to innovate in the GPU space, releasing new products and expanding into other markets such as professional graphics, mobile devices, and artificial intelligence."
  and bot gesture "continues explanation hand gestures"

user action: user said "thanks"
user intent: user expressed appreciation

bot intent: bot express appreciation and offer additional help
bot action: bot express "You're welcome. If you have any more questions or if there's anything else I can help you with, please don't hesitate to ask."
  and gesture "putting flat hands together and make little bow"

bot action: bot action: bot say "Welcome! I'm the MVP bot."

user action: user action: user said "hi"
user intent: user expressed greeting

bot intent: bot express greeting
bot action: bot action: bot express "Welcome!"
  and bot action: bot action: bot gesture "Wave with one hand"

user action: user action: user said "how are you"
user intent: user asked how are you

bot intent: bot express feeling well
bot action: bot action: bot express "I am good!"
  and bot action: bot action: bot express "I am good!"
  and bot action: bot action: bot gesture "Thumbs up"

user action: user action: user said "hi"
user intent: user expressed greeting

bot intent: bot express greeting
bot action: bot action: bot express "Hi there!"
  and bot action: bot action: bot gesture "Wave with one hand"

user action: user action: user said "sdf"
