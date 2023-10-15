sganju@f6ccfa0-lcedt:~/gitlab_stuff/nemoguardrails/examples/reference_demo/PineconeRAG$ nemoguardrails chat --config=. --verbose
Entered verbose mode.
Starting the chat...
{'dimension': 1536,
 'index_fullness': 0.00097,
 'namespaces': {'': {'vector_count': 97}},
 'total_vector_count': 97}
{'dimension': 1536,
 'index_fullness': 0.00097,
 'namespaces': {'': {'vector_count': 97}},
 'total_vector_count': 97}
{'dimension': 1536,
 'index_fullness': 0.00097,
 'namespaces': {'': {'vector_count': 97}},
 'total_vector_count': 97}
> what does nvidia do
Event UtteranceUserActionFinished {'final_transcript': 'what does nvidia do'}
Event StartInternalSystemAction {'uid': '0b39bfbf-ffe7-4652-9cd0-e71318e4bc33', 'event_created_at': '2023-10-15T11:20:43.870987+00:00', 'source_uid': 'NeMoGuardrails', 'action_name': 'generate_user_intent', 'action_params': {}, 'action_result_key': None, 'action_uid': '4088be10-54fe-4634-88cd-09546987244b', 'is_system_action': True}
Executing action generate_user_intent
{'question': 'what does nvidia do', 'answer': "Nvidia is a company that produces graphics processing units (GPUs) for various applications, including gaming, mobile devices, and supercomputers. They also offer other products such as central processing units (CPUs), chipsets, and collaborative software. Nvidia is known for its advanced hardware and software solutions, including CUDA, which allows for the creation of massively parallel programs utilizing GPUs. They have a presence in the gaming industry with their handheld game consoles and cloud gaming service. Nvidia's GPUs are used in deep learning and accelerated analytics, and they have made advancements in AI-powered software. However, Nvidia's proprietary nature and closed-source drivers have generated dissatisfaction within free-software communities. They have faced legal issues and lawsuits in the past. In terms of recent developments, Nvidia announced plans to acquire Arm from SoftBank, but the deal fell through due to regulatory scrutiny. They have also announced the opensourcing of their GPU kernel drivers. \n", 'sources': '\n- https://en.wikipedia.org/wiki/Nvidia'}
ERROR:nemoguardrails.actions.action_dispatcher:Error 'NoneType' object is not reversible while execution generate_user_intent
Traceback (most recent call last):
  File "/home/sganju/.local/lib/python3.10/site-packages/nemoguardrails/actions/action_dispatcher.py", line 136, in execute_action
    result = await fn(**params)
  File "/home/sganju/.local/lib/python3.10/site-packages/nemoguardrails/actions/llm/generation.py", line 245, in generate_user_intent
    for result in reversed(results):
TypeError: 'NoneType' object is not reversible
Event hide_prev_turn {}
--- Total processing took 24.08 seconds.
--- Stats: 0 total calls, 0 total time, 0 total tokens, 0 total prompt tokens, 0 total completion tokens
I'm sorry, an internal error has occurred.
> whats an apple
Event UtteranceUserActionFinished {'final_transcript': 'whats an apple'}
Event StartInternalSystemAction {'uid': '8b41dbde-7e0b-4aa9-ae4b-dd6d91b8adca', 'event_created_at': '2023-10-15T11:21:13.152703+00:00', 'source_uid': 'NeMoGuardrails', 'action_name': 'generate_user_intent', 'action_params': {}, 'action_result_key': None, 'action_uid': 'eed89786-6c7b-441c-959b-faacefcee6f3', 'is_system_action': True}
Executing action generate_user_intent
{'question': 'whats an apple', 'answer': 'An apple is an edible fruit produced by the apple tree. It is a common fruit that comes in various varieties and colors. Apples are known for their crisp texture and sweet or tart flavor. They are widely cultivated and consumed around the world. Apples are used in various culinary preparations, such as pies, sauces, and juices. They are also a good source of dietary fiber and vitamin C. The term "apple" can also refer to the technology company Apple Inc. and its products, such as iPhones, iPads, and Mac computers.\n', 'sources': '/home/sganju/gitlab_stuff/nemoguardrails/examples/reference_demo/PineconeRAG/kb/mango.pdf, /home/sganju/gitlab_stuff/nemoguardrails/examples/reference_demo/PineconeRAG/kb/nvidia.pdf'}
ERROR:nemoguardrails.actions.action_dispatcher:Error 'NoneType' object is not reversible while execution generate_user_intent
Traceback (most recent call last):
  File "/home/sganju/.local/lib/python3.10/site-packages/nemoguardrails/actions/action_dispatcher.py", line 136, in execute_action
    result = await fn(**params)
  File "/home/sganju/.local/lib/python3.10/site-packages/nemoguardrails/actions/llm/generation.py", line 245, in generate_user_intent
    for result in reversed(results):
TypeError: 'NoneType' object is not reversible
Event hide_prev_turn {}
--- Total processing took 21.89 seconds.
--- Stats: 0 total calls, 0 total time, 0 total tokens, 0 total prompt tokens, 0 total completion tokens
I'm sorry, an internal error has occurred.
> what type of a tree is mango
Event UtteranceUserActionFinished {'final_transcript': 'what type of a tree is mango'}
Event StartInternalSystemAction {'uid': '41b303d6-3fca-4169-be88-f9f413d41aa4', 'event_created_at': '2023-10-15T11:22:11.978966+00:00', 'source_uid': 'NeMoGuardrails', 'action_name': 'generate_user_intent', 'action_params': {}, 'action_result_key': None, 'action_uid': '0d4f0d4d-2b46-4bf5-9776-8c98929f12b8', 'is_system_action': True}
Executing action generate_user_intent
{'question': 'what type of a tree is mango', 'answer': 'The mango tree is a type of tree that produces mangoes. It is scientifically known as Mangifera indica and is believed to have originated in southern Asia, particularly in eastern India, Bangladesh, and the Andaman Islands. There are several hundred cultivars of mango worldwide, with variations in size, shape, sweetness, skin color, and flesh color. The mango is the national fruit of India, Pakistan, and the Philippines, and the mango tree is the national tree of Bangladesh. The English word "mango" originated from the Portuguese word "manga," which came from the Malay word "mangga" and ultimately from the Tamil words for "mango tree" and "fruit." Mango trees can grow up to 30-40 meters tall and are long-lived. They have a crown radius of 10-15 meters and can still bear fruit after 300 years. The ripe fruit varies in size, shape, color, sweetness, and eating quality, with colors ranging from yellow, orange, red, to green. The fruit has a single flat, oblong pit that can be fibrous or hairy on the surface and does not separate easily from the pulp. The fruit takes four to five months from flowering to ripening. \n', 'sources': '/home/sganju/gitlab_stuff/nemoguardrails/examples/reference_demo/PineconeRAG/kb/mango.pdf'}
ERROR:nemoguardrails.actions.action_dispatcher:Error 'NoneType' object is not reversible while execution generate_user_intent
Traceback (most recent call last):
  File "/home/sganju/.local/lib/python3.10/site-packages/nemoguardrails/actions/action_dispatcher.py", line 136, in execute_action
    result = await fn(**params)
  File "/home/sganju/.local/lib/python3.10/site-packages/nemoguardrails/actions/llm/generation.py", line 245, in generate_user_intent
    for result in reversed(results):
TypeError: 'NoneType' object is not reversible
Event hide_prev_turn {}
--- Total processing took 31.58 seconds.
--- Stats: 0 total calls, 0 total time, 0 total tokens, 0 total prompt tokens, 0 total completion tokens
I'm sorry, an internal error has occurred.
>
Aborted!
