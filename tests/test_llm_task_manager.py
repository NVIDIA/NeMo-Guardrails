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

import textwrap

import pytest

from nemoguardrails import RailsConfig
from nemoguardrails.llm.taskmanager import LLMTaskManager
from nemoguardrails.llm.types import Task
from nemoguardrails.llm.prompts import get_prompt


def test_openai_text_davinci_prompts():
    """Test the prompts for the OpenAI text-davinci-003 model."""
    config = RailsConfig.from_content(
        yaml_content=textwrap.dedent(
            """
            models:
             - type: main
               engine: openai
               model: text-davinci-003
            """
        )
    )

    assert config.models[0].engine == "openai"

    llm_task_manager = LLMTaskManager(config)

    generate_user_intent_prompt = llm_task_manager.render_task_prompt(
        task=Task.GENERATE_USER_INTENT
    )

    assert isinstance(generate_user_intent_prompt, str)
    assert "This is how the user talks" in generate_user_intent_prompt


@pytest.mark.parametrize(
    "task",
    [
        Task.GENERATE_USER_INTENT,
        Task.GENERATE_NEXT_STEPS,
        Task.GENERATE_BOT_MESSAGE,
        Task.GENERATE_VALUE,
    ],
)
def test_openai_gpt_3_5_turbo_prompts(task):
    """Test the prompts for the OpenAI GPT-3 5 Turbo model."""
    config = RailsConfig.from_content(
        yaml_content=textwrap.dedent(
            """
            models:
             - type: main
               engine: openai
               model: gpt-3.5-turbo
            """
        )
    )

    assert config.models[0].engine == "openai"

    llm_task_manager = LLMTaskManager(config)

    task_prompt = llm_task_manager.render_task_prompt(
        task=task,
        context={"examples": 'user "Hello there!"\n  express greeting'},
    )

    assert isinstance(task_prompt, list)


@pytest.mark.parametrize(
    "task, expected_prompt",
    [
        ("summarize_text", "Text: test.\nSummarize the above text."),
        ("compose_response", "Text: test.\nCompose a response using the above text."),
    ],
)
def test_custom_task_prompts(task, expected_prompt):
    """Test the prompts for the OpenAI GPT-3 5 Turbo model with custom
    prompts for custom tasks."""
    config = RailsConfig.from_content(
        yaml_content=textwrap.dedent(
            """
            models:
             - type: main
               engine: openai
               model: gpt-3.5-turbo
            prompts:
            - task: summarize_text
              content: |-
                  Text: {{ user_input }}
                  Summarize the above text.
            - task: compose_response
              content: |-
                  Text: {{ user_input }}
                  Compose a response using the above text.
            """
        )
    )

    assert config.models[0].engine == "openai"

    llm_task_manager = LLMTaskManager(config)

    user_input = "test."
    task_prompt = llm_task_manager.render_task_prompt(
        task=task,
        context={"user_input": user_input},
    )

    assert task_prompt == expected_prompt

def test_prompt_length_exceeded_empty_events():
    """Test the prompts for the OpenAI GPT-3 5 Turbo model."""
    config = RailsConfig.from_content(
        yaml_content=textwrap.dedent(
            """
            models:
             - type: main
               engine: openai
               model: text-davinci-003
            prompts:
            - task: generate_user_intent
              max_length: 2000
              content: |-
                
                {{ general_instruction }}
                
                # This is how a conversation between a user and the bot can go:
                {{ sample_conversation }}

                # This is how the user talks:
                {{ examples }}

                # This is the current conversation between the user and the bot:
                {{ sample_conversation | first_turns(2) }}
                {{ history | colang }}
                    )
                )"""))

    assert config.models[0].engine == "openai"
    llm_task_manager = LLMTaskManager(config)

    with pytest.raises(Exception):
        generate_user_intent_prompt = llm_task_manager.render_task_prompt(
            task=Task.GENERATE_USER_INTENT,
            context={"examples": 'user "Hello there!"\n  express greeting'},
            events=[]
        )

def test_prompt_length_exceeded_compressed_history():
    """Test the prompts for the OpenAI GPT-3 5 Turbo model."""
    config = RailsConfig.from_content(
        yaml_content=textwrap.dedent(
            """
            models:
             - type: main
               engine: openai
               model: text-davinci-003
            prompts:
            - task: generate_user_intent
              max_length: 3000
              content: |-
                
                {{ general_instruction }}
                
                # This is how a conversation between a user and the bot can go:
                {{ sample_conversation }}

                # This is how the user talks:
                {{ examples }}

                # This is the current conversation between the user and the bot:
                {{ sample_conversation | first_turns(2) }}
                {{ history | colang }}
                    )
                )"""))

    max_task_prompt_length = get_prompt(config, Task.GENERATE_USER_INTENT).max_length
    assert config.models[0].engine == "openai"
    llm_task_manager = LLMTaskManager(config)

    generate_user_intent_prompt = llm_task_manager.render_task_prompt(
        task=Task.GENERATE_USER_INTENT,
        context={"examples": 'user "Hello there!"\n  express greeting'},
        events=[{'type': 'StartInternalSystemAction', 'uid': '68d642d3-88ce-418f-823c-23c2f8e09ee3', 'event_created_at': '2023-10-02T14:47:48.470160+00:00', 'source_uid': 'NeMoGuardrails', 'action_name': 'retrieve_relevant_chunks', 'action_params': {}, 'action_result_key': None, 'action_uid': '9f9fb218-c252-44c1-ac4b-09fa4fc500c4', 'is_system_action': True}, {'type': 'StartInternalSystemAction', 'uid': 'b0ca31b1-1073-4976-aa39-19f2d5e411f8', 'event_created_at': '2023-10-02T14:47:48.483462+00:00', 'source_uid': 'NeMoGuardrails', 'action_name': 'generate_bot_message', 'action_params': {}, 'action_result_key': None, 'action_uid': '4434f746-0a19-4262-8dea-9e833c0f553f', 'is_system_action': True}, {'type': 'ContextUpdate', 'uid': '03166f90-d19e-48e4-b619-ae5dda622ba0', 'event_created_at': '2023-10-02T14:47:51.633418+00:00', 'source_uid': 'NeMoGuardrails', 'data': {}}, {'type': 'InternalSystemActionFinished', 'uid': 'cbda7c33-cf46-4689-b643-ecfe4eb87594', 'event_created_at': '2023-10-02T14:47:51.633468+00:00', 'source_uid': 'NeMoGuardrails', 'action_uid': '4434f746-0a19-4262-8dea-9e833c0f553f', 'action_name': 'generate_bot_message', 'action_params': {}, 'action_result_key': None, 'status': 'success', 'is_success': True, 'return_value': None, 'events': [{'type': 'StartUtteranceBotAction', 'uid': '11e63d5f-2086-430d-b24b-df89f713befc', 'event_created_at': '2023-10-02T14:47:51.633285+00:00', 'source_uid': 'NeMoGuardrails', 'script': 'The unemployment rate in July 2021 was 4.9 percent.', 'action_info_modality': 'bot_speech', 'action_info_modality_policy': 'replace', 'action_uid': '3613fb5f-e27b-4272-9e5f-e76a3651c70b'}], 'is_system_action': True, 'action_finished_at': '2023-10-02T14:47:51.633486+00:00'}, {'type': 'StartUtteranceBotAction', 'uid': '11e63d5f-2086-430d-b24b-df89f713befc', 'event_created_at': '2023-10-02T14:47:51.633285+00:00', 'source_uid': 'NeMoGuardrails', 'script': 'The unemployment rate in July 2021 was 4.9 percent.', 'action_info_modality': 'bot_speech', 'action_info_modality_policy': 'replace', 'action_uid': '3613fb5f-e27b-4272-9e5f-e76a3651c70b'}, {'type': 'Listen', 'uid': 'd52180e9-e35c-42ac-aa90-0488f72b9faa', 'event_created_at': '2023-10-02T14:47:51.635363+00:00', 'source_uid': 'NeMoGuardrails'}, {'type': 'UtteranceUserActionFinished', 'final_transcript': 'i asked for 2023'}, {'type': 'StartInternalSystemAction', 'uid': '24831b23-bb09-4ab2-9461-0d0cb8208790', 'event_created_at': '2023-10-02T14:47:56.182466+00:00', 'source_uid': 'NeMoGuardrails', 'action_name': 'generate_user_intent', 'action_params': {}, 'action_result_key': None, 'action_uid': 'd60f7dce-b53e-4b43-9ef9-2d1e1913e8f2', 'is_system_action': True}, {'type': 'InternalSystemActionFinished', 'uid': 'b1340236-f790-40ff-86c1-d5230d377c57', 'event_created_at': '2023-10-02T14:48:03.302010+00:00', 'source_uid': 'NeMoGuardrails', 'action_uid': 'd60f7dce-b53e-4b43-9ef9-2d1e1913e8f2', 'action_name': 'generate_user_intent', 'action_params': {}, 'action_result_key': None, 'status': 'success', 'is_success': True, 'return_value': None, 'events': [{'type': 'UserIntent', 'uid': '70996fee-d993-4891-b83c-7ccabc305442', 'event_created_at': '2023-10-02T14:48:03.301901+00:00', 'source_uid': 'NeMoGuardrails', 'intent': 'ask about headline numbers'}], 'is_system_action': True, 'action_finished_at': '2023-10-02T14:48:03.302035+00:00'}, {'type': 'UserIntent', 'uid': '70996fee-d993-4891-b83c-7ccabc305442', 'event_created_at': '2023-10-02T14:48:03.301901+00:00', 'source_uid': 'NeMoGuardrails', 'intent': 'ask about headline numbers'}, {'type': 'BotIntent', 'intent': 'response about headline numbers'}, {'type': 'StartInternalSystemAction', 'uid': 'cc1651f7-cd78-464a-adcd-89b71bb27112', 'event_created_at': '2023-10-02T14:48:03.306123+00:00', 'source_uid': 'NeMoGuardrails', 'action_name': 'retrieve_relevant_chunks', 'action_params': {}, 'action_result_key': None, 'action_uid': 'a28d478e-ad57-4155-8b45-6cce1c544ab0', 'is_system_action': True}, {'type': 'StartInternalSystemAction', 'uid': '7dd9ada2-57cc-4c1b-8692-11d70080f28b', 'event_created_at': '2023-10-02T14:48:03.320049+00:00', 'source_uid': 'NeMoGuardrails', 'action_name': 'generate_bot_message', 'action_params': {}, 'action_result_key': None, 'action_uid': '03a83a71-d39a-4548-9b8c-34e297bce3cf', 'is_system_action': True}, {'type': 'ContextUpdate', 'uid': '09c8267e-bca8-4d96-92d7-48bbb40a41fa', 'event_created_at': '2023-10-02T14:48:05.073799+00:00', 'source_uid': 'NeMoGuardrails', 'data': {}}, {'type': 'InternalSystemActionFinished', 'uid': 'ac5c60b4-45bb-4069-99a2-40ca312279b8', 'event_created_at': '2023-10-02T14:48:05.073848+00:00', 'source_uid': 'NeMoGuardrails', 'action_uid': '03a83a71-d39a-4548-9b8c-34e297bce3cf', 'action_name': 'generate_bot_message', 'action_params': {}, 'action_result_key': None, 'status': 'success', 'is_success': True, 'return_value': None, 'events': [{'type': 'StartUtteranceBotAction', 'uid': '1168e4f6-645a-4d63-b96a-36c2031f7734', 'event_created_at': '2023-10-02T14:48:05.073668+00:00', 'source_uid': 'NeMoGuardrails', 'script': 'Sorry, I do not have the unemployment rate for July 2023.', 'action_info_modality': 'bot_speech', 'action_info_modality_policy': 'replace', 'action_uid': '9069bd5d-2ddb-4ce4-a8a5-f17c9bec5c43'}], 'is_system_action': True, 'action_finished_at': '2023-10-02T14:48:05.073866+00:00'}, {'type': 'StartUtteranceBotAction', 'uid': '1168e4f6-645a-4d63-b96a-36c2031f7734', 'event_created_at': '2023-10-02T14:48:05.073668+00:00', 'source_uid': 'NeMoGuardrails', 'script': 'Sorry, I do not have the unemployment rate for July 2023.', 'action_info_modality': 'bot_speech', 'action_info_modality_policy': 'replace', 'action_uid': '9069bd5d-2ddb-4ce4-a8a5-f17c9bec5c43'}, {'type': 'Listen', 'uid': '4719388b-502a-4120-9470-18d243639b18', 'event_created_at': '2023-10-02T14:48:05.076219+00:00', 'source_uid': 'NeMoGuardrails'}, {'type': 'UtteranceUserActionFinished', 'final_transcript': 'ok, no worries'}, {'type': 'StartInternalSystemAction', 'uid': 'a7fbcdd7-53e2-4ae4-b3c1-b8e443a355b1', 'event_created_at': '2023-10-02T14:48:09.507420+00:00', 'source_uid': 'NeMoGuardrails', 'action_name': 'generate_user_intent', 'action_params': {}, 'action_result_key': None, 'action_uid': '4d58f717-17e5-4d74-bedb-3f5119132a18', 'is_system_action': True}, {'type': 'InternalSystemActionFinished', 'uid': '45750eda-6e74-4e6c-821f-07a1968206ff', 'event_created_at': '2023-10-02T14:48:14.761867+00:00', 'source_uid': 'NeMoGuardrails', 'action_uid': '4d58f717-17e5-4d74-bedb-3f5119132a18', 'action_name': 'generate_user_intent', 'action_params': {}, 'action_result_key': None, 'status': 'success', 'is_success': True, 'return_value': None, 'events': [{'type': 'UserIntent', 'uid': '8760aa44-e507-4b7d-b7bb-2c0c7e12cf1e', 'event_created_at': '2023-10-02T14:48:14.761761+00:00', 'source_uid': 'NeMoGuardrails', 'intent': 'express appreciation'}], 'is_system_action': True, 'action_finished_at': '2023-10-02T14:48:14.761891+00:00'}, {'type': 'UserIntent', 'uid': '8760aa44-e507-4b7d-b7bb-2c0c7e12cf1e', 'event_created_at': '2023-10-02T14:48:14.761761+00:00', 'source_uid': 'NeMoGuardrails', 'intent': 'express appreciation'}, {'type': 'StartInternalSystemAction', 'uid': '1b7f2e42-ee72-4883-b4ec-b9f211064a4b', 'event_created_at': '2023-10-02T14:48:14.764301+00:00', 'source_uid': 'NeMoGuardrails', 'action_name': 'generate_next_step', 'action_params': {}, 'action_result_key': None, 'action_uid': '05ec5d83-6231-44f7-b0dc-df2a6ca01e67', 'is_system_action': True}, {'type': 'InternalSystemActionFinished', 'uid': '3da031ba-09dc-4270-aade-7285c6a48c7d', 'event_created_at': '2023-10-02T14:48:16.662875+00:00', 'source_uid': 'NeMoGuardrails', 'action_uid': '05ec5d83-6231-44f7-b0dc-df2a6ca01e67', 'action_name': 'generate_next_step', 'action_params': {}, 'action_result_key': None, 'status': 'success', 'is_success': True, 'return_value': None, 'events': [{'type': 'BotIntent', 'uid': 'e4c65100-a668-4b81-9ad7-fa8670910f02', 'event_created_at': '2023-10-02T14:48:16.662769+00:00', 'source_uid': 'NeMoGuardrails', 'intent': 'express appreciation and offer additional help'}], 'is_system_action': True, 'action_finished_at': '2023-10-02T14:48:16.662900+00:00'}, {'type': 'BotIntent', 'uid': 'e4c65100-a668-4b81-9ad7-fa8670910f02', 'event_created_at': '2023-10-02T14:48:16.662769+00:00', 'source_uid': 'NeMoGuardrails', 'intent': 'express appreciation and offer additional help'}, {'type': 'StartInternalSystemAction', 'uid': '4c8fd64b-a1f0-40aa-9d17-7547948daafe', 'event_created_at': '2023-10-02T14:48:16.679846+00:00', 'source_uid': 'NeMoGuardrails', 'action_name': 'generate_bot_message', 'action_params': {}, 'action_result_key': None, 'action_uid': '1bdce6ce-80e3-42b6-a2db-5977fc07dcfd', 'is_system_action': True}, {'type': 'ContextUpdate', 'uid': 'fe5fbf1b-c090-42fe-9e2d-193f1355d7c8', 'event_created_at': '2023-10-02T14:48:20.362653+00:00', 'source_uid': 'NeMoGuardrails', 'data': {}}, {'type': 'InternalSystemActionFinished', 'uid': '9fa3cd5c-b87f-40ed-bc4f-7654340a550b', 'event_created_at': '2023-10-02T14:48:20.362703+00:00', 'source_uid': 'NeMoGuardrails', 'action_uid': '1bdce6ce-80e3-42b6-a2db-5977fc07dcfd', 'action_name': 'generate_bot_message', 'action_params': {}, 'action_result_key': None, 'status': 'success', 'is_success': True, 'return_value': None, 'events': [{'type': 'StartUtteranceBotAction', 'uid': '26dfad26-8850-4f12-bcc8-e05c44ab3d4e', 'event_created_at': '2023-10-02T14:48:20.362524+00:00', 'source_uid': 'NeMoGuardrails', 'script': "You're welcome. If you have any more questions or if there's anything else I can help you with, please don't hesitate to ask.", 'action_info_modality': 'bot_speech', 'action_info_modality_policy': 'replace', 'action_uid': '8c01cd8f-248f-4035-a722-7e6dd085e07d'}], 'is_system_action': True, 'action_finished_at': '2023-10-02T14:48:20.362720+00:00'}, {'type': 'StartUtteranceBotAction', 'uid': '26dfad26-8850-4f12-bcc8-e05c44ab3d4e', 'event_created_at': '2023-10-02T14:48:20.362524+00:00', 'source_uid': 'NeMoGuardrails', 'script': "You're welcome. If you have any more questions or if there's anything else I can help you with, please don't hesitate to ask.", 'action_info_modality': 'bot_speech', 'action_info_modality_policy': 'replace', 'action_uid': '8c01cd8f-248f-4035-a722-7e6dd085e07d'}, {'type': 'Listen', 'uid': '50d47569-12b8-465c-9930-2b2e5abfcccb', 'event_created_at': '2023-10-02T14:48:20.365484+00:00', 'source_uid': 'NeMoGuardrails'}, {'type': 'UtteranceUserActionFinished', 'final_transcript': 'which was the best performing sector?'}, {'type': 'StartInternalSystemAction', 'uid': '0dbb1691-2485-48d7-a4e9-1197695bbeac', 'event_created_at': '2023-10-02T14:48:30.977598+00:00', 'source_uid': 'NeMoGuardrails', 'action_name': 'generate_user_intent', 'action_params': {}, 'action_result_key': None, 'action_uid': '20183a9c-a949-42a9-bb8c-3a98024971ce', 'is_system_action': True}, {'type': 'InternalSystemActionFinished', 'uid': '32bff9c4-059d-432a-88a6-2730fe233f3c', 'event_created_at': '2023-10-02T14:48:33.373010+00:00', 'source_uid': 'NeMoGuardrails', 'action_uid': '20183a9c-a949-42a9-bb8c-3a98024971ce', 'action_name': 'generate_user_intent', 'action_params': {}, 'action_result_key': None, 'status': 'success', 'is_success': True, 'return_value': None, 'events': [{'type': 'UserIntent', 'uid': '28404ddf-6a5f-4424-997f-6c8735fcdc3b', 'event_created_at': '2023-10-02T14:48:33.372902+00:00', 'source_uid': 'NeMoGuardrails', 'intent': 'ask about establishment survey data'}], 'is_system_action': True, 'action_finished_at': '2023-10-02T14:48:33.373035+00:00'}, {'type': 'UserIntent', 'uid': '28404ddf-6a5f-4424-997f-6c8735fcdc3b', 'event_created_at': '2023-10-02T14:48:33.372902+00:00', 'source_uid': 'NeMoGuardrails', 'intent': 'ask about establishment survey data'}, {'type': 'BotIntent', 'intent': 'response about establishment survey data'}, {'type': 'StartInternalSystemAction', 'uid': '62aa06af-e0df-448c-bdca-cda82aca5974', 'event_created_at': '2023-10-02T14:48:33.378119+00:00', 'source_uid': 'NeMoGuardrails', 'action_name': 'retrieve_relevant_chunks', 'action_params': {}, 'action_result_key': None, 'action_uid': '80d505b7-9d4a-4eda-8e7c-30284639e812', 'is_system_action': True}, {'type': 'InternalSystemActionFinished', 'uid': 'c0b09464-9eb9-4849-9542-f5575fad8338', 'event_created_at': '2023-10-02T14:48:35.232219+00:00', 'source_uid': 'NeMoGuardrails', 'action_uid': 'dfe783dd-6a51-44ce-a28d-89e3278de250', 'action_name': 'generate_bot_message', 'action_params': {}, 'action_result_key': None, 'status': 'success', 'is_success': True, 'return_value': None, 'events': [{'type': 'StartUtteranceBotAction', 'uid': 'b97eb19e-d27b-4e0b-b440-dae08fd0db90', 'event_created_at': '2023-10-02T14:48:35.232039+00:00', 'source_uid': 'NeMoGuardrails', 'script': 'According to the establishment survey data, the leisure and hospitality sector had the highest job growth in March 2021 with an increase of 72,000 jobs.', 'action_info_modality': 'bot_speech', 'action_info_modality_policy': 'replace', 'action_uid': '5e565985-0167-4ab3-b591-a03ee3f3b35a'}], 'is_system_action': True, 'action_finished_at': '2023-10-02T14:48:35.232237+00:00'}, {'type': 'StartUtteranceBotAction', 'uid': 'b97eb19e-d27b-4e0b-b440-dae08fd0db90', 'event_created_at': '2023-10-02T14:48:35.232039+00:00', 'source_uid': 'NeMoGuardrails', 'script': 'According to the establishment survey data, the leisure and hospitality sector had the highest job growth in March 2021 with an increase of 72,000 jobs.', 'action_info_modality': 'bot_speech', 'action_info_modality_policy': 'replace', 'action_uid': '5e565985-0167-4ab3-b591-a03ee3f3b35a'}, {'type': 'Listen', 'uid': '8c73bb1c-2393-45c4-b4c1-121dead0ff15', 'event_created_at': '2023-10-02T14:48:35.235122+00:00', 'source_uid': 'NeMoGuardrails'}, {'type': 'UtteranceUserActionFinished', 'final_transcript': 'which was the worst?'}, {'type': 'StartInternalSystemAction', 'uid': 'b411cd98-5382-4777-8100-452c4e2422e7', 'event_created_at': '2023-10-02T14:48:43.079607+00:00', 'source_uid': 'NeMoGuardrails', 'action_name': 'generate_user_intent', 'action_params': {}, 'action_result_key': None, 'action_uid': '6aac22c5-e24a-46ae-8c05-3668bd79635e', 'is_system_action': True}, {'type': 'InternalSystemActionFinished', 'uid': 'f4847a08-6001-4c80-9751-1b79dd055932', 'event_created_at': '2023-10-02T14:49:03.800667+00:00', 'source_uid': 'NeMoGuardrails', 'action_uid': '6aac22c5-e24a-46ae-8c05-3668bd79635e', 'action_name': 'generate_user_intent', 'action_params': {}, 'action_result_key': None, 'status': 'success', 'is_success': True, 'return_value': None, 'events': [{'type': 'UserIntent', 'uid': 'c42600de-90ba-4b2d-8548-8a400749b3c4', 'event_created_at': '2023-10-02T14:49:03.800559+00:00', 'source_uid': 'NeMoGuardrails', 'intent': 'ask about establishment survey data'}], 'is_system_action': True, 'action_finished_at': '2023-10-02T14:49:03.800692+00:00'}, {'type': 'UserIntent', 'uid': 'c42600de-90ba-4b2d-8548-8a400749b3c4', 'event_created_at': '2023-10-02T14:49:03.800559+00:00', 'source_uid': 'NeMoGuardrails', 'intent': 'ask about establishment survey data'}, {'type': 'BotIntent', 'intent': 'response about establishment survey data'}, {'type': 'StartInternalSystemAction', 'uid': 'c06c3208-aed1-4615-b1c5-85d9f843f521', 'event_created_at': '2023-10-02T14:49:03.805802+00:00', 'source_uid': 'NeMoGuardrails', 'action_name': 'retrieve_relevant_chunks', 'action_params': {}, 'action_result_key': None, 'action_uid': '8346e413-b5da-4db3-96a2-ca67455defb8', 'is_system_action': True}, {'type': 'StartInternalSystemAction', 'uid': '26d7933c-7b6c-48d6-89a5-b3271ac46789', 'event_created_at': '2023-10-02T14:49:03.822351+00:00', 'source_uid': 'NeMoGuardrails', 'action_name': 'generate_bot_message', 'action_params': {}, 'action_result_key': None, 'action_uid': '3b44a786-b2f0-4af4-b27d-0e22eedc2542', 'is_system_action': True}, {'type': 'ContextUpdate', 'uid': '128cc92d-3155-4df9-b322-58482f13cfb3', 'event_created_at': '2023-10-02T14:49:05.427680+00:00', 'source_uid': 'NeMoGuardrails', 'data': {}}, {'type': 'InternalSystemActionFinished', 'uid': '9783dc6f-2ed6-45c4-a8fd-7a25e111b7bf', 'event_created_at': '2023-10-02T14:49:05.427728+00:00', 'source_uid': 'NeMoGuardrails', 'action_uid': '3b44a786-b2f0-4af4-b27d-0e22eedc2542', 'action_name': 'generate_bot_message', 'action_params': {}, 'action_result_key': None, 'status': 'success', 'is_success': True, 'return_value': None, 'events': [{'type': 'StartUtteranceBotAction', 'uid': '206bdec3-62ba-4d4c-a4ad-0c1143f94254', 'event_created_at': '2023-10-02T14:49:05.427547+00:00', 'source_uid': 'NeMoGuardrails', 'script': 'The construction sector had the worst job growth in March 2021, with a decrease of 32,000 jobs.', 'action_info_modality': 'bot_speech', 'action_info_modality_policy': 'replace', 'action_uid': '7295e6bd-658d-4bb8-b620-31ff14211e37'}], 'is_system_action': True, 'action_finished_at': '2023-10-02T14:49:05.427746+00:00'}, {'type': 'StartUtteranceBotAction', 'uid': '206bdec3-62ba-4d4c-a4ad-0c1143f94254', 'event_created_at': '2023-10-02T14:49:05.427547+00:00', 'source_uid': 'NeMoGuardrails', 'script': 'The construction sector had the worst job growth in March 2021, with a decrease of 32,000 jobs.', 'action_info_modality': 'bot_speech', 'action_info_modality_policy': 'replace', 'action_uid': '7295e6bd-658d-4bb8-b620-31ff14211e37'}, {'type': 'Listen', 'uid': '7974d0ca-dbd0-4105-8d1d-8621c9fc781c', 'event_created_at': '2023-10-02T14:49:05.430559+00:00', 'source_uid': 'NeMoGuardrails'}, {'type': 'UtteranceUserActionFinished', 'final_transcript': 'should it not be 2023?'}, {'type': 'StartInternalSystemAction', 'uid': 'c5efed13-e370-47da-b5db-35593076a5d0', 'event_created_at': '2023-10-02T14:49:13.155764+00:00', 'source_uid': 'NeMoGuardrails', 'action_name': 'generate_user_intent', 'action_params': {}, 'action_result_key': None, 'action_uid': 'ccb58a6f-ddff-4bc3-b032-7c437d53001b', 'is_system_action': True}, {'type': 'InternalSystemActionFinished', 'uid': '223a9ab2-0f54-4e3c-acc7-991961b8471b', 'event_created_at': '2023-10-02T14:49:17.788545+00:00', 'source_uid': 'NeMoGuardrails', 'action_uid': 'ccb58a6f-ddff-4bc3-b032-7c437d53001b', 'action_name': 'generate_user_intent', 'action_params': {}, 'action_result_key': None, 'status': 'success', 'is_success': True, 'return_value': None, 'events': [{'type': 'UserIntent', 'uid': '8e6596ff-af94-4b4b-9e40-b7fcdbc0a1b6', 'event_created_at': '2023-10-02T14:49:17.788443+00:00', 'source_uid': 'NeMoGuardrails', 'intent': 'ask about headline numbers'}], 'is_system_action': True, 'action_finished_at': '2023-10-02T14:49:17.788568+00:00'}, {'type': 'UserIntent', 'uid': '8e6596ff-af94-4b4b-9e40-b7fcdbc0a1b6', 'event_created_at': '2023-10-02T14:49:17.788443+00:00', 'source_uid': 'NeMoGuardrails', 'intent': 'ask about headline numbers'}, {'type': 'BotIntent', 'intent': 'response about headline numbers'}, {'type': 'StartInternalSystemAction', 'uid': 'bf257c5d-c47e-403d-8d6a-f1eca5183b70', 'event_created_at': '2023-10-02T14:49:17.792579+00:00', 'source_uid': 'NeMoGuardrails', 'action_name': 'retrieve_relevant_chunks', 'action_params': {}, 'action_result_key': None, 'action_uid': '78bfea59-7cce-4308-af74-489ddc66852d', 'is_system_action': True}, {'type': 'StartInternalSystemAction', 'uid': '583d1fde-541b-4fcb-9b0a-70e5ffeac59d', 'event_created_at': '2023-10-02T14:49:17.806987+00:00', 'source_uid': 'NeMoGuardrails', 'action_name': 'generate_bot_message', 'action_params': {}, 'action_result_key': None, 'action_uid': '615103f5-b24b-45a9-8b6f-4631020c9fa0', 'is_system_action': True}, {'type': 'ContextUpdate', 'uid': 'd3a285cb-5d44-467f-80f1-31d1ad6354b0', 'event_created_at': '2023-10-02T14:49:23.274752+00:00', 'source_uid': 'NeMoGuardrails', 'data': {}}, {'type': 'InternalSystemActionFinished', 'uid': 'e6660639-f3e0-4295-ae35-9f6f95512b35', 'event_created_at': '2023-10-02T14:49:23.274801+00:00', 'source_uid': 'NeMoGuardrails', 'action_uid': '615103f5-b24b-45a9-8b6f-4631020c9fa0', 'action_name': 'generate_bot_message', 'action_params': {}, 'action_result_key': None, 'status': 'success', 'is_success': True, 'return_value': None, 'events': [{'type': 'StartUtteranceBotAction', 'uid': '6de6e7a8-6f38-418d-9c7a-e7d85e4003d6', 'event_created_at': '2023-10-02T14:49:23.274619+00:00', 'source_uid': 'NeMoGuardrails', 'script': 'Sorry, I do not have the unemployment rate for July 2023.', 'action_info_modality': 'bot_speech', 'action_info_modality_policy': 'replace', 'action_uid': '96377729-4fd5-4610-b6a0-0b84102188a1'}], 'is_system_action': True, 'action_finished_at': '2023-10-02T14:49:23.274819+00:00'}, {'type': 'StartUtteranceBotAction', 'uid': '6de6e7a8-6f38-418d-9c7a-e7d85e4003d6', 'event_created_at': '2023-10-02T14:49:23.274619+00:00', 'source_uid': 'NeMoGuardrails', 'script': 'Sorry, I do not have the unemployment rate for July 2023.', 'action_info_modality': 'bot_speech', 'action_info_modality_policy': 'replace', 'action_uid': '96377729-4fd5-4610-b6a0-0b84102188a1'}, {'type': 'Listen', 'uid': '76e1ab52-c2f5-4107-8271-ffc82aa64d34', 'event_created_at': '2023-10-02T14:49:23.277321+00:00', 'source_uid': 'NeMoGuardrails'}, {'type': 'UtteranceUserActionFinished', 'final_transcript': 'okay'}, {'type': 'StartInternalSystemAction', 'uid': 'fadde2a8-94b6-40d5-b314-9cf6cdb9e672', 'event_created_at': '2023-10-02T14:49:28.313804+00:00', 'source_uid': 'NeMoGuardrails', 'action_name': 'generate_user_intent', 'action_params': {}, 'action_result_key': None, 'action_uid': 'e6539310-ec6d-4de7-bde2-cadd92864b72', 'is_system_action': True}]
    )
    assert len(generate_user_intent_prompt) <= max_task_prompt_length