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

"""A simplified modeling of the CoFlows engine."""
import uuid
from collections import deque
from dataclasses import dataclass, field
from enum import Enum
from typing import Deque, Dict, List, Optional

from nemoguardrails.colang.v1_1.runtime.sliding import slide
from nemoguardrails.utils import new_event_dict


@dataclass
class InteractionLoopType(Enum):
    """The type of the interaction loop."""

    NEW = "new"  # Every new instance of the flow will live in its own new loop
    PARENT = "parent"  # Every new instance of the flow will live in the same loop as its the parent
    NAMED = "named"  # Every new instance of the flow will live in the loop with the given name


@dataclass
class FlowConfig:
    """The configuration of a flow."""

    # A unique id of the flow.
    id: str

    # The sequence of elements that compose the flow.
    elements: List[dict]

    # Interaction loop
    loop_id: Optional[str] = None
    loop_type: InteractionLoopType = InteractionLoopType.PARENT

    # The priority of the flow. Higher priority flows are executed first.
    # TODO: Check for what this is used exactly
    priority: float = 1.0

    # Whether it is an extension flow or not.
    # Extension flows can interrupt other flows on actionable steps.
    is_extension: bool = False

    # Whether this flow can be interrupted or not
    # TODO: Check for what this is used exactly
    is_interruptible: bool = True

    # Whether this flow is a subflow
    # TODO: Remove
    is_subflow: bool = False

    # The events that can trigger this flow to advance.
    # TODO: This will need to be dynamically determined based on current heads
    trigger_event_types = [
        "UserIntent",
        "BotIntent",
        "StartAction",
        "InternalSystemActionFinished",
    ]

    # The actual source code, if available
    source_code: Optional[str] = None


class FlowHeadStatus(Enum):
    """The status of a flow."""

    ACTIVE = "active"
    PAUSED = "pause"
    MATCHED = "matched"
    FINISHED = "finished"
    ABORTED = "aborted"


@dataclass
class FlowHead:
    """The flow head that points to a certain element in the flow"""

    # The position of the flow element the head is pointing to
    position: int

    # The flow of the head
    flow_state_uid: str

    # A unique time id of the most recent event that had an effect on this head
    event_time_uid: str = ""

    # The current state of the flow head
    status: FlowHeadStatus = FlowHeadStatus.ACTIVE


class FlowStatus(Enum):
    """The status of a flow."""

    INACTIVE = "inactive"
    ACTIVE = "active"
    INTERRUPTED = "interrupted"
    ABORTED = "aborted"
    COMPLETED = "completed"


@dataclass
class FlowState:
    """The state of a flow."""

    # The unique id of an instance of a flow.
    uid: str

    # The id of the flow.
    flow_id: str

    # Interaction loop id
    loop_id: str

    # The position in the sequence of elements that compose the flow.
    # TODO: Generalize to have multiple heads for branching head statements like when/else
    head: FlowHead

    # Parent flow id
    # TODO: Implement proper parenting
    parent_uid: Optional[str] = None

    # Child flow ids
    child_uids: List[str] = field(default_factory=list)

    # The current state of the flow
    status: FlowStatus = FlowStatus.ACTIVE

    # The UID of the flows that interrupted this one
    interrupted_by = None


@dataclass
class State:
    """A state of a flow-driven system."""

    # The current set of variables in the state.
    context: dict

    # The current set of flows in the state.
    flow_states: Dict[str, FlowState]

    # The configuration of all the flows that are available.
    flow_configs: Dict[str, FlowConfig]

    # Queue of internal events
    internal_events: Deque[dict] = deque()

    # The next step of the flow-driven system
    next_step: Optional[dict] = None
    next_step_by_flow_uid: Optional[str] = None
    next_step_priority: float = 0.0

    # The comment is extract from the source code
    next_step_comment: Optional[str] = None

    # The updates to the context that should be applied before the next step
    context_updates: dict = field(default_factory=dict)

    def initialize(self) -> None:
        """
        Initialize the state to make it ready for the story start.
        """

        self.internal_events = deque()

        # Create flow states from flow config and start with head at position 0.
        self.flow_states = dict()
        for flow_config in self.flow_configs.values():
            loop_id: Optional[str] = None
            if flow_config.loop_type == InteractionLoopType.NEW:
                loop_id = str(uuid.uuid4())
            elif flow_config.loop_type == InteractionLoopType.NAMED:
                loop_id = flow_config.loop_id
            # For type InteractionLoopType.PARENT we keep it None to infer loop_id at run_time from parent

            flow_id = str(uuid.uuid4())
            flow_state = FlowState(
                uid=flow_id,
                flow_id=flow_config.id,
                loop_id=loop_id,
                head=FlowHead(0, flow_id),
                status=FlowStatus(FlowStatus.INACTIVE),
            )
            self.flow_states.update({flow_id: flow_state})


def compute_next_state(state: State, external_event: dict) -> State:
    """
    Computes the next state of the flow-driven system.
    """

    # Create a unique event time id to identify and track the resulting steps from the current event,
    # potentially leading to conflicts between actions
    external_event["event_time_uid"] = str(uuid.uuid4())

    # Initialize the new state
    new_state = State(
        context=state.context,
        flow_states={},
        internal_events=deque([external_event]),
        flow_configs=state.flow_configs,
    )

    heads_actionable: List[FlowHead] = []

    while new_state.internal_events:
        event = new_state.internal_events.popleft()

        # Find all heads of flows where event is relevant
        # TODO: Create a set to speed this up with all flow head related events
        heads_matching: List[FlowHead] = []
        heads_not_matching: List[FlowHead] = []

        for flow_state in state.flow_states.values():
            flow_config = state.flow_configs[flow_state.flow_id]
            # TODO: Generalize to multiple heads in flow
            head = flow_state.head
            head.event_time_uid = event["event_time_uid"]
            element = flow_config.elements[head.position]

            if _is_match_element(element):
                # TODO: Assign matching score
                if _is_matching(element, event):
                    head.status = FlowHeadStatus.MATCHED
                    heads_matching.append(head)
                else:
                    head.status = FlowHeadStatus.PAUSED
                    heads_not_matching.append(head)

        # Abort all flows that had a mismatch when there is no other match
        if not heads_matching:
            for head in heads_not_matching:
                head.status = FlowHeadStatus.ABORTED
            # return new_state

        # Advance all matching heads ...
        for head in heads_matching:
            head.position += 1
            _slide(new_state, state.flow_states[head.flow_state_uid])

            flow_config = state.flow_configs[
                state.flow_states[head.flow_state_uid].flow_id
            ]
            if _is_actionable(flow_config.elements[head.position]):
                heads_actionable.append(head)

            if flow_state.head.status == FlowHeadStatus.FINISHED:
                # If a flow finished, we mark it as completed
                flow_state.status = FlowStatus.COMPLETED

    # Now, all heads are either on a matching or send_event (start action) statement

    # Check for potential conflicts between actionable statements
    if len(heads_actionable) > 1:
        for head in heads_actionable:
            print(head.event_time_uid)
            pass

    return new_state


def _is_actionable(element: dict) -> bool:
    """Checks if the given element is actionable."""
    if element["_type"] == "run_action":
        if (
            element["action_name"] == "utter"
            and element["action_params"]["value"] == "..."
        ):
            return False

        return True

    return False


def _is_match_element(element: dict) -> bool:
    return element["_type"] == "match_event"


# TODO: Refactor this
def _is_matching(element: dict, event: dict) -> bool:
    """Checks if the given element matches the given event."""

    # The element type is the first key in the element dictionary
    element_type = element["_type"]

    if event["type"] == "InternalEvent":
        return (
            element_type == "match_event"
            and element["event_name"] == "StartFlow"
            and element["event_params"] == event["event_params"]
        )
    elif event["type"] == "UserIntent":
        return element_type == "UserIntent" and (
            element["intent_name"] == "..." or element["intent_name"] == event["intent"]
        )

    elif event["type"] == "BotIntent":
        return (
            element_type == "start_action"
            and element["action_name"] == "utter"
            and (
                element["action_params"]["value"] == "..."
                or element["action_params"]["value"] == event["intent"]
            )
        )

    elif event["type"] == "InternalSystemActionFinished":
        # Currently, we only match successful execution of actions
        if event["status"] != "success":
            return False

        return (
            element_type == "start_action"
            and element["action_name"] == event["action_name"]
        )

    elif event["type"] == "UtteranceUserActionFinished":
        return element_type == "UtteranceUserActionFinished" and (
            element["final_transcript"] == "..."
            or element["final_transcript"] == event["final_transcript"]
        )

    elif event["type"] == "StartUtteranceBotAction":
        return element_type == "StartUtteranceBotAction" and (
            element["script"] == "..." or element["script"] == event["script"]
        )

    else:
        # In this case, we try to match the event by type explicitly, and all the properties.
        if event["type"] != element_type:
            return False

        # We need to match all properties used in the element. We also use the "..." wildcard
        # to mach anything.
        for key, value in element.items():
            # Skip potentially private keys.
            if key.startswith("_"):
                continue
            if value == "...":
                continue
            if event.get(key) != value:
                return False

        return True


def _record_next_step(
    new_state: State,
    flow_state: FlowState,
    flow_config: FlowConfig,
    priority_modifier: float = 1.0,
):
    """Helper to record the next step."""
    if (
        new_state.next_step is None
        or new_state.next_step_priority < flow_config.priority
    ) and _is_actionable(flow_config.elements[flow_state.head.position]):
        new_state.next_step = flow_config.elements[flow_state.head.position]
        new_state.next_step_by_flow_uid = flow_state.uid
        new_state.next_step_priority = flow_config.priority * priority_modifier

        # Extract the comment, if any.
        new_state.next_step_comment = (
            flow_config.elements[flow_state.head.position]
            .get("_source_mapping", {})
            .get("comment")
        )


def _call_subflow(new_state: State, flow_state: FlowState) -> Optional[FlowState]:
    """Helper to call a subflow.

    The head for `flow_state` is expected to be on a "flow" element.
    """
    flow_config = new_state.flow_configs[flow_state.flow_id]
    subflow_state = FlowState(
        flow_id=flow_config.elements[flow_state.head]["flow_name"],
        status=FlowStatus.ACTIVE,
        head=FlowHead(0),
        uid=str(uuid.uuid4()),
    )

    # Move the head by 1, so that when it will resume, it will be on the next element.
    flow_state.head += 1

    # We slide the subflow.
    _slide_with_subflows(new_state, subflow_state)

    # If the subflow finished immediately, we just return with the head advanced
    if subflow_state.head < 0:
        return None

    # We mark the current flow as interrupted.
    flow_state.status = FlowStatus.INTERRUPTED

    # Record the id of the flow that interrupted the current flow.
    flow_state.interrupted_by = subflow_state.uid

    # Add any new subflow to the new state
    new_state.flow_states.append(subflow_state)

    # Check if we have a next step from the subflow
    subflow_config = new_state.flow_configs[subflow_state.flow_id]
    _record_next_step(new_state, subflow_state, subflow_config)

    return subflow_state


def _slide(state: State, flow_state: FlowState) -> Optional[int]:
    """Slides the provided flow, if applicable."""
    flow_config = state.flow_configs[flow_state.flow_id]
    # TODO: Fix negative flow head positions for 'Finished' flows
    flow_state.head.position = slide(state, flow_config, flow_state.head)
    if flow_state.head.position < 0:
        flow_state.head.status = FlowHeadStatus.FINISHED
        flow_state.head.position = 0
    _record_next_step(state, flow_state, flow_config)


def _step_to_event(step: dict) -> dict:
    """Helper to convert a next step coming from a flow element into the actual event."""
    step_type = step["_type"]

    if step_type == "StartAction":
        if step["action_name"] == "utter":
            return {
                "type": "BotIntent",
                "intent": step["action_params"]["value"],
            }

        else:
            action_name = step["action_name"]
            action_params = step.get("action_params", {})
            action_result_key = step.get("action_result_key")

            return new_event_dict(
                "StartInternalSystemAction",
                action_name=action_name,
                action_params=action_params,
                action_result_key=action_result_key,
            )
    else:
        raise ValueError(f"Unknown next step type: {step_type}")


# NOTE (schuellc): Are we going to replace this with a stateful approach
def compute_next_steps(
    history: List[dict], flow_configs: Dict[str, FlowConfig]
) -> List[dict]:
    """Computes the next step in a flow-driven system given a history of events."""
    state = State(context={}, flow_states=[], flow_configs=flow_configs)

    # First, we process the history and apply any alterations e.g. 'hide_prev_turn'
    actual_history = []
    for event in history:
        # NOTE (schuellc): Why is this needed?
        if event["type"] == "hide_prev_turn":
            # we look up the last `UtteranceUserActionFinished` event and remove everything after
            end = len(actual_history) - 1
            while (
                end > 0 and actual_history[end]["type"] != "UtteranceUserActionFinished"
            ):
                end -= 1

            assert actual_history[end]["type"] == "UtteranceUserActionFinished"
            actual_history = actual_history[0:end]
        else:
            actual_history.append(event)

    for event in actual_history:
        state = compute_next_state(state, event)

        # NOTE (Jul 24, Razvan): this is a quick fix. Will debug further.
        if event["type"] == "bot_intent" and event["intent"] == "stop":
            # Reset all flows
            state.flow_states = []

    next_steps = []

    # If we have context updates after this event, we first add that.
    if state.context_updates:
        next_steps.append(new_event_dict("ContextUpdate", data=state.context_updates))

    # If we have a next step, we make sure to convert it to proper event structure.
    # NOTE (schuellc): What's the difference between a step and a event?
    if state.next_step:
        next_step_event = _step_to_event(state.next_step)
        if next_step_event["type"] == "bot_intent" and state.next_step_comment:
            # For bot intents, we use the comment as instructions
            next_step_event["instructions"] = state.next_step_comment

        next_steps.append(next_step_event)

    # Finally, we check if there was an explicit "stop" request
    if actual_history:
        last_event = actual_history[-1]
        # NOTE (schuellc): Why is this needed?
        if last_event["type"] == "BotIntent" and last_event["intent"] == "stop":
            # In this case, we remove any next steps
            next_steps = []

    return next_steps


def compute_context(history: List[dict]):
    """Computes the context given a history of events.

    # We also include a few special context variables:
    - $last_user_message: the last message sent by the user.
    - $last_bot_message: the last message sent by the bot.
    """
    context = {
        "last_user_message": None,
        "last_bot_message": None,
    }

    for event in history:
        if event["type"] == "ContextUpdate":
            context.update(event["data"])

        if event["type"] == "UtteranceUserActionFinished":
            context["last_user_message"] = event["final_transcript"]

        elif event["type"] == "StartUtteranceBotAction":
            context["last_bot_message"] = event["script"]

    return context
