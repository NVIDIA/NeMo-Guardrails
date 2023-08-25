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

    # TODO: Replace bot say by UMIM action events
    # flow main
    #   await bot say "Hello world"

    config = {
        "main": FlowConfig(
            id="main",
            loop_id="main",
            elements=[
                {
                    "_type": "match_event",
                    "event_name": "StartFlow",
                    "event_params": {"flow_name": "main"},
                },
                {
                    "_type": "start_action",
                    "action_name": "utter",
                    "action_params": {"value": "'Hello world'"},
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
            "flow_name": "main",
        },
    )
    assert state.next_step == {
        "_type": "start_action",
        "action_name": "utter",
        "action_params": {"value": "'Hello world'"},
    }


def test_start_a_flow():
    """Test the start of a child flow from the main flow"""

    # TODO: Replace bot say by UMIM action events
    # flow a
    #   await bot say "Hello world"
    #
    # flow main
    #   start a

    config = {
        "a": FlowConfig(
            id="a",
            elements=[
                {
                    "_type": "match_event",
                    "event_name": "StartFlow",
                    "event_params": {"flow_name": "a"},
                },
                {
                    "_type": "run_action",
                    "action_name": "utter",
                    "action_params": {"value": "'Hello world'"},
                },
            ],
        ),
        "main": FlowConfig(
            id="main",
            loop_id="main",
            elements=[
                {
                    "_type": "match_event",
                    "event_name": "StartFlow",
                    "event_params": {"flow_name": "main"},
                },
                {
                    "_type": "send_internal_event",
                    "event_name": "StartFlow",
                    "event_params": {"flow_name": "a"},
                },
                {
                    "_type": "match_event",
                    "event_name": "FlowStarted",
                    "event_params": {"flow_name": "a"},
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
            "flow_name": "main",
        },
    )
    assert state.next_step == {
        "_type": "run_action",
        "action_name": "utter",
        "action_params": {"value": "'Hello world'"},
    }


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
                    "flow_name": "a",
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
                    "flow_name": "main",
                },
                {
                    "_type": "send_internal_event",
                    "type": "StartFlow",
                    "flow_name": "a",
                },
                {
                    "_type": "match_event",
                    "type": "FlowStarted",
                    "flow_name": "a",
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
            "flow_name": "main",
            "parent_flow_uid": state.main_flow_state.uid,
        },
    )
    assert state.next_step is None
    state = compute_next_state(
        state,
        {
            "type": "UtteranceUserActionFinished",
            "final_transcript": "Hi",
        },
    )
    assert state.next_step == {
        "_type": "run_action",
        "type": "StartUtteranceBotAction",
        "text": "Hello",
    }


if __name__ == "__main__":
    test_conflicting_actions()
