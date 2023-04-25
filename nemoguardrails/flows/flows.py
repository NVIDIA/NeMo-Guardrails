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
from dataclasses import dataclass, field
from enum import Enum
from typing import Dict, List, Optional

from nemoguardrails.flows.sliding import slide


@dataclass
class FlowConfig:
    """The configuration of a flow."""

    # A unique id of the flow.
    id: str

    # The sequence of elements that compose the flow.
    elements: List[dict]

    # The priority of the flow. Higher priority flows are executed first.
    priority: float = 1.0

    # Whether it is an extension flow or not.
    # Extension flows can interrupt other flows on actionable steps.
    is_extension: bool = False

    # Weather this flow can be interrupted or not
    is_interruptible: bool = True

    # The events that can trigger this flow to advance.
    trigger_event_types = ["user_intent", "bot_intent", "run_action", "action_finished"]

    # The actual source code, if available
    source_code: Optional[str] = None


class FlowStatus(Enum):
    """The status of a flow."""

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

    # The position in the sequence of elements that compose the flow.
    head: int

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
    flow_states: List[FlowState]

    # The configuration of all the flows that are available.
    flow_configs: Dict[str, FlowConfig]

    # The next step of the flow-driven system
    next_step: Optional[dict] = None

    # The updates to the context that should be applied before the next step
    context_updates: dict = field(default_factory=dict)


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


def _is_match(element: dict, event: dict) -> bool:
    """Checks if the given element matches the given event."""

    # The element type is the first key in the element dictionary
    element_type = element["_type"]

    if event["type"] == "user_intent":
        return element_type == "user_intent" and (
            element["intent_name"] == "..." or element["intent_name"] == event["intent"]
        )

    elif event["type"] == "bot_intent":
        return (
            element_type == "run_action"
            and element["action_name"] == "utter"
            and (
                element["action_params"]["value"] == "..."
                or element["action_params"]["value"] == event["intent"]
            )
        )

    elif event["type"] == "action_finished":
        # Currently, we only match successful execution of actions
        if event["status"] != "success":
            return False

        return (
            element_type == "run_action"
            and element["action_name"] == event["action_name"]
        )

    elif event["type"] == "user_said":
        return element_type == "user_said" and (
            element["content"] == "..." or element["content"] == event["content"]
        )

    elif event["type"] == "bot_said":
        return element_type == "bot_said" and (
            element["content"] == "..." or element["content"] == event["content"]
        )

    return False


def compute_next_state(state: State, event: dict) -> State:
    """Computes the next state of the flow-driven system.

    Currently, this is a very simplified implementation, with the following assumptions:

    - All flows are singleton i.e. you can't have multiple instances of the same flow.
    - Flows can be interrupted by one flow at a time.
    - Flows are resumed when the interruption flow completes.
    - No prioritization between flows, the first one that can decide something will be used.
    """

    # We don't advance flow on `start_action`, but on `action_finished`.
    if event["type"] == "start_action":
        return state

    # We don't need to decide any next step on context updates.
    if event["type"] == "context_update":
        # TODO: add support to also remove keys from the context.
        #  maybe with a special context key e.g. "__remove__": ["key1", "key2"]
        state.context.update(event["data"])
        state.context_updates = {}
        state.next_step = None
        return state

    # Initialize the new state
    new_state = State(
        context=state.context, flow_states=[], flow_configs=state.flow_configs
    )

    # The UID of the flow that will determine the next step
    next_step_by_flow_uid = None

    # The priority of the current next step.
    next_step_priority = 0

    # This is to handle an edge case in the simplified implementation
    extension_flow_completed = False

    # First, we try to advance the existing flows
    for flow_state in state.flow_states:
        flow_config = state.flow_configs[flow_state.flow_id]

        # We skip processing any completed/aborted flows
        if (
            flow_state.status == FlowStatus.COMPLETED
            or flow_state.status == FlowStatus.ABORTED
        ):
            continue

        # If it's not a completed flow, we have a valid head element
        flow_head_element = flow_config.elements[flow_state.head]

        # If the flow was interrupted, we just copy it to the new state
        if flow_state.status == FlowStatus.INTERRUPTED:
            new_state.flow_states.append(flow_state)
            continue

        # If the flow is not triggered by the current even type, we copy it as is
        if event["type"] not in flow_config.trigger_event_types:
            new_state.flow_states.append(flow_state)

            # If we don't have a next step up to this point, and the current flow is on
            # an actionable item, we set it as the next step.
            if new_state.next_step is None and _is_actionable(flow_head_element):
                new_state.next_step = flow_head_element
                next_step_by_flow_uid = flow_state.uid

                # Decrease a bit the priority to allow a flow that decides on the current
                # event to take precedence.
                next_step_priority = 0.9 * flow_config.priority
            continue

        # If we're at a branching point, we look at all individual heads.
        matching_head = None

        if flow_head_element["_type"] == "branch":
            for branch_head in flow_head_element["branch_heads"]:
                if _is_match(
                    flow_config.elements[flow_state.head + branch_head], event
                ):
                    matching_head = flow_state.head + branch_head + 1
        else:
            if _is_match(flow_head_element, event):
                matching_head = flow_state.head + 1

        if matching_head:
            # The flow can advance
            flow_state.head = matching_head

            # We slide the flow until the next actionable element
            flow_state.head = slide(new_state, flow_config, flow_state.head)

            new_state.flow_states.append(flow_state)

            # If we did not reach the end of the flow, we add it to the new state
            # (by convention, when we reach the end of the flow, the head is set to -1 * last head)
            if flow_state.head >= 0:
                # And if we don't have a next step yet, we set it to the next element
                if (
                    new_state.next_step is None
                    or next_step_priority < flow_config.priority
                ) and _is_actionable(flow_config.elements[flow_state.head]):
                    new_state.next_step = flow_config.elements[flow_state.head]
                    next_step_by_flow_uid = flow_state.uid
                    next_step_priority = flow_config.priority
            else:
                # If a flow finished, we mark it as completed
                flow_state.status = FlowStatus.COMPLETED

                if flow_config.is_extension:
                    extension_flow_completed = True

        # we don't interrupt on executable elements or if the flow is not interruptible
        elif (
            _is_actionable(flow_config.elements[flow_state.head])
            or not flow_config.is_interruptible
        ):
            flow_state.status = FlowStatus.ABORTED
            new_state.flow_states.append(flow_state)
        else:
            flow_state.status = FlowStatus.INTERRUPTED
            new_state.flow_states.append(flow_state)

    # Next, we try to start new flows
    for flow_config in state.flow_configs.values():
        # If a flow with the same id is started, we skip
        if flow_config.id in [fs.flow_id for fs in new_state.flow_states]:
            continue

        # We try to slide first, just in case a flow starts with sliding logic
        start_head = slide(new_state, flow_config, 0)

        # If the first element matches the current event, we start a new flow
        if _is_match(flow_config.elements[start_head], event):
            flow_uid = str(uuid.uuid4())
            flow_state = FlowState(
                uid=flow_uid, flow_id=flow_config.id, head=start_head + 1
            )
            new_state.flow_states.append(flow_state)

            # We also need to slide
            flow_state.head = slide(new_state, flow_config, flow_state.head)

            # And if we don't have a next step yet, we set it to the next element
            flow_head_element = flow_config.elements[flow_state.head]
            if (
                new_state.next_step is None or next_step_priority < flow_config.priority
            ) and _is_actionable(flow_head_element):
                new_state.next_step = flow_head_element
                next_step_by_flow_uid = flow_uid
                next_step_priority = flow_config.priority

    # If there's any extension flow that has completed, we re-activate all aborted flows
    if extension_flow_completed:
        for flow_state in new_state.flow_states:
            if flow_state.status == FlowStatus.ABORTED:
                flow_state.status = FlowStatus.ACTIVE

                # And potentially use them for the next decision
                flow_config = state.flow_configs[flow_state.flow_id]
                if (
                    new_state.next_step is None
                    or next_step_priority < flow_config.priority
                ) and _is_actionable(flow_config.elements[flow_state.head]):
                    new_state.next_step = flow_config.elements[flow_state.head]
                    next_step_by_flow_uid = flow_state.uid
                    next_step_priority = flow_config.priority

    # If there are any flows that have been interrupted in this iteration, we consider
    # them to be interrupted by the flow that determined the next step.
    for flow_state in new_state.flow_states:
        if (
            flow_state.status == FlowStatus.INTERRUPTED
            and flow_state.interrupted_by is None
        ):
            flow_state.interrupted_by = next_step_by_flow_uid

    # We compute the decision flow config and state
    decision_flow_config = None
    decision_flow_state = None

    for flow_state in new_state.flow_states:
        if flow_state.uid == next_step_by_flow_uid:
            decision_flow_config = state.flow_configs[flow_state.flow_id]
            decision_flow_state = flow_state

    # If we have aborted flows, and the current flow is an extension, when we interrupt them.
    # We are only interested when the extension flow actually decided, not just started.
    if (
        decision_flow_config
        and decision_flow_config.is_extension
        and decision_flow_state.head > 1
    ):
        for flow_state in new_state.flow_states:
            if (
                flow_state.status == FlowStatus.ABORTED
                and state.flow_configs[flow_state.flow_id].is_interruptible
            ):
                flow_state.status = FlowStatus.INTERRUPTED
                flow_state.interrupted_by = next_step_by_flow_uid

    # If there are flows that were waiting on completed flows, we reactivate them
    for flow_state in new_state.flow_states:
        if flow_state.status == FlowStatus.INTERRUPTED:
            # TODO: optimize this with a dict of statuses
            for _flow_state in new_state.flow_states:
                if _flow_state.uid == flow_state.interrupted_by:
                    if _flow_state.status == FlowStatus.COMPLETED:
                        flow_state.status = FlowStatus.ACTIVE
                        flow_state.interrupted_by = []

                        flow_config = state.flow_configs[flow_state.flow_id]
                        # Also, they can be used for decision as well.

                        if (
                            new_state.next_step is None
                            or next_step_priority < flow_config.priority
                        ) and _is_actionable(flow_config.elements[flow_state.head]):
                            new_state.next_step = flow_config.elements[flow_state.head]
                            next_step_priority = flow_config.priority
                    break

    return new_state


def _step_to_event(step: dict) -> dict:
    """Helper to convert a next step coming from a flow element into the actual event."""
    step_type = step["_type"]

    if step_type == "run_action":
        if step["action_name"] == "utter":
            return {
                "type": "bot_intent",
                "intent": step["action_params"]["value"],
            }

        else:
            action_name = step["action_name"]
            action_params = step.get("action_params", {})
            action_result_key = step.get("action_result_key")

            return {
                "type": "start_action",
                "action_name": action_name,
                "action_params": action_params,
                "action_result_key": action_result_key,
            }
    else:
        raise ValueError(f"Unknown next step type: {step_type}")


def compute_next_steps(
    history: List[dict], flow_configs: Dict[str, FlowConfig]
) -> List[dict]:
    """Computes the next step in a flow-driven system given a history of events."""
    state = State(context={}, flow_states=[], flow_configs=flow_configs)

    # First, we process the history and apply any alterations e.g. 'hide_prev_turn'
    actual_history = []
    for event in history:
        if event["type"] == "hide_prev_turn":
            # we look up the last `user_said` event and remove everything after
            end = len(actual_history) - 1
            while end > 0 and actual_history[end]["type"] != "user_said":
                end -= 1

            assert actual_history[end]["type"] == "user_said"
            actual_history = actual_history[0:end]
        else:
            actual_history.append(event)

    for event in actual_history:
        state = compute_next_state(state, event)

    next_steps = []

    # If we have context updates after this event, we first add that.
    if state.context_updates:
        next_steps.append({"type": "context_update", "data": state.context_updates})

    # If we have a next step, we make sure to convert it to proper event structure.
    if state.next_step:
        next_steps.append(_step_to_event(state.next_step))

    # Finally, we check if there was an explicit "stop" request
    if actual_history:
        last_event = actual_history[-1]
        if last_event["type"] == "bot_intent" and last_event["intent"] == "stop":
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
        if event["type"] == "context_update":
            context.update(event["data"])

        if event["type"] == "user_said":
            context["last_user_message"] = event["content"]

        elif event["type"] == "bot_said":
            context["last_bot_message"] = event["content"]

    return context
