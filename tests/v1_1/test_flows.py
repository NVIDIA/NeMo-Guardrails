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
import copy
import json
import logging
import sys

from rich.logging import RichHandler

from nemoguardrails.colang import parse_colang_file
from nemoguardrails.colang.v1_1.runtime.flows import (
    ActionStatus,
    FlowEvent,
    State,
    run_to_completion,
)
from nemoguardrails.utils import EnhancedJSONEncoder
from tests.utils import convert_parsed_colang_to_flow_config, is_data_in_events

FORMAT = "%(message)s"
logging.basicConfig(
    level=logging.DEBUG,
    format=FORMAT,
    datefmt="[%X,%f]",
    handlers=[RichHandler(markup=True)],
)

start_main_flow_event = FlowEvent(name="StartFlow", arguments={"flow_id": "main"})


def _init_state(colang_content) -> State:
    config = convert_parsed_colang_to_flow_config(
        parse_colang_file(
            filename="",
            content=colang_content,
            include_source_mapping=True,
            version="1.1",
        )
    )

    json.dump(config, sys.stdout, indent=4, cls=EnhancedJSONEncoder)
    state = State(context={}, flow_states=[], flow_configs=config)
    state.initialize()
    print("---------------------------------")
    json.dump(state.flow_configs, sys.stdout, indent=4, cls=EnhancedJSONEncoder)

    return state


def test_send_umim_event():
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


def test_match_umim_event():
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


def test_child_flow_abort():
    """Test start a child flow two times"""

    content = """
    flow a
      start b

    flow b
      await UtteranceBotAction(script="Hi")

    flow main
      start a
      match b.Failed()
      start UtteranceBotAction(script="Done")
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
                "type": "StopUtteranceBotAction",
            },
            {
                "type": "StartUtteranceBotAction",
                "script": "Done",
            },
            {
                "type": "StopUtteranceBotAction",
            },
        ],
    )


def test_conflicting_actions_v_a():
    """Test the action conflict resolution"""

    content = """
    flow a
      match UtteranceUserAction.Finished()
      start UtteranceBotAction(script="Hello")
      start UtteranceBotAction(script="How are you")

    flow main
      start a
      match UtteranceUserAction.Finished(final_transcript="Hi")
      start UtteranceBotAction(script="Hello")
      start UtteranceBotAction(script="Bye")
    """

    state = run_to_completion(_init_state(content), start_main_flow_event)
    assert state.outgoing_events == []
    state = run_to_completion(
        state,
        {
            "type": "UtteranceUserActionFinished",
            "final_transcript": "Hi",
        },
    )
    assert is_data_in_events(
        state.outgoing_events,
        [
            {
                "type": "StartUtteranceBotAction",
                "script": "Hello",
            },
            {
                "type": "StartUtteranceBotAction",
                "script": "Bye",
            },
            {
                "type": "StopUtteranceBotAction",
            },
            {
                "type": "StopUtteranceBotAction",
            },
        ],
    )


def test_conflicting_actions_v_b():
    """Test the action conflict resolution"""

    content = """
    flow a
      match UtteranceUserAction.Finished(final_transcript="Hi")
      start UtteranceBotAction(script="Hello")
      start UtteranceBotAction(script="How are you")

    flow main
      start a
      match UtteranceUserAction.Finished()
      start UtteranceBotAction(script="Hello")
      start UtteranceBotAction(script="Bye")
    """

    state = run_to_completion(_init_state(content), start_main_flow_event)
    assert state.outgoing_events == []
    state = run_to_completion(
        state,
        {
            "type": "UtteranceUserActionFinished",
            "final_transcript": "Hi",
        },
    )
    assert is_data_in_events(
        state.outgoing_events,
        [
            {
                "type": "StartUtteranceBotAction",
                "script": "Hello",
            },
            {
                "type": "StartUtteranceBotAction",
                "script": "How are you",
            },
            {
                "type": "StopUtteranceBotAction",
            },
            {
                "type": "StopUtteranceBotAction",
            },
        ],
    )


def test_conflicting_actions_with_flow_priorities():
    """Test the action conflict resolution"""

    content = """
    flow a $p
      priority $p
      match UtteranceUserAction.Finished(final_transcript="Go")
      start UtteranceBotAction(script="A")

    flow b $p
      priority $p
      match UtteranceUserAction.Finished(final_transcript="Go")
      start UtteranceBotAction(script="B")

    flow main
      start a 1.0 as $ref_a
      start b 0.9 as $ref_b
      match $ref_a.Finished()
      start a 0.9 as $ref_a
      start b 1.0 as $ref_b
      match $ref_b.Finished()
      start UtteranceBotAction(script="End")
    """

    state = run_to_completion(_init_state(content), start_main_flow_event)
    assert state.outgoing_events == []
    state = run_to_completion(
        state,
        {
            "type": "UtteranceUserActionFinished",
            "final_transcript": "Go",
        },
    )
    assert is_data_in_events(
        state.outgoing_events,
        [
            {
                "type": "StartUtteranceBotAction",
                "script": "A",
            },
            {
                "type": "StopUtteranceBotAction",
            },
        ],
    )
    state = run_to_completion(
        state,
        {
            "type": "UtteranceUserActionFinished",
            "final_transcript": "Go",
        },
    )
    assert is_data_in_events(
        state.outgoing_events,
        [
            {
                "type": "StartUtteranceBotAction",
                "script": "B",
            },
            {
                "type": "StopUtteranceBotAction",
            },
            {
                "type": "StartUtteranceBotAction",
                "script": "End",
            },
            {
                "type": "StopUtteranceBotAction",
            },
        ],
    )


def test_conflicting_actions_branching_length():
    """Test the action conflict resolution"""

    content = """
    flow a
      match UtteranceUserAction.Finished()
      start b

    flow b
      start UtteranceBotAction(script="Hello")
      start UtteranceBotAction(script="How are you")

    flow main
      start a
      match UtteranceUserAction.Finished(final_transcript="Hi")
      start UtteranceBotAction(script="Hello")
      start UtteranceBotAction(script="Bye")
    """

    state = run_to_completion(_init_state(content), start_main_flow_event)
    assert state.outgoing_events == []
    state = run_to_completion(
        state,
        {
            "type": "UtteranceUserActionFinished",
            "final_transcript": "Hi",
        },
    )
    assert is_data_in_events(
        state.outgoing_events,
        [
            {
                "type": "StartUtteranceBotAction",
                "script": "Hello",
            },
            {
                "type": "StartUtteranceBotAction",
                "script": "Bye",
            },
            {
                "type": "StopUtteranceBotAction",
            },
            {
                "type": "StopUtteranceBotAction",
            },
        ],
    )


def test_conflicting_actions_reference_sharing():
    """Test the action conflict resolution"""

    content = """
    flow a
      match UtteranceUserAction.Finished()
      start UtteranceBotAction(script="Hello") as $ref
      match $ref.Finished()
      start UtteranceBotAction(script="How are you")
      match UtteranceUserAction.Finished()
      start UtteranceBotAction(script="Should not be executed")

    flow main
      start a
      match UtteranceUserAction.Finished(final_transcript="Hi")
      start UtteranceBotAction(script="Hello") as $ref
      match $ref.Finished()
      start UtteranceBotAction(script="How are you")
      start UtteranceBotAction(script="Great")
      match UtteranceUserAction.Finished()
    """

    state = run_to_completion(_init_state(content), start_main_flow_event)
    assert state.outgoing_events == []
    state = run_to_completion(
        state,
        {
            "type": "UtteranceUserActionFinished",
            "final_transcript": "Hi",
        },
    )
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
            "final_script": "blabla",
            "action_uid": state.outgoing_events[0]["action_uid"],
        },
    )
    assert is_data_in_events(
        state.outgoing_events,
        [
            {
                "type": "StartUtteranceBotAction",
                "script": "How are you",
            },
            {
                "type": "StartUtteranceBotAction",
                "script": "Great",
            },
        ],
    )
    state = run_to_completion(
        state,
        {
            "type": "UtteranceUserActionFinished",
            "final_transcript": "Test",
        },
    )
    assert is_data_in_events(
        state.outgoing_events,
        [
            {
                "type": "StopUtteranceBotAction",
            },
            {
                "type": "StopUtteranceBotAction",
            },
        ],
    )


def test_flow_parameters_action_wrapper():
    """Test flow parameter action wrapper mechanic"""

    content = """
    flow bot say $script
      await UtteranceBotAction(script=$script)

    flow main
      await bot say $script="Hi"
    """

    state = run_to_completion(_init_state(content), start_main_flow_event)
    assert is_data_in_events(
        state.outgoing_events,
        [
            {
                "type": "StartUtteranceBotAction",
                "script": "Hi",
            },
        ],
    )


def test_flow_parameters_event_wrapper():
    """Test flow parameter event wrapper mechanic"""

    content = """
    flow user said $transcript
      match UtteranceUserAction.Finished(final_transcript=$transcript)

    flow main
      await user said $transcript="Hi"
      start UtteranceBotAction(script="Yes")
    """

    state = run_to_completion(_init_state(content), start_main_flow_event)
    assert state.outgoing_events == []
    state = run_to_completion(
        state,
        {
            "type": "UtteranceUserActionFinished",
            "final_transcript": "Hi",
        },
    )
    assert is_data_in_events(
        state.outgoing_events,
        [
            {
                "type": "StartUtteranceBotAction",
                "script": "Yes",
            },
            {
                "type": "StopUtteranceBotAction",
            },
        ],
    )


def test_flow_parameters_positional_parameter():
    """Test positional flow parameters"""

    content = """
    flow bot say $script
      await UtteranceBotAction(script=$script)

    flow main
      await bot say "Hi"
    """

    state = run_to_completion(_init_state(content), start_main_flow_event)
    assert is_data_in_events(
        state.outgoing_events,
        [
            {
                "type": "StartUtteranceBotAction",
                "script": "Hi",
            },
        ],
    )


def test_flow_parameters_default_parameter():
    """Test default flow parameters"""

    content = """
    flow bot say $script="Howdy"
      await UtteranceBotAction(script=$script)

    flow main
      await bot say
    """

    state = run_to_completion(_init_state(content), start_main_flow_event)
    assert is_data_in_events(
        state.outgoing_events,
        [
            {
                "type": "StartUtteranceBotAction",
                "script": "Howdy",
            },
        ],
    )


def test_distributed_flow_matching():
    """Test flow default parameters."""

    content = """
    flow user said $transcript
      match UtteranceUserAction.Finished(final_transcript=$transcript)

    flow bot say $script
      await UtteranceBotAction(script=$script)

    flow a
      match user said $transcript="Hi"
      bot say 'Check1'

    flow b
      match user said $transcript="Hello"
      bot say 'Check2'

    flow main
      start a
      start b
      start user said "Hi"
      start user said "Hello"
      match UtteranceUserAction.Finished(final_transcript="wait")
    """

    state = run_to_completion(_init_state(content), start_main_flow_event)
    assert state.outgoing_events == []
    state = run_to_completion(
        state,
        {
            "type": "UtteranceUserActionFinished",
            "final_transcript": "Hello",
        },
    )
    assert is_data_in_events(
        state.outgoing_events,
        [
            {
                "type": "StartUtteranceBotAction",
                "script": "Check2",
            }
        ],
    )


def test_activate_flow_mechanism():
    """Test the activate a flow mechanism"""

    content = """
    flow a
      start UtteranceBotAction(script="Start")
      match UtteranceUserAction().Finished(final_transcript="Hi")
      start UtteranceBotAction(script="End")

    flow main
      activate a
      match WaitAction().Finished()
    """

    state = run_to_completion(_init_state(content), start_main_flow_event)
    assert is_data_in_events(
        state.outgoing_events,
        [
            {
                "type": "StartUtteranceBotAction",
                "script": "Start",
            }
        ],
    )
    state = run_to_completion(
        state,
        {
            "type": "UtteranceUserActionFinished",
            "final_transcript": "Hi",
        },
    )
    assert is_data_in_events(
        state.outgoing_events,
        [
            {
                "type": "StartUtteranceBotAction",
                "script": "End",
            },
            {
                "type": "StopUtteranceBotAction",
            },
            {
                "type": "StopUtteranceBotAction",
            },
            {
                "type": "StartUtteranceBotAction",
                "script": "Start",
            },
        ],
    )
    state = run_to_completion(
        state,
        {
            "type": "UtteranceUserActionFinished",
            "final_transcript": "Hi",
        },
    )
    assert is_data_in_events(
        state.outgoing_events,
        [
            {
                "type": "StartUtteranceBotAction",
                "script": "End",
            },
            {
                "type": "StopUtteranceBotAction",
            },
            {
                "type": "StopUtteranceBotAction",
            },
            {
                "type": "StartUtteranceBotAction",
                "script": "Start",
            },
        ],
    )


def test_finish_flow_event():
    """Test the FinishFlow event that will immediately finish a flow"""

    content = """
    flow a
      await UtteranceBotAction(script="Hi")

    flow b
      match a
      await UtteranceBotAction(script="Yes")

    flow main
      start b
      start a
      match UtteranceUserAction().Finished(final_transcript="Hi")
      send FinishFlow(flow_id="a")
      match WaitAction().Finished()
    """

    state = run_to_completion(_init_state(content), start_main_flow_event)
    assert is_data_in_events(
        state.outgoing_events,
        [
            {
                "type": "StartUtteranceBotAction",
                "script": "Hi",
            },
        ],
    )
    state = run_to_completion(
        state,
        {
            "type": "UtteranceUserActionFinished",
            "final_transcript": "Hi",
        },
    )
    assert is_data_in_events(
        state.outgoing_events,
        [
            {
                "type": "StopUtteranceBotAction",
            },
            {
                "type": "StartUtteranceBotAction",
                "script": "Yes",
            },
        ],
    )


def test_match_specificity_mechanic():
    """Test the FinishFlow event that will immediately finish a flow"""

    content = """
    flow user said something
      match UtteranceUserAction().Finished()

    flow user said $transcript
      match UtteranceUserAction().Finished(final_transcript=$transcript)

    flow something
      user said something
      start UtteranceBotAction(script="something")

    flow hello
      await user said "hello"
      start UtteranceBotAction(script="hi")

    flow goodbye
      await user said "goodbye"
      start UtteranceBotAction(script="bye")

    flow something failed
      match something.Failed()
      start UtteranceBotAction(script="something failed")

    flow hello failed
      match hello.Failed()
      start UtteranceBotAction(script="hello failed")

    flow goodbye failed
      match goodbye.Failed()
      start UtteranceBotAction(script="goodbye failed")

    flow main
      activate something and something failed
      activate hello and hello failed
      activate goodbye and goodbye failed
      match WaitAction().Finished()
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
            "final_transcript": "hello",
        },
    )
    assert is_data_in_events(
        state.outgoing_events,
        [
            {
                "type": "StartUtteranceBotAction",
                "script": "hi",
            },
            {
                "type": "StopUtteranceBotAction",
            },
            {
                "type": "StartUtteranceBotAction",
                "script": "something failed",
            },
            {
                "type": "StopUtteranceBotAction",
            },
        ],
    )
    state = run_to_completion(
        state,
        {
            "type": "UtteranceUserActionFinished",
            "final_transcript": "goodbye",
        },
    )
    assert is_data_in_events(
        state.outgoing_events,
        [
            {
                "type": "StartUtteranceBotAction",
                "script": "bye",
            },
            {
                "type": "StopUtteranceBotAction",
            },
            {
                "type": "StartUtteranceBotAction",
                "script": "something failed",
            },
            {
                "type": "StopUtteranceBotAction",
            },
        ],
    )


def test_match_failure_flow_abort():
    """Test the mechanism where a match statement FlowFinished/FlowFailed will abort the flow
    if it fails to be satisfied"""

    content = """
    flow a
      start b
      match b

    flow b
      match WaitAction().Finished()

    flow c
      match UtteranceUserAction().Finished(final_transcript="Start")
      send StopFlow(flow_id="b")

    flow main
      start a
      start c
      match FlowFailed(flow_id="a")
      await UtteranceBotAction(script="Yes")
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
            "final_transcript": "Start",
        },
    )
    assert is_data_in_events(
        state.outgoing_events,
        [
            {
                "type": "StartUtteranceBotAction",
                "script": "Yes",
            }
        ],
    )


def test_abort_flow_propagation_v_a():
    """Test that when a child flow has failed, the parent flow will also fail if
    matched on the FlowFinished() of the child flow."""

    content = """
    flow a
      await b
      await UtteranceBotAction(script="No1")

    flow b
      match UtteranceUserAction().Finished(final_transcript="Hi")
      await UtteranceBotAction(script="No2")

    flow c
      match FlowFailed(flow_id="a")
      await UtteranceBotAction(script="No3")

    flow main
      start a
      start c
      send StopFlow(flow_id="b")
      match WaitAction().Finished()
    """

    state = run_to_completion(_init_state(content), start_main_flow_event)
    assert is_data_in_events(
        state.outgoing_events,
        [
            {
                "type": "StartUtteranceBotAction",
                "script": "No3",
            }
        ],
    )


def test_abort_flow_propagation_v_b():
    """Test that when a child flow finished, the parent flow will fail if
    it was waiting for FlowFailed() of the child flow."""

    content = """
    flow a
      start b
      match FlowFailed(flow_id="b")

    flow b
      match UtteranceUserAction().Finished(final_transcript="Start")

    flow c
      match FlowFailed(flow_id="a")
      await UtteranceBotAction(script="Ok")

    flow main
      start a
      start c
      match WaitAction().Finished()
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
            "final_transcript": "Start",
        },
    )
    assert is_data_in_events(
        state.outgoing_events,
        [
            {
                "type": "StartUtteranceBotAction",
                "script": "Ok",
            }
        ],
    )


def test_while_loop_mechanic():
    """"""

    content = """
    flow main

      while $ref is None
        match UtteranceUserAction().Finished(final_transcript="End") as $ref
        start UtteranceBotAction(script="Test")

      start UtteranceBotAction(script="Done")
    """

    config = _init_state(content)
    state = run_to_completion(config, start_main_flow_event)
    assert is_data_in_events(
        state.outgoing_events,
        [],
    )
    state = run_to_completion(
        state,
        {
            "type": "UtteranceUserActionFinished",
            "final_transcript": "End",
        },
    )
    assert is_data_in_events(
        state.outgoing_events,
        [
            {
                "type": "StartUtteranceBotAction",
                "script": "Test",
            },
            {
                "type": "StartUtteranceBotAction",
                "script": "Done",
            },
            {
                "type": "StopUtteranceBotAction",
            },
            {
                "type": "StopUtteranceBotAction",
            },
        ],
    )


# TODO: Think about how to add back duplicate removal in normalization
# def test_start_and_grouping():
#     """"""

#     content = """
#     flow bot say $script
#       await UtteranceBotAction(script=$script)

#     flow main
#         start bot say "A"
#           and bot say "B"
#           and UtteranceBotAction(script="C")
#           and bot say "A"
#     """

#     state = run_to_completion(_init_state(content), start_main_flow_event)
#     assert is_data_in_events(
#         state.outgoing_events,
#         [
#             {
#                 "type": "StartUtteranceBotAction",
#                 "script": "A",
#             },
#             {
#                 "type": "StartUtteranceBotAction",
#                 "script": "B",
#             },
#             {
#                 "type": "StartUtteranceBotAction",
#                 "script": "C",
#             },
#             {
#                 "type": "StopUtteranceBotAction",
#             },
#             {
#                 "type": "StopUtteranceBotAction",
#             },
#             {
#                 "type": "StopUtteranceBotAction",
#             },
#         ],
#     )


def test_match_and_grouping():
    """"""

    content = """
    flow bot say $script
      await UtteranceBotAction(script=$script)

    flow main
        start bot say "A" as $ref_a
          and bot say "B" as $ref_b
          and UtteranceBotAction(script="C") as $ref_c
        match $ref_a.Finished()
          and $ref_b.Finished()
          and $ref_c.Finished()
        start bot say "Done"
    """

    state = run_to_completion(_init_state(content), start_main_flow_event)
    events = copy.deepcopy(state.outgoing_events)
    assert is_data_in_events(
        state.outgoing_events,
        [
            {
                "type": "StartUtteranceBotAction",
                "script": "A",
            },
            {
                "type": "StartUtteranceBotAction",
                "script": "B",
            },
            {
                "type": "StartUtteranceBotAction",
                "script": "C",
            },
        ],
    )
    state = run_to_completion(
        state,
        {
            "type": "UtteranceBotActionFinished",
            "final_script": "A",
            "action_uid": events[0]["action_uid"],
        },
    )
    assert is_data_in_events(state.outgoing_events, [])
    state = run_to_completion(
        state,
        {
            "type": "UtteranceBotActionFinished",
            "final_script": "B",
            "action_uid": events[1]["action_uid"],
        },
    )
    assert is_data_in_events(state.outgoing_events, [])
    state = run_to_completion(
        state,
        {
            "type": "UtteranceBotActionFinished",
            "final_script": "C",
            "action_uid": events[2]["action_uid"],
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


def test_start_or_grouping():
    """"""

    content = """
    flow bot say $script
      await UtteranceBotAction(script=$script)

    flow main
        $number = 0
        while $number < 10
          start bot say "Hi"
            or bot say "Hello"
            or bot say "Welcome"
          $number = $number + 1
        await bot say "Done"
    """

    state = run_to_completion(_init_state(content), start_main_flow_event)
    assert len(state.outgoing_events) == 11


def test_await_or_grouping():
    """"""

    content = """
    flow user said $transcript
      match UtteranceUserAction().Finished(final_transcript=$transcript)

    flow main
        await user said "A"
          or UtteranceBotAction(script="B")
          or user said "C"
        start UtteranceBotAction(script="Match")
    """

    state = run_to_completion(_init_state(content), start_main_flow_event)
    assert is_data_in_events(
        state.outgoing_events,
        [
            {
                "type": "StartUtteranceBotAction",
                "script": "B",
            }
        ],
    )
    state = run_to_completion(
        state,
        {
            "type": "UtteranceUserActionFinished",
            "final_transcript": "A",
        },
    )
    assert is_data_in_events(
        state.outgoing_events,
        [
            {
                "type": "StopUtteranceBotAction",
            },
            {
                "type": "StartUtteranceBotAction",
                "script": "Match",
            },
            {
                "type": "StopUtteranceBotAction",
            },
        ],
    )
    state = run_to_completion(_init_state(content), start_main_flow_event)
    assert is_data_in_events(
        state.outgoing_events,
        [
            {
                "type": "StartUtteranceBotAction",
                "script": "B",
            }
        ],
    )
    state = run_to_completion(
        state,
        {
            "type": "UtteranceBotActionFinished",
            "final_script": "B",
            "action_uid": state.outgoing_events[0]["action_uid"],
        },
    )
    assert is_data_in_events(
        state.outgoing_events,
        [
            {
                "type": "StartUtteranceBotAction",
                "script": "Match",
            },
            {
                "type": "StopUtteranceBotAction",
            },
        ],
    )
    state = run_to_completion(_init_state(content), start_main_flow_event)
    assert is_data_in_events(
        state.outgoing_events,
        [
            {
                "type": "StartUtteranceBotAction",
                "script": "B",
            }
        ],
    )
    state = run_to_completion(
        state,
        {
            "type": "UtteranceUserActionFinished",
            "final_transcript": "C",
        },
    )
    assert is_data_in_events(
        state.outgoing_events,
        [
            {
                "type": "StopUtteranceBotAction",
            },
            {
                "type": "StartUtteranceBotAction",
                "script": "Match",
            },
            {
                "type": "StopUtteranceBotAction",
            },
        ],
    )


def test_await_or_group_finish():
    """"""

    content = """
    flow bot say $text
      # llm: exclude
      await UtteranceBotAction(script=$text) as $action

    flow bot express greeting
      bot say "Hi there!"
        or bot say "Welcome!"

    flow main
      bot express greeting
    """

    config = _init_state(content)
    state = run_to_completion(config, start_main_flow_event)
    assert is_data_in_events(
        state.outgoing_events,
        [
            {
                "type": "StartUtteranceBotAction",
            }
        ],
    )
    state = run_to_completion(
        state,
        {
            "type": "UtteranceBotActionFinished",
            "final_script": state.outgoing_events[0]["script"],
            "action_uid": state.outgoing_events[0]["action_uid"],
        },
    )
    assert is_data_in_events(
        state.outgoing_events,
        [],
    )


def test_await_and_or_grouping():
    """"""

    content = """
    flow user said $transcript
      match UtteranceUserAction().Finished(final_transcript=$transcript)

    flow main
        await (user said "A" and user said "B")
          or (user said "C" and user said "D")
        start UtteranceBotAction(script="Match")
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
            "final_transcript": "A",
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
            "final_transcript": "C",
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
            "final_transcript": "B",
        },
    )
    assert is_data_in_events(
        state.outgoing_events,
        [
            {
                "type": "StartUtteranceBotAction",
                "script": "Match",
            },
            {
                "type": "StopUtteranceBotAction",
            },
        ],
    )

    state = run_to_completion(_init_state(content), start_main_flow_event)
    assert is_data_in_events(
        state.outgoing_events,
        [],
    )
    state = run_to_completion(
        state,
        {
            "type": "UtteranceUserActionFinished",
            "final_transcript": "B",
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
            "final_transcript": "C",
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
            "final_transcript": "D",
        },
    )
    assert is_data_in_events(
        state.outgoing_events,
        [
            {
                "type": "StartUtteranceBotAction",
                "script": "Match",
            },
            {
                "type": "StopUtteranceBotAction",
            },
        ],
    )


def test_await_multimodal_action():
    """"""

    content = """
    flow bot say $text
      await UtteranceBotAction(script=$text) as $action

    flow bot gesture $gesture
      await GestureBotAction(gesture=$gesture) as $action

    flow bot express $text
      await bot say $text

    flow main
        start bot express "Hi"
        start bot gesture "Wave"
        match UtteranceUserAction().Finished()
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
                "type": "StartGestureBotAction",
                "gesture": "Wave",
            },
        ],
    )


def test_activate_and_grouping():
    """"""

    content = """
    flow a
      start UtteranceBotAction(script="A")
      match UtteranceUserAction().Finished(final_transcript="a")

    flow b
      start UtteranceBotAction(script="B")
      match UtteranceUserAction().Finished(final_transcript="b")

    flow main
        activate a and b
        match UtteranceUserAction().Finished(final_transcript="end")
    """

    state = run_to_completion(_init_state(content), start_main_flow_event)
    assert is_data_in_events(
        state.outgoing_events,
        [
            {
                "type": "StartUtteranceBotAction",
                "script": "A",
            },
            {
                "type": "StartUtteranceBotAction",
                "script": "B",
            },
        ],
    )
    state = run_to_completion(
        state,
        {
            "type": "UtteranceUserActionFinished",
            "final_transcript": "a",
        },
    )
    assert is_data_in_events(
        state.outgoing_events,
        [
            {
                "type": "StopUtteranceBotAction",
            },
            {
                "type": "StartUtteranceBotAction",
                "script": "A",
            },
        ],
    )
    state = run_to_completion(
        state,
        {
            "type": "UtteranceUserActionFinished",
            "final_transcript": "b",
        },
    )
    assert is_data_in_events(
        state.outgoing_events,
        [
            {
                "type": "StopUtteranceBotAction",
            },
            {
                "type": "StartUtteranceBotAction",
                "script": "B",
            },
        ],
    )


def test_if_branching_mechanic():
    """"""

    content = """
    flow main
      while $action_ref_3 is None
        if $event_ref_1 is None
          start UtteranceBotAction(script="Action1") as $event_ref_1
        else if $event_ref_2 is None
          start UtteranceBotAction(script="Action2") as $event_ref_2
        else
          start UtteranceBotAction(script="ActionElse") as $action_ref_3
        start UtteranceBotAction(script="Next")
    """

    config = _init_state(content)
    state = run_to_completion(config, start_main_flow_event)
    assert is_data_in_events(
        state.outgoing_events,
        [
            {
                "type": "StartUtteranceBotAction",
                "script": "Action1",
            },
            {
                "type": "StartUtteranceBotAction",
                "script": "Next",
            },
            {
                "type": "StartUtteranceBotAction",
                "script": "Action2",
            },
            {
                "type": "StartUtteranceBotAction",
                "script": "Next",
            },
            {
                "type": "StartUtteranceBotAction",
                "script": "ActionElse",
            },
            {
                "type": "StartUtteranceBotAction",
                "script": "Next",
            },
            {
                "type": "StopUtteranceBotAction",
            },
            {
                "type": "StopUtteranceBotAction",
            },
            {
                "type": "StopUtteranceBotAction",
            },
            {
                "type": "StopUtteranceBotAction",
            },
            {
                "type": "StopUtteranceBotAction",
            },
            {
                "type": "StopUtteranceBotAction",
            },
        ],
    )


def test_event_reference_member_access():
    """"""

    content = """
    flow main
      match UtteranceUserAction().Finished() as $ref
      start UtteranceBotAction(script=$ref.arguments.final_transcript)
    """

    config = _init_state(content)
    state = run_to_completion(config, start_main_flow_event)
    assert is_data_in_events(
        state.outgoing_events,
        [],
    )
    state = run_to_completion(
        state,
        {
            "type": "UtteranceUserActionFinished",
            "final_transcript": "Hi there!",
        },
    )
    assert is_data_in_events(
        state.outgoing_events,
        [
            {
                "type": "StartUtteranceBotAction",
                "script": "Hi there!",
            },
            {
                "type": "StopUtteranceBotAction",
            },
        ],
    )


def test_action_reference_member_access():
    """"""

    content = """
    flow main
      start UtteranceBotAction(script="Hello") as $ref
      start UtteranceBotAction(script=$ref.start_event_arguments.script)
    """

    config = _init_state(content)
    state = run_to_completion(config, start_main_flow_event)
    assert is_data_in_events(
        state.outgoing_events,
        [
            {
                "type": "StartUtteranceBotAction",
                "script": "Hello",
            },
            {
                "type": "StartUtteranceBotAction",
                "script": "Hello",
            },
            {
                "type": "StopUtteranceBotAction",
            },
            {
                "type": "StopUtteranceBotAction",
            },
        ],
    )


def test_flow_references_member_access():
    """"""

    content = """
    flow bot say $text
      start UtteranceBotAction(script=$text) as $action_ref

    flow main
      start bot say "Hello" as $flow_ref
      start UtteranceBotAction(script=$flow_ref.context.action_ref.start_event_arguments.script)
    """

    config = _init_state(content)
    state = run_to_completion(config, start_main_flow_event)
    assert is_data_in_events(
        state.outgoing_events,
        [
            {
                "type": "StartUtteranceBotAction",
                "script": "Hello",
            },
            {
                "type": "StopUtteranceBotAction",
            },
            {
                "type": "StartUtteranceBotAction",
                "script": "Hello",
            },
            {
                "type": "StopUtteranceBotAction",
            },
        ],
    )


def test_values_in_strings():
    """"""

    content = """
    flow main
      start UtteranceBotAction(script="Roger") as $ref
      start UtteranceBotAction(script="Hi {$ref.start_event_arguments.script}!")
    """

    config = _init_state(content)
    state = run_to_completion(config, start_main_flow_event)
    assert is_data_in_events(
        state.outgoing_events,
        [
            {
                "type": "StartUtteranceBotAction",
                "script": "Roger",
            },
            {
                "type": "StartUtteranceBotAction",
                "script": "Hi Roger!",
            },
            {
                "type": "StopUtteranceBotAction",
            },
            {
                "type": "StopUtteranceBotAction",
            },
        ],
    )


def test_flow_return_values():
    """"""

    content = """
    flow a
      return "success"

    flow b
      return 100

    flow c
      $result = "failed"
      return $result

    flow main
      $result_a = await a
      $result_b = await b
      $result_c = await c
      start UtteranceBotAction(script="{$result_a} {$result_b} {$result_c}")
    """

    config = _init_state(content)
    state = run_to_completion(config, start_main_flow_event)
    assert is_data_in_events(
        state.outgoing_events,
        [
            {
                "type": "StartUtteranceBotAction",
                "script": "success 100 failed",
            },
            {
                "type": "StopUtteranceBotAction",
            },
        ],
    )


def test_break_continue_statement_a():
    """"""

    content = """
    flow main
      $count = -1
      while True
        $count = $count + 1
        start UtteranceBotAction(script="S:{$count}")
        if $count < 1
          $count = $count
        elif $count < 3
          continue
        elif $count == 3
          break
        start UtteranceBotAction(script="E:{$count}")
      start UtteranceBotAction(script="Done")
    """

    config = _init_state(content)
    state = run_to_completion(config, start_main_flow_event)
    assert is_data_in_events(
        state.outgoing_events,
        [
            {
                "type": "StartUtteranceBotAction",
                "script": "S:0",
            },
            {
                "type": "StartUtteranceBotAction",
                "script": "E:0",
            },
            {
                "type": "StartUtteranceBotAction",
                "script": "S:1",
            },
            {
                "type": "StartUtteranceBotAction",
                "script": "S:2",
            },
            {
                "type": "StartUtteranceBotAction",
                "script": "S:3",
            },
            {
                "type": "StartUtteranceBotAction",
                "script": "Done",
            },
            {
                "type": "StopUtteranceBotAction",
            },
            {
                "type": "StopUtteranceBotAction",
            },
            {
                "type": "StopUtteranceBotAction",
            },
            {
                "type": "StopUtteranceBotAction",
            },
            {
                "type": "StopUtteranceBotAction",
            },
            {
                "type": "StopUtteranceBotAction",
            },
        ],
    )


def test_break_continue_statement_b():
    """"""

    content = """
    flow main
      while True
        start UtteranceBotAction(script="A")
        while True
          break
          start UtteranceBotAction(script="E1")
        start UtteranceBotAction(script="B")
        break
        start UtteranceBotAction(script="E2")
      start UtteranceBotAction(script="C")
    """

    config = _init_state(content)
    state = run_to_completion(config, start_main_flow_event)
    assert is_data_in_events(
        state.outgoing_events,
        [
            {
                "type": "StartUtteranceBotAction",
                "script": "A",
            },
            {
                "type": "StartUtteranceBotAction",
                "script": "B",
            },
            {
                "type": "StartUtteranceBotAction",
                "script": "C",
            },
            {
                "type": "StopUtteranceBotAction",
            },
            {
                "type": "StopUtteranceBotAction",
            },
            {
                "type": "StopUtteranceBotAction",
            },
        ],
    )


# TODO: Stop actions/flows from cases that did not trigger in 'when' structure
def test_when_or_core_mechanics():
    """"""

    content = """
    flow user said $transcript
      match UtteranceUserAction.Finished(final_transcript=$transcript)

    flow main
      while True
        when UtteranceUserActionFinished(final_transcript="A")
          start UtteranceBotAction(script="A")
        orwhen UtteranceUserAction().Finished(final_transcript="B")
          start UtteranceBotAction(script="B")
        orwhen user said "C"
          start UtteranceBotAction(script="C")
          break
    """

    config = _init_state(content)
    state = run_to_completion(config, start_main_flow_event)
    assert is_data_in_events(
        state.outgoing_events,
        [],
    )
    state = run_to_completion(
        state,
        {
            "type": "UtteranceUserActionFinished",
            "final_transcript": "A",
        },
    )
    assert is_data_in_events(
        state.outgoing_events,
        [
            {
                "type": "StartUtteranceBotAction",
                "script": "A",
            },
        ],
    )
    state = run_to_completion(
        state,
        {
            "type": "UtteranceUserActionFinished",
            "final_transcript": "B",
        },
    )
    assert is_data_in_events(
        state.outgoing_events,
        [
            {
                "type": "StartUtteranceBotAction",
                "script": "B",
            },
        ],
    )
    state = run_to_completion(
        state,
        {
            "type": "UtteranceUserActionFinished",
            "final_transcript": "C",
        },
    )
    assert is_data_in_events(
        state.outgoing_events,
        [
            {
                "type": "StartUtteranceBotAction",
                "script": "C",
            },
            {
                "type": "StopUtteranceBotAction",
            },
            {
                "type": "StopUtteranceBotAction",
            },
            {
                "type": "StopUtteranceBotAction",
            },
        ],
    )


def test_when_or_bot_action_mechanics():
    """"""

    content = """
    flow main
      while True
        when UtteranceBotAction(script="Happens immediately")
          start UtteranceBotAction(script="A")
        orwhen UtteranceUserActionFinished(final_transcript="B")
          start UtteranceBotAction(script="B")
          break
    """

    config = _init_state(content)
    state = run_to_completion(config, start_main_flow_event)
    assert is_data_in_events(
        state.outgoing_events,
        [
            {
                "type": "StartUtteranceBotAction",
                "script": "Happens immediately",
            },
        ],
    )
    state = run_to_completion(
        state,
        {
            "type": "UtteranceBotActionFinished",
            "final_script": "Happens immediately",
            "action_uid": state.outgoing_events[0]["action_uid"],
        },
    )
    assert is_data_in_events(
        state.outgoing_events,
        [
            {
                "type": "StartUtteranceBotAction",
                "script": "A",
            },
            {
                "type": "StartUtteranceBotAction",
                "script": "Happens immediately",
            },
        ],
    )
    state = run_to_completion(
        state,
        {
            "type": "UtteranceUserActionFinished",
            "final_transcript": "B",
        },
    )
    assert is_data_in_events(
        state.outgoing_events,
        [
            {
                "type": "StopUtteranceBotAction",
            },
            {
                "type": "StartUtteranceBotAction",
                "script": "B",
            },
            {
                "type": "StopUtteranceBotAction",
            },
            {
                "type": "StopUtteranceBotAction",
            },
        ],
    )


def test_when_or_group_mechanics():
    """"""

    content = """
    flow user said $transcript
      match UtteranceUserAction.Finished(final_transcript=$transcript)

    flow main
      while True
        when UtteranceUserActionFinished(final_transcript="A")
          start UtteranceBotAction(script="A")
        orwhen (user said "B" and user said "C")
          start UtteranceBotAction(script="BC")
        orwhen (user said "D" or user said "E")
          start UtteranceBotAction(script="DE")
          break
    """

    config = _init_state(content)
    state = run_to_completion(config, start_main_flow_event)
    assert is_data_in_events(
        state.outgoing_events,
        [],
    )
    state = run_to_completion(
        state,
        {
            "type": "UtteranceUserActionFinished",
            "final_transcript": "A",
        },
    )
    assert is_data_in_events(
        state.outgoing_events,
        [
            {
                "type": "StartUtteranceBotAction",
                "script": "A",
            },
        ],
    )
    state = run_to_completion(
        state,
        {
            "type": "UtteranceUserActionFinished",
            "final_transcript": "B",
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
            "final_transcript": "C",
        },
    )
    assert is_data_in_events(
        state.outgoing_events,
        [
            {
                "type": "StartUtteranceBotAction",
                "script": "BC",
            },
        ],
    )
    state = run_to_completion(
        state,
        {
            "type": "UtteranceUserActionFinished",
            "final_transcript": "E",
        },
    )
    assert is_data_in_events(
        state.outgoing_events,
        [
            {
                "type": "StartUtteranceBotAction",
                "script": "DE",
            },
            {
                "type": "StopUtteranceBotAction",
            },
            {
                "type": "StopUtteranceBotAction",
            },
            {
                "type": "StopUtteranceBotAction",
            },
        ],
    )


def test_when_or_competing_events_mechanics():
    """"""

    content = """
    flow user said something
      match UtteranceUserAction.Finished()

    flow user said $transcript
      match UtteranceUserAction.Finished(final_transcript=$transcript)

    flow main
      while True
        when user said "hello"
          start UtteranceBotAction(script="A")
        orwhen user said something
          start UtteranceBotAction(script="B")
        orwhen user said "hi"
          start UtteranceBotAction(script="C")
          break
    """

    config = _init_state(content)
    state = run_to_completion(config, start_main_flow_event)
    assert is_data_in_events(
        state.outgoing_events,
        [],
    )
    state = run_to_completion(
        state,
        {
            "type": "UtteranceUserActionFinished",
            "final_transcript": "hello",
        },
    )
    assert is_data_in_events(
        state.outgoing_events,
        [
            {
                "type": "StartUtteranceBotAction",
                "script": "A",
            }
        ],
    )
    state = run_to_completion(
        state,
        {
            "type": "UtteranceUserActionFinished",
            "final_transcript": "something 123",
        },
    )
    assert is_data_in_events(
        state.outgoing_events,
        [
            {
                "type": "StartUtteranceBotAction",
                "script": "B",
            }
        ],
    )
    state = run_to_completion(
        state,
        {
            "type": "UtteranceUserActionFinished",
            "final_transcript": "hi",
        },
    )
    assert is_data_in_events(
        state.outgoing_events,
        [
            {
                "type": "StartUtteranceBotAction",
                "script": "C",
            },
            {
                "type": "StopUtteranceBotAction",
            },
            {
                "type": "StopUtteranceBotAction",
            },
            {
                "type": "StopUtteranceBotAction",
            },
        ],
    )


def test_abort_flow():
    """"""

    content = """
    flow a
      match UtteranceUserAction.Finished(final_transcript="go")
      abort
      start UtteranceBotAction(script="Error")

    flow main
      start a
      match FlowFailed(flow_id="a")
      start UtteranceBotAction(script="Success")
    """

    config = _init_state(content)
    state = run_to_completion(config, start_main_flow_event)
    assert is_data_in_events(
        state.outgoing_events,
        [],
    )
    state = run_to_completion(
        state,
        {
            "type": "UtteranceUserActionFinished",
            "final_transcript": "go",
        },
    )
    assert is_data_in_events(
        state.outgoing_events,
        [
            {
                "type": "StartUtteranceBotAction",
                "script": "Success",
            },
            {
                "type": "StopUtteranceBotAction",
            },
        ],
    )


def test_multi_flow_level_member_access():
    """"""

    content = """
    flow user said $transcript
      match UtteranceUserAction.Finished(final_transcript=$transcript) as $event
      $final_transcript = $event.arguments.final_transcript

    flow user instructed bot
      user said "do something" as $user_said_flow
      $instruction = $user_said_flow.context.final_transcript

    flow main
      await user instructed bot as $ref
      start UtteranceBotAction(script=$ref.context.instruction)
    """

    config = _init_state(content)
    state = run_to_completion(config, start_main_flow_event)
    assert is_data_in_events(
        state.outgoing_events,
        [],
    )
    state = run_to_completion(
        state,
        {
            "type": "UtteranceUserActionFinished",
            "final_transcript": "do something",
        },
    )
    assert is_data_in_events(
        state.outgoing_events,
        [
            {
                "type": "StartUtteranceBotAction",
                "script": "do something",
            },
            {
                "type": "StopUtteranceBotAction",
            },
        ],
    )


def test_FlowStart_event_fallback():
    """"""

    content = """
    flow a
      match StartFlow() as $ref
      start UtteranceBotAction(script="Success")
      send FlowStarted(flow_id=$ref.arguments.flow_id,param="test")

    flow main
      start a
      start unknown fl $param="test"
      start UtteranceBotAction(script="End")
    """

    config = _init_state(content)
    state = run_to_completion(config, start_main_flow_event)
    assert is_data_in_events(
        state.outgoing_events,
        [
            {
                "type": "StartUtteranceBotAction",
                "script": "Success",
            },
            {
                "type": "StopUtteranceBotAction",
            },
            {
                "type": "StartUtteranceBotAction",
                "script": "End",
            },
            {
                "type": "StopUtteranceBotAction",
            },
        ],
    )


def test_multi_level_member_match_from_reference():
    """"""

    content = """
    flow a
      match UtteranceUserAction.Finished(final_transcript="Done")

    flow main
      send StartFlow(flow_id="a")
      match FlowStarted(flow_id="a") as $event_ref
      match $event_ref.flow.Finished()
      start UtteranceBotAction(script="End")
    """

    config = _init_state(content)
    state = run_to_completion(config, start_main_flow_event)
    assert is_data_in_events(
        state.outgoing_events,
        [],
    )
    state = run_to_completion(
        state,
        {
            "type": "UtteranceUserActionFinished",
            "final_transcript": "Done",
        },
    )
    assert is_data_in_events(
        state.outgoing_events,
        [
            {
                "type": "StartUtteranceBotAction",
                "script": "End",
            },
            {
                "type": "StopUtteranceBotAction",
            },
        ],
    )


def test_flow_deactivation_on_parent_flow_finished():
    """"""

    content = """
    flow a
      start UtteranceBotAction(script="Started")
      match UtteranceUserAction.Finished(final_transcript="too late")

    flow main
      start a
    """

    config = _init_state(content)
    state = run_to_completion(config, start_main_flow_event)
    assert is_data_in_events(
        state.outgoing_events,
        [
            {
                "type": "StartUtteranceBotAction",
                "script": "Started",
            },
            {
                "type": "StopUtteranceBotAction",
            },
        ],
    )
    state = run_to_completion(
        state,
        {
            "type": "UtteranceUserActionFinished",
            "final_transcript": "too late",
        },
    )
    assert is_data_in_events(
        state.outgoing_events,
        [],
    )


def test_event_action_wrapper_abstraction():
    """"""

    content = """
    flow user said $text
      match UtteranceUserAction.Finished(final_transcript=$text) as $event

    flow bot say $text
      await UtteranceBotAction(script=$text) as $action

    flow bot express $text
      bot say $text

    flow bot express greeting
      bot express "hi"

    flow user expressed greeting
      user said "hi"
        or user said "hello"

    flow greeting
      user expressed greeting
      bot express greeting

    flow main
      activate greeting
      match UtteranceUserAction.Finished(final_transcript="End")
    """

    config = _init_state(content)
    state = run_to_completion(config, start_main_flow_event)
    assert is_data_in_events(
        state.outgoing_events,
        [],
    )
    state = run_to_completion(
        state,
        {
            "type": "UtteranceUserActionFinished",
            "final_transcript": "hi",
        },
    )
    assert is_data_in_events(
        state.outgoing_events,
        [
            {
                "type": "StartUtteranceBotAction",
                "script": "hi",
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
        [],
    )
    state = run_to_completion(
        state,
        {
            "type": "UtteranceUserActionFinished",
            "final_transcript": "hi",
        },
    )
    assert is_data_in_events(
        state.outgoing_events,
        [
            {
                "type": "StartUtteranceBotAction",
                "script": "hi",
            }
        ],
    )


# TODO: Check if we really need this
# def test_start_sibling_flow_mechanism():
#     """"""

#     content = """
#     flow a
#       match UtteranceUserAction.Finished(final_transcript="1")
#       send StartSiblingFlow(flow_id="a")
#       start UtteranceBotAction(script="A")
#       match UtteranceUserAction.Finished(final_transcript="2")
#       start UtteranceBotAction(script="B")

#     flow main
#       activate a
#       match UtteranceUserAction.Finished(final_transcript="End")
#     """

#     config = _init_state(content)
#     state = run_to_completion(config, start_main_flow_event)
#     assert is_data_in_events(
#         state.outgoing_events,
#         [],
#     )
#     state = run_to_completion(
#         state,
#         {
#             "type": "UtteranceUserActionFinished",
#             "final_transcript": "1",
#         },
#     )
#     assert is_data_in_events(
#         state.outgoing_events,
#         [
#             {
#                 "type": "StartUtteranceBotAction",
#                 "script": "A",
#             },
#         ],
#     )
#     state = run_to_completion(
#         state,
#         {
#             "type": "UtteranceUserActionFinished",
#             "final_transcript": "1",
#         },
#     )
#     assert is_data_in_events(
#         state.outgoing_events,
#         [
#             {
#                 "type": "StartUtteranceBotAction",
#                 "script": "A",
#             },
#         ],
#     )
#     state = run_to_completion(
#         state,
#         {
#             "type": "UtteranceUserActionFinished",
#             "final_transcript": "2",
#         },
#     )
#     assert is_data_in_events(
#         state.outgoing_events,
#         [
#             {
#                 "type": "StartUtteranceBotAction",
#                 "script": "B",
#             },
#             {
#                 "type": "StopUtteranceBotAction",
#             },
#             {
#                 "type": "StopUtteranceBotAction",
#             },
#             {
#                 "type": "StopUtteranceBotAction",
#             },
#         ],
#     )
#     state = run_to_completion(
#         state,
#         {
#             "type": "UtteranceUserActionFinished",
#             "final_transcript": "1",
#         },
#     )
#     assert is_data_in_events(
#         state.outgoing_events,
#         [
#             {
#                 "type": "StartUtteranceBotAction",
#                 "script": "A",
#             },
#         ],
#     )


# def test_stop_flow():
#     """"""

#     content = """
#     flow user said $transcript
#       match UtteranceUserAction.Finished(final_transcript=$transcript)

#     flow user said failed $transcript
#       match (user said $transcript).Failed()
#       start UtteranceBotAction(script="flow user said {$transcript} failed")

#     flow main
#       activate user said failed "hi" and user said failed "bye"
#       start user said "hi" and user said "bye"

#       match UtteranceUserAction.Finished(final_transcript="step 1")
#       stop user said "hi"
#       match UtteranceUserAction.Finished(final_transcript="step 2")
#       stop user said "bye"

#       start user said "hi" and user said "bye"
#       match UtteranceUserAction.Finished(final_transcript="step 3")
#       stop user said
#     """

#     config = _init_state(content)
#     state = run_to_completion(config, start_main_flow_event)
#     assert is_data_in_events(
#         state.outgoing_events,
#         [],
#     )
#     state = run_to_completion(
#         state,
#         {
#             "type": "UtteranceUserActionFinished",
#             "final_transcript": "step 1",
#         },
#     )
#     assert is_data_in_events(
#         state.outgoing_events,
#         [
#             {
#                 "type": "StartUtteranceBotAction",
#                 "script": "flow user said hi failed",
#             },
#         ],
#     )
#     state = run_to_completion(
#         state,
#         {
#             "type": "UtteranceUserActionFinished",
#             "final_transcript": "step 2",
#         },
#     )
#     assert is_data_in_events(
#         state.outgoing_events,
#         [
#             {
#                 "type": "StartUtteranceBotAction",
#                 "script": "flow user said bye failed",
#             },
#         ],
#     )
#     state = run_to_completion(
#         state,
#         {
#             "type": "UtteranceUserActionFinished",
#             "final_transcript": "step 3",
#         },
#     )
#     assert is_data_in_events(
#         state.outgoing_events,
#         [
#             {
#                 "type": "StartUtteranceBotAction",
#                 "script": "flow user said hi failed",
#             },
#             {
#                 "type": "StartUtteranceBotAction",
#                 "script": "flow user said bye failed",
#             },
#         ],
#     )


def test_user_action_reference():
    """"""

    content = """
    flow main
      match UtteranceUserAction.Started() as $event_ref
      start UtteranceBotAction(script="Started user action: {$event_ref.action.name}")
      match $event_ref.action.Finished(final_transcript="End")
      start UtteranceBotAction(script="Success")
    """

    config = _init_state(content)
    state = run_to_completion(config, start_main_flow_event)
    assert is_data_in_events(
        state.outgoing_events,
        [],
    )
    state = run_to_completion(
        state,
        {
            "type": "UtteranceUserActionStarted",
            "uid": "d4a265bb-4a27-4d28-8ca5-80cc73dc4707",
            "event_created_at": "2023-09-12T13:01:16.334940+00:00",
            "source_uid": "umim_tui_app",
            "action_uid": "cc63b1a0-5703-4e80-b66b-2734c13abcf3",
            "action_info_modality": "user_speech",
        },
    )
    assert is_data_in_events(
        state.outgoing_events,
        [
            {
                "type": "StartUtteranceBotAction",
                "script": "Started user action: UtteranceUserAction",
            },
        ],
    )
    state = run_to_completion(
        state,
        {
            "type": "UtteranceUserActionFinished",
            "uid": "d4a265bb-4a27-4d28-8ca5-80cc73dc4707",
            "event_created_at": "2023-09-12T13:01:16.334940+00:00",
            "source_uid": "umim_tui_app",
            "action_uid": "cc63b1a0-5703-4e80-b66b-2734c13abcf3",
            "final_transcript": "End",
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
                "script": "Success",
            },
            {
                "type": "StopUtteranceBotAction",
            },
            {
                "type": "StopUtteranceBotAction",
            },
        ],
    )


def test_stop_bot_action():
    """"""

    content = """
    flow main
      start UtteranceBotAction(script="This is a long sentence...") as $ref
      match UtteranceUserAction.Finished(final_transcript="Stop")
      send $ref.Stop()
    """

    config = _init_state(content)
    state = run_to_completion(config, start_main_flow_event)
    assert is_data_in_events(
        state.outgoing_events,
        [
            {
                "type": "StartUtteranceBotAction",
                "script": "This is a long sentence...",
            }
        ],
    )
    state = run_to_completion(
        state,
        {"type": "UtteranceUserActionFinished", "final_transcript": "Stop"},
    )
    assert is_data_in_events(
        state.outgoing_events,
        [
            {
                "type": "StopUtteranceBotAction",
            }
        ],
    )


# TODO: Double-check if the behavior of an or-group makes sense in combination with separated interaction loops
def test_independent_flow_loop_mechanics():
    """"""

    content = """
    flow bot say $script
      # loop_id: NEW
      await UtteranceBotAction(script=$script)

    flow main
      start bot say "Hi" or bot say "Hello"
    """

    config = _init_state(content)
    state = run_to_completion(config, start_main_flow_event)
    assert is_data_in_events(
        state.outgoing_events,
        [
            {
                "type": "StartUtteranceBotAction",
                "script": "Hi",
            },
            {
                "type": "StartUtteranceBotAction",
                "script": "Hello",
            },
            {
                "type": "StopUtteranceBotAction",
            },
            {
                "type": "StopUtteranceBotAction",
            },
        ],
    )


def test_list_parameters():
    """"""

    content = """
    flow bot say $scripts
      await UtteranceBotAction(script=$scripts[0])

    flow main
      start bot say ["Hi", "Hello"]
    """

    config = _init_state(content)
    state = run_to_completion(config, start_main_flow_event)
    assert is_data_in_events(
        state.outgoing_events,
        [
            {
                "type": "StartUtteranceBotAction",
                "script": "Hi",
            },
            {
                "type": "StopUtteranceBotAction",
            },
        ],
    )


def test_dict_parameters():
    """"""

    content = """
    flow bot say $scripts
      await UtteranceBotAction(script=$scripts["value2"])

    flow main
      start bot say {"value1": "something", "value2": "Hello"}
    """

    config = _init_state(content)
    state = run_to_completion(config, start_main_flow_event)
    assert is_data_in_events(
        state.outgoing_events,
        [
            {
                "type": "StartUtteranceBotAction",
                "script": "Hello",
            },
            {
                "type": "StopUtteranceBotAction",
            },
        ],
    )


def test_mixed_multimodal_group_actions():
    """"""

    content = """
    flow bot say $text
      # llm: exclude
      await UtteranceBotAction(script=$text) as $action

    flow bot gesture $gesture
      # llm: exclude
      await GestureBotAction(gesture=$gesture) as $action

    flow bot express $text
      # llm: exclude
      await bot say $text

    flow bot express feeling well
      bot express "I am good!"
        and (bot gesture "Thumbs up" or bot gesture "Smile")

    flow bot express feeling bad
      bot express "I am not good!"
        and (bot gesture "Thumbs down" or bot gesture "Sad face")

    flow main
      #bot say "One" and (bot gesture "Two" or bot gesture "Three")
      bot express feeling well
        or bot express feeling bad
      match NeverComingEvent()
    """

    config = _init_state(content)
    state = run_to_completion(config, start_main_flow_event)
    assert is_data_in_events(
        state.outgoing_events,
        [
            {
                "type": "StartUtteranceBotAction",
            },
            {
                "type": "StartGestureBotAction",
            },
        ],
    )


if __name__ == "__main__":
    test_mixed_multimodal_group_actions()
