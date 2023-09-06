"""Test the core flow mechanics"""
import json
import logging
import sys

from rich.logging import RichHandler

from nemoguardrails.colang import parse_colang_file
from nemoguardrails.colang.v1_1.runtime.flows import (
    ActionStatus,
    State,
    compute_next_state,
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

start_main_flow_event = {
    "type": "StartFlow",
    "flow_id": "main",
}


def _init_state(colang_content) -> State:
    config = convert_parsed_colang_to_flow_config(
        parse_colang_file(
            filename="",
            content=colang_content,
            include_source_mapping=False,
            version="1.1",
        )
    )

    state = State(context={}, flow_states=[], flow_configs=config)
    state.initialize()
    json.dump(state.flow_configs, sys.stdout, indent=4, cls=EnhancedJSONEncoder)

    return state


def test_send_umim_event():
    """Test to start an UMIM event"""

    content = """
    flow main
      start UtteranceBotAction(script="Hello world")
    """

    state = compute_next_state(_init_state(content), start_main_flow_event)
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
      #start UtteranceBotAction(script="Hello world") as $action_ref
      #$action_ref = UtteranceBotAction(script="Hello world")
      #send $action_ref.Start() # start UtteranceBotAction(script="Hello world")
    """
    state = compute_next_state(_init_state(content), start_main_flow_event)
    assert is_data_in_events(
        state.outgoing_events,
        [
            {
                "type": "StartUtteranceBotAction",
                "script": "Hello world",
            }
        ],
    )


def test_await_action():
    """Test to await an UMIM action"""

    content = """
    flow main
      start UtteranceBotAction(script="Hello world")
      match UtteranceBotActionFinished(final_script="Hello world")
      start UtteranceBotAction(script="Done")
    """
    state = compute_next_state(_init_state(content), start_main_flow_event)
    assert is_data_in_events(
        state.outgoing_events,
        [
            {
                "type": "StartUtteranceBotAction",
                "script": "Hello world",
            }
        ],
    )
    state.outgoing_events.clear()
    state = compute_next_state(
        state,
        {
            "type": "UtteranceBotActionFinished",
            "final_script": "Hello world",
        },
    )
    assert is_data_in_events(
        state.outgoing_events,
        [
            {
                "type": "StartUtteranceBotAction",
                "script": "Done",
            }
        ],
    )


def test_await_action_compact_notation():
    """Test to await an UMIM action with compact notation"""

    content = """
    flow main
      await UtteranceBotAction(script="Hello world")
      start UtteranceBotAction(script="Done")
    """
    state = compute_next_state(_init_state(content), start_main_flow_event)
    assert is_data_in_events(
        state.outgoing_events,
        [
            {
                "type": "StartUtteranceBotAction",
                "script": "Hello world",
            }
        ],
    )
    action_uid = state.outgoing_events[0]["action_uid"]
    state.outgoing_events.clear()
    state = compute_next_state(
        state,
        {
            "type": "UtteranceBotActionFinished",
            "final_script": "Hello world",
            "action_uid": action_uid,
        },
    )
    assert is_data_in_events(
        state.outgoing_events,
        [
            {
                "type": "StartUtteranceBotAction",
                "script": "Done",
            }
        ],
    )


def test_await_action_with_reference():
    """Test to await an UMIM action"""

    content = """
    flow main
      start UtteranceBotAction(script="Hello world") as $action_ref
      match $action_ref.Finished()
      start UtteranceBotAction(script="Done")
    """
    state = compute_next_state(_init_state(content), start_main_flow_event)
    assert is_data_in_events(
        state.outgoing_events,
        [
            {
                "type": "StartUtteranceBotAction",
                "script": "Hello world",
            }
        ],
    )
    action_uid = state.outgoing_events[0]["action_uid"]
    state.outgoing_events.clear()
    state = compute_next_state(
        state,
        {
            "type": "UtteranceBotActionFinished",
            "final_script": "Hello world",
            "action_uid": action_uid,
        },
    )
    assert is_data_in_events(
        state.outgoing_events,
        [
            {
                "type": "StartUtteranceBotAction",
                "script": "Done",
            }
        ],
    )


def test_action_state_update():
    """Test the action state update"""

    content = """
    flow main
      start UtteranceBotAction(script="Hello world") as $action_ref1
      start UtteranceBotAction(script="Hi") as $action_ref2
      match $action_ref1.Finished()
    """
    state = compute_next_state(_init_state(content), start_main_flow_event)
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
    state.outgoing_events.clear()
    action_ref2 = state.main_flow_state.context["action_ref2"]
    action_uid = action_ref2["value"]
    state = compute_next_state(
        state,
        {
            "type": "UtteranceBotActionFinished",
            "final_script": "Hi",
            "action_uid": action_uid,
        },
    )
    assert state.main_flow_state.actions[action_uid].status == ActionStatus.FINISHED


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

    state = compute_next_state(_init_state(content), start_main_flow_event)
    assert is_data_in_events(
        state.outgoing_events,
        [
            {
                "type": "StartUtteranceBotAction",
                "script": "Hello world",
            }
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

    state = compute_next_state(_init_state(content), start_main_flow_event)
    assert is_data_in_events(
        state.outgoing_events,
        [
            {
                "type": "StartUtteranceBotAction",
                "script": "Hello world",
            }
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

    state = compute_next_state(_init_state(content), start_main_flow_event)
    assert is_data_in_events(
        state.outgoing_events,
        [
            {
                "type": "StartUtteranceBotAction",
                "script": "Flow a started",
            },
            {
                "type": "StartUtteranceBotAction",
                "script": "Flow a finished",
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

    state = compute_next_state(_init_state(content), start_main_flow_event)
    assert is_data_in_events(
        state.outgoing_events,
        [
            {
                "type": "StartUtteranceBotAction",
                "script": "Flow a started",
            },
            {
                "type": "StartUtteranceBotAction",
                "script": "Flow a finished",
            },
        ],
    )


def test_start_child_flow_two_times():
    """Test start a child flow two times"""

    content = """
    flow a
      start UtteranceBotAction(script="Hi")
      match UtteranceBotActionFinished(final_script="Hi")

    flow main
      # start a
      send StartFlow(flow_id="a")
      match FlowStarted(flow_id="a")
      # await a
      send StartFlow(flow_id="a")
      match FlowStarted(flow_id="a")
    """

    state = compute_next_state(_init_state(content), start_main_flow_event)
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
      # start b
      send StartFlow(flow_id="b")
      match FlowStarted(flow_id="b")

    flow b
      # await UtteranceBotAction(script="Hi")
      start UtteranceBotAction(script="Hi")
      match UtteranceBotActionFinished(final_script="Hi")

    flow main
      # start a
      send StartFlow(flow_id="a")
      match FlowStarted(flow_id="a")
      # match b.Failed()
      match FlowFailed(flow_id="b")
      # start UtteranceBotAction(script="Done")
      start UtteranceBotAction(script="Done")
    """
    state = compute_next_state(_init_state(content), start_main_flow_event)
    assert is_data_in_events(
        state.outgoing_events,
        [
            {
                "type": "StartUtteranceBotAction",
                "script": "Hi",
            },
            {
                "type": "StartUtteranceBotAction",
                "script": "Done",
            },
        ],
    )


def test_conflicting_actions():
    """Test the action conflict resolution"""

    content = """
    flow a
      match UtteranceUserActionFinished(final_transcript="Hi")
      start UtteranceBotAction(script="Hello")
      start UtteranceBotAction(script="How are you")

    flow main
      # start a
      send StartFlow(flow_id="a")
      match FlowStarted(flow_id="a")
      match UtteranceUserActionFinished(final_transcript="Hi")
      start UtteranceBotAction(script="Hello")
      start UtteranceBotAction(script="Bye")
    """

    state = compute_next_state(_init_state(content), start_main_flow_event)
    assert state.outgoing_events == []
    state = compute_next_state(
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
        ],
    )


def test_flow_parameters():
    """Test the action conflict resolution"""

    content = """
    flow bot say $script
      await UtteranceBotAction(script=$script)

    flow main
      await bot say $script="Hi"
    """

    state = compute_next_state(_init_state(content), start_main_flow_event)
    assert state.outgoing_events == []
    state = compute_next_state(
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
        ],
    )


if __name__ == "__main__":
    test_send_umim_event()
