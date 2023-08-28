"""Test the core flow mechanics"""
import logging

from rich.logging import RichHandler

from nemoguardrails.colang.v1_1.runtime.flows import (
    FlowConfig,
    InteractionLoopType,
    State,
    compute_next_state,
)

FORMAT = "%(message)s"
logging.basicConfig(
    level=logging.DEBUG,
    format=FORMAT,
    datefmt="[%X,%f]",
    handlers=[RichHandler(markup=True)],
)


def test_start_main_flow():
    """Test the start of the main flow"""

    # flow main
    #   send UtteranceBotAction("Hello world").Start()

    config = {
        "main": FlowConfig(
            id="main",
            loop_id="main",
            elements=[
                {
                    "_type": "match_event",
                    "type": "StartFlow",
                    "flow_id": "main",
                },
                {
                    "_type": "run_action",
                    "type": "StartUtteranceBotAction",
                    "text": "Hello world",
                },
            ],
        ),
    }

    state = State(context={}, flow_states=[], flow_configs=config)
    state.initialize()

    state = compute_next_state(
        state,
        {
            "type": "StartFlow",
            "flow_id": "main",
            "parent_flow_uid": state.main_flow_state.uid,
        },
    )
    assert state.next_steps == [
        {
            "_type": "run_action",
            "type": "StartUtteranceBotAction",
            "text": "Hello world",
        }
    ]


def test_start_a_flow():
    """Test the start of a child flow"""

    # flow a
    #   send UtteranceBotAction("Hello world").Start()
    #
    # flow main
    #   start a

    config = {
        "a": FlowConfig(
            id="a",
            elements=[
                {
                    "_type": "match_event",
                    "type": "StartFlow",
                    "flow_id": "a",
                },
                {
                    "_type": "run_action",
                    "type": "StartUtteranceBotAction",
                    "text": "Hello world",
                },
            ],
        ),
        "main": FlowConfig(
            id="main",
            loop_id="main",
            elements=[
                {
                    "_type": "match_event",
                    "type": "StartFlow",
                    "flow_id": "main",
                },
                {
                    "_type": "send_internal_event",
                    "type": "StartFlow",
                    "flow_id": "a",
                },
                {
                    "_type": "match_event",
                    "type": "FlowStarted",
                    "flow_id": "a",
                },
            ],
        ),
    }

    state = State(context={}, flow_states=[], flow_configs=config)
    state.initialize()

    state = compute_next_state(
        state,
        {
            "type": "StartFlow",
            "flow_id": "main",
            "parent_flow_uid": state.main_flow_state.uid,
        },
    )
    assert state.next_steps == [
        {
            "_type": "run_action",
            "type": "StartUtteranceBotAction",
            "text": "Hello world",
        }
    ]


def test_await_a_flow():
    """Test await a child flow"""

    # flow a
    #   send UtteranceBotAction("Flow a started").Start()
    #
    # flow main
    #   await a
    #   send UtteranceBotAction("Flow a finished").Start()

    config = {
        "a": FlowConfig(
            id="a",
            elements=[
                {
                    "_type": "match_event",
                    "type": "StartFlow",
                    "flow_id": "a",
                },
                {
                    "_type": "run_action",
                    "type": "StartUtteranceBotAction",
                    "text": "Flow a started",
                },
            ],
        ),
        "main": FlowConfig(
            id="main",
            loop_id="main",
            elements=[
                {
                    "_type": "match_event",
                    "type": "StartFlow",
                    "flow_id": "main",
                },
                {
                    "_type": "send_internal_event",
                    "type": "StartFlow",
                    "flow_id": "a",
                },
                {
                    "_type": "match_event",
                    "type": "FlowStarted",
                    "flow_id": "a",
                },
                {
                    "_type": "match_event",
                    "type": "FlowFinished",
                    "flow_id": "a",
                },
            ],
        ),
    }

    state = State(context={}, flow_states=[], flow_configs=config)
    state.initialize()

    state = compute_next_state(
        state,
        {
            "type": "StartFlow",
            "flow_id": "main",
            "parent_flow_uid": state.main_flow_state.uid,
        },
    )
    assert state.next_steps == [
        {
            "_type": "run_action",
            "type": "StartUtteranceBotAction",
            "text": "Flow a started",
        }
    ]


def test_start_child_flow_two_times():
    """Test start a child flow two times"""

    # flow a
    #   send UtteranceBotAction("Hi").Start()
    #   match UtteranceBotAction("Hi").Finished()
    #
    # flow main
    #   start a
    #   await a

    config = {
        "a": FlowConfig(
            id="a",
            elements=[
                {
                    "_type": "match_event",
                    "type": "StartFlow",
                    "flow_id": "a",
                },
                {
                    "_type": "run_action",
                    "type": "StartUtteranceBotAction",
                    "text": "Hi",
                },
                {
                    "_type": "match_event",
                    "type": "UtteranceBotFinished",
                    "text": "Hi",
                },
            ],
        ),
        "main": FlowConfig(
            id="main",
            loop_id="main",
            elements=[
                {
                    "_type": "match_event",
                    "type": "StartFlow",
                    "flow_id": "main",
                },
                {
                    "_type": "send_internal_event",
                    "type": "StartFlow",
                    "flow_id": "a",
                },
                {
                    "_type": "match_event",
                    "type": "FlowStarted",
                    "flow_id": "a",
                },
                {
                    "_type": "send_internal_event",
                    "type": "StartFlow",
                    "flow_id": "a",
                },
                {
                    "_type": "match_event",
                    "type": "FlowStarted",
                    "flow_id": "a",
                },
                {
                    "_type": "match_event",
                    "type": "FlowFinished",
                    "flow_id": "a",
                },
            ],
        ),
    }

    state = State(context={}, flow_states=[], flow_configs=config)
    state.initialize()

    state = compute_next_state(
        state,
        {
            "type": "StartFlow",
            "flow_id": "main",
            "parent_flow_uid": state.main_flow_state.uid,
        },
    )
    assert state.next_steps == [
        {
            "_type": "run_action",
            "type": "StartUtteranceBotAction",
            "text": "Hi",
        },
        {
            "_type": "run_action",
            "type": "StartUtteranceBotAction",
            "text": "Hi",
        },
    ]


def test_conflicting_actions():
    """Test the action conflict resolution"""

    # flow a
    #   match UtteranceUserAction("Hi").Finished()
    #   send UtteranceBotAction("Hello").Start()
    #   send UtteranceBotAction("How are you").Start()
    #
    # flow main
    #   start a
    #   match UtteranceUserAction("Hi").Finished()
    #   send UtteranceBotAction("Hello").Start()
    #   send UtteranceBotAction("Bye").Start()

    config = {
        "a": FlowConfig(
            id="a",
            elements=[
                {
                    "_type": "match_event",
                    "type": "StartFlow",
                    "flow_id": "a",
                },
                {
                    "_type": "match_event",
                    "type": "UtteranceUserActionFinished",
                    "final_transcript": "Hi",
                },
                {
                    "_type": "run_action",
                    "type": "StartUtteranceBotAction",
                    "text": "Hello",
                },
                {
                    "_type": "run_action",
                    "type": "StartUtteranceBotAction",
                    "text": "How are you",
                },
            ],
        ),
        "main": FlowConfig(
            id="main",
            loop_id="main",
            elements=[
                {
                    "_type": "match_event",
                    "type": "StartFlow",
                    "flow_id": "main",
                },
                {
                    "_type": "send_internal_event",
                    "type": "StartFlow",
                    "flow_id": "a",
                },
                {
                    "_type": "match_event",
                    "type": "FlowStarted",
                    "flow_id": "a",
                },
                {
                    "_type": "match_event",
                    "type": "UtteranceUserActionFinished",
                    "final_transcript": "Hi",
                },
                {
                    "_type": "run_action",
                    "type": "StartUtteranceBotAction",
                    "text": "Hello",
                },
                {
                    "_type": "run_action",
                    "type": "StartUtteranceBotAction",
                    "text": "Bye",
                },
            ],
        ),
    }

    state = State(context={}, flow_states=[], flow_configs=config)
    state.initialize()

    state = compute_next_state(
        state,
        {
            "type": "StartFlow",
            "flow_id": "main",
            "parent_flow_uid": state.main_flow_state.uid,
        },
    )
    assert state.next_steps == []
    state = compute_next_state(
        state,
        {
            "type": "UtteranceUserActionFinished",
            "final_transcript": "Hi",
        },
    )
    assert state.next_steps == [
        {
            "_type": "run_action",
            "type": "StartUtteranceBotAction",
            "text": "Hello",
        },
        {
            "_type": "run_action",
            "type": "StartUtteranceBotAction",
            "text": "How are you",
        },
    ]


if __name__ == "__main__":
    test_start_main_flow()
