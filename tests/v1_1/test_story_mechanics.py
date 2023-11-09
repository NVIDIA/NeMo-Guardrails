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
import logging

from rich.logging import RichHandler

from nemoguardrails.colang.v1_1.runtime.flows import ActionStatus
from nemoguardrails.colang.v1_1.runtime.statemachine import (
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


def test_when_else_deep_hierarchy_case_match():
    """"""

    content = """
    flow user said $transcript
      match UtteranceUserAction().Finished(final_transcript=$transcript)

    flow bot say $script
      await UtteranceBotAction(script=$script)

    flow bot said something
      match UtteranceBotAction().Finished()

    flow bot asked something
      match FlowFinished(flow_id="bot ask")

    flow bot ask $text
      await bot say $text

    flow observer
      # meta: loop_id=observer
      while True
        when bot asked something
          start GestureBotAction(gesture="Case 1")
        orwhen bot said something
          start GestureBotAction(gesture="Case 2")

    flow main
      activate observer
      bot say "Hi"
      bot ask "How are you"
      match WaitAction().Finished()
    """

    config = _init_state(content)
    state = run_to_completion(config, start_main_flow_event)
    assert is_data_in_events(
        state.outgoing_events,
        [
            {
                "type": "StartUtteranceBotAction",
                "script": "Hi",
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
        [
            {
                "type": "StartUtteranceBotAction",
                "script": "How are you",
            },
            {
                "type": "StartGestureBotAction",
                "gesture": "Case 2",
            },
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
        [
            {
                "type": "StartGestureBotAction",
                "gesture": "Case 1",
            },
        ],
    )


def test_when_conflict_issue():
    """"""

    content = """
    flow user said something
      match UtteranceUserAction.Finished() as $event

    flow bot say $script
      await UtteranceBotAction(script=$script)

    flow bot said something
      match UtteranceBotAction().Finished()

    flow observer
      # meta: loop_id=observer
      while True
        when bot said something or user said something
          start GestureBotAction(gesture="test")

    flow main
      activate observer
      bot say "Start"
      when user said something
        bot say "Ok"
    """

    config = _init_state(content)
    state = run_to_completion(config, start_main_flow_event)
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
            "type": "UtteranceBotActionFinished",
            "final_script": state.outgoing_events[0]["script"],
            "action_uid": state.outgoing_events[0]["action_uid"],
        },
    )
    assert is_data_in_events(
        state.outgoing_events,
        [
            {
                "type": "StartGestureBotAction",
                "gesture": "test",
            }
        ],
    )
    state = run_to_completion(
        state,
        {
            "type": "UtteranceUserActionFinished",
            "final_transcript": "Something",
        },
    )
    assert is_data_in_events(
        state.outgoing_events,
        [
            {
                "type": "StartGestureBotAction",
                "gesture": "test",
            },
            {
                "type": "StartUtteranceBotAction",
                "script": "Ok",
            },
        ],
    )


def test_flow_event_competition():
    """"""

    content = """
    flow a
      match UtteranceUserAction.Finished(final_transcript="Start")
      send TestEvent1()

    flow main
      start a
      match UtteranceUserAction.Finished()
      send TestEvent2()
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
            "final_transcript": "Start",
        },
    )
    assert is_data_in_events(
        state.outgoing_events,
        [
            {
                "type": "TestEvent1",
            }
        ],
    )


def test_flow_bot_question_repetition():
    """"""

    content = """
    flow _bot_say $text
      await UtteranceBotAction(script=$text) as $action

    flow bot gesture $gesture
      await GestureBotAction(gesture=$gesture) as $action

    flow bot ask $text
      await _bot_say $text

    flow user said something
      match UtteranceUserAction.Finished() as $event

    flow bot said something
      match UtteranceBotAction().Finished() as $event

    flow bot asked something
      match FlowFinished(flow_id="bot ask") as $event

    flow user was silent $time_s
      while True
        start TimerBotAction(timer_name="user_silence", duration=$time_s) as $timer_ref
        when $timer_ref.Finished()
          break
        orwhen UtteranceUserAction.Started() or UtteranceUserAction.TranscriptUpdated()
          send $timer_ref.Stop()
          match UtteranceUserAction.Finished()
        orwhen UtteranceUserAction.Finished()
          send $timer_ref.Stop()

    flow question repetition $time
      bot asked something as $ref
      when user was silent 5.0
        $question = $ref.context.event.arguments.text
        bot ask $question
      orwhen user said something or bot said something
        return

    flow main
      activate question repetition
      bot ask "This is a question!"
        and bot gesture "Waving hands"
      match WaitEvent()
    """

    config = _init_state(content)
    state = run_to_completion(config, start_main_flow_event)
    assert is_data_in_events(
        state.outgoing_events,
        [
            {
                "type": "StartUtteranceBotAction",
                "script": "This is a question!",
            },
            {
                "type": "StartGestureBotAction",
                "gesture": "Waving hands",
            },
        ],
    )
    state_copy = copy.deepcopy(state)
    state = run_to_completion(
        state,
        {
            "type": "GestureBotActionFinished",
            "action_uid": state.outgoing_events[1]["action_uid"],
        },
    )
    assert is_data_in_events(
        state.outgoing_events,
        [],
    )
    state = run_to_completion(
        state,
        {
            "type": "UtteranceBotActionFinished",
            "final_script": state_copy.outgoing_events[0]["script"],
            "action_uid": state_copy.outgoing_events[0]["action_uid"],
        },
    )
    assert is_data_in_events(
        state.outgoing_events,
        [
            {"type": "StartTimerBotAction"},
        ],
    )
    state = run_to_completion(
        state,
        {
            "type": "TimerBotActionFinished",
            "action_uid": state.outgoing_events[0]["action_uid"],
        },
    )
    assert is_data_in_events(
        state.outgoing_events,
        [
            {
                "type": "StartUtteranceBotAction",
                "script": "This is a question!",
            }
        ],
    )


if __name__ == "__main__":
    test_when_else_deep_hierarchy_case_match()
