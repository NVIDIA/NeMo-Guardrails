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

from nemoguardrails.colang.v2_x.runtime.statemachine import (
    InternalEvent,
    run_to_completion,
)
from tests.utils import _init_state, is_data_in_events

FORMAT = "%(message)s"
logging.basicConfig(
    level=logging.DEBUG,
    format=FORMAT,
    datefmt="[%X,%f]",
    handlers=[RichHandler(markup=True)],
)

start_main_flow_event = InternalEvent(name="StartFlow", arguments={"flow_id": "main"})


def test_child_flow_abort():
    """Test to match failure of child flow."""

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
    """Test the action conflict resolution where main flow wins."""

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
    """Test the action conflict resolution where flow a wins."""

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
    """Test the action conflict resolution based on priorities."""

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
    """Test the action conflict resolution with event branching of different lengths."""

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
    """Test the action conflict resolution action reference sharing."""

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
            "final_script": "Hello",
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
    """Test flow parameter action wrapper mechanic."""

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
    """Test flow parameter event wrapper mechanic."""

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
    """Test positional flow parameters."""

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
    """Test default flow parameters."""

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


def test_flow_started_matching():
    """Test matching to flow started events."""

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
    """Test the activate a flow mechanism."""

    content = """
    flow a $text
      start UtteranceBotAction(script=$text)
      match UtteranceUserAction().Finished(final_transcript="Hi")
      start UtteranceBotAction(script="End")

    flow main
      activate a "Start"
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


def test_activate_and_grouping():
    """Test and-grouping with activate statement."""

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


def test_stop_activated_flow_mechanism():
    """Test to stop an activated flow."""

    content = """
    flow a
      while True
        start UtteranceBotAction(script="Start")
        match UtteranceUserAction().Finished(final_transcript="Hi")

    flow main
      activate a
      send StopFlow(flow_id="a")
      start UtteranceBotAction(script="End")
      match WaitAction().Finished()
    """

    state = run_to_completion(_init_state(content), start_main_flow_event)
    assert is_data_in_events(
        state.outgoing_events,
        [
            {
                "type": "StartUtteranceBotAction",
                "script": "Start",
            },
            {
                "type": "StopUtteranceBotAction",
            },
            {
                "type": "StartUtteranceBotAction",
                "script": "End",
            },
        ],
    )


def test_finish_flow_event():
    """Test the FinishFlow event that will immediately finish a flow."""

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


def test_match_event_specificity_mechanic():
    """Test flow conflict resolution based on event specificity."""

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
    if it is impossible to be satisfied."""

    content = """
    flow a
      await b

    flow b
      match WaitAction().Finished()

    flow c
      match UtteranceUserAction().Finished(final_transcript="Start")
      send StopFlow(flow_id="b")

    flow main
      start a as $ref_a
      start c
      match $ref_a.Failed()
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
      start b as $ref_b
      match $ref_b.Failed()

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


def test_flow_deactivation():
    """Test if an activated flow is fully stopped when parent has finished."""

    content = """
    flow a
      match UtteranceUserAction().Finished(final_transcript="Tick")
      start UtteranceBotAction(script="Tack")

    flow main
      activate a
      match UtteranceUserAction().Finished(final_transcript="Next")
      send FinishFlow(flow_id="a", deactivate=True)
      match WaitEvent()
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
            "final_transcript": "Tick",
        },
    )
    assert is_data_in_events(
        state.outgoing_events,
        [
            {
                "type": "StartUtteranceBotAction",
                "script": "Tack",
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
            "final_transcript": "Next",
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
            "final_transcript": "Tick",
        },
    )
    assert is_data_in_events(
        state.outgoing_events,
        [],
    )


def test_implicit_flow_deactivation():
    """Test if an activated flow is fully stopped when parent has finished."""

    content = """
    flow a
      activate b
      match UtteranceUserAction().Finished(final_transcript="End")
      start UtteranceBotAction(script="Done")

    flow b
      activate c
      match WaitEvent()

    flow c
      match UtteranceUserAction().Finished(final_transcript="Ping")
      start UtteranceBotAction(script="Pong")

    flow main
      await a
      match WaitEvent()
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
            "final_transcript": "Ping",
        },
    )
    assert is_data_in_events(
        state.outgoing_events,
        [
            {
                "type": "StartUtteranceBotAction",
                "script": "Pong",
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
            "final_transcript": "End",
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
    state = run_to_completion(
        state,
        {
            "type": "UtteranceUserActionFinished",
            "final_transcript": "Next",
        },
    )
    assert is_data_in_events(
        state.outgoing_events,
        [],
    )


def test_concurrent_flows_with_actions():
    """Check basic concurrent flow mechanism."""

    content = """
    flow a
      match UtteranceUserAction().Finished(final_transcript="One")
      start UtteranceBotAction(script="One")
      match UtteranceUserAction().Finished(final_transcript="Two")
      match UtteranceUserAction().Finished(final_transcript="Three")

    flow b
      match UtteranceUserAction().Finished(final_transcript="One")
      start UtteranceBotAction(script="One")
      start UtteranceBotAction(script="Two")
      match UtteranceUserAction().Finished(final_transcript="Two")

    flow c
      match UtteranceUserAction().Finished(final_transcript="One")
      start UtteranceBotAction(script="One")
      start UtteranceBotAction(script="Two")

    flow main
      await a and b and c
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
            "final_transcript": "One",
        },
    )
    assert is_data_in_events(
        state.outgoing_events,
        [
            {
                "type": "StartUtteranceBotAction",
                "script": "One",
            },
            {
                "type": "StartUtteranceBotAction",
                "script": "Two",
            },
        ],
    )
    state = run_to_completion(
        state,
        {
            "type": "UtteranceUserActionFinished",
            "final_transcript": "Two",
        },
    )
    assert is_data_in_events(
        state.outgoing_events,
        [
            {
                "type": "StopUtteranceBotAction",
            }
        ],
    )
    state = run_to_completion(
        state,
        {
            "type": "UtteranceUserActionFinished",
            "final_transcript": "Three",
        },
    )
    assert is_data_in_events(
        state.outgoing_events,
        [
            {
                "type": "StopUtteranceBotAction",
            }
        ],
    )


def test_interaction_loops():
    """Test that flows in different interaction loops don't interfere."""

    content = """
    @loop("a")
    flow a
      match UtteranceUserAction().Finished()
      start GestureBotAction(script="Smile 1")
      match UtteranceUserAction().Finished()
      start UtteranceBotAction(script="Two")
      match UtteranceUserAction().Finished()

    flow b
      match UtteranceUserAction().Finished(final_transcript="One")
      start UtteranceBotAction(script="One")
      match UtteranceUserAction().Finished(final_transcript="Two")
      start GestureBotAction(script="Smile 2")
      match UtteranceUserAction().Finished(final_transcript="Three")

    flow main
      start a and b
      match Event()
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
            "final_transcript": "One",
        },
    )
    assert is_data_in_events(
        state.outgoing_events,
        [
            {
                "type": "StartUtteranceBotAction",
                "script": "One",
            },
            {
                "type": "StartGestureBotAction",
                "script": "Smile 1",
            },
        ],
    )
    state = run_to_completion(
        state,
        {
            "type": "UtteranceUserActionFinished",
            "final_transcript": "Two",
        },
    )
    assert is_data_in_events(
        state.outgoing_events,
        [
            {
                "type": "StartGestureBotAction",
                "script": "Smile 2",
            },
            {
                "type": "StartUtteranceBotAction",
                "script": "Two",
            },
        ],
    )


def test_interaction_loop_with_new():
    """Test that flows in different interaction loops don't interfere using NEW as loop id."""

    content = """
    @loop("NEW")
    flow a
      match UtteranceUserAction().Finished()
      start GestureBotAction(script="Smile 1")
      match UtteranceUserAction().Finished()
      start UtteranceBotAction(script="Two")
      match UtteranceUserAction().Finished()

    flow b
      match UtteranceUserAction().Finished(final_transcript="One")
      start UtteranceBotAction(script="One")
      start a
      match UtteranceUserAction().Finished(final_transcript="Two")
      start GestureBotAction(script="Smile 2")
      match UtteranceUserAction().Finished(final_transcript="Three")

    flow main
      start a and b
      match Event()
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
            "final_transcript": "One",
        },
    )
    assert is_data_in_events(
        state.outgoing_events,
        [
            {
                "type": "StartUtteranceBotAction",
                "script": "One",
            },
            {
                "type": "StartGestureBotAction",
                "script": "Smile 1",
            },
        ],
    )
    state = run_to_completion(
        state,
        {
            "type": "UtteranceUserActionFinished",
            "final_transcript": "Two",
        },
    )
    assert is_data_in_events(
        state.outgoing_events,
        [
            {
                "type": "StartGestureBotAction",
                "script": "Smile 2",
            },
            {
                "type": "StartUtteranceBotAction",
                "script": "Two",
            },
            {
                "type": "StartGestureBotAction",
                "script": "Smile 1",
            },
        ],
    )


def test_flow_overriding():
    """Test flow overriding mechanic."""

    content = """
    @override
    flow a
      match UtteranceUserAction().Finished(final_transcript="One")
      await UtteranceBotAction(script="One")

    flow a
      match UtteranceUserAction().Finished(final_transcript="One")
      await UtteranceBotAction(script="Two")

    flow b
      match UtteranceUserAction().Finished(final_transcript="Two")
      await UtteranceBotAction(script="One")

    @override
    flow b
      match UtteranceUserAction().Finished(final_transcript="Two")
      await UtteranceBotAction(script="Two")

    flow main
      start a and b
      match Event()
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
            "final_transcript": "One",
        },
    )
    assert is_data_in_events(
        state.outgoing_events,
        [
            {
                "type": "StartUtteranceBotAction",
                "script": "One",
            },
        ],
    )
    state = run_to_completion(
        state,
        {
            "type": "UtteranceUserActionFinished",
            "final_transcript": "Two",
        },
    )
    assert is_data_in_events(
        state.outgoing_events,
        [
            {
                "type": "StartUtteranceBotAction",
                "script": "Two",
            },
        ],
    )


def test_flow_parameter_await_mechanism():
    """Test flow overriding mechanic."""

    content = """
    flow a $text $test
      $text = "bye"
      $test = 32
      start UtteranceBotAction(script="{$text} {$test}")

    flow main
      await a "hi" $test=123
      await UtteranceBotAction(script="Success")
      match Event()
    """

    state = run_to_completion(_init_state(content), start_main_flow_event)
    assert is_data_in_events(
        state.outgoing_events,
        [
            {
                "type": "StartUtteranceBotAction",
                "script": "bye 32",
            },
            {
                "type": "StopUtteranceBotAction",
            },
            {
                "type": "StartUtteranceBotAction",
                "script": "Success",
            },
        ],
    )


if __name__ == "__main__":
    test_flow_parameter_await_mechanism()
