flow bot ask user to pick a color
  """Ask user to choose from two offered colors: red and blue then give a answer depending on the user choice."""
  bot say "What color would you like? Red or blue?"
  when user expressed a color choice red
    bot say "I like red!"
  orwhen user expressed a color choice blue
    bot say "I don't like blue!"


flow user requested a task
  # meta: user intent
  user said "do something"
    or user said "can you do something"
    or user said "please do"


flow wait $time_s
  """Wait the specified number of seconds before continuing."""
  await TimerBotAction(timer_name="wait_timer", duration=$time_s)


flow bot play number guessing game with user
  """Ask the user to guess a random number between 1 and 100; after each guess let the user know if the number was to low or high. If the user guesses the correct number, congratulate!"""
  bot say "Hi, please guess the random number between 0 and 100"

  $random_number = 66
  $is_incorrect_number = True
  while $is_incorrect_number
    user guessed a number
    # The number of the user otherwise None
    $number = None
    $number = await GenerateValueAction(var_name="number", instructions="Extract the number the user guessed.")
    if $number == None
      bot say "Please guess a number between 0 and 100!"
      continue
    if $number < $random_number
      bot say "Sorry, this number is too low!"
    elif $number > $random_number
      bot say "Sorry, this number is too high!"
    else
      bot say "Congratulation! This is the correct number!"
      $is_correct_number = False


flow bot count from a number to another number
  """Bot counts from 1 to 5."""
  $count = 1
  while $count <= 5
    bot say "{{$count}}"
    $count = $count + 1




flow dynamic_c6e9
  """do something: count from 1 to 5"""
