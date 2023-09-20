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
    level=logging.INFO,
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


def test_match_umim_event():
    """Test to match an UMIM event"""

    content = """
    flow main
      match UtteranceUserAction.Finished(final_transcript="Hi")
      send StartUtteranceBotAction(script="Hello world")
    """

    state = compute_next_state(_init_state(content), start_main_flow_event)
    assert is_data_in_events(
        state.outgoing_events,
        [],
    )
    state = compute_next_state(
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


def test_start_match_action_on_action_parameter():
    """Test to start and match an UMIM action based on action parameters"""

    content = """
    flow main
      start UtteranceBotAction(script="Hello world")
      match UtteranceBotAction(script="Hello world").Finished()
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
    state = compute_next_state(
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
            }
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
    state = compute_next_state(
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
    state = compute_next_state(
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
            }
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
    state = compute_next_state(
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
    state = compute_next_state(
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
            }
        ],
    )


def test_await_action():
    """Test to await an UMIM action"""

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
    state = compute_next_state(
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
            }
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
    action_uid = state.outgoing_events[1]["action_uid"]
    state = compute_next_state(
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
      await UtteranceBotAction(script="Hi")

    flow main
      start a
      await a
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
      start b

    flow b
      await UtteranceBotAction(script="Hi")

    flow main
      start a
      # b.Failed()
      match FlowFailed(flow_id="b")
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
                "script": "How are you",
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


def test_conflicting_actions_reference_sharing():
    """Test the action conflict resolution"""

    content = """
    flow a
      match UtteranceUserAction.Finished()
      start UtteranceBotAction(script="Hello") as $ref
      match $ref.Finished()
      start UtteranceBotAction(script="How are you")
      match UtteranceUserAction.Finished()
      start UtteranceBotAction(script="Perfect")

    flow main
      start a
      match UtteranceUserAction.Finished(final_transcript="Hi")
      start UtteranceBotAction(script="Hello") as $ref
      match $ref.Finished()
      start UtteranceBotAction(script="How are you")
      start UtteranceBotAction(script="Great")
      match UtteranceUserAction.Finished()
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
            }
        ],
    )
    state = compute_next_state(
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
    state = compute_next_state(
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
                "type": "StartUtteranceBotAction",
                "script": "Perfect",
            }
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

    state = compute_next_state(_init_state(content), start_main_flow_event)
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
                "script": "Yes",
            }
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

    state = compute_next_state(_init_state(content), start_main_flow_event)
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

    state = compute_next_state(_init_state(content), start_main_flow_event)
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
      match UtteranceUserAction(final_transcript="wait")
    """

    state = compute_next_state(_init_state(content), start_main_flow_event)
    assert state.outgoing_events == []
    state = compute_next_state(
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

    state = compute_next_state(_init_state(content), start_main_flow_event)
    assert is_data_in_events(
        state.outgoing_events,
        [
            {
                "type": "StartUtteranceBotAction",
                "script": "Start",
            }
        ],
    )
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
                "script": "End",
            },
            {
                "type": "StartUtteranceBotAction",
                "script": "Start",
            },
        ],
    )
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
                "script": "End",
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

    state = compute_next_state(_init_state(content), start_main_flow_event)
    assert is_data_in_events(
        state.outgoing_events,
        [
            {
                "type": "StartUtteranceBotAction",
                "script": "Hi",
            },
        ],
    )
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
                "script": "Yes",
            }
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
      send AbortFlow(flow_id="b")

    flow main
      start a
      start c
      match FlowFailed(flow_id="a")
      await UtteranceBotAction(script="Yes")
    """

    state = compute_next_state(_init_state(content), start_main_flow_event)
    assert is_data_in_events(
        state.outgoing_events,
        [],
    )
    state = compute_next_state(
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
      send AbortFlow(flow_id="b")
      match WaitAction().Finished()
    """

    state = compute_next_state(_init_state(content), start_main_flow_event)
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

    state = compute_next_state(_init_state(content), start_main_flow_event)
    assert is_data_in_events(
        state.outgoing_events,
        [],
    )
    state = compute_next_state(
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
    state = compute_next_state(config, start_main_flow_event)
    assert is_data_in_events(
        state.outgoing_events,
        [],
    )
    state = compute_next_state(
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
        ],
    )


# def test_while_loop_break_mechanic():
#     """"""

#     content = """
#     flow main

#       while $ref is None
#         match UtteranceUserAction().Finished(final_transcript="End") as $ref
#         break
#         start UtteranceBotAction(script="Test")

#       start UtteranceBotAction(script="Done")
#     """

#     config = _init_state(content)
#     state = compute_next_state(config, start_main_flow_event)
#     assert is_data_in_events(
#         state.outgoing_events,
#         [],
#     )


def test_start_grouping():
    """"""

    content = """
    flow bot say $script
      await UtteranceBotAction(script=$script)

    flow main
        start bot say "A"
          and bot say "B"
          and UtteranceBotAction(script="C")
          and bot say "A"
    """

    state = compute_next_state(_init_state(content), start_main_flow_event)
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


def test_match_or_grouping():
    """"""

    content = """
    flow user said $transcript
      match UtteranceUserAction().Finished(final_transcript=$transcript)

    flow main
        await user said "A"
          or UtteranceUserAction().Finished(final_transcript="B")
          or user said "C"
        start UtteranceBotAction(script="Match")
    """

    state = compute_next_state(_init_state(content), start_main_flow_event)
    assert is_data_in_events(
        state.outgoing_events,
        [],
    )
    state = compute_next_state(
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
                "script": "Match",
            },
        ],
    )
    state = compute_next_state(_init_state(content), start_main_flow_event)
    assert is_data_in_events(
        state.outgoing_events,
        [],
    )
    state = compute_next_state(
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
        ],
    )
    state = compute_next_state(_init_state(content), start_main_flow_event)
    assert is_data_in_events(
        state.outgoing_events,
        [],
    )
    state = compute_next_state(
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
                "script": "Match",
            },
        ],
    )


def test_match_and_or_grouping():
    """"""

    content = """
    flow user said $transcript
      match UtteranceUserAction().Finished(final_transcript=$transcript)

    flow main
        await (user said "A" and user said "B")
          or (user said "C" and user said "D")
        start UtteranceBotAction(script="Match")
    """

    state = compute_next_state(_init_state(content), start_main_flow_event)
    assert is_data_in_events(
        state.outgoing_events,
        [],
    )
    state = compute_next_state(
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
    state = compute_next_state(
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
    state = compute_next_state(
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
        ],
    )

    state = compute_next_state(_init_state(content), start_main_flow_event)
    assert is_data_in_events(
        state.outgoing_events,
        [],
    )
    state = compute_next_state(
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
    state = compute_next_state(
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
    state = compute_next_state(
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

    state = compute_next_state(_init_state(content), start_main_flow_event)
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
    state = compute_next_state(
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
                "type": "StartUtteranceBotAction",
                "script": "A",
            },
        ],
    )
    state = compute_next_state(
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
    state = compute_next_state(config, start_main_flow_event)
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
    state = compute_next_state(config, start_main_flow_event)
    assert is_data_in_events(
        state.outgoing_events,
        [],
    )
    state = compute_next_state(
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
            }
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
    state = compute_next_state(config, start_main_flow_event)
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
        ],
    )


if __name__ == "__main__":
    test_if_branching_mechanic()
