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

"""Test the core flow mechanics"""
import logging

from rich.logging import RichHandler

from nemoguardrails import RailsConfig
from nemoguardrails.colang.v1_1.runtime.flows import ActionStatus
from nemoguardrails.colang.v1_1.runtime.statemachine import (
    InternalEvent,
    run_to_completion,
)
from tests.utils import TestChat, _init_state, is_data_in_events

FORMAT = "%(message)s"
logging.basicConfig(
    level=logging.DEBUG,
    format=FORMAT,
    datefmt="[%X,%f]",
    handlers=[RichHandler(markup=True)],
)

start_main_flow_event = InternalEvent(name="StartFlow", arguments={"flow_id": "main"})


def test_send_umim_action_event():
    """Test to start an UMIM event"""

    content = """
    flow main
      send StartUtteranceBotAction(script="Hello world")
    """

    state = run_to_completion(_init_state(content), start_main_flow_event)
    assert is_data_in_events(
        state.outgoing_events,
        [
            {
                "type": "StartUtteranceBotAction",
                "script": "Hello world",
            }
        ],
    )


def test_match_umim_action_event():
    """Test to match an UMIM event"""

    content = """
    flow main
      match UtteranceUserAction.Finished(final_transcript="Hi")
      send StartUtteranceBotAction(script="Hello world")
    """

    state = run_to_completion(_init_state(content), start_main_flow_event)
    assert is_data_in_events(
        state.outgoing_events,
        [],
    )
    state = run_to_completion(
        state,
        {
            "type": "UtteranceUserActionFinished",
            "uid": "d4a265bb-4a27-4d28-8ca5-80cc73dc4707",
            "event_created_at": "2023-09-12T13:01:16.334940+00:00",
            "source_uid": "umim_tui_app",
            "action_uid": "cc63b1a0-5703-4e80-b66b-2734c13abcf3",
            "final_transcript": "Hi",
            "is_success": True,
            "action_info_modality": "user_speech",
            "action_info_modality_policy": "replace",
            "action_finished_at": "2023-09-12T13:01:16.334954+00:00",
        },
    )
    assert is_data_in_events(
        state.outgoing_events,
        [
            {
                "type": "StartUtteranceBotAction",
                "script": "Hello world",
            }
        ],
    )


def test_start_action():
    """Test to start an UMIM action"""

    content = """
    flow main
      start UtteranceBotAction(script="Hello world")
    """
    state = run_to_completion(_init_state(content), start_main_flow_event)
    assert is_data_in_events(
        state.outgoing_events,
        [
            {
                "type": "StartUtteranceBotAction",
                "script": "Hello world",
            },
            {
                "type": "StopUtteranceBotAction",
            },
        ],
    )


def test_start_match_action_on_action_parameter():
    """Test to start and match an UMIM action based on action parameters"""

    content = """
    flow main
      start UtteranceBotAction(script="Hello world")
      match UtteranceBotAction(script="Hello world").Finished()
      start UtteranceBotAction(script="Done")
    """
    state = run_to_completion(_init_state(content), start_main_flow_event)
    assert is_data_in_events(
        state.outgoing_events,
        [
            {
                "type": "StartUtteranceBotAction",
                "script": "Hello world",
            }
        ],
    )
    state = run_to_completion(
        state,
        {
            "type": "UtteranceBotActionFinished",
            "final_script": "Hello world",
            "action_uid": state.outgoing_events[0]["action_uid"],
        },
    )
    assert is_data_in_events(
        state.outgoing_events,
        [
            {
                "type": "StartUtteranceBotAction",
                "script": "Done",
            },
            {
                "type": "StopUtteranceBotAction",
            },
        ],
    )


def test_start_mismatch_action_on_action_parameter():
    """Test to start and match an UMIM action based on action parameters"""

    content = """
    flow main
      start UtteranceBotAction(script="Hello world")
      match UtteranceBotAction(script="Hello").Finished()
      start UtteranceBotAction(script="Done")
    """
    state = run_to_completion(_init_state(content), start_main_flow_event)
    assert is_data_in_events(
        state.outgoing_events,
        [
            {
                "type": "StartUtteranceBotAction",
                "script": "Hello world",
            }
        ],
    )
    state = run_to_completion(
        state,
        {
            "type": "UtteranceBotActionFinished",
            "final_script": "Hello world",
            "action_uid": state.outgoing_events[0]["action_uid"],
        },
    )
    assert is_data_in_events(
        state.outgoing_events,
        [],
    )


def test_start_match_action_on_event_parameter():
    """Test to start and match an UMIM action based on action parameters"""

    content = """
    flow main
      start UtteranceBotAction(script="Hello world")
      match UtteranceBotAction.Finished(final_script="Hello world")
      start UtteranceBotAction(script="Done")
    """
    state = run_to_completion(_init_state(content), start_main_flow_event)
    assert is_data_in_events(
        state.outgoing_events,
        [
            {
                "type": "StartUtteranceBotAction",
                "script": "Hello world",
            }
        ],
    )
    state = run_to_completion(
        state,
        {
            "type": "UtteranceBotActionFinished",
            "final_script": "Hello world",
            "action_uid": state.outgoing_events[0]["action_uid"],
        },
    )
    assert is_data_in_events(
        state.outgoing_events,
        [
            {
                "type": "StartUtteranceBotAction",
                "script": "Done",
            },
            {
                "type": "StopUtteranceBotAction",
            },
        ],
    )


def test_start_mismatch_action_on_event_parameter():
    """Test to start and match an UMIM action based on action parameters"""

    content = """
    flow main
      start UtteranceBotAction(script="Hello world")
      match UtteranceBotAction.Finished(final_script="Hello")
      start UtteranceBotAction(script="Done")
    """
    state = run_to_completion(_init_state(content), start_main_flow_event)
    assert is_data_in_events(
        state.outgoing_events,
        [
            {
                "type": "StartUtteranceBotAction",
                "script": "Hello world",
            }
        ],
    )
    state = run_to_completion(
        state,
        {
            "type": "UtteranceBotActionFinished",
            "final_script": "Hello world",
            "action_uid": state.outgoing_events[0]["action_uid"],
        },
    )
    assert is_data_in_events(
        state.outgoing_events,
        [],
    )


def test_start_match_action_with_reference():
    """Test to start and match an UMIM action based on action parameters"""

    content = """
    flow main
      start UtteranceBotAction(script="Hello world") as $action_ref
      match $action_ref.Finished()
      start UtteranceBotAction(script="Done")
    """
    state = run_to_completion(_init_state(content), start_main_flow_event)
    assert is_data_in_events(
        state.outgoing_events,
        [
            {
                "type": "StartUtteranceBotAction",
                "script": "Hello world",
            }
        ],
    )
    state = run_to_completion(
        state,
        {
            "type": "UtteranceBotActionFinished",
            "final_script": "Hello world",
            "action_uid": state.outgoing_events[0]["action_uid"],
        },
    )
    assert is_data_in_events(
        state.outgoing_events,
        [
            {
                "type": "StartUtteranceBotAction",
                "script": "Done",
            },
            {
                "type": "StopUtteranceBotAction",
            },
        ],
    )


def test_await_action():
    """Test to await an UMIM action"""

    content = """
    flow main
      await UtteranceBotAction(script="Hello world")
      start UtteranceBotAction(script="Done")
    """
    state = run_to_completion(_init_state(content), start_main_flow_event)
    assert is_data_in_events(
        state.outgoing_events,
        [
            {
                "type": "StartUtteranceBotAction",
                "script": "Hello world",
            }
        ],
    )
    state = run_to_completion(
        state,
        {
            "type": "UtteranceBotActionFinished",
            "final_script": "Hello world",
            "action_uid": state.outgoing_events[0]["action_uid"],
        },
    )
    assert is_data_in_events(
        state.outgoing_events,
        [
            {
                "type": "StartUtteranceBotAction",
                "script": "Done",
            },
            {
                "type": "StopUtteranceBotAction",
            },
        ],
    )


def test_implicit_action_state_update():
    """Test the action state update"""

    content = """
    flow main
      start UtteranceBotAction(script="Hello world") as $action_ref1
      start UtteranceBotAction(script="Hi") as $action_ref2
      match $action_ref1.Finished()
    """
    state = run_to_completion(_init_state(content), start_main_flow_event)
    assert is_data_in_events(
        state.outgoing_events,
        [
            {
                "type": "StartUtteranceBotAction",
                "script": "Hello world",
            },
            {
                "type": "StartUtteranceBotAction",
                "script": "Hi",
            },
        ],
    )
    action_uid = state.outgoing_events[1]["action_uid"]
    state = run_to_completion(
        state,
        {
            "type": "UtteranceBotActionFinished",
            "final_script": "Hi",
            "action_uid": action_uid,
        },
    )
    assert state.actions[action_uid].status == ActionStatus.FINISHED


def test_start_a_flow():
    """Test the start of a child flow with full event notation"""

    content = """
    flow a
      start UtteranceBotAction(script="Hello world")

    flow main
      # start a
      send StartFlow(flow_id="a")
      match FlowStarted(flow_id="a")
    """

    state = run_to_completion(_init_state(content), start_main_flow_event)
    assert is_data_in_events(
        state.outgoing_events,
        [
            {
                "type": "StartUtteranceBotAction",
                "script": "Hello world",
            },
            {
                "type": "StopUtteranceBotAction",
            },
        ],
    )


def test_start_a_flow_compact_notation():
    """Test the start of a child flow using 'start' notation"""

    content = """
    flow a
      start UtteranceBotAction(script="Hello world")

    flow main
      start a
    """

    state = run_to_completion(_init_state(content), start_main_flow_event)
    assert is_data_in_events(
        state.outgoing_events,
        [
            {
                "type": "StartUtteranceBotAction",
                "script": "Hello world",
            },
            {
                "type": "StopUtteranceBotAction",
            },
        ],
    )


def test_start_match_flow_with_reference():
    """Test to start and match an UMIM action based on action parameters"""

    content = """
    flow bot say hello
      await UtteranceBotAction(script="Hello") as $action_ref

    flow main
      start bot say hello as $flow_ref
      match $flow_ref.Finished()
      start UtteranceBotAction(script="Done")
    """
    state = run_to_completion(_init_state(content), start_main_flow_event)
    assert is_data_in_events(
        state.outgoing_events,
        [
            {
                "type": "StartUtteranceBotAction",
                "script": "Hello",
            }
        ],
    )
    state = run_to_completion(
        state,
        {
            "type": "UtteranceBotActionFinished",
            "final_script": "Hello",
            "action_uid": state.outgoing_events[0]["action_uid"],
        },
    )
    assert is_data_in_events(
        state.outgoing_events,
        [
            {
                "type": "StartUtteranceBotAction",
                "script": "Done",
            },
            {
                "type": "StopUtteranceBotAction",
            },
        ],
    )


def test_await_a_flow():
    """Test await a child flow"""

    content = """
    flow a
      start UtteranceBotAction(script="Flow a started")

    flow main
      # await a
      send StartFlow(flow_id="a")
      match FlowStarted(flow_id="a")
      match FlowFinished(flow_id="a")
      start UtteranceBotAction(script="Flow a finished")
    """

    state = run_to_completion(_init_state(content), start_main_flow_event)
    assert is_data_in_events(
        state.outgoing_events,
        [
            {
                "type": "StartUtteranceBotAction",
                "script": "Flow a started",
            },
            {
                "type": "StopUtteranceBotAction",
            },
            {
                "type": "StartUtteranceBotAction",
                "script": "Flow a finished",
            },
            {
                "type": "StopUtteranceBotAction",
            },
        ],
    )


def test_await_a_flow_compact_notation():
    """Test await a child flow with compact notation 'await'"""

    content = """
    flow a
      start UtteranceBotAction(script="Flow a started")

    flow main
      await a
      start UtteranceBotAction(script="Flow a finished")
    """

    state = run_to_completion(_init_state(content), start_main_flow_event)
    assert is_data_in_events(
        state.outgoing_events,
        [
            {
                "type": "StartUtteranceBotAction",
                "script": "Flow a started",
            },
            {
                "type": "StopUtteranceBotAction",
            },
            {
                "type": "StartUtteranceBotAction",
                "script": "Flow a finished",
            },
            {
                "type": "StopUtteranceBotAction",
            },
        ],
    )


def test_start_child_flow_two_times():
    """Test start a child flow two times"""

    content = """
    flow a
      await UtteranceBotAction(script="Hi")

    flow main
      start a
      await a
    """

    state = run_to_completion(_init_state(content), start_main_flow_event)
    assert is_data_in_events(
        state.outgoing_events,
        [
            {
                "type": "StartUtteranceBotAction",
                "script": "Hi",
            },
            {
                "type": "StartUtteranceBotAction",
                "script": "Hi",
            },
        ],
    )


def test_event_simple_parameter_match():
    """Test start a child flow two times"""

    content = """
    flow main
      match Event1(a=1)
      start UtteranceBotAction(script="OK1")
      match Event1(a=1)
      await UtteranceBotAction(script="OK2")
    """
    state = run_to_completion(_init_state(content), start_main_flow_event)
    assert is_data_in_events(
        state.outgoing_events,
        [],
    )
    state = run_to_completion(
        state,
        {
            "type": "Event1",
            "a": 1,
        },
    )
    assert is_data_in_events(
        state.outgoing_events,
        [
            {
                "type": "StartUtteranceBotAction",
                "script": "OK1",
            }
        ],
    )
    state = run_to_completion(
        state,
        {
            "type": "Event1",
            "a": 2,
        },
    )
    assert is_data_in_events(
        state.outgoing_events,
        [],
    )
    state = run_to_completion(
        state,
        {
            "type": "Event1",
            "b": 2,
        },
    )
    assert is_data_in_events(
        state.outgoing_events,
        [],
    )
    state = run_to_completion(
        state,
        {
            "type": "Event1",
        },
    )
    assert is_data_in_events(
        state.outgoing_events,
        [],
    )
    state = run_to_completion(
        state,
        {
            "type": "Event1",
            "a": 1,
            "b": 1,
        },
    )
    assert is_data_in_events(
        state.outgoing_events,
        [
            {
                "type": "StartUtteranceBotAction",
                "script": "OK2",
            }
        ],
    )


def test_event_dict_parameter_match():
    """Test start a child flow two times"""

    content = """
    flow main
      match Event1(param={"a":1})
      start UtteranceBotAction(script="OK1")
      match Event1(param={"a":1})
      await UtteranceBotAction(script="OK2")
    """
    state = run_to_completion(_init_state(content), start_main_flow_event)
    assert is_data_in_events(
        state.outgoing_events,
        [],
    )
    state = run_to_completion(
        state,
        {
            "type": "Event1",
            "param": {"a": 1},
        },
    )
    assert is_data_in_events(
        state.outgoing_events,
        [
            {
                "type": "StartUtteranceBotAction",
                "script": "OK1",
            }
        ],
    )
    state = run_to_completion(
        state,
        {
            "type": "Event1",
            "param": {"a": 2},
        },
    )
    assert is_data_in_events(
        state.outgoing_events,
        [],
    )
    state = run_to_completion(
        state,
        {
            "type": "Event1",
            "param": {"b": 1},
        },
    )
    assert is_data_in_events(
        state.outgoing_events,
        [],
    )
    state = run_to_completion(
        state,
        {
            "type": "Event1",
            "param": {},
        },
    )
    assert is_data_in_events(
        state.outgoing_events,
        [],
    )
    state = run_to_completion(
        state,
        {
            "type": "Event1",
            "param": {"a": 1, "b": 1},
        },
    )
    assert is_data_in_events(
        state.outgoing_events,
        [
            {
                "type": "StartUtteranceBotAction",
                "script": "OK2",
            }
        ],
    )


def test_event_set_parameter_match():
    """Test start a child flow two times"""

    content = """
    flow main
      match Event1(param={"a"})
      start UtteranceBotAction(script="OK1")
      match Event1(param={r".*"})
      start UtteranceBotAction(script="OK2")
      match Event1(param={"c","a"})
      await UtteranceBotAction(script="OK3")
    """
    state = run_to_completion(_init_state(content), start_main_flow_event)
    assert is_data_in_events(
        state.outgoing_events,
        [],
    )
    state = run_to_completion(
        state,
        {
            "type": "Event1",
            "param": {"c"},
        },
    )
    assert is_data_in_events(
        state.outgoing_events,
        [],
    )
    state = run_to_completion(
        state,
        {
            "type": "Event1",
            "param": {"a", "b"},
        },
    )
    assert is_data_in_events(
        state.outgoing_events,
        [
            {
                "type": "StartUtteranceBotAction",
                "script": "OK1",
            }
        ],
    )
    state = run_to_completion(
        state,
        {
            "type": "Event1",
            "param": {},
        },
    )
    assert is_data_in_events(
        state.outgoing_events,
        [],
    )
    state = run_to_completion(
        state,
        {
            "type": "Event1",
            "param": {"sdfsd"},
        },
    )
    assert is_data_in_events(
        state.outgoing_events,
        [
            {
                "type": "StartUtteranceBotAction",
                "script": "OK2",
            }
        ],
    )
    state = run_to_completion(
        state,
        {
            "type": "Event1",
            "param": {"a", "b"},
        },
    )
    assert is_data_in_events(
        state.outgoing_events,
        [],
    )
    state = run_to_completion(
        state,
        {
            "type": "Event1",
            "param": {"a", "c"},
        },
    )
    assert is_data_in_events(
        state.outgoing_events,
        [
            {
                "type": "StartUtteranceBotAction",
                "script": "OK3",
            }
        ],
    )


def test_event_list_parameter_match():
    """Test start a child flow two times"""

    content = """
    flow main
      match Event1(param=[1,2])
      start UtteranceBotAction(script="OK1")
      match Event1(param=[1,2])
      start UtteranceBotAction(script="OK2")
      match Event1(param=[r".*",2])
      await UtteranceBotAction(script="OK3")
    """
    state = run_to_completion(_init_state(content), start_main_flow_event)
    assert is_data_in_events(
        state.outgoing_events,
        [],
    )
    state = run_to_completion(
        state,
        {
            "type": "Event1",
            "param": [1],
        },
    )
    assert is_data_in_events(
        state.outgoing_events,
        [],
    )
    state = run_to_completion(
        state,
        {
            "type": "Event1",
            "param": [2, 1],
        },
    )
    assert is_data_in_events(
        state.outgoing_events,
        [],
    )
    state = run_to_completion(
        state,
        {
            "type": "Event1",
            "param": [0, 1, 5, 2, 0],
        },
    )
    assert is_data_in_events(
        state.outgoing_events,
        [
            {
                "type": "StartUtteranceBotAction",
                "script": "OK1",
            }
        ],
    )
    state = run_to_completion(
        state,
        {
            "type": "Event1",
            "param": [2],
        },
    )
    assert is_data_in_events(
        state.outgoing_events,
        [],
    )
    state = run_to_completion(
        state,
        {
            "type": "Event1",
            "param": [],
        },
    )
    assert is_data_in_events(
        state.outgoing_events,
        [],
    )
    state = run_to_completion(
        state,
        {
            "type": "Event1",
            "param": [2, 1],
        },
    )
    assert is_data_in_events(
        state.outgoing_events,
        [],
    )
    state = run_to_completion(
        state,
        {
            "type": "Event1",
            "param": [1, 2, 3],
        },
    )
    assert is_data_in_events(
        state.outgoing_events,
        [
            {
                "type": "StartUtteranceBotAction",
                "script": "OK2",
            }
        ],
    )
    state = run_to_completion(
        state,
        {
            "type": "Event1",
            "param": [5, 2],
        },
    )
    assert is_data_in_events(
        state.outgoing_events,
        [
            {
                "type": "StartUtteranceBotAction",
                "script": "OK3",
            }
        ],
    )


def test_event_custom_regex_parameter_match():
    """Test more complex regex parameters."""

    content = """
    flow main
      while True
        when VisualFormSceneAction.InputUpdated(interim_inputs=[{"id": r"\\bemail\\b", "value": r".*"}]) as $e
          start UtteranceBotAction(script="Success")
    """
    state = run_to_completion(_init_state(content), start_main_flow_event)
    assert is_data_in_events(
        state.outgoing_events,
        [],
    )
    state = run_to_completion(
        state,
        {
            "type": "VisualFormSceneActionInputUpdated",
            "interim_inputs": [{"id": "email", "value": "test"}],
        },
    )
    assert is_data_in_events(
        state.outgoing_events,
        [
            {
                "type": "StartUtteranceBotAction",
                "script": "Success",
            }
        ],
    )
    state = run_to_completion(
        state,
        {
            "type": "VisualFormSceneActionInputUpdated",
            "interim_inputs": [{"id": "sdfsdf", "value": "test"}],
        },
    )
    assert is_data_in_events(
        state.outgoing_events,
        [],
    )
    state = run_to_completion(
        state,
        {
            "type": "VisualFormSceneActionInputUpdated",
            "interim_inputs": [{"id": "sdfsdf email sdf", "value": ""}],
        },
    )
    assert is_data_in_events(
        state.outgoing_events,
        [
            {
                "type": "StartUtteranceBotAction",
                "script": "Success",
            }
        ],
    )


def test_event_corner_cases_regex_parameter_match():
    """Test corner cases for regex matches"""

    content = """
    flow main
      while True
        when VisualFormSceneAction.InputUpdated(interim_inputs=[{"id" : "ter", "r": 'r"[ab]+"', "value": r"^[r'a]+$"}]) as $e
          start UtteranceBotAction(script="Success")
    """

    state = run_to_completion(_init_state(content), start_main_flow_event)
    assert is_data_in_events(
        state.outgoing_events,
        [],
    )
    state = run_to_completion(
        state,
        {
            "type": "VisualFormSceneActionInputUpdated",
            "interim_inputs": [
                {"id": "ter", "r": 'r"[ab]+"', "value": "rar'araaaaarr"}
            ],
        },
    )
    assert is_data_in_events(
        state.outgoing_events,
        [
            {
                "type": "StartUtteranceBotAction",
                "script": "Success",
            }
        ],
    )
    state = run_to_completion(
        state,
        {
            "type": "VisualFormSceneActionInputUpdated",
            "interim_inputs": [
                {"id": "ter", "r": 'r"[ab]+"', "value": 'rar"araaaaarr'}
            ],
        },
    )
    assert is_data_in_events(
        state.outgoing_events,
        [],
    )


def test_action_event_requeuing():
    config = RailsConfig.from_content(
        colang_content="""
        flow main
          match UtteranceUserAction.Finished(final_transcript="start")
          start UtteranceBotAction(script="started")
          match UtteranceBotAction.Started()
          start UtteranceBotAction(script="success")
        """,
        yaml_content="""
        colang_version: "1.1"
        """,
    )

    chat = TestChat(
        config,
        llm_completions=[],
    )

    chat >> "start"
    chat << "started\nsuccess"


def test_update_context():
    """Test to update the context."""

    content = """
    flow main
      global $test
      match UtteranceUserAction.Finished(final_transcript="step1")
      start UtteranceBotAction(script="{{$test}}")
      match UtteranceUserAction.Finished(final_transcript="step2")
      start UtteranceBotAction(script="{{$test}}")
    """
    state = run_to_completion(_init_state(content), start_main_flow_event)
    assert is_data_in_events(
        state.outgoing_events,
        [],
    )
    state = run_to_completion(
        state,
        {
            "type": "ContextUpdate",
            "data": {
                "test": 13,
            },
        },
    )
    assert is_data_in_events(
        state.outgoing_events,
        [],
    )
    state = run_to_completion(
        state,
        {
            "type": "UtteranceUserActionFinished",
            "final_transcript": "step1",
        },
    )
    assert is_data_in_events(
        state.outgoing_events,
        [
            {
                "type": "StartUtteranceBotAction",
                "script": "13",
            },
        ],
    )
    state = run_to_completion(
        state,
        {
            "type": "ContextUpdate",
            "data": {
                "test": 5,
            },
        },
    )
    state = run_to_completion(
        state,
        {
            "type": "UtteranceUserActionFinished",
            "final_transcript": "step2",
        },
    )
    assert is_data_in_events(
        state.outgoing_events,
        [
            {
                "type": "StartUtteranceBotAction",
                "script": "5",
            },
            {
                "type": "StopUtteranceBotAction",
            },
            {
                "type": "StopUtteranceBotAction",
            },
        ],
    )


if __name__ == "__main__":
    test_update_context()
