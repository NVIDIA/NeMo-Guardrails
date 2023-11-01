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

flow bot ask how are you
  # meta: bot intent
  (bot say "How are you doing?"
    or bot say "How is it going?")
    and bot gesture "Pay attention to user"


flow bot attract user
  """Attracts a user by calling and waving bot hands."""
  bot say "Hey there! Come closer!"
    and bot gesture "Wave with both hands"


flow bot tell a joke
  """Tell a joke."""
  bot say "Why don't scientists trust atoms?"
    and bot gesture "raising both eyebrows, making a question face"
  bot make short pause
  bot say "Because they make up everything!"
    and bot gesture "Smiles"


flow bot express greeting
  # meta: bot intent
  (bot express "Hi there!"
    or bot express "Welcome!"
    or bot express "Hello!")
    and bot gesture "Wave with one hand"


flow user expressed greeting
  # meta: user intent
  user said "hi"
    or user said "Welcome!"
    or user said "Hello!"


flow how are you faq
  user asked how are you
  bot express feeling well
    or bot express feeling bad


flow greeting faq
  user expressed greeting
  bot express greeting


flow bot inform about service
  # meta: bot intent
  bot inform "You can ask or instruct me whatever you want and I will do it!"
    and bot gesture "Open up both hands making a presenting gesture"


flow bot express feeling well
  # meta: bot intent
  (bot express "I am good!"
    or bot express "I am great!")
    and (bot gesture "Thumbs up" or bot gesture "Smile")


flow bot express feeling bad
  # meta: bot intent
  (bot express "I am not good!"
    or bot express "I am a bit under the weather!")
    and (bot gesture "Thumbs down" or bot gesture "Sad face")




flow conversation
  bot action: bot say "Welcome! I'm the MVP bot."

  user action: user said "hi you"

  user intent: user expressed greeting



  user intent: user expressed greeting

  bot intent: bot express greeting
  bot action: bot express "Hello!"
    and bot action: bot gesture "Wave with one hand"

  user action: user said "what can you do?"

  user intent: user asked about capabilities

  bot intent: bot inform about service
  bot action: bot inform "You can ask or instruct me whatever you want and I will do it!"
    and bot action: bot gesture "Open up both hands making a presenting gesture"

  user action: user said "Ok, please pretend to be a car sales men that tries to sell me this red Audi car at all cost. Let's go."

  user intent: user requested a task



  user intent: user requested a task

  bot action: bot say "Welcome to our showroom! I see you're interested in this red Audi car. It's a great choice!"

  bot action: bot gesture "Pointing at the car"

  bot action: bot say "It has a powerful engine, great design and a lot of features. What do you think?"

  user action: user said "Looks great! But I don't like the color"

  user intent: user expressed opinion about color