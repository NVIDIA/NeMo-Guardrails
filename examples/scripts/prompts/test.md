flow bot inform about service

# meta: bot intent

  bot inform "You can ask or instruct me whatever you want and I will do it!"
    and bot gesture "Open up both hands making a presenting gesture"

flow user expressed a color choice
  """The user expressed a color choice."""
  user said "blue"
    or user said "red"
    or user said "I take the green option"
    or user said "I like black"

flow user expressed greeting

# meta: user intent

  user said "hi"
    or user said "Welcome!"
    or user said "Hello!"

flow user asked how are you

# meta: user intent

  user said "how are you"

flow user provided custom instructions

# meta: user intent

  user said "do something"
    or user said "can you do something"
    or user said "please do"

flow conversation
  bot say "Welcome! I'm the MVP bot."
  user said "hi"
  user expressed greeting
  bot express greeting
  bot express "Welcome!"
    and bot gesture "Wave with one hand"
  user said "how are you"
  user asked how are you
  bot express feeling well
  bot express "I am great!"
    and bot express "I am great!"
    and bot gesture "Thumbs up"
  user said "sdfsdf"
