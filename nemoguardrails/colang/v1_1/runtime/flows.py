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

from __future__ import annotations

import copy
import logging
import uuid
from collections import deque
from dataclasses import asdict, dataclass, field
from enum import Enum
from functools import partial
from typing import Any, Callable, Deque, Dict, List, Optional, Union

from nemoguardrails.colang.v1_1.lang.colang_ast import Element, Spec, SpecOp
from nemoguardrails.colang.v1_1.runtime.eval import eval_expression
from nemoguardrails.colang.v1_1.runtime.utils import create_readable_uuid
from nemoguardrails.utils import new_event_dict, new_uid

# from rich.logging import RichHandler  # isort:skip

# FORMAT = "%(message)s"
# logging.basicConfig(
#     level=logging.DEBUG,
#     format=FORMAT,
#     datefmt="[%X,%f]",
#     handlers=[RichHandler(markup=True)],
# )

"""
Questions:
* What's the plan with the state
  - Distribution of helper functions? E.g. internal event creation?
* Should we have only 'send', 'match' and assignment at the basis of the language, everything else can be expended to that
  - Assignment of actions
* Where should this extension be done? Since we need the context of the flows and actions
* Not everything is a SpecOp in ast, e.g. comments
* Handling of double quotation
* Transformer must extract flow parameters
"""


class ContextVariableType(Enum):
    """The type of a context variable."""

    PRIMITIVE = "primitive"
    EVENT_REFERENCE = "event_reference"
    ACTION_REFERENCE = "action_reference"
    FLOW_REFERENCE = "action_reference"


@dataclass
class Event:
    """The base event class."""

    # The unique id of the event
    # uid: str

    # Name of the event
    name: str

    # Context that contains all relevant event arguments
    arguments: dict

    # A list of matching scores from the event sequence triggered by external event
    matching_scores: List[float] = field(default_factory=list)


@dataclass
class ActionEvent(Event):
    """The action event class."""

    # An event can belong to an action
    action: Optional[str] = None

    @classmethod
    def from_umim_event(cls, event: dict) -> ActionEvent:
        """Creates an event from a flat dictionary."""
        new_event = ActionEvent(event["type"], {})
        new_event.arguments = dict(
            [(key, event[key]) for key in event if key not in ["type", "action_uid"]]
        )
        if "action_uid" in event:
            new_event.action_uid = event["action_uid"]
        return new_event


@dataclass
class FlowEvent(Event):
    """The flow event class."""

    # An event can belong to a flow
    flow: Optional[str] = None


class ActionStatus(Enum):
    """The type of a context variable."""

    INITIALIZED = "initialized"
    STARTING = "starting"
    STARTED = "started"
    STOPPING = "stopping"
    FINISHED = "finished"


class Action:
    """The action groups and manages the action events."""

    def __init__(
        self, name: str, arguments: Dict[str, Any], flow_uid: Optional[str] = None
    ) -> None:
        # The unique id of the action
        self.uid: str = new_uid()

        # Name of the action
        self.name = name

        # An action belongs to the flow that it started
        self.flow_uid = flow_uid

        # State of the action
        self.status: ActionStatus = ActionStatus.INITIALIZED

        # Context that contains all relevant action parameters
        self.context: dict = {}

        # The arguments that will be used for the start event
        self.start_event_arguments = arguments

        # The action event name mapping
        self._event_name_map = {
            "Start": self.start,
            "Change": self.change,
            "Stop": self.stop,
            "Started": self.started_event,
            "Updated": self.updated_event,
            "Finished": self.finished_event,
        }

    # Process an event
    def process_event(self, event: Event) -> None:
        """Processes event and updates action accordingly."""
        if "Action" in event.name and event.action_uid == self.uid:
            if "ActionStarted" in event.name:
                self.context.update(event.arguments)
                self.status = ActionStatus.STARTED
            elif "ActionUpdated" in event.name:
                self.context.update(event.arguments)
            elif "ActionFinished" in event.name:
                self.context.update(event.arguments)
                self.status = ActionStatus.FINISHED

    def get_event(self, name: str, arguments: dict) -> Callable[[], ActionEvent]:
        """Returns the corresponding action event."""
        return self._event_name_map[name](arguments)

    # Action events to send
    def start(self, args: dict) -> ActionEvent:
        """Starts the action. Takes no arguments."""
        self.status = ActionStatus.STARTING
        return ActionEvent(f"Start{self.name}", self.start_event_arguments, self.uid)

    def change(self, args: dict) -> ActionEvent:
        """Changes a parameter of a started action."""
        return ActionEvent(f"Change{self.name}", args["arguments"], self.uid)

    def stop(self, args: dict) -> ActionEvent:
        """Stops a started action. Takes no arguments."""
        self.status = ActionStatus.STOPPING
        return ActionEvent(f"Stop{self.name}", {}, self.uid)

    # Action events to match
    def started_event(self, args: dict) -> ActionEvent:
        """Returns the Started action event."""
        arguments = args.copy()
        arguments["action_arguments"] = self.start_event_arguments
        return ActionEvent(f"{self.name}Started", arguments, self.uid)

    def updated_event(self, args: dict) -> ActionEvent:
        """Returns the Updated parameter action event."""
        arguments = args.copy()
        arguments["action_arguments"] = self.start_event_arguments
        return ActionEvent(
            f"{self.name}{args['parameter_name']}Updated", arguments, self.uid
        )

    def finished_event(self, args: dict) -> ActionEvent:
        """Returns the Finished action event."""
        arguments = args.copy()
        arguments["action_arguments"] = self.start_event_arguments
        return ActionEvent(f"{self.name}Finished", arguments, self.uid)


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
    elements: List[Union[Element, SpecOp, dict]]

    # Interaction loop
    loop_id: Optional[str] = None
    loop_type: InteractionLoopType = InteractionLoopType.PARENT

    # The priority of the flow. Higher priority flows are executed first.
    # TODO: Check for what this is used exactly
    # priority: float = 1.0

    # Whether it is an extension flow or not.
    # Extension flows can interrupt other flows on actionable steps.
    # is_extension: bool = False

    # Whether this flow can be interrupted or not
    # TODO: Check for what this is used exactly
    # is_interruptible: bool = True

    # The events that can trigger this flow to advance.
    # TODO: This will need to be dynamically determined based on current heads
    # trigger_event_types = [
    #     "UserIntent",
    #     "BotIntent",
    #     "StartAction",
    #     "InternalSystemActionFinished",
    # ]

    # The actual source code, if available
    source_code: Optional[str] = None


@dataclass
class FlowHead:
    """The flow head that points to a certain element in the flow"""

    # The unique id of a flow head
    uid: str

    # The position of the flow element the head is pointing to
    position: int

    # The flow of the head
    flow_state_uid: str

    # Matching score history of previous matches that resulted in this head to be advanced
    matching_scores: List[float]


class FlowStatus(Enum):
    """The status of a flow."""

    INACTIVE = "inactive"
    STARTING = "starting"
    STARTED = "started"
    ACTIVE = "active"
    INTERRUPTED = "interrupted"
    ABORTED = "aborted"
    COMPLETED = "completed"


# TODO: Rename just to "Flow" for better clarity, also all variables flow_state -> flow
@dataclass
class FlowState:
    """The state of a flow."""

    # The unique id of the flow instance
    uid: str

    # The name id of the flow
    flow_id: str

    # Interaction loop id
    loop_id: str

    # The position in the sequence of elements that compose the flow.
    # TODO: Generalize to have multiple heads for branching head statements like when/else
    head: FlowHead

    # All actions that were instantiated since the beginning of the flow
    action_uids: List[str]

    # The current set of variables in the flow state.
    context: dict

    # Child flow ids
    arguments: dict = field(default_factory=dict)

    # Parent flow id
    # TODO: Implement proper parenting
    parent_uid: Optional[str] = None

    # Child flow ids
    child_flow_uids: List[str] = field(default_factory=list)

    # The current state of the flow
    status: FlowStatus = FlowStatus.INACTIVE

    # The UID of the flows that interrupted this one
    # interrupted_by = None

    # The flow event name mapping
    _event_name_map: dict = field(init=False)

    def __post_init__(self) -> None:
        self._event_name_map = {
            "Start": self.start,
            "Stop": self.stop,
            "Pause": self.pause,
            "Resume": self.resume,
            "Started": self.started_event,
            "Paused": self.paused_event,
            "Resumed": self.resumed_event,
            "Finished": self.finished_event,
            "Failed": self.failed_event,
        }

    def get_event(self, name: str, arguments: dict) -> Callable[[], FlowEvent]:
        """Returns the corresponding action event."""
        return self._event_name_map[name](arguments)

    # Flow events to send
    def start(self, args: dict) -> FlowEvent:
        """Starts the flow. Takes no arguments."""
        return FlowEvent("StartFlow", {"flow_id": self.flow_id})

    def stop(self, args: dict) -> FlowEvent:
        """Stops the flow. Takes no arguments."""
        return FlowEvent("StopFlow", {"flow_id": self.flow_id})

    def pause(self, args: dict) -> FlowEvent:
        """Pauses the flow. Takes no arguments."""
        return FlowEvent("PauseFlow", {"flow_id": self.flow_id})

    def resume(self, args: dict) -> FlowEvent:
        """Resumes the flow. Takes no arguments."""
        return FlowEvent("ResumeFlow", {"flow_id": self.flow_id})

    # Flow events to match
    def started_event(self, args: dict) -> FlowEvent:
        """Returns the flow Started event."""
        arguments = args.copy()
        arguments["flow_id"] = self.flow_id
        arguments["flow_arguments"] = self.arguments
        return FlowEvent("FlowStarted", arguments)

    def paused_event(self, args: dict) -> FlowEvent:
        """Returns the flow Pause event."""
        arguments = args.copy()
        arguments["flow_id"] = self.flow_id
        arguments["flow_arguments"] = self.arguments
        return FlowEvent("FlowPaused", arguments)

    def resumed_event(self, args: dict) -> FlowEvent:
        """Returns the flow Resumed event."""
        arguments = args.copy()
        arguments["flow_id"] = self.flow_id
        arguments["flow_arguments"] = self.arguments
        return FlowEvent("FlowResumed", arguments)

    def finished_event(self, args: dict) -> FlowEvent:
        """Returns the flow Finished event."""
        arguments = args.copy()
        arguments["flow_id"] = self.flow_id
        arguments["flow_arguments"] = self.arguments
        return FlowEvent("FlowFinished", arguments)

    def failed_event(self, args: dict) -> FlowEvent:
        """Returns the flow Failed event."""
        arguments = args.copy()
        arguments["flow_id"] = self.flow_id
        arguments["flow_arguments"] = self.arguments
        return FlowEvent("FlowFailed", arguments)


@dataclass
class State:
    """A state of a flow-driven system."""

    # The current set of variables in the state.
    context: dict

    # The current set of flows in the state with their uid as key.
    flow_states: Dict[str, FlowState]

    # The configuration of all the flows that are available.
    flow_configs: Dict[str, FlowConfig]

    # All actions that were instantiated in a flow that is still referenced somewhere
    actions: Dict[str, Action] = field(default_factory=dict)

    # Queue of internal events
    internal_events: Deque[Event] = field(default_factory=deque)

    # The main flow state
    main_flow_state: FlowState = None

    # The next step of the flow-driven system
    outgoing_events: List[dict] = field(default_factory=list)

    # The comment is extract from the source code
    # next_steps_comment: List[str] = field(default_factory=list)

    # The updates to the context that should be applied before the next step
    context_updates: dict = field(default_factory=dict)

    ########################
    # Helper data structures
    ########################

    # dictionary that maps from flow_id (name) to all available flow states
    flow_id_states: Dict[str, List[FlowState]] = field(default_factory=dict)

    def initialize(self) -> None:
        """
        Initialize the state to make it ready for the story start.
        """

        self.internal_events = deque()

        assert "main" in self.flow_configs, "No main flow found!"

        self.flow_states = dict()

        # TODO: Think about where to put this
        # Transform and resolve flow configuration element notation (actions, flows, ...)
        config_changed = True
        while config_changed:
            config_changed = False
            for flow_config in self.flow_configs.values():
                new_elements: List[Union[SpecOp, dict]] = []
                for element in flow_config.elements:
                    if not isinstance(element, SpecOp):
                        # It's a comment
                        new_elements.append(element)
                    elif element.op == "await":
                        if element.spec.name in self.flow_configs:
                            # It's a flow
                            flow_ref_uid = f"_flow_ref_{new_uid()}"
                            new_elements.append(
                                SpecOp(
                                    op="start",
                                    spec=element.spec,
                                    ref=_create_ref_ast_dict_helper(flow_ref_uid),
                                )
                            )
                            new_elements.append(
                                SpecOp(
                                    op="match",
                                    spec=Spec(
                                        var_name=flow_ref_uid,
                                        members=_create_member_ast_dict_helper(
                                            "Finished", {}
                                        ),
                                    ),
                                )
                            )
                            config_changed = True
                        else:
                            # It's an UMIM action
                            action_ref_uid = f"_action_ref_{new_uid()}"
                            new_elements.append(
                                SpecOp(
                                    op="start",
                                    spec=element.spec,
                                    ref=_create_ref_ast_dict_helper(action_ref_uid),
                                )
                            )
                            new_elements.append(
                                SpecOp(
                                    op="match",
                                    spec=Spec(
                                        var_name=action_ref_uid,
                                        members=_create_member_ast_dict_helper(
                                            "Finished", {}
                                        ),
                                    ),
                                )
                            )
                            config_changed = True
                    elif element.op == "start":
                        if element.spec.name in self.flow_configs:
                            # It's a flow
                            element_ref = element.ref
                            if element_ref is None:
                                flow_ref_uid = f"_flow_ref_{new_uid()}"
                                element_ref = _create_ref_ast_dict_helper(flow_ref_uid)
                            new_elements.append(
                                SpecOp(
                                    op="_new_instance",
                                    spec=element.spec,
                                    ref=element_ref,
                                )
                            )
                            spec = element.spec
                            spec.members = _create_member_ast_dict_helper("Start", {})
                            spec.var_name = element_ref["elements"][0]["elements"][
                                0
                            ].lstrip("$")
                            new_elements.append(SpecOp(op="send", spec=spec))
                            config_changed = True
                        else:
                            # It's an UMIM action
                            element_ref = element.ref
                            if element_ref is None:
                                action_ref_uid = f"_action_ref_{new_uid()}"
                                element_ref = _create_ref_ast_dict_helper(
                                    action_ref_uid
                                )
                            new_elements.append(
                                SpecOp(
                                    op="_new_instance",
                                    spec=element.spec,
                                    ref=element_ref,
                                )
                            )
                            spec = element.spec
                            spec.members = _create_member_ast_dict_helper("Start", {})
                            spec.var_name = element_ref["elements"][0]["elements"][
                                0
                            ].lstrip("$")
                            new_elements.append(SpecOp(op="send", spec=spec))
                    elif element.op == "match":
                        if element.spec.name in self.flow_configs:
                            # It's a flow
                            new_elements.append(
                                SpecOp(
                                    op="match",
                                    spec=Spec(
                                        name=element.spec.name,
                                        members=_create_member_ast_dict_helper(
                                            "Finished", {}
                                        ),
                                        arguments={"flow_id": f"'{element.spec.name}'"},
                                    ),
                                )
                            )
                            config_changed = True
                        else:
                            # It's an UMIM event
                            new_elements.append(element)
                    else:
                        new_elements.append(element)
                flow_config.elements = new_elements

        # Create main flow state first
        main_flow_config = self.flow_configs["main"]
        main_flow = _add_new_flow_instance(
            self, _create_flow_instance(main_flow_config)
        )
        if main_flow_config.loop_id is None:
            main_flow.loop_id = create_readable_uuid("main")
        else:
            main_flow.loop_id = main_flow_config.loop_id
        self.main_flow_state = main_flow

        # Create flow states for all other flows and start with head at position 0.
        for flow_config in self.flow_configs.values():
            if flow_config.id != "main":
                _add_new_flow_instance(self, _create_flow_instance(flow_config))


def _create_ref_ast_dict_helper(ref_name: str) -> dict:
    return {
        "_type": "capture_ref",
        "elements": [{"_type": "var_name", "elements": [f"{ref_name}"]}],
    }


def _create_member_ast_dict_helper(name: str, arguments: dict) -> list:
    return [
        {
            "_type": "spec",
            "_source": None,
            "name": name,
            "arguments": arguments,
            "members": None,
            "var_name": None,
        }
    ]


def _create_flow_instance(
    flow_config: FlowConfig, parent_uid: Optional[str] = None
) -> FlowState:
    loop_uid: Optional[str] = None
    if flow_config.loop_type == InteractionLoopType.NEW:
        loop_uid = new_uid()
    elif flow_config.loop_type == InteractionLoopType.NAMED:
        loop_uid = flow_config.loop_id
    # For type InteractionLoopType.PARENT we keep it None to infer loop_id at run_time from parent

    flow_uid = create_readable_uuid(flow_config.id)
    flow_state = FlowState(
        uid=flow_uid,
        context={},
        parent_uid=parent_uid,
        action_uids=[],
        flow_id=flow_config.id,
        loop_id=loop_uid,
        head=FlowHead(
            uid=new_uid(),
            position=0,
            flow_state_uid=flow_uid,
            matching_scores=[],
        ),
    )

    return flow_state


def _add_new_flow_instance(state, flow_state: FlowState) -> FlowState:
    # Update state structures
    state.flow_states.update({flow_state.uid: flow_state})
    if flow_state.flow_id in state.flow_id_states:
        state.flow_id_states[flow_state.flow_id].append(flow_state)
    else:
        state.flow_id_states.update({flow_state.flow_id: [flow_state]})

    return flow_state


# Define a custom sorting key function for pairwise comparisons
def _custom_sort_key(input_list):
    return tuple(input_list)


def _sort_heads_from_matching_scores(heads: List[FlowHead]) -> List[FlowHead]:
    score_lists = [(head.matching_scores, head) for head in heads]
    sorted_lists = sorted(score_lists, key=_custom_sort_key, reverse=True)
    return [e[1] for e in sorted_lists]


def compute_next_state(state: State, external_event: dict) -> State:
    """
    Computes the next state of the flow-driven system.
    """
    logging.info(f"Process event: {external_event}")

    converted_external_event = ActionEvent.from_umim_event(external_event)

    # Initialize the new state
    new_state = copy.copy(state)
    new_state.internal_events = deque([converted_external_event])
    new_state.outgoing_events.clear()

    # Clear all matching scores
    for flow_state in state.flow_states.values():
        head = flow_state.head
        head.matching_scores.clear()

    heads_actionable: List[FlowHead] = []

    while new_state.internal_events:
        event = new_state.internal_events.popleft()
        logging.info(f"Process internal event: {event}")

        # Handle internal events that have no default matchers in flows yet
        if event.name == "AbortFlow":
            flow_state = state.flow_states[event.arguments["flow_instance_uid"]]
            _abort_flow(new_state, flow_state, event.matching_scores)
        # elif event.name == "ResumeFlow":
        #     pass
        # elif event.name == "PauseFlow":
        #     pass

        # Find all heads of flows where event is relevant
        heads_matching: List[FlowHead] = []
        heads_not_matching: List[FlowHead] = []
        match_order_score = 1.0

        # TODO: Create a head dict for all active flows to speed this up
        # Iterate over all flow states to check for the heads to match the event
        for flow_state in state.flow_states.values():
            if not _is_listening_flow(flow_state):
                # Don't process flows that are no longer active
                continue

            flow_config = state.flow_configs[flow_state.flow_id]
            # TODO: Generalize to multiple heads in flow
            head = flow_state.head

            element = flow_config.elements[head.position]
            if _is_match_op_element(element):
                # TODO: Assign matching score
                matching_score = _compute_event_matching_score(
                    new_state, flow_state, element, event
                )
                if matching_score > 0.0:
                    head.matching_scores = event.matching_scores.copy()
                    # Make sure that we can always resolve conflicts, using the matching score
                    matching_score *= match_order_score
                    match_order_score *= 0.99
                    head.matching_scores.append(matching_score)

                    heads_matching.append(head)
                    logging.info(f"Matching head (score: {matching_score}): {head}")
                else:
                    heads_not_matching.append(head)

        # Handle internal event matching
        for head in heads_matching:
            if event.name == "StartFlow":
                flow_state = _get_flow_state_from_head(state, head)
                flow_config = _get_flow_config_from_head(state, head)
                # Start flow and link to parent flow
                if flow_state != state.main_flow_state:
                    parent_flow_uid = event.arguments["source_flow_instance_uid"]
                    parent_flow = state.flow_states[parent_flow_uid]
                    flow_state.parent_uid = parent_flow_uid
                    flow_state.loop_id = parent_flow.loop_id
                    flow_state.context = event.arguments
                    parent_flow.child_flow_uids.append(flow_state.uid)
                # Initialize new flow instance of flow
                _add_new_flow_instance(new_state, _create_flow_instance(flow_config))
            # TODO: Introduce default matching statements with heads for all flows
            # elif event.name == "AbortFlow":
            #     _abort_flow(new_state, flow_state)
            # elif event.name == "ResumeFlow":
            #     pass
            # elif event.name == "PauseFlow":
            #     pass

        # Abort all flows that had a mismatch when there is no other match
        # Not sure if we ever need this!
        # if not heads_matching:
        #     for head in heads_not_matching:
        #         flow_state = _get_flow_state_from_head(new_state, head)
        #         _abort_flow(new_state, flow_state, [])
        # return new_state

        # Advance front of all advancing heads until all heads are on a match-statement
        heads_advancing = heads_matching
        while heads_advancing:
            heads_actionable = _advance_head_front(new_state, heads_advancing)
            # Now, all heads are either on a matching or an action (start action, send event) statement

            # Check for potential conflicts between actionable heads
            heads_advancing = []
            if len(heads_actionable) == 1:
                # If we have no or only one actionable head there are no conflicts
                heads_advancing = heads_actionable
                _create_outgoing_event_from_actionable_element(
                    new_state, heads_actionable[0]
                )
            else:
                # Group all actionable heads by their flows interaction loop
                head_groups: Dict[str, List[FlowHead]] = {}
                for head in heads_actionable:
                    flow_state = _get_flow_state_from_head(new_state, head)
                    if flow_state.loop_id in head_groups:
                        head_groups[flow_state.loop_id].append(head)
                    else:
                        head_groups.update({flow_state.loop_id: [head]})

                # Find winning and loosing heads for each group
                for group in head_groups.values():
                    ordered_heads = _sort_heads_from_matching_scores(group)
                    winning_action = _get_flow_config_from_head(
                        new_state, ordered_heads[0]
                    ).elements[ordered_heads[0].position]

                    heads_advancing.append(ordered_heads[0])
                    _create_outgoing_event_from_actionable_element(
                        new_state, ordered_heads[0]
                    )
                    for head in ordered_heads[1:]:
                        if (
                            winning_action
                            == _get_flow_config_from_head(new_state, head).elements[
                                head.position
                            ]
                        ):
                            heads_advancing.append(head)
                        else:
                            flow_state = _get_flow_state_from_head(state, head)
                            logging.info(f"Conflicting action at head: {head}")
                            _abort_flow(new_state, flow_state, head.matching_scores)

        # Now, all heads are on a match-statement, so let's process the next internal event

    # Update all external event related actions in all flows that were not updated yet
    for flow_state in state.flow_states.values():
        if not _is_listening_flow(flow_state):
            # Don't process flows that are no longer active
            continue

        for action_uid in flow_state.action_uids:
            action = new_state.actions[action_uid]
            if (
                action.status == ActionStatus.INITIALIZED
                or action.status == ActionStatus.FINISHED
            ):
                continue
            action.process_event(converted_external_event)

    return new_state


def _advance_head_front(state: State, heads: List[FlowHead]) -> List[FlowHead]:
    """
    Advances all provided heads to the next blocking elements (actionable or matching) and returns all heads on
    actionable elements.
    """
    heads_actionable: List[FlowHead] = []
    for head in heads:
        flow_state = _get_flow_state_from_head(state, head)
        flow_config = _get_flow_config_from_head(state, head)

        if flow_state.status == FlowStatus.INACTIVE:
            flow_state.status = FlowStatus.STARTING

        head.position += 1

        internal_events = slide(state, flow_state, flow_config, flow_state.head)
        flow_finished = flow_state.head.position >= len(flow_config.elements)
        state.internal_events.extend(internal_events)

        if flow_finished:
            logging.info(f"Flow {head.flow_state_uid} finished with last element")
        else:
            logging.info(
                f"Head in flow {head.flow_state_uid} advanced to element: {flow_config.elements[head.position]}"
            )

        if flow_finished or _is_match_op_element(flow_config.elements[head.position]):
            if flow_state.status == FlowStatus.STARTING:
                flow_state.status = FlowStatus.STARTED
                event = create_flow_started_internal_event(
                    flow_state.uid, head.matching_scores
                )
                _push_internal_event(state, event)
        elif _is_action_op_element(flow_config.elements[head.position]):
            heads_actionable.append(head)

        # Check if flow has finished
        # TODO: Refactor to properly finish flow and all its child flows
        if flow_finished:
            _finish_flow(state, head)

    return heads_actionable


INTERNAL_EVENTS = {
    "StartFlow",
    "AbortFLow",
    "FlowStarted",
    "FlowFinished",
    "FlowFailed",
}


# TODO: Implement support for more sliding operations
def slide(
    state: State, flow_state: FlowState, flow_config: FlowConfig, head: FlowHead
) -> Deque[dict]:
    """Tries to slide a flow with the provided head."""
    head_position = head.position

    internal_events: Deque[dict] = deque()

    # TODO: Implement global/local flow context handling
    # context = state.context
    # context = flow_state.context

    while True:
        # if we reached the end, we stop
        if head_position == len(flow_config.elements) or head_position < 0:
            return internal_events

        # prev_head = head_position
        element = flow_config.elements[head_position]

        if not isinstance(element, SpecOp):
            # Non op statement (e.g. a comment)
            head_position += 1
            continue

        logging.info(f"Sliding step: '{element.op}'")

        if element.op == "send" and element.spec.name in INTERNAL_EVENTS:
            # Evaluate expressions (eliminate all double quotes)
            event_arguments = _evaluate_arguments(
                element.spec.arguments, flow_state.context
            )
            event_arguments.update({"source_flow_instance_uid": head.flow_state_uid})
            event = create_internal_event(
                element.spec.name, event_arguments, head.matching_scores
            )
            _push_internal_event(state, event)
            head_position += 1
        elif element.op == "_new_instance":
            if element.spec.name in state.flow_configs:
                # It's a flow
                evaluated_arguments = _evaluate_arguments(
                    element.spec.arguments, flow_state.context
                )
                flow_config = state.flow_configs[element.spec.name]
                new_flow_state = _create_flow_instance(flow_config, flow_state)

                flow_state.actions.update({action.uid: action})
                reference_name = element.ref["elements"][0]["elements"][0].lstrip("$")
                flow_state.context.update(
                    {
                        reference_name: {
                            "type": ContextVariableType.ACTION_REFERENCE,
                            "value": action.uid,
                        }
                    }
                )
            else:
                # It's an action
                evaluated_arguments = _evaluate_arguments(
                    element.spec.arguments, flow_state.context
                )
                action = Action(
                    name=element.spec.name,
                    arguments=evaluated_arguments,
                    flow_uid=head.flow_state_uid,
                )
                state.actions.update({action.uid: action})
                flow_state.action_uids.append(action.uid)
                reference_name = element.ref["elements"][0]["elements"][0].lstrip("$")
                flow_state.context.update(
                    {
                        reference_name: {
                            "type": ContextVariableType.ACTION_REFERENCE,
                            "value": action.uid,
                        }
                    }
                )
            head_position += 1
        else:
            # Not a sliding element
            break

    # If we got this far, it means we had a match and the flow advanced
    head.position = head_position
    return internal_events


def _abort_flow(
    state: State, flow_state: FlowState, matching_scores: List[float]
) -> None:
    """Aborts a flow instance and all its active child flows."""
    # Generate FlowFailed event
    event = create_flow_failed_internal_event(flow_state.uid, matching_scores)
    _push_internal_event(state, event)

    # abort all running child flows
    for child_flow_uid in flow_state.child_flow_uids:
        child_flow_state = state.flow_states[child_flow_uid]
        if _is_listening_flow(child_flow_state):
            event = create_abort_flow_internal_event(
                child_flow_state.uid, flow_state.uid, matching_scores
            )
            _push_internal_event(state, event)

    flow_state.status = FlowStatus.ABORTED

    logging.info(f"Flow '{flow_state.flow_id}' aborted/failed")


def _finish_flow(state: State, head: FlowHead) -> None:
    """Finishes a flow instance and all active its child flows."""
    flow_state = _get_flow_state_from_head(state, head)

    # Generate FlowFinished event
    event = create_flow_finished_internal_event(flow_state.uid, head.matching_scores)
    _push_internal_event(state, event)

    # Abort all running child flows
    for child_flow_uid in flow_state.child_flow_uids:
        child_flow_state = state.flow_states[child_flow_uid]
        if _is_listening_flow(child_flow_state):
            event = create_abort_flow_internal_event(
                child_flow_state.uid, flow_state.uid, head.matching_scores
            )
            _push_internal_event(state, event)

    flow_state.status = FlowStatus.COMPLETED

    logging.info(f"Flow '{flow_state.flow_id}' finished")


def _is_listening_flow(flow_state: FlowState) -> bool:
    return (
        flow_state.status == FlowStatus.INACTIVE
        or flow_state.status == FlowStatus.ACTIVE
        or flow_state.status == FlowStatus.STARTED
        or flow_state.status == FlowStatus.STARTING
    )


def _push_internal_event(state: State, event: dict) -> None:
    state.internal_events.append(event)
    logging.info(f"Created internal event: {event}")


def _get_head_element_from_head(state: State, head: FlowHead) -> SpecOp:
    """Returns the element at the flow head position"""
    return _get_flow_config_from_head(state, head).elements[head.position]


def _get_flow_config_from_head(state: State, head: FlowHead) -> FlowConfig:
    """Returns the flow config of the flow of the head"""
    return state.flow_configs[_get_flow_state_from_head(state, head).flow_id]


def _get_flow_state_from_head(state: State, head: FlowHead) -> FlowState:
    """Returns the flow state of the flow head"""
    return state.flow_states[head.flow_state_uid]


def _is_action_op_element(element: SpecOp) -> bool:
    """Checks if the given element is actionable."""
    return (
        isinstance(element, SpecOp)
        and element.op == "send"
        and element.spec.name not in INTERNAL_EVENTS
    )


def _evaluate_arguments(arguments: dict, context: dict) -> dict:
    return dict([(key, eval_expression(arguments[key], context)) for key in arguments])


def _is_match_op_element(element: SpecOp) -> bool:
    return isinstance(element, SpecOp) and element.op == "match"


def _compute_event_matching_score(
    state: State, flow_state: FlowState, element: SpecOp, event: Event
) -> float:
    """Checks if the given element matches the given event."""

    assert _is_match_op_element(element), f"Element '{element}' is not a match element!"

    ref_event = _get_event_from_element(state, flow_state, element)

    # element_spec = element["spec"]

    # element_spec_args = element["spec"]["arguments"] or {}
    # element_spec_args = dict(
    #     [
    #         (key, eval_expression(element_spec_args[key], flow_state.context))
    #         for key in element_spec_args
    #     ]
    # )

    # # Convert element to matching reference event
    # ref_event: Event
    # if element_spec["var_name"] is not None:
    #     # Element refers to a reference variable
    #     variable_name = element_spec["var_name"]
    #     if variable_name not in flow_state.context:
    #         logging.warning(f"Unkown variable: '{variable_name}'!")
    #         return 0.0

    #     # Resolve variable
    #     context_variable = flow_state.context[variable_name]
    #     if context_variable["type"] == ContextVariableType.ACTION_REFERENCE:
    #         action = flow_state.actions[context_variable["value"]]
    #         action_event_name = element.spec.members[0]["name"]
    #         ref_event: Event = action.get_event(action_event_name, element_spec_args)
    # else:
    #     # Element refers to an event
    #     ref_event = Event(element_spec["name"], event.arguments)

    FUZZY_MATCH_FACTOR = 0.5

    # Compute matching score based on event argument matching
    if event.name == "StartFlow":
        for var in event.arguments:
            if (
                var in ref_event.arguments
                and event.arguments[var] != ref_event.arguments[var]
            ):
                return 0.0

        return float(
            ref_event.name == "StartFlow"
            and ref_event.arguments["flow_id"] == event.arguments["flow_id"]
        )
    elif event.name in INTERNAL_EVENTS:
        return float(
            ref_event.name == event.name
            and ref_event.arguments["flow_id"]
            == state.flow_states[event.arguments["source_flow_instance_uid"]].flow_id
        )
    else:
        # Its an UMIM event
        if ref_event.name != event.name:
            return 0.0

        if (
            ref_event.action_uid is not None
            and ref_event.action_uid != event.action_uid
        ):
            return 0.0

        if event.action_uid is not None:
            action_arguments = state.actions[event.action_uid].start_event_arguments
            event.arguments["action_arguments"] = action_arguments

        # score = 1.0
        # for key, value in element.items():
        #     # Skip potentially private keys.
        #     if key.startswith("_"):
        #         continue
        #     if value == "...":
        #         score *= FUZZY_MATCH_FACTOR
        #     if event.get(key) != value:
        #         return float(False)

        return _compute_arguments_dict_matching_score(
            event.arguments, ref_event.arguments
        )


def _compute_arguments_dict_matching_score(args: dict, ref_args: dict) -> float:
    score = 1.0
    for key in args.keys():
        if key in ref_args:
            if isinstance(args[key], dict) and isinstance(ref_args[key], dict):
                # If both values are dictionaries, recursively compare them
                score *= _compute_arguments_dict_matching_score(
                    args[key], ref_args[key]
                )
            elif args[key] == ref_args[key]:
                continue
            else:
                return 0.0
        else:
            # This is a fuzzy match since the argument is missing
            score *= 0.9
    return score


def _get_event_from_element(
    state: State, flow_state: FlowState, element: dict
) -> Event:
    """
    Converts the element into the corresponding event if possible.

    Cases:
    1) Bare event: send/match UtteranceBotActionFinished(args)
    2) Event as member of a action or flow constructor: send/match UtteranceBotAction(args).Finished(args)
    3) Event as member of a action or flow reference: send/match $ref.Finished(args) (This is action/flow specific)
    """

    element_spec: Spec = element.spec

    action: Action
    if element_spec["var_name"] is not None:
        # Case 3)
        variable_name = element_spec["var_name"]
        if variable_name not in flow_state.context:
            raise Exception((f"Unkown variable: '{variable_name}'!"))

        # Resolve variable
        context_variable = flow_state.context[variable_name]
        if context_variable["type"] == ContextVariableType.EVENT_REFERENCE:
            raise NotImplementedError
        elif context_variable["type"] == ContextVariableType.ACTION_REFERENCE:
            action = state.actions[context_variable["value"]]
            action_event_name = element_spec.members[0]["name"]
            action_event_arguments = element_spec.members[0]["arguments"]
            action_event_arguments = _evaluate_arguments(
                action_event_arguments, flow_state.context
            )
            action_event: Event = action.get_event(
                action_event_name, action_event_arguments
            )
            action_event.action_uid = action.uid
            return action_event
        elif context_variable["type"] == ContextVariableType.FLOW_REFERENCE:
            raise NotImplementedError

    if element_spec.members is not None:
        # Case 2)
        if element_spec.name in state.flow_configs:
            # Flow object
            flow_config = state.flow_configs[element_spec.name]
            temp_flow_state = _create_flow_instance(flow_config)
            flow_event_name = element_spec.members[0]["name"]
            flow_event_arguments = element_spec.members[0]["arguments"]
            flow_event_arguments = _evaluate_arguments(
                flow_event_arguments, flow_state.context
            )
            flow_event: FlowEvent = temp_flow_state.get_event(
                flow_event_name, flow_event_arguments
            )
            if element["op"] == "match":
                # Delete action_uid from event since the action is only a helper object
                flow_event.flow = None
            return flow_event
        else:
            # Action object
            action_arguments = _evaluate_arguments(
                element_spec.arguments, flow_state.context
            )
            action = Action(element_spec.name, action_arguments, flow_state.flow_id)
            # TODO: refactor the following repetition of code (see above)
            action_event_name = element_spec.members[0]["name"]
            action_event_arguments = element_spec.members[0]["arguments"]
            action_event_arguments = _evaluate_arguments(
                action_event_arguments, flow_state.context
            )
            action_event: ActionEvent = action.get_event(
                action_event_name, action_event_arguments
            )
            if element["op"] == "match":
                # Delete action_uid from event since the action is only a helper object
                action_event.action_uid = None
            return action_event
    else:
        # Case 1)
        if element_spec.name in state.flow_configs:
            # Flow object
            raise NotImplementedError
        else:
            # Action object
            event_arguments = _evaluate_arguments(
                element_spec.arguments, flow_state.context
            )
            action_event = Event(element_spec.name, event_arguments)
            return action_event

    # else:
    #     # Element refers to an event
    #     ref_event = Event(element_spec["name"], event.arguments)

    # if element.ref is not None and element.ref["_type"] == "capture_ref":
    #     ref_name = element.ref["elements"][0]["elements"][0].lstrip("$")
    #     reference = flow_state.context[ref_name]
    #     if reference["type"] == ContextVariableType.EVENT_REFERENCE:
    #         raise NotImplementedError
    #     elif reference["type"] == ContextVariableType.ACTION_REFERENCE:
    #         action = flow_state.actions[reference["value"]]
    #     elif reference["type"] == ContextVariableType.FLOW_REFERENCE:
    #         raise NotImplementedError
    # elif element_spec.members is not None:
    #     action_event_name = element_spec.members[0]["name"]

    # else:
    #     pass

    # action_event_name = element_spec.members[0]["name"]
    # event: Event = action.get_event(action_event_name, evaluated_event_arguments)
    # event_name = event.name
    # evaluated_event_arguments = event.arguments

    # action_event_name = element.spec.members[0]["name"]
    # ref_event: Event = action.get_event(action_event_name, element_spec_args)


def _create_outgoing_event_from_actionable_element(
    state: State,
    head: FlowHead,
) -> None:
    """Helper to create an outgoing event from the flow head element."""
    flow_state = _get_flow_state_from_head(state, head)
    element = _get_head_element_from_head(state, head)
    assert _is_action_op_element(
        element
    ), f"Cannot create an event from a non actionable flow element {element}!"

    # Evaluate expressions (eliminate all double quotes)
    # evaluated_event_arguments = _evaluate_arguments(
    #     element.spec.arguments, flow_state.context
    # )

    if element.op == "send":
        # event_name: str
        # if element.ref is not None and element.ref["_type"] == "capture_ref":
        #     ref_name = element.ref["elements"][0]["elements"][0].lstrip("$")
        #     reference = flow_state.context[ref_name]
        #     if reference["type"] == ContextVariableType.EVENT_REFERENCE:
        #         raise NotImplementedError
        #     elif reference["type"] == ContextVariableType.ACTION_REFERENCE:
        #         action = flow_state.actions[reference["value"]]
        #         action_event_name = element.spec.members[0]["name"]
        #         event: Event = action.get_event(
        #             action_event_name, evaluated_event_arguments
        #         )
        #         event_name = event.name
        #         evaluated_event_arguments = event.arguments
        #         evaluated_event_arguments["action_uid"] = action.uid
        #     elif reference["type"] == ContextVariableType.FLOW_REFERENCE:
        #         raise NotImplementedError
        # else:
        #     event_name = element.spec.name
        #     evaluated_event_arguments["action_uid"] = new_uid()

        event = _get_event_from_element(state, flow_state, element)
        umim_event = create_umim_action_event(event, event.arguments)

        state.outgoing_events.append(umim_event)

    # Extract the comment, if any
    # state.next_steps_comment = element.get("_source_mapping", {}).get("comment")


# NOTE (schuellc): Are we going to replace this with a stateful approach
def compute_next_events(
    history: List[dict], flow_configs: Dict[str, FlowConfig]
) -> List[dict]:
    """Computes the next step in a flow-driven system given a history of events."""
    state = State(context={}, flow_states={}, flow_configs=flow_configs)
    state.initialize()

    # First, we process the history and apply any alterations e.g. 'hide_prev_turn'
    actual_history = []
    for event in history:
        # NOTE (schuellc): Why is this needed?
        if event.name == "hide_prev_turn":
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
        if event.name == "bot_intent" and event["intent"] == "stop":
            # Reset all flows
            state.flow_states = {}

    next_events = []

    # If we have context updates after this event, we first add that.
    if state.context_updates:
        next_events.append(new_event_dict("ContextUpdate", data=state.context_updates))

    # If we have a next step, we make sure to convert it to proper event structure.
    for next_step_event in state.outgoing_events:
        next_events.append(next_step_event)

    # Finally, we check if there was an explicit "stop" request
    if actual_history:
        last_event = actual_history[-1]
        # NOTE (schuellc): Why is this needed?
        if last_event.name == "BotIntent" and last_event["intent"] == "stop":
            # In this case, we remove any next steps
            next_events = []

    return next_events


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
        if event.name == "ContextUpdate":
            context.update(event["data"])

        if event.name == "UtteranceUserActionFinished":
            context["last_user_message"] = event["final_transcript"]

        elif event.name == "StartUtteranceBotAction":
            context["last_bot_message"] = event["script"]

    return context


def create_abort_flow_internal_event(
    flow_instance_uid: str, source_flow_instance_uid: str, matching_scores: List[float]
) -> Event:
    """Returns 'AbortFlow' internal event"""
    return create_internal_event(
        "AbortFlow",
        {
            "flow_instance_uid": flow_instance_uid,
            "source_flow_instance_uid": source_flow_instance_uid,
        },
        matching_scores,
    )


def create_flow_started_internal_event(
    source_flow_instance_uid: str, matching_scores: List[float]
) -> Event:
    """Returns 'FlowStarted' internal event"""
    return create_internal_event(
        "FlowStarted",
        {"source_flow_instance_uid": source_flow_instance_uid},
        matching_scores,
    )


def create_flow_finished_internal_event(
    source_flow_instance_uid: str, matching_scores: List[float]
) -> Event:
    """Returns 'FlowFinished' internal event"""
    return create_internal_event(
        "FlowFinished",
        {"source_flow_instance_uid": source_flow_instance_uid},
        matching_scores,
    )


def create_flow_failed_internal_event(
    source_flow_instance_uid: str, matching_scores: List[float]
) -> Event:
    """Returns 'FlowFailed' internal event"""
    return create_internal_event(
        "FlowFailed",
        {"source_flow_instance_uid": source_flow_instance_uid},
        matching_scores,
    )


def create_internal_event(
    event_name: str, event_args: dict, matching_scores: List[float]
) -> Event:
    """Returns an internal event for the provided event data"""
    event = Event(event_name, event_args, matching_scores=matching_scores)
    return event


def create_umim_action_event(event: Event, event_args: dict) -> Dict[str, Any]:
    """Returns an outgoing UMIM event for the provided action data"""
    if event.action_uid is not None:
        return new_event_dict(event.name, action_uid=event.action_uid, **event_args)
    else:
        return new_event_dict(event.name, **event_args)
