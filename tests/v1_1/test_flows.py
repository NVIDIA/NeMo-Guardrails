"""Test the core flow mechanics"""
import json
import logging
import sys

from rich.logging import RichHandler

from nemoguardrails.colang import parse_colang_file
from nemoguardrails.colang.v1_1.runtime.flows import State, compute_next_state
from nemoguardrails.utils import EnhancedJSONEncoder
from tests.utils import convert_parsed_colang_to_flow_config, is_data_in_events

FORMAT = "%(message)s"
logging.basicConfig(
    level=logging.DEBUG,
    format=FORMAT,
    datefmt="[%X,%f]",
    handlers=[RichHandler(markup=True)],
)


def test_send_umim_event():
    """Test to start an UMIM event"""

    content = """
    flow main
      send StartUtteranceBotAction(script="Hello world")
    """
    config = convert_parsed_colang_to_flow_config(
        parse_colang_file(
            filename="", content=content, include_source_mapping=False, version="1.1"
        )
    )

    state = State(context={}, flow_states=[], flow_configs=config)
    state.initialize()
    json.dump(state.flow_configs, sys.stdout, indent=4, cls=EnhancedJSONEncoder)

    state = compute_next_state(
        state,
        {
            "type": "StartFlow",
            "flow_id": "main",
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
      #start UtteranceBotAction(script="Hello world") as $action_ref
      #$action_ref = UtteranceBotAction(script="Hello world")
      #send $action_ref.Start() # send StartUtteranceBotAction(script="Hello world")
    """
    config = convert_parsed_colang_to_flow_config(
        parse_colang_file(
            filename="", content=content, include_source_mapping=False, version="1.1"
        )
    )
    state = State(context={}, flow_states=[], flow_configs=config)
    state.initialize()
    json.dump(state.flow_configs, sys.stdout, indent=4, cls=EnhancedJSONEncoder)

    state = compute_next_state(
        state,
        {
            "type": "StartFlow",
            "flow_id": "main",
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


def test_await_action():
    """Test to await an UMIM action"""

    content = """
    flow main
      send StartUtteranceBotAction(script="Hello world")
      match UtteranceBotActionFinished(script="Hello world")
      send StartUtteranceBotAction(script="Done")
    """
    config = convert_parsed_colang_to_flow_config(
        parse_colang_file(
            filename="", content=content, include_source_mapping=False, version="1.1"
        )
    )

    state = State(context={}, flow_states=[], flow_configs=config)
    state.initialize()
    json.dump(state.flow_configs, sys.stdout, indent=4, cls=EnhancedJSONEncoder)

    state = compute_next_state(
        state,
        {
            "type": "StartFlow",
            "flow_id": "main",
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
    state.outgoing_events.clear()
    state = compute_next_state(
        state,
        {
            "type": "UtteranceBotActionFinished",
            "script": "Hello world",
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
    """
    config = convert_parsed_colang_to_flow_config(
        parse_colang_file(
            filename="", content=content, include_source_mapping=False, version="1.1"
        )
    )

    json.dump(config, sys.stdout, indent=4, cls=EnhancedJSONEncoder)
    state = State(context={}, flow_states=[], flow_configs=config)
    state.initialize()
    json.dump(state.flow_configs, sys.stdout, indent=4, cls=EnhancedJSONEncoder)

    state = compute_next_state(
        state,
        {
            "type": "StartFlow",
            "flow_id": "main",
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
    state.outgoing_events.clear()
    state = compute_next_state(
        state,
        {
            "type": "UtteranceBotActionFinished",
            "script": "Hello world",
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
      send StartUtteranceBotAction(script="Done")
    """
    config = convert_parsed_colang_to_flow_config(
        parse_colang_file(
            filename="", content=content, include_source_mapping=False, version="1.1"
        )
    )

    state = State(context={}, flow_states=[], flow_configs=config)
    state.initialize()
    json.dump(state.flow_configs, sys.stdout, indent=4, cls=EnhancedJSONEncoder)

    state = compute_next_state(
        state,
        {
            "type": "StartFlow",
            "flow_id": "main",
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
    state.outgoing_events.clear()
    state = compute_next_state(
        state,
        {
            "type": "UtteranceBotActionFinished",
            "script": "Hello world",
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


def test_start_a_flow():
    """Test the start of a child flow with full event notation"""

    content = """
    flow a
      send StartUtteranceBotAction(script="Hello world")

    flow main
      # start a
      send StartFlow(flow_id="a")
      match FlowStarted(flow_id="a")
    """

    config = convert_parsed_colang_to_flow_config(
        parse_colang_file(
            filename="", content=content, include_source_mapping=False, version="1.1"
        )
    )

    state = State(context={}, flow_states=[], flow_configs=config)
    state.initialize()
    json.dump(state.flow_configs, sys.stdout, indent=4, cls=EnhancedJSONEncoder)

    state = compute_next_state(
        state,
        {
            "type": "StartFlow",
            "flow_id": "main",
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


def test_start_a_flow_compact_notation():
    """Test the start of a child flow using 'start' notation"""

    content = """
    flow a
      send StartUtteranceBotAction(script="Hello world")

    flow main
      start a
    """

    config = convert_parsed_colang_to_flow_config(
        parse_colang_file(
            filename="", content=content, include_source_mapping=False, version="1.1"
        )
    )

    state = State(context={}, flow_states=[], flow_configs=config)
    state.initialize()
    json.dump(state.flow_configs, sys.stdout, indent=4, cls=EnhancedJSONEncoder)

    state = compute_next_state(
        state,
        {
            "type": "StartFlow",
            "flow_id": "main",
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


def test_await_a_flow():
    """Test await a child flow"""

    content = """
    flow a
      send StartUtteranceBotAction(script="Flow a started")

    flow main
      # await a
      send StartFlow(flow_id="a")
      match FlowStarted(flow_id="a")
      match FlowFinished(flow_id="a")
      send StartUtteranceBotAction(script="Flow a finished")
    """

    config = convert_parsed_colang_to_flow_config(
        parse_colang_file(
            filename="", content=content, include_source_mapping=False, version="1.1"
        )
    )

    state = State(context={}, flow_states=[], flow_configs=config)
    state.initialize()
    json.dump(state.flow_configs, sys.stdout, indent=4, cls=EnhancedJSONEncoder)

    state = compute_next_state(
        state,
        {
            "type": "StartFlow",
            "flow_id": "main",
        },
    )
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
      send StartUtteranceBotAction(script="Flow a started")

    flow main
      await a
      send StartUtteranceBotAction(script="Flow a finished")
    """

    config = convert_parsed_colang_to_flow_config(
        parse_colang_file(
            filename="", content=content, include_source_mapping=False, version="1.1"
        )
    )

    state = State(context={}, flow_states=[], flow_configs=config)
    state.initialize()
    json.dump(state.flow_configs, sys.stdout, indent=4, cls=EnhancedJSONEncoder)

    state = compute_next_state(
        state,
        {
            "type": "StartFlow",
            "flow_id": "main",
        },
    )
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
      send StartUtteranceBotAction(script="Hi")
      match UtteranceBotActionFinished(script="Hi")

    flow main
      # start a
      send StartFlow(flow_id="a")
      match FlowStarted(flow_id="a")
      # await a
      send StartFlow(flow_id="a")
      match FlowStarted(flow_id="a")
    """

    config = convert_parsed_colang_to_flow_config(
        parse_colang_file(
            filename="", content=content, include_source_mapping=False, version="1.1"
        )
    )

    state = State(context={}, flow_states=[], flow_configs=config)
    state.initialize()
    json.dump(state.flow_configs, sys.stdout, indent=4, cls=EnhancedJSONEncoder)

    state = compute_next_state(
        state,
        {
            "type": "StartFlow",
            "flow_id": "main",
        },
    )
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
      send StartUtteranceBotAction(script="Hi")
      match UtteranceBotActionFinished(script="Hi")

    flow main
      # start a
      send StartFlow(flow_id="a")
      match FlowStarted(flow_id="a")
      # match b.Failed()
      match FlowFailed(flow_id="b")
      # start UtteranceBotAction(script="Done")
      send StartUtteranceBotAction(script="Done")
    """
    config = convert_parsed_colang_to_flow_config(
        parse_colang_file(
            filename="", content=content, include_source_mapping=False, version="1.1"
        )
    )

    state = State(context={}, flow_states=[], flow_configs=config)
    state.initialize()
    json.dump(state.flow_configs, sys.stdout, indent=4, cls=EnhancedJSONEncoder)

    state = compute_next_state(
        state,
        {
            "type": "StartFlow",
            "flow_id": "main",
        },
    )
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
      send StartUtteranceBotAction(script="Hello")
      send StartUtteranceBotAction(script="How are you")

    flow main
      # start a
      send StartFlow(flow_id="a")
      match FlowStarted(flow_id="a")
      match UtteranceUserActionFinished(final_transcript="Hi")
      send StartUtteranceBotAction(script="Hello")
      send StartUtteranceBotAction(script="Bye")
    """

    config = convert_parsed_colang_to_flow_config(
        parse_colang_file(
            filename="", content=content, include_source_mapping=False, version="1.1"
        )
    )

    state = State(context={}, flow_states=[], flow_configs=config)
    state.initialize()
    json.dump(state.flow_configs, sys.stdout, indent=4, cls=EnhancedJSONEncoder)

    state = compute_next_state(
        state,
        {
            "type": "StartFlow",
            "flow_id": "main",
        },
    )
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

    result = parse_colang_file(
        filename="", content=content, include_source_mapping=False, version="1.1"
    )
    config = convert_parsed_colang_to_flow_config(result)

    json.dump(config, sys.stdout, indent=4, cls=EnhancedJSONEncoder)
    state = State(context={}, flow_states=[], flow_configs=config)
    state.initialize()
    json.dump(state.flow_configs, sys.stdout, indent=4, cls=EnhancedJSONEncoder)

    state = compute_next_state(
        state,
        {
            "type": "StartFlow",
            "flow_id": "main",
        },
    )
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
    test_await_action_with_reference()
