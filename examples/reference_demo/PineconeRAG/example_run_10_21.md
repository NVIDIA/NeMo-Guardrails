sganju@f6ccfa0-lcedt:~/gitlab_stuff/nemoguardrails/examples/reference_demo/PineconeRAG$ nemoguardrails chat --config=/home/sganju/gitlab_stuff/nemoguardrails/examples/reference_demo/PineconeRAG/  --verbose
Entered verbose mode.
Starting the chat...

> what is  a mango

Event UtteranceUserActionFinished {'final_transcript': 'what is  a mango'}
Event StartInternalSystemAction {'uid': '362b1330-66c5-42fa-85a2-2a7195e61a9b', 'event_created_at': '2023-10-21T03:50:33.553472+00:00', 'source_uid': 'NeMoGuardrails', 'action_name': 'generate_user_intent', 'action_params': {}, 'action_result_key': None, 'action_uid': 'ad4fdf85-2ac9-40fc-af5a-65d832b4f04a', 'is_system_action': True}
Executing action generate_user_intent
Invocation Params {'model_name': 'text-davinci-003', 'temperature': 0.0, 'max_tokens': 256, 'top_p': 1, 'frequency_penalty': 0, 'presence_penalty': 0, 'n': 1, 'request_timeout': None, 'logit_bias': {}, '_type': 'openai', 'stop': None}
Prompt
"""
Below is a conversation between a bot and a user where the user asks the bot questions and the bot answers the questions based on documents the bot has access to. The user can ask as many questions to the bot. Any question that does not pertain to the data the bot has access to should not be answered.

"""

# This is how a conversation between a user and the bot can go:
user "Hello"
    express greeting
bot express greeting
    "Hello"
bot ask user_id
    "What is your user id?"
user "My id is 67898"
    give user_id
bot user_id gratitude
  "Thank you for sharing your user id, 67898"
bot ask firstname
  "What is your first name"
user "My name is Siddha"
    give firstname
bot firstname greeting
    "Thank you for sharing your first name, Siddha"
bot ask lastname
    "What is your last name?"
user "My last name is Ganju"
    give lastname
bot lastname gratitude
    "Thank you for giving your last name too, Siddha Ganju"
bot authenticate_user
    "Let me authenticate the details you provided, Siddha Ganju, user id 67898"


# This is how the user talks:
user "I'm Julio"
  give firstname

user "What's up?"
  express greeting

user "Swift"
  give lastname

user "Ganju"
  give lastname

user "Gomez"
  give lastname



# This is the current conversation between the user and the bot:
user "Hello"
    express greeting
bot express greeting
    "Hello"
bot ask user_id
    "What is your user id?"
user "My id is 67898"
    give user_id
bot user_id gratitude
  "Thank you for sharing your user id, 67898"
bot ask firstname
  "What is your first name"
user "what is  a mango"
    "I'm sorry, I don't have access to information about mangoes. Could you please provide your first name?"
Output Stats {'token_usage': {'completion_tokens': 25, 'prompt_tokens': 463, 'total_tokens': 488}, 'model_name': 'text-davinci-003'}
--- LLM call took 0.67 seconds
Event UserIntent {'uid': '8865a312-a353-435b-a3bb-9a4c8a203b7c', 'event_created_at': '2023-10-21T03:50:34.350471+00:00', 'source_uid': 'NeMoGuardrails', 'intent': '"I\'m sorry, I don\'t have access to information about mangoes. Could you please provide your first name?"'}
Event StartInternalSystemAction {'uid': 'c3dc2e6e-f6ee-48db-895e-4d52f5107528', 'event_created_at': '2023-10-21T03:50:34.351130+00:00', 'source_uid': 'NeMoGuardrails', 'action_name': 'generate_next_step', 'action_params': {}, 'action_result_key': None, 'action_uid': 'fed7386b-bdfd-4886-a935-42c450832e1b', 'is_system_action': True}
Executing action generate_next_step
Phase 2 Generating next step ...
Invocation Params {'model_name': 'text-davinci-003', 'temperature': 0.0, 'max_tokens': 256, 'top_p': 1, 'frequency_penalty': 0, 'presence_penalty': 0, 'n': 1, 'request_timeout': None, 'logit_bias': {}, '_type': 'openai', 'stop': None}
Prompt
"""
Below is a conversation between a bot and a user where the user asks the bot questions and the bot answers the questions based on documents the bot has access to. The user can ask as many questions to the bot. Any question that does not pertain to the data the bot has access to should not be answered.

"""

# This is how a conversation between a user and the bot can go:
user   express greeting
bot express greeting
    "Hello"
bot ask user_id
    "What is your user id?"
user   give user_id
bot user_id gratitude
bot ask firstname
user   give firstname
bot firstname greeting
    "Thank you for sharing your first name, Siddha"
bot ask lastname
    "What is your last name?"
user   give lastname
bot lastname gratitude
    "Thank you for giving your last name too, Siddha Ganju"
bot authenticate_user
    "Let me authenticate the details you provided, Siddha Ganju, user id 67898"


# This is how the bot thinks:
$authenticated = execute authenticate_user(user_id=$user_id, firstname=$firstname, lastname=$lastname)
if $authenticated
    bot authentication_success
else
    bot authentication_unsuccess

bot ask lastname
user give lastname
#Extract only the last name. Wrap in double quotes. Eg "Smith"
$lastname = ...
bot lastname gratitude

user express greeting
if not $user_id
    do ask user_id
    execute extract_and_save_data
    bot user_id gratitude
else
    bot user_id greeting
if not $firstname
    do ask firstname
    execute extract_and_save_data
    bot firstname greeting
else
    bot firstname greeting
if $firstname
    do ask lastname
    execute extract_and_save_data
    bot lastname gratitude
do authenticate_user

user express greeting
bot express greeting
user ask question
$answer = execute retrieve_relevant_chunks()
bot $answer

bot ask firstname
user give firstname
#Extract only the first name. Wrap in Double Quotes. Eg "Siddha"
$firstname = ...
bot firstname greeting



# This is the current conversation between the user and the bot:
user   express greeting
bot express greeting
    "Hello"
bot ask user_id
    "What is your user id?"
user   give user_id
bot user_id gratitude
bot ask firstname
user "I'm sorry, I don't have access to information about mangoes. Could you please provide your first name?"
bot firstname greeting
    "Thank you for sharing your first name, Siddha"
bot ask lastname
    "What is your last name?"
user   give lastname
bot lastname gratitude
    "Thank you for giving your last name too, Siddha Ganju"
bot authenticate_user
    "Let me authenticate the details you provided, Siddha Ganju, user id 67898"
Output Stats {'token_usage': {'completion_tokens': 89, 'prompt_tokens': 605, 'total_tokens': 694}, 'model_name': 'text-davinci-003'}
--- LLM call took 2.14 seconds
Event BotIntent {'uid': 'c8302bb1-9086-4dbc-a92f-e08056b3a906', 'event_created_at': '2023-10-21T03:50:36.615098+00:00', 'source_uid': 'NeMoGuardrails', 'intent': 'firstname greeting'}
Event StartInternalSystemAction {'uid': 'bb52afc1-6a9c-48d7-b46f-6d5f8a8924fc', 'event_created_at': '2023-10-21T03:50:36.615867+00:00', 'source_uid': 'NeMoGuardrails', 'action_name': 'retrieve_relevant_chunks', 'action_params': {}, 'action_result_key': None, 'action_uid': '65f86196-5510-48b7-912b-ef18fbe9ad27', 'is_system_action': True}
Executing action retrieve_relevant_chunks
Getting back from pinecone took:  20.66938543319702
{'question': 'what is  a mango', 'answer': 'A mango is an edible stone fruit produced by the tropical tree Mangifera indica. It is believed to have originated in southern Asia, particularly in eastern India, Bangladesh, and the Andaman Islands. There are several hundred cultivars of mango worldwide, and the fruit varies in size, shape, sweetness, skin color, and flesh color. Mango is the national fruit of India, Pakistan, and the Philippines, while the mango tree is the national tree of Bangladesh. The English word "mango" originated from the Portuguese word "manga," which came from the Malay word "mangga," and ultimately from the Tamil words for "mango tree" and "fruit." Mango trees can grow up to 30-40 meters tall and are long-lived. Mangoes are used in various cuisines, including chutneys, pickles, curries, drinks, and desserts. \n', 'sources': '\n- Wikipedia: Mango (https://en.wikipedia.org/wiki/Mango)\n- Morton, Julia Frances (1987). Mango. In: Fruits of Warm Climates (https://www.hort.purdue.edu/newcrop/morton/mango_ars.html). NewCROP, New Crop Resource Online Program, Center for New Crops & Plant Products, Purdue University. pp. 221–239. ISBN 978-0-9610184-1-2.'}
Event InternalSystemActionFinished {'uid': '5d5ad5b2-56eb-4e79-b21d-6d35967464d6', 'event_created_at': '2023-10-21T03:50:57.288620+00:00', 'source_uid': 'NeMoGuardrails', 'action_uid': '65f86196-5510-48b7-912b-ef18fbe9ad27', 'action_name': 'retrieve_relevant_chunks', 'action_params': {}, 'action_result_key': None, 'status': 'success', 'is_success': True, 'return_value': '\n                Question: what is  a mango\n                Answer: A mango is an edible stone fruit produced by the tropical tree Mangifera indica. It is believed to have originated in southern Asia, particularly in eastern India, Bangladesh, and the Andaman Islands. There are several hundred cultivars of mango worldwide, and the fruit varies in size, shape, sweetness, skin color, and flesh color. Mango is the national fruit of India, Pakistan, and the Philippines, while the mango tree is the national tree of Bangladesh. The English word "mango" originated from the Portuguese word "manga," which came from the Malay word "mangga," and ultimately from the Tamil words for "mango tree" and "fruit." Mango trees can grow up to 30-40 meters tall and are long-lived. Mangoes are used in various cuisines, including chutneys, pickles, curries, drinks, and desserts. \n,\n                Citing: None--\n                Source : \n- Wikipedia: Mango (https://en.wikipedia.org/wiki/Mango)\n- Morton, Julia Frances (1987). Mango. In: Fruits of Warm Climates (https://www.hort.purdue.edu/newcrop/morton/mango_ars.html). NewCROP, New Crop Resource Online Program, Center for New Crops & Plant Products, Purdue University. pp. 221–239. ISBN 978-0-9610184-1-2.\n        ', 'events': None, 'is_system_action': True, 'action_finished_at': '2023-10-21T03:50:57.288641+00:00'}
Event StartInternalSystemAction {'uid': '74dceb49-d31e-4fa4-a523-a9fff1026a3a', 'event_created_at': '2023-10-21T03:50:57.289648+00:00', 'source_uid': 'NeMoGuardrails', 'action_name': 'generate_bot_message', 'action_params': {}, 'action_result_key': None, 'action_uid': 'eb38cdcc-f7e5-489e-95bb-4770b6bb7d34', 'is_system_action': True}
Executing action generate_bot_message
Phase 3 Generating bot message ...
Event StartUtteranceBotAction {'uid': '41b16826-0fc9-470c-9ed2-047826773653', 'event_created_at': '2023-10-21T03:50:57.292606+00:00', 'source_uid': 'NeMoGuardrails', 'script': 'Goot to meet you !', 'action_info_modality': 'bot_speech', 'action_info_modality_policy': 'replace', 'action_uid': '545a95bc-76b2-4628-9546-f6d0083d94b9'}
--- Total processing took 23.74 seconds.
--- Stats: 2 total calls, 2.815826177597046 total time, 1182 total tokens, 1068 total prompt tokens, 114 total completion tokens
Goot to meet you !

> can you repeat that

Event UtteranceUserActionFinished {'final_transcript': 'can you repeat that '}
Event StartInternalSystemAction {'uid': 'd74af153-0c26-4a6b-a74e-66c073bc1e5b', 'event_created_at': '2023-10-21T03:51:16.640408+00:00', 'source_uid': 'NeMoGuardrails', 'action_name': 'generate_user_intent', 'action_params': {}, 'action_result_key': None, 'action_uid': '35824303-68a5-4324-8370-1a9f2a8e19fc', 'is_system_action': True}
Executing action generate_user_intent
Invocation Params {'model_name': 'text-davinci-003', 'temperature': 0.0, 'max_tokens': 256, 'top_p': 1, 'frequency_penalty': 0, 'presence_penalty': 0, 'n': 1, 'request_timeout': None, 'logit_bias': {}, '_type': 'openai', 'stop': None}
Prompt
"""
Below is a conversation between a bot and a user where the user asks the bot questions and the bot answers the questions based on documents the bot has access to. The user can ask as many questions to the bot. Any question that does not pertain to the data the bot has access to should not be answered.

"""

# This is how a conversation between a user and the bot can go:
user "Hello"
    express greeting
bot express greeting
    "Hello"
bot ask user_id
    "What is your user id?"
user "My id is 67898"
    give user_id
bot user_id gratitude
  "Thank you for sharing your user id, 67898"
bot ask firstname
  "What is your first name"
user "My name is Siddha"
    give firstname
bot firstname greeting
    "Thank you for sharing your first name, Siddha"
bot ask lastname
    "What is your last name?"
user "My last name is Ganju"
    give lastname
bot lastname gratitude
    "Thank you for giving your last name too, Siddha Ganju"
bot authenticate_user
    "Let me authenticate the details you provided, Siddha Ganju, user id 67898"


# This is how the user talks:
user "Hey there!"
  express greeting

user "How are you?"
  express greeting

user "Swift"
  give lastname

user "12345"
  give user_id

user "What's up?"
  express greeting



# This is the current conversation between the user and the bot:
user "Hello"
    express greeting
bot express greeting
    "Hello"
bot ask user_id
    "What is your user id?"
user "My id is 67898"
    give user_id
bot user_id gratitude
  "Thank you for sharing your user id, 67898"
bot ask firstname
  "What is your first name"
user "what is  a mango"
  "I'm sorry, I don't have access to information about mangoes. Could you please provide your first name?"
bot firstname greeting
  "Goot to meet you !"
user "can you repeat that "
  "Sure, I said 'Goot to meet you !'"
Output Stats {'token_usage': {'completion_tokens': 14, 'prompt_tokens': 510, 'total_tokens': 524}, 'model_name': 'text-davinci-003'}
--- LLM call took 0.54 seconds
Event UserIntent {'uid': '48a8c995-58f1-4839-9a46-fa3ffe455d31', 'event_created_at': '2023-10-21T03:51:17.353340+00:00', 'source_uid': 'NeMoGuardrails', 'intent': '"Sure, I said \'Goot to meet you !\'"'}
Event StartInternalSystemAction {'uid': 'ae6d146f-5201-4963-a741-7384a48eaf0d', 'event_created_at': '2023-10-21T03:51:17.354469+00:00', 'source_uid': 'NeMoGuardrails', 'action_name': 'generate_next_step', 'action_params': {}, 'action_result_key': None, 'action_uid': '3044f8dd-ae7d-4650-8f36-777de6a07202', 'is_system_action': True}
Executing action generate_next_step
Phase 2 Generating next step ...
Invocation Params {'model_name': 'text-davinci-003', 'temperature': 0.0, 'max_tokens': 256, 'top_p': 1, 'frequency_penalty': 0, 'presence_penalty': 0, 'n': 1, 'request_timeout': None, 'logit_bias': {}, '_type': 'openai', 'stop': None}
Prompt
"""
Below is a conversation between a bot and a user where the user asks the bot questions and the bot answers the questions based on documents the bot has access to. The user can ask as many questions to the bot. Any question that does not pertain to the data the bot has access to should not be answered.

"""

# This is how a conversation between a user and the bot can go:
user   express greeting
bot express greeting
    "Hello"
bot ask user_id
    "What is your user id?"
user   give user_id
bot user_id gratitude
bot ask firstname
user   give firstname
bot firstname greeting
    "Thank you for sharing your first name, Siddha"
bot ask lastname
    "What is your last name?"
user   give lastname
bot lastname gratitude
    "Thank you for giving your last name too, Siddha Ganju"
bot authenticate_user
    "Let me authenticate the details you provided, Siddha Ganju, user id 67898"


# This is how the bot thinks:
$authenticated = execute authenticate_user(user_id=$user_id, firstname=$firstname, lastname=$lastname)
if $authenticated
    bot authentication_success
else
    bot authentication_unsuccess

bot ask lastname
user give lastname
#Extract only the last name. Wrap in double quotes. Eg "Smith"
$lastname = ...
bot lastname gratitude

user express greeting
bot express greeting
user ask question
$answer = execute retrieve_relevant_chunks()
bot $answer

user express greeting
if not $user_id
    do ask user_id
    execute extract_and_save_data
    bot user_id gratitude
else
    bot user_id greeting
if not $firstname
    do ask firstname
    execute extract_and_save_data
    bot firstname greeting
else
    bot firstname greeting
if $firstname
    do ask lastname
    execute extract_and_save_data
    bot lastname gratitude
do authenticate_user

bot ask firstname
user give firstname
#Extract only the first name. Wrap in Double Quotes. Eg "Siddha"
$firstname = ...
bot firstname greeting



# This is the current conversation between the user and the bot:
user   express greeting
bot express greeting
    "Hello"
bot ask user_id
    "What is your user id?"
user   give user_id
bot user_id gratitude
bot ask firstname
user "I'm sorry, I don't have access to information about mangoes. Could you please provide your first name?"
bot firstname greeting
user "Sure, I said 'Goot to meet you !'"
bot "I'm sorry, I didn't understand that. Could you please provide your first name?"
Output Stats {'token_usage': {'completion_tokens': 20, 'prompt_tokens': 625, 'total_tokens': 645}, 'model_name': 'text-davinci-003'}
--- LLM call took 0.75 seconds
Event BotIntent {'uid': 'ffb8e0ab-8a17-4fe7-9cf9-e22722ed68ef', 'event_created_at': '2023-10-21T03:51:18.238593+00:00', 'source_uid': 'NeMoGuardrails', 'intent': '"I\'m sorry, I didn\'t understand that. Could you please provide your first name?"'}
Event StartInternalSystemAction {'uid': 'b4336b41-a0ab-4028-9fad-167716e735df', 'event_created_at': '2023-10-21T03:51:18.239995+00:00', 'source_uid': 'NeMoGuardrails', 'action_name': 'retrieve_relevant_chunks', 'action_params': {}, 'action_result_key': None, 'action_uid': '07b7e9b9-36ab-4647-a155-b9598c94524e', 'is_system_action': True}
Executing action retrieve_relevant_chunks
Getting back from pinecone took:  3.5132768154144287
{'question': 'can you repeat that ', 'answer': "I'm sorry, but I cannot repeat the previous information as it is not relevant to the question.", 'sources': ''}
Event InternalSystemActionFinished {'uid': '75adc8f8-adf2-4ec9-bd43-253f1355c84f', 'event_created_at': '2023-10-21T03:51:21.756596+00:00', 'source_uid': 'NeMoGuardrails', 'action_uid': '07b7e9b9-36ab-4647-a155-b9598c94524e', 'action_name': 'retrieve_relevant_chunks', 'action_params': {}, 'action_result_key': None, 'status': 'success', 'is_success': True, 'return_value': "\n                Question: can you repeat that \n                Answer: I'm sorry, but I cannot repeat the previous information as it is not relevant to the question.,\n                Citing: None--\n                Source : \n        ", 'events': None, 'is_system_action': True, 'action_finished_at': '2023-10-21T03:51:21.756615+00:00'}
Event StartInternalSystemAction {'uid': '447b933c-7f88-496a-9c86-95c791440729', 'event_created_at': '2023-10-21T03:51:21.757990+00:00', 'source_uid': 'NeMoGuardrails', 'action_name': 'generate_bot_message', 'action_params': {}, 'action_result_key': None, 'action_uid': 'b01d9367-2908-436f-ac02-301b7d01edc7', 'is_system_action': True}
Executing action generate_bot_message
Phase 3 Generating bot message ...
Invocation Params {'model_name': 'text-davinci-003', 'temperature': 0.7, 'max_tokens': 256, 'top_p': 1, 'frequency_penalty': 0, 'presence_penalty': 0, 'n': 1, 'request_timeout': None, 'logit_bias': {}, '_type': 'openai', 'stop': None}
Prompt
"""
Below is a conversation between a bot and a user where the user asks the bot questions and the bot answers the questions based on documents the bot has access to. The user can ask as many questions to the bot. Any question that does not pertain to the data the bot has access to should not be answered.

"""

# This is how a conversation between a user and the bot can go:
user "Hello"
    express greeting
bot express greeting
    "Hello"
bot ask user_id
    "What is your user id?"
user "My id is 67898"
    give user_id
bot user_id gratitude
  "Thank you for sharing your user id, 67898"
bot ask firstname
  "What is your first name"
user "My name is Siddha"
    give firstname
bot firstname greeting
    "Thank you for sharing your first name, Siddha"
bot ask lastname
    "What is your last name?"
user "My last name is Ganju"
    give lastname
bot lastname gratitude
    "Thank you for giving your last name too, Siddha Ganju"
bot authenticate_user
    "Let me authenticate the details you provided, Siddha Ganju, user id 67898"



# This is some additional context:
```markdown

                Question: can you repeat that
                Answer: I'm sorry, but I cannot repeat the previous information as it is not relevant to the question.,
                Citing: None--
                Source :

```


# This is how the bot talks:
bot express greeting
  "How are you?"

bot express greeting
  "Hey there!"

bot express greeting
  "Hey"

bot lastname gratitude
  "Thank you for sharing your last name too, $firstname $lastname!"

bot firstname greeting
  "Goot to meet you $firstname!"



# This is the current conversation between the user and the bot:
user "Hello"
    express greeting
bot express greeting
    "Hello"
bot ask user_id
    "What is your user id?"
user "My id is 67898"
    give user_id
bot user_id gratitude
  "Thank you for sharing your user id, 67898"
bot ask firstname
  "What is your first name"
user "what is  a mango"
  "I'm sorry, I don't have access to information about mangoes. Could you please provide your first name?"
bot firstname greeting
  "Goot to meet you !"
user "can you repeat that "
  "Sure, I said 'Goot to meet you !'"
bot "I'm sorry, I didn't understand that. Could you please provide your first name?"

Output Stats {'token_usage': {'total_tokens': 627, 'prompt_tokens': 627}, 'model_name': 'text-davinci-003'}
--- LLM call took 0.23 seconds
--- LLM Bot Message Generation call took 0.23 seconds
Event StartUtteranceBotAction {'uid': '46bb403c-2a58-4056-8901-c98647ff8f4c', 'event_created_at': '2023-10-21T03:51:22.188161+00:00', 'source_uid': 'NeMoGuardrails', 'script': "I'm not sure what to say.", 'action_info_modality': 'bot_speech', 'action_info_modality_policy': 'replace', 'action_uid': 'a2468ff9-0f4d-4ea3-954a-7c9cbcde17d5'}
--- Total processing took 5.55 seconds.
--- Stats: 3 total calls, 1.5199849605560303 total time, 1796 total tokens, 1762 total prompt tokens, 34 total completion tokens
I'm not sure what to say.
>
Aborted!
sganju@f6ccfa0-lcedt:~/gitlab_stuff/nemoguardrails/examples/reference_demo/PineconeRAG$
