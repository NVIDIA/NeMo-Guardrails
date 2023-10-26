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
import random
import re
import time
from collections import deque
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Callable, Deque, Dict, List, Optional, Tuple, Union, cast

from dataclasses_json import dataclass_json

from nemoguardrails.colang.v1_1.lang.colang_ast import (
    Abort,
    Assignment,
    BeginScope,
    Break,
    CatchPatternFailure,
    Continue,
    Element,
    EndScope,
    FlowParamDef,
    ForkHead,
    Goto,
    If,
    Label,
    MergeHeads,
    Priority,
    Return,
    Spec,
    SpecOp,
    SpecType,
    WaitForHeads,
    When,
    While,
)
from nemoguardrails.colang.v1_1.runtime.eval import eval_expression
from nemoguardrails.colang.v1_1.runtime.utils import new_readable_uid, new_var_uid
from nemoguardrails.utils import new_event_dict, new_uid

log = logging.getLogger(__name__)

random_seed = int(time.time())


class InternalEvents:
    """All internal event types."""

    START_FLOW = "StartFlow"
    FINISH_FLOW = "FinishFlow"
    STOP_FLOW = "StopFlow"
    FLOW_STARTED = "FlowStarted"
    FLOW_FINISHED = "FlowFinished"
    FLOW_FAILED = "FlowFailed"
    START_SIBLING_FLOW = "StartSiblingFlow"
    DISABLE_FLOW_INSTANCE_RESTART = "DisableFlowInstanceRestart"
    UNHANDLED_EVENT = "UnhandledEvent"
    DYNAMIC_FLOW_FINISHED = "DynamicFlowFinished"  # TODO: Check if this is needed

    ALL = {
        START_FLOW,
        FINISH_FLOW,
        STOP_FLOW,
        FLOW_STARTED,
        FLOW_FINISHED,
        FLOW_FAILED,
        START_SIBLING_FLOW,
        DISABLE_FLOW_INSTANCE_RESTART,
        UNHANDLED_EVENT,
        DYNAMIC_FLOW_FINISHED,
    }


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

    def is_equal(self, other: Event) -> bool:
        if isinstance(other, Event):
            return self.name == other.name and self.arguments == other.arguments
        return NotImplemented

    def __eq__(self, other: Event) -> bool:
        return self.is_equal(other)

    def __str__(self) -> str:
        return f"[bold blue]{self.name}[/] {self.arguments}"


@dataclass
class ActionEvent(Event):
    """The action event class."""

    # The event can belong to an action
    action_uid: Optional[str] = None

    # This is the action reference to enable direct access via expressions
    # This needs to be consistent with the action_uid
    action: Optional[Action] = None

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
class InternalEvent(Event):
    """The flow event class."""

    # An event can belong to a flow
    flow: Optional[FlowState] = None


class ActionStatus(Enum):
    """The type of a context variable."""

    INITIALIZED = "initialized"
    STARTING = "starting"
    STARTED = "started"
    STOPPING = "stopping"
    FINISHED = "finished"


class Action:
    """The action groups and manages the action events."""

    # The action event name mapping
    _event_name_map = {
        "Started": "started_event",
        "Updated": "updated_event",
        "Finished": "finished_event",
        "Start": "start_event",
        "Change": "change_event",
        "Stop": "stop_event",
    }

    @classmethod
    def from_event(cls, event: ActionEvent) -> Optional[Action]:
        """Returns the name of the action if event name conforms with UMIM convention."""
        for name in cls._event_name_map:
            if name in event.name:
                action = Action(event.name.replace(name, ""), {})
                action.uid = event.action_uid
                action.status = (
                    ActionStatus.STARTED
                    if name != "Finished"
                    else ActionStatus.FINISHED
                )
                return action
        return None

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

    # Process an event
    def process_event(self, event: ActionEvent) -> None:
        """Processes event and updates action accordingly."""
        # TODO: This matching can easily break if action names are badly chosen
        if "Action" in event.name and event.action_uid == self.uid:
            if "ActionStarted" in event.name:
                self.context.update(event.arguments)
                self.status = ActionStatus.STARTED
            elif "ActionUpdated" in event.name:
                self.context.update(event.arguments)
            elif "ActionFinished" in event.name:
                self.context.update(event.arguments)
                self.status = ActionStatus.FINISHED
            elif "Start" in event.name:
                self.context.update(event.arguments)
                self.status = ActionStatus.STARTING
            elif "Stop" in event.name:
                self.context.update(event.arguments)
                self.status = ActionStatus.STOPPING

    def get_event(self, name: str, arguments: dict) -> Callable[[], ActionEvent]:
        """Returns the corresponding action event."""
        assert name in Action._event_name_map, f"Event '{name}' not available!"
        func = getattr(self, Action._event_name_map[name])
        return func(arguments)

    # Action events to send
    def start_event(self, args: dict) -> ActionEvent:
        """Starts the action. Takes no arguments."""
        return ActionEvent(
            name=f"Start{self.name}",
            arguments=self.start_event_arguments,
            action_uid=self.uid,
        )

    def change_event(self, args: dict) -> ActionEvent:
        """Changes a parameter of a started action."""
        return ActionEvent(
            name=f"Change{self.name}", arguments=args["arguments"], action_uid=self.uid
        )

    def stop_event(self, args: dict) -> ActionEvent:
        """Stops a started action. Takes no arguments."""
        return ActionEvent(name=f"Stop{self.name}", arguments={}, action_uid=self.uid)

    # Action events to match
    def started_event(self, args: dict) -> ActionEvent:
        """Returns the Started action event."""
        arguments = args.copy()
        arguments["action_arguments"] = self.start_event_arguments
        return ActionEvent(
            name=f"{self.name}Started", arguments=arguments, action_uid=self.uid
        )

    def updated_event(self, args: dict) -> ActionEvent:
        """Returns the Updated parameter action event."""
        arguments = args.copy()
        arguments["action_arguments"] = self.start_event_arguments
        return ActionEvent(
            name=f"{self.name}{args['parameter_name']}Updated",
            arguments=arguments,
            action_uid=self.uid,
        )

    def finished_event(self, args: dict) -> ActionEvent:
        """Returns the Finished action event."""
        arguments = args.copy()
        arguments["action_arguments"] = self.start_event_arguments
        return ActionEvent(
            name=f"{self.name}Finished", arguments=arguments, action_uid=self.uid
        )


class InteractionLoopType(Enum):
    """The type of the interaction loop."""

    NEW = "new"  # Every new instance of the flow will live in its own new loop
    PARENT = "parent"  # Every new instance of the flow will live in the same loop as its the parent
    NAMED = "named"  # Every new instance of the flow will live in the loop with the given name


ElementType = Union[Element, SpecOp, dict]


@dataclass
class FlowConfig:
    """The configuration of a flow."""

    # A unique id of the flow.
    id: str

    # The sequence of elements that compose the flow.
    elements: List[ElementType]

    # The flow parameters
    parameters: List[FlowParamDef]

    # All the label element positions in the flow
    element_labels: Dict[str, int] = field(default_factory=dict)

    # Interaction loop
    loop_id: Optional[str] = None
    loop_type: InteractionLoopType = InteractionLoopType.PARENT

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

    # Whether a head is active or not (a head fork will deactivate the parent head)
    active: bool = True

    # List of all scopes that are relevant for the head
    scope_uids: List[str] = field(default_factory=list)

    # If a flow head is forked it will create new child heads
    child_head_uids: List[str] = field(default_factory=list)

    # If set a flow failure will be diverted to the label, otherwise it will abort the flow
    # Mainly used to simplify inner flow logic
    catch_pattern_failure_label: Optional[str] = None

    def get_child_head_uids(self, state: State) -> List[str]:
        """ "Return uids of all child heads (recursively)."""
        flow_state = state.flow_states[self.flow_state_uid]
        child_uids: List[str] = []
        for uid in self.child_head_uids:
            child_uids.append(uid)
            # TODO: Make sure that child head uids are kept up-to-date
            if uid in flow_state.heads:
                child_uids.extend(flow_state.heads[uid].get_child_head_uids(state))
        return child_uids

    def __eq__(self, other: Any) -> bool:
        if isinstance(other, FlowHead):
            return self.uid == other.uid
        return NotImplemented

    def __hash__(self):
        return hash(self.uid)

    def __str__(self) -> str:
        return f"flow='{self.flow_state_uid.split(')',1)[0][1:]}' pos={self.position}"


class FlowStatus(Enum):
    """The status of a flow."""

    WAITING = "waiting"  # Waiting for the flow to start (first match statement)
    STARTING = "starting"  # Flow has been started but head is not yet at the next match statement
    STARTED = "started"  # Flow is considered started when head arrived at second match statement
    STOPPING = "stopping"  # Flow was stopped from inside ('abort') but did not yet stop all child flows or actions
    STOPPED = "stopped"  # Flow has stopped/failed and all child flows and actions
    FINISHING = "finishing"  # Flow has finished (end or early return), did not yet stop child flows or actions
    FINISHED = (
        "finished"  # Flow has finished and all child flows and actions were stopped
    )


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

    # All the heads that point to the positions in the sequence of elements that compose the flow.
    heads: Dict[str, FlowHead] = field(default_factory=dict)

    # All active/open scopes that contain a tuple of flow uids and action uids that were started within that scope
    scopes: Dict[str, Tuple(List[str], List[str])] = field(default_factory=dict)

    # All actions that were instantiated since the beginning of the flow
    action_uids: List[str] = field(default_factory=list)

    # The current set of variables in the flow state.
    context: dict = field(default_factory=dict)

    # The current priority of the flow instance that is used for action resolution.
    priority: float = 1.0

    # Child flow ids
    arguments: List[str] = field(default_factory=list)

    # Parent flow id
    # TODO: Implement proper parenting
    parent_uid: Optional[str] = None

    # Child flow ids
    child_flow_uids: List[str] = field(default_factory=list)

    # The current state of the flow
    status: FlowStatus = FlowStatus.WAITING

    # An activated flow will restart immediately when finished
    activated: bool = False

    # True if a new instance was started either by restarting or
    # a early 'start_new_flow_instance' label
    new_instance_started: bool = False

    # The UID of the flows that interrupted this one
    # interrupted_by = None

    # The flow event name mapping
    _event_name_map: dict = field(init=False)

    @property
    def active_heads(self):
        """Returns all active heads of this flow."""
        return {id: h for (id, h) in self.heads.items() if h.active}

    def __post_init__(self) -> None:
        self._event_name_map = {
            "Start": "start_event",
            "Stop": "stop_event",
            "Pause": "pause_event",
            "Resume": "resume_event",
            "Started": "started_event",
            "Paused": "paused_event",
            "Resumed": "resumed_event",
            "Finished": "finished_event",
            "Failed": "failed_event",
        }

    def get_event(self, name: str, arguments: dict) -> Callable[[], InternalEvent]:
        """Returns the corresponding action event."""
        assert name in self._event_name_map, f"Event '{name}' not available!"
        func = getattr(self, self._event_name_map[name])
        return func(arguments)

    # Flow events to send
    def start_event(self, args: dict) -> InternalEvent:
        """Starts the flow. Takes no arguments."""
        return InternalEvent(
            name=InternalEvents.START_FLOW, arguments={"flow_id": self.flow_id}
        )

    def finish_event(self, args: dict) -> InternalEvent:
        """Finishes the flow. Takes no arguments."""
        return InternalEvent(
            name=InternalEvents.FINISH_FLOW,
            arguments={"flow_id": self.flow_id, "flow_instance_uid": self.uid},
        )

    def stop_event(self, args: dict) -> InternalEvent:
        """Stops the flow. Takes no arguments."""
        return InternalEvent(
            name="StopFlow",
            arguments={"flow_id": self.flow_id, "flow_instance_uid": self.uid},
        )

    def pause_event(self, args: dict) -> InternalEvent:
        """Pauses the flow. Takes no arguments."""
        return InternalEvent(
            name="PauseFlow",
            arguments={"flow_id": self.flow_id, "flow_instance_uid": self.uid},
        )

    def resume_event(self, args: dict) -> InternalEvent:
        """Resumes the flow. Takes no arguments."""
        return InternalEvent(
            name="ResumeFlow",
            arguments={"flow_id": self.flow_id, "flow_instance_uid": self.uid},
        )

    # Flow events to match
    def started_event(self, args: dict) -> InternalEvent:
        """Returns the flow Started event."""
        return self._create_event(InternalEvents.FLOW_STARTED, args)

    # def paused_event(self, args: dict) -> FlowEvent:
    #     """Returns the flow Pause event."""
    #     return self._create_event(InternalEvents.FLOW_PAUSED, args)

    # def resumed_event(self, args: dict) -> FlowEvent:
    #     """Returns the flow Resumed event."""
    #     return self._create_event(InternalEvents.FLOW_RESUMED, args)

    def finished_event(self, args: dict) -> InternalEvent:
        """Returns the flow Finished event."""
        return self._create_event(InternalEvents.FLOW_FINISHED, args)

    def failed_event(self, args: dict) -> InternalEvent:
        """Returns the flow Failed event."""
        return self._create_event(InternalEvents.FLOW_FAILED, args)

    def _create_event(self, event_type: str, args: dict) -> InternalEvent:
        arguments = args.copy()
        arguments["flow_id"] = self.flow_id
        arguments.update(
            dict(
                [
                    (arg, self.context[arg])
                    for arg in self.arguments
                    if arg in self.context
                ]
            )
        )
        return InternalEvent(event_type, arguments)


@dataclass_json
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

    # The most recent N events that have been processed. Will be capped at a
    # reasonable limit e.g. 100. The history is needed when prompting the LLM for example.
    last_events: List[dict] = field(default_factory=list)

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
        for flow_config in self.flow_configs.values():
            initialize_flow(self, flow_config)

        # Create main flow state first
        main_flow_config = self.flow_configs["main"]
        main_flow = add_new_flow_instance(self, create_flow_instance(main_flow_config))
        if main_flow_config.loop_id is None:
            main_flow.loop_id = new_readable_uid("main")
        else:
            main_flow.loop_id = main_flow_config.loop_id
        self.main_flow_state = main_flow

        # Create flow states for all other flows and start with head at position 0.
        for flow_config in self.flow_configs.values():
            if flow_config.id != "main":
                add_new_flow_instance(self, create_flow_instance(flow_config))


class ColangSyntaxError(Exception):
    """Raises when there is invalid Colang syntax detected"""

    pass


class ColangValueError(Exception):
    """Raises when there is an invalid value detected in a Colang expression"""

    pass


class ColangRuntimeError(Exception):
    """Raises when there is a Colang related runtime exception."""

    pass


def initialize_flow(state: State, flow_config: FlowConfig) -> None:
    # Transform and resolve flow configuration element notation (actions, flows, ...)
    flow_config.elements = expand_elements(flow_config.elements, state.flow_configs)

    # Extract flow loop id if available
    if flow_config.source_code:
        match = re.search(r"#\W*loop_id:\W*(\w*)", flow_config.source_code)
        if match:
            flow_config.loop_id = match.group(1)

    # Extract all the label elements
    for idx, element in enumerate(flow_config.elements):
        if isinstance(element, Label):
            flow_config.element_labels.update({element["name"]: idx})


def expand_elements(
    elements: List[ElementType],
    flow_configs: Dict[str, FlowConfig],
    continue_break_labels: Optional[Tuple[str, str]] = None,
) -> List[ElementType]:
    elements_changed = True
    while elements_changed:
        elements_changed = False
        new_elements: List[ElementType] = []
        for element in elements:
            expanded_elems: List[ElementType] = []
            if isinstance(element, SpecOp):
                if element.op == "send":
                    expanded_elems = _expand_send_element(element)
                elif element.op == "match":
                    expanded_elems = _expand_match_element(element)
                elif element.op == "start":
                    expanded_elems = _expand_start_element(element)
                elif element.op == "stop":
                    expanded_elems = _expand_stop_element(element)
                elif element.op == "activate":
                    expanded_elems = _expand_activate_element(element)
                elif element.op == "await":
                    expanded_elems = _expand_await_element(element)
                if len(expanded_elems) > 0:
                    elements_changed = True
            elif isinstance(element, While):
                expanded_elems = _expand_while_stmt_element(element, flow_configs)
            elif isinstance(element, If):
                expanded_elems = _expand_if_element(element, flow_configs)
                elements_changed = True  # Makes sure to update continue/break elements
            elif isinstance(element, When):
                expanded_elems = _expand_when_stmt_element(element, flow_configs)
                elements_changed = True  # Makes sure to update continue/break elements
            elif isinstance(element, Continue):
                if element.label is None and continue_break_labels is not None:
                    element.label = continue_break_labels[0]
            elif isinstance(element, Break):
                if element.label is None and continue_break_labels is not None:
                    element.label = continue_break_labels[1]

            if len(expanded_elems) > 0:
                new_elements.extend(expanded_elems)
            else:
                new_elements.extend([element])

        elements = new_elements
    return elements


def _expand_element_group(element: SpecOp) -> List[ElementType]:
    # TODO: Simplify for a single or group (we don't need head forking)
    new_elements: List[ElementType] = []

    normalized_group = normalize_element_groups(element.spec)

    if len(normalized_group["elements"]) == 1:
        # Only one and-group
        for and_group in normalized_group["elements"]:
            for group_element in and_group["elements"]:
                new_elements.append(
                    SpecOp(
                        op=element.op,
                        spec=group_element,
                    )
                )
    else:
        # Multiple and-groups
        fork_element = ForkHead()
        fork_head_uids: List(str) = []
        group_label_elements: List[Label] = []
        failure_label_name = f"failure_label_{new_var_uid()}"
        failure_label_element = Label(name=failure_label_name)
        end_label_name = f"end_label_{new_var_uid()}"
        goto_end_element = Goto(label=end_label_name)
        end_label_element = Label(name=end_label_name)

        for group_idx, and_group in enumerate(normalized_group["elements"]):
            group_label_name = f"group_{group_idx}_{new_var_uid()}"
            group_label_elements.append(Label(name=group_label_name))
            fork_head_uids.append(new_var_uid())
            fork_element.head_uids.append(fork_head_uids[-1])
            fork_element.labels.append(group_label_name)

        # Generate new element sequence
        new_elements.append(CatchPatternFailure(label=failure_label_name))
        new_elements.append(fork_element)
        for group_idx, and_group in enumerate(normalized_group["elements"]):
            new_elements.append(group_label_elements[group_idx])
            for group_element in and_group["elements"]:
                new_elements.append(
                    SpecOp(
                        op=element.op,
                        spec=group_element,
                    )
                )
            new_elements.append(goto_end_element)
        new_elements.append(failure_label_element)
        new_elements.append(WaitForHeads(number=len(normalized_group["elements"])))
        new_elements.append(CatchPatternFailure(label=None))
        new_elements.append(Abort())
        new_elements.append(end_label_element)
        new_elements.append(MergeHeads(head_uids=fork_head_uids))

    return new_elements


def _expand_start_element(
    element: SpecOp,
) -> List[ElementType]:
    new_elements: List[ElementType] = []
    if isinstance(element.spec, Spec):
        # Single element
        if element.spec.spec_type == SpecType.FLOW and element.spec.members is None:
            # It's a flow
            # send StartFlow(flow_id="FLOW_NAME")
            element.spec.arguments.update(
                {
                    "flow_id": f"'{element.spec.name}'",
                    "flow_start_uid": f"'{new_var_uid()}'",
                }
            )
            new_elements.append(
                SpecOp(
                    op="send",
                    spec=Spec(
                        name=InternalEvents.START_FLOW,
                        arguments=element.spec.arguments,
                        spec_type=SpecType.EVENT,
                    ),
                )
            )
            # match FlowStarted(...) as $_flow_event_ref
            flow_event_ref_uid = f"_flow_event_ref_{new_var_uid()}"
            new_elements.append(
                SpecOp(
                    op="match",
                    spec=Spec(
                        name=InternalEvents.FLOW_STARTED,
                        arguments=element.spec.arguments,
                        ref=_create_ref_ast_dict_helper(flow_event_ref_uid),
                        spec_type=SpecType.EVENT,
                    ),
                    info={"internal": True},
                )
            )
            # $flow_ref = $_flow_event_ref.flow
            element_ref = element.spec.ref
            if element_ref is None:
                flow_ref_uid = f"_flow_ref_{new_var_uid()}"
                element_ref = _create_ref_ast_dict_helper(flow_ref_uid)
            new_elements.append(
                Assignment(
                    key=element_ref["elements"][0]["elements"][0].lstrip("$"),
                    expression=f"${flow_event_ref_uid}.flow",
                )
            )
        elif element.spec.spec_type == SpecType.ACTION:
            # It's an UMIM action
            element_ref = element.spec.ref
            if element_ref is None:
                action_event_ref_uid = f"_action_ref_{new_var_uid()}"
                element_ref = _create_ref_ast_dict_helper(action_event_ref_uid)
                element.spec.ref = element_ref
            new_elements.append(
                SpecOp(
                    op="_new_action_instance",
                    spec=element.spec,
                )
            )
            new_elements.append(
                SpecOp(
                    op="send",
                    spec=Spec(
                        name=element.spec.name,
                        arguments=element.spec.arguments,
                        members=_create_member_ast_dict_helper("Start", {}),
                        var_name=element_ref["elements"][0]["elements"][0].lstrip("$"),
                        spec_type=SpecType.EVENT,
                    ),
                )
            )
        else:
            raise ColangSyntaxError(
                f"'await' keyword cannot be used on '{element.spec.spec_type}'"
            )
    else:
        # Element group
        new_elements = _expand_element_group(element)

    return new_elements


def _expand_stop_element(
    element: SpecOp,
) -> List[ElementType]:
    new_elements: List[ElementType] = []
    if isinstance(element.spec, Spec):
        # Single element
        raise NotImplementedError()
        if (
            element.spec.spec_type == SpecType.REFERENCE
            and element.spec.members is None
        ):
            # It's a reference to a flow or action
            new_elements.append(
                SpecOp(
                    op="send",
                    spec=Spec(
                        name=InternalEvents.STOP_FLOW,
                        arguments=element.spec.arguments,
                        spec_type=SpecType.EVENT,
                    ),
                )
            )
        else:
            raise ColangSyntaxError(
                f"'stop' keyword cannot yet be used on '{element.spec.spec_type}'"
            )
    else:
        # Element group
        new_elements = _expand_element_group(element)

    return new_elements


def _expand_send_element(
    element: SpecOp,
) -> List[ElementType]:
    new_elements: List[ElementType] = []
    if isinstance(element.spec, Spec):
        # Single send element
        if element.spec.spec_type != SpecType.EVENT and element.spec.members is None:
            raise ColangSyntaxError(
                f"Cannot send a non-event type: '{element.spec.spec_type}'"
            )
    elif isinstance(element.spec, dict):
        # Element group
        new_elements = _expand_element_group(element)

    return new_elements


def _expand_match_element(
    element: SpecOp,
) -> List[ElementType]:
    new_elements: List[ElementType] = []
    if isinstance(element.spec, Spec):
        # Single match element
        if element.spec.spec_type == SpecType.FLOW and element.spec.members is None:
            # It's a flow
            element_ref = element.spec.ref
            if element_ref is None:
                element_ref = _create_ref_ast_dict_helper(
                    f"_flow_event_ref_{new_var_uid()}"
                )

            arguments = {"flow_id": f"'{element.spec.name}'"}
            for arg in element.spec.arguments:
                arguments.update({arg: element.spec.arguments[arg]})

            new_elements.append(
                SpecOp(
                    op="match",
                    spec=Spec(
                        name=InternalEvents.FLOW_FINISHED,
                        arguments=arguments,
                        ref=element_ref,
                        spec_type=SpecType.EVENT,
                    ),
                    return_var_name=element.return_var_name,
                )
            )
            if element.return_var_name is not None:
                new_elements.append(
                    Assignment(
                        key=element.return_var_name,
                        expression=f"${element_ref['elements'][0]['elements'][0]}.arguments.return_value",
                    )
                )
        elif (
            element.spec.spec_type == SpecType.EVENT or element.spec.members is not None
        ):
            # It's an event
            if element.return_var_name is not None:
                element_ref = element.spec.ref
                if element_ref is None:
                    element_ref = _create_ref_ast_dict_helper(
                        f"_event_ref_{new_var_uid()}"
                    )

                return_var_name = element.return_var_name

                element.spec.ref = element_ref
                element.return_var_name = None

                new_elements.append(element)
                new_elements.append(
                    Assignment(
                        key=return_var_name,
                        expression=f"${element_ref['elements'][0]['elements'][0]}.arguments.return_value",
                    )
                )
        else:
            raise ColangSyntaxError(
                f"Unsupported spec type: '{element.spec.spec_type}'"
            )

    elif isinstance(element.spec, dict):
        # Element group
        normalized_group = normalize_element_groups(element.spec)

        if (
            len(normalized_group["elements"]) == 1
            and len(normalized_group["elements"][0]["elements"]) == 1
        ):
            # Only one and-group with a single element
            new_elements.append(
                SpecOp(
                    op=element.op,
                    spec=normalized_group["elements"][0]["elements"][0],
                )
            )
        else:
            fork_element = ForkHead()
            fork_head_uids: List(str) = []
            event_label_elements: List[Label] = []
            event_match_elements: List[SpecOp] = []
            goto_group_elements: List[Goto] = []
            group_label_elements: List[Label] = []
            wait_for_heads_elements: List[WaitForHeads] = []
            end_label_name = f"end_label_{new_var_uid()}"
            goto_end_element = Goto(label=end_label_name)
            end_label_element = Label(name=end_label_name)

            element_idx = 0
            for group_idx, and_group in enumerate(normalized_group["elements"]):
                group_label_name = f"group_{group_idx}_{new_var_uid()}"
                group_label_elements.append(Label(name=group_label_name))
                goto_group_elements.append(Goto(label=group_label_name))
                wait_for_heads_elements.append(
                    WaitForHeads(number=len(and_group["elements"]))
                )

                for match_element in and_group["elements"]:
                    label_name = f"event_{element_idx}_{new_var_uid()}"
                    event_label_elements.append(Label(name=label_name))
                    fork_head_uids.append(new_var_uid())
                    fork_element.head_uids.append(fork_head_uids[-1])
                    fork_element.labels.append(label_name)
                    event_match_elements.append(
                        SpecOp(
                            op="match",
                            spec=match_element,
                        ),
                    )
                    element_idx += 1

            # Generate new element sequence
            element_idx = 0
            new_elements.append(fork_element)
            for group_idx, and_group in enumerate(normalized_group["elements"]):
                for match_element in and_group["elements"]:
                    new_elements.append(event_label_elements[element_idx])
                    new_elements.append(event_match_elements[element_idx])
                    new_elements.append(goto_group_elements[group_idx])
                    element_idx += 1
                new_elements.append(group_label_elements[group_idx])
                new_elements.append(wait_for_heads_elements[group_idx])
                new_elements.append(MergeHeads(head_uids=fork_head_uids))
                new_elements.append(goto_end_element)
            new_elements.append(end_label_element)

    else:
        raise ColangSyntaxError(f"Unknown element type '{type(element.spec)}'")

    return new_elements


def _expand_await_element(
    element: SpecOp,
) -> List[ElementType]:
    new_elements: List[ElementType] = []
    if isinstance(element.spec, Spec):
        # Single element
        if (
            element.spec.spec_type == SpecType.FLOW
            or element.spec.spec_type == SpecType.ACTION
        ) and element.spec.members is None:
            # It's a flow or an UMIM action
            element_ref = element.spec.ref
            if element_ref is None:
                element_ref = _create_ref_ast_dict_helper(f"_ref_{new_var_uid()}")

            element.spec.ref = element_ref
            new_elements.append(
                SpecOp(
                    op="start",
                    spec=element.spec,
                )
            )
            new_elements.append(
                SpecOp(
                    op="match",
                    spec=Spec(
                        var_name=element_ref["elements"][0]["elements"][0].lstrip("$"),
                        members=_create_member_ast_dict_helper("Finished", {}),
                        spec_type=SpecType.REFERENCE,
                    ),
                    return_var_name=element.return_var_name,
                )
            )
        else:
            raise ColangSyntaxError(f"Unsupported spec type '{element.spec}'")
    else:
        # Element group
        normalized_group = normalize_element_groups(element.spec)

        fork_element = ForkHead()
        fork_head_uids: List(str) = []
        group_label_elements: List[Label] = []
        begin_scope_elements: List[BeginScope] = []
        end_scope_elements: List[EndScope] = []
        start_elements: List[List[SpecOp]] = []
        match_elements: List[List[Spec]] = []
        failure_label_name = f"failure_label_{new_var_uid()}"
        failure_label_element = Label(name=failure_label_name)
        end_label_name = f"end_label_{new_var_uid()}"
        goto_end_element = Goto(label=end_label_name)
        end_label_element = Label(name=end_label_name)

        for group_idx, and_group in enumerate(normalized_group["elements"]):
            group_label_name = f"group_{group_idx}_{new_var_uid()}"
            group_label_elements.append(Label(name=group_label_name))
            scope_name = f"scope_{group_idx}_{new_var_uid()}"
            begin_scope_elements.append(BeginScope(name=scope_name))
            end_scope_elements.append(EndScope(name=scope_name))
            fork_head_uids.append(new_var_uid())
            fork_element.head_uids.append(fork_head_uids[-1])
            fork_element.labels.append(group_label_name)
            start_elements.append([])
            match_elements.append([])
            for group_element in and_group["elements"]:
                reference_name = f"_ref_{new_var_uid()}"
                group_element_copy = copy.deepcopy(group_element)
                group_element_copy.ref = _create_ref_ast_dict_helper(reference_name)
                start_elements[-1].append(
                    SpecOp(
                        op="start",
                        spec=group_element_copy,
                    )
                )
                match_elements[-1].append(
                    Spec(
                        var_name=reference_name,
                        members=_create_member_ast_dict_helper("Finished", {}),
                        spec_type=SpecType.REFERENCE,
                    )
                )

        # Generate new element sequence
        if len(normalized_group["elements"]) == 1:
            # Single and-group
            and_group = normalized_group["elements"][0]
            for idx, _ in enumerate(and_group["elements"]):
                new_elements.append(start_elements[0][idx])
            match_group = {"_type": "spec_and", "elements": match_elements[0]}
            new_elements.append(SpecOp(op="match", spec=match_group))
        else:
            # Multiple and-groups
            new_elements.append(CatchPatternFailure(label=failure_label_name))
            new_elements.append(fork_element)
            for group_idx, and_group in enumerate(normalized_group["elements"]):
                new_elements.append(group_label_elements[group_idx])
                new_elements.append(begin_scope_elements[group_idx])
                for idx, _ in enumerate(and_group["elements"]):
                    new_elements.append(start_elements[group_idx][idx])
                match_group = {
                    "_type": "spec_and",
                    "elements": match_elements[group_idx],
                }
                new_elements.append(SpecOp(op="match", spec=match_group))
                new_elements.append(goto_end_element)
            new_elements.append(failure_label_element)
            new_elements.append(WaitForHeads(number=len(normalized_group["elements"])))
            new_elements.append(CatchPatternFailure(label=None))
            new_elements.append(Abort())
            new_elements.append(end_label_element)
            new_elements.append(MergeHeads(head_uids=fork_head_uids))
            new_elements.append(CatchPatternFailure(label=None))
            for group_idx, _ in enumerate(normalized_group["elements"]):
                new_elements.append(end_scope_elements[group_idx])

    return new_elements


def _expand_activate_element(
    element: SpecOp,
) -> List[ElementType]:
    new_elements: List[ElementType] = []
    if isinstance(element.spec, Spec):
        # Single match element
        if element.spec.spec_type == SpecType.FLOW and element.spec.members is None:
            # It's a flow
            element.spec.arguments.update(
                {
                    "flow_id": f"'{element.spec.name}'",
                    "flow_start_uid": f"'{new_var_uid()}'",
                    "activated": "True",
                }
            )
            new_elements.append(
                SpecOp(
                    op="send",
                    spec=Spec(
                        name=InternalEvents.START_FLOW,
                        arguments=element.spec.arguments,
                        spec_type=SpecType.EVENT,
                    ),
                )
            )
            new_elements.append(
                SpecOp(
                    op="match",
                    spec=Spec(
                        name=InternalEvents.FLOW_STARTED,
                        arguments=element.spec.arguments,
                        spec_type=SpecType.EVENT,
                    ),
                    info={"internal": True},
                )
            )
        else:
            # It's an UMIM event
            raise ColangSyntaxError(
                f"Only flows can be activated but not '{element.spec.spec_type}'!"
            )
    elif isinstance(element.spec, dict):
        # Multiple match elements
        normalized_group = normalize_element_groups(element.spec)
        if len(normalized_group["elements"]) > 1:
            raise NotImplementedError("Activating 'or' groups not implemented yet!")
        for group_element in normalized_group["elements"][0]["elements"]:
            new_elements.append(
                SpecOp(
                    op="activate",
                    spec=group_element,
                )
            )

    return new_elements


def _expand_while_stmt_element(
    element: While, flow_configs: Dict[str, FlowConfig]
) -> List[ElementType]:
    new_elements: List[ElementType] = []

    label_uid = new_var_uid()
    begin_label = Label(name=f"_while_begin_{label_uid}")
    end_label = Label(name=f"_while_end_{label_uid}")
    goto_end = Goto(
        label=end_label.name,
        expression=f"not ({element.expression})",
    )
    goto_begin = Goto(
        label=begin_label.name,
        expression="True",
    )
    body_elements = expand_elements(
        element.elements, flow_configs, [begin_label.name, end_label.name]
    )

    new_elements = [begin_label, goto_end]
    new_elements.extend(body_elements)
    new_elements.extend([goto_begin, end_label])

    return new_elements


def _expand_if_element(
    element: If, flow_configs: Dict[str, FlowConfig]
) -> List[ElementType]:
    elements: List[ElementType] = []

    if_else_body_label_name = f"if_else_body_label_{new_var_uid()}"
    if_end_label_name = f"if_end_label_{new_var_uid()}"

    # TODO: optimize for cases when the else section is missing
    elements.append(
        Goto(
            expression=f"not({element.expression})",
            label=if_end_label_name
            if not element.else_elements
            else if_else_body_label_name,
        )
    )
    elements.extend(expand_elements(element.then_elements, flow_configs))

    if element.else_elements:
        elements.append(Goto(label=if_end_label_name))
        elements.append(Label(name=if_else_body_label_name))
        elements.extend(expand_elements(element.else_elements, flow_configs))

    elements.append(Label(name=if_end_label_name))

    return elements


def _expand_when_stmt_element(
    element: When, flow_configs: Dict[str, FlowConfig]
) -> List[ElementType]:
    stmt_uid = new_var_uid()

    init_case_label_names: List[str] = []
    cases_fork_head_element = ForkHead()
    cases_fork_head_uids: List[str] = []
    groups_fork_head_elements: List[ForkHead] = []
    failure_case_label_names: List[str] = []
    scope_label_names: List[List[str]] = []
    group_label_names: List[List[str]] = []
    group_start_elements: List[List[List[Spec]]] = []
    group_match_elements: List[List[List[Spec]]] = []
    case_label_names: List[str] = []
    else_label_name = f"when_else_label_{stmt_uid}"
    else_statement_label_name = f"when_else_statement_label_{stmt_uid}"
    end_label_name = f"when_end_label_{stmt_uid}"

    for case_idx, case_element in enumerate(element.when_specs):
        case_uid = str(chr(ord("a") + case_idx))
        init_case_label_names.append(f"init_case_{case_uid}_label_{stmt_uid}")
        cases_fork_head_uids.append(new_var_uid())
        cases_fork_head_element.head_uids.append(cases_fork_head_uids[-1])
        cases_fork_head_element.labels.append(init_case_label_names[case_idx])
        failure_case_label_names.append(f"failure_case_{case_uid}_label_{stmt_uid}")
        case_label_names.append(f"case_{case_uid}_label_{stmt_uid}")
        groups_fork_head_elements.append(ForkHead())

        if isinstance(case_element, Spec):
            # Single element
            case_element = {
                "_type": "spec_and",
                "elements": [case_element],
            }

        normalized_group = normalize_element_groups(case_element)

        group_label_names.append([])
        scope_label_names.append([])
        group_start_elements.append([])
        group_match_elements.append([])
        for group_idx, and_group in enumerate(normalized_group["elements"]):
            group_label_names[case_idx].append(
                f"group_{case_uid}_{group_idx}_label_{stmt_uid}"
            )
            scope_label_names[case_idx].append(
                f"scope_{case_uid}_{group_idx}_label_{stmt_uid}"
            )
            groups_fork_head_elements[case_idx].labels.append(
                group_label_names[case_idx][group_idx]
            )

            group_start_elements[case_idx].append([])
            group_match_elements[case_idx].append([])
            for group_element in and_group["elements"]:
                match_element = copy.deepcopy(group_element)

                ref_uid = None
                if (
                    group_element.spec_type == SpecType.FLOW
                    or group_element.spec_type == SpecType.ACTION
                ) and group_element.members is None:
                    # Add start element
                    ref_uid = f"_ref_{new_var_uid()}"
                    if group_element.ref is None:
                        group_element.ref = _create_ref_ast_dict_helper(ref_uid)
                    else:
                        ref_uid = group_element.ref["elements"][0]["elements"][0]
                    group_start_elements[case_idx][group_idx].append(group_element)

                # Add match element
                if ref_uid:
                    match_element.name = None
                    match_element.var_name = ref_uid
                    match_element.members = _create_member_ast_dict_helper(
                        "Finished", {}
                    )
                    match_element.spec_type = SpecType.REFERENCE
                group_match_elements[case_idx][group_idx].append(match_element)

    new_elements: List[ElementType] = []
    new_elements.append(cases_fork_head_element)
    for case_idx, case_element in enumerate(element.when_specs):
        # Case init groups
        new_elements.append(Label(name=init_case_label_names[case_idx]))
        new_elements.append(
            CatchPatternFailure(label=failure_case_label_names[case_idx])
        )
        new_elements.append(groups_fork_head_elements[case_idx])

        # And-group element groups
        for group_idx, group_label_name in enumerate(group_label_names[case_idx]):
            new_elements.append(Label(name=group_label_name))
            new_elements.append(BeginScope(name=scope_label_names[case_idx][group_idx]))

            if group_start_elements[case_idx][group_idx]:
                new_elements.append(
                    SpecOp(
                        op="start",
                        spec={
                            "_type": "spec_and",
                            "elements": group_start_elements[case_idx][group_idx],
                        },
                    )
                )
            new_elements.append(
                SpecOp(
                    op="match",
                    spec={
                        "_type": "spec_and",
                        "elements": group_match_elements[case_idx][group_idx],
                    },
                )
            )
            new_elements.append(Goto(label=case_label_names[case_idx]))

            # Case groups
            new_elements.append(Label(name=case_label_names[case_idx]))
            new_elements.append(MergeHeads(head_uids=cases_fork_head_uids))
            new_elements.append(CatchPatternFailure(label=None))
            for scope_labels in scope_label_names:
                for scope_label in scope_labels:
                    new_elements.append(EndScope(name=scope_label))
            new_elements.extend(
                expand_elements(element.then_elements[case_idx], flow_configs)
            )
            new_elements.append(Goto(label=end_label_name))

            # Failure case groups
            new_elements.append(Label(name=failure_case_label_names[case_idx]))
            new_elements.append(WaitForHeads(number=len(group_label_names[case_idx])))
            new_elements.append(CatchPatternFailure(label=None))
            new_elements.append(Goto(label=else_label_name))

        # Else group
        new_elements.append(Label(name=else_label_name))
        new_elements.append(WaitForHeads(number=len(group_label_names)))
        if element.else_elements is None:
            new_elements.append(Abort())
        else:
            new_elements.append(Goto(label=else_statement_label_name))

            new_elements.append(Label(name=else_statement_label_name))
            new_elements.extend(expand_elements(element.else_elements, flow_configs))

        # End label
        new_elements.append(Label(name=end_label_name))

    return new_elements


def _expand_when_stmt_element_old(
    element: When, flow_configs: Dict[str, FlowConfig]
) -> List[ElementType]:
    start_elements: List[SpecOp] = []
    fork_head_element = ForkHead()
    when_group_labels: List[str] = []
    when_elements: List[SpecOp] = []
    end_label_name = f"when_end_label_{new_var_uid()}"
    goto_end_label = Goto(label=end_label_name)
    end_label = Label(name=end_label_name)

    for idx, when_element in enumerate(element.when_specs):
        when_group_label_name = f"when_group_{idx}_label_{new_var_uid()}"
        fork_head_element.labels.append(when_group_label_name)
        when_group_labels.append(Label(name=when_group_label_name))
        if isinstance(when_element, Spec):
            # Single element
            if when_element.spec_type == SpecType.FLOW:
                # It's a flow
                flow_ref_uid = f"_flow_ref_{new_var_uid()}"
                when_element.ref = _create_ref_ast_dict_helper(flow_ref_uid)
                start_elements.append(
                    SpecOp(
                        op="start",
                        spec=when_element,
                    )
                )
                when_elements.append(
                    SpecOp(
                        op="match",
                        spec=Spec(
                            var_name=flow_ref_uid,
                            members=_create_member_ast_dict_helper("Finished", {}),
                            spec_type=SpecType.REFERENCE,
                        ),
                    )
                )
            elif (
                when_element.spec_type == SpecType.ACTION
                and when_element.members is None
            ):
                # It's an UMIM action
                action_ref_uid = f"_action_ref_{new_var_uid()}"
                when_element.ref = _create_ref_ast_dict_helper(action_ref_uid)
                start_elements.append(
                    SpecOp(
                        op="start",
                        spec=when_element,
                    )
                )
                when_elements.append(
                    SpecOp(
                        op="match",
                        spec=Spec(
                            var_name=action_ref_uid,
                            members=_create_member_ast_dict_helper("Finished", {}),
                            spec_type=SpecType.REFERENCE,
                        ),
                    )
                )
            elif (
                (
                    when_element.spec_type == SpecType.ACTION
                    or when_element.spec_type == SpecType.ACTION
                )
                and when_element.members is not None
                or (
                    when_element.spec_type == SpecType.EVENT
                    and when_element.members is None
                )
            ):
                # It's an UMIM event
                when_elements.append(
                    SpecOp(
                        op="match",
                        spec=when_element,
                    )
                )
            else:
                raise ColangSyntaxError(f"Unsupported spec type '{element.spec}'")
        else:
            # Element group
            # TODO: Fix this such that action are also supported using references for flows and actions
            normalized_group = normalize_element_groups(when_element)
            unique_group = convert_to_single_and_element_group(normalized_group)
            for and_group in unique_group["elements"]:
                for match_element in and_group["elements"]:
                    if match_element.spec_type == SpecType.FLOW:
                        # It's a flow
                        start_elements.append(
                            SpecOp(
                                op="start",
                                spec=match_element,
                            )
                        )
                    else:
                        # It's an UMIM action
                        pass
            when_elements.append(
                SpecOp(
                    op="match",
                    spec=when_element,
                )
            )

    new_elements: List[ElementType] = []
    new_elements.extend(start_elements)
    new_elements.append(fork_head_element)
    for idx, when_group_label in enumerate(when_group_labels):
        new_elements.append(when_group_label)
        new_elements.append(when_elements[idx])
        new_elements.append(MergeHeads())
        new_elements.extend(expand_elements(element.then_elements[idx], flow_configs))
        new_elements.append(goto_end_label)
    new_elements.append(end_label)

    return new_elements


def normalize_element_groups(group: Union[Spec, dict]) -> dict:
    """
    Normalize groups to the disjunctive normal form (DNF),
    resulting in a single or group that contains multiple and groups.
    """

    if isinstance(group, Spec):
        group = {"_type": "spec_and", "elements": [group]}

    if group["_type"] == "spec_or":
        return flatten_or_group(
            {
                "_type": "spec_or",
                "elements": [
                    normalize_element_groups(elem)
                    if isinstance(elem, dict)
                    else {"_type": "spec_and", "elements": [elem]}
                    for elem in group["elements"]
                ],
            }
        )
    elif group["_type"] == "spec_and":
        results = [{"_type": "spec_and", "elements": []}]
        for elem in group["elements"]:
            normalized = (
                normalize_element_groups(elem)
                if isinstance(elem, dict)
                else {
                    "_type": "spec_or",
                    "elements": [{"_type": "spec_and", "elements": [elem]}],
                }
            )

            # Distribute using the property: A and (B or C) = (A and B) or (A and C)
            new_results = []
            for res_elem in results:
                for norm_elem in normalized["elements"]:
                    new_elem = {
                        "_type": "spec_and",
                        "elements": res_elem["elements"] + norm_elem["elements"],
                    }
                    new_results.append(new_elem)
            results = new_results

        # Remove duplicate elements from groups
        # for idx, and_group in enumerate(results):
        #     results[idx] = uniquify_element_group(and_group)

        # TODO: Remove duplicated and groups
        return flatten_or_group({"_type": "spec_or", "elements": results})

    return {}


def flatten_or_group(group: dict):
    """Flattens a group that has multiple or levels to a single one."""
    new_elements = []
    for elem in group["elements"]:
        if isinstance(elem, dict) and elem["_type"] == "spec_or":
            new_elements.extend(elem["elements"])
        else:
            new_elements.append(elem)
    return {"_type": "spec_or", "elements": new_elements}


def uniquify_element_group(group: dict) -> dict:
    """Remove all duplicate elements from group."""
    unique_elements: Dict[Tuple[int, Spec]] = {}
    for element in group["elements"]:
        unique_elements.setdefault(element.hash(), element)
    new_group = group.copy()
    new_group["elements"] = [e for e in unique_elements.values()]
    return new_group


def convert_to_single_and_element_group(group: dict) -> dict:
    """Convert element group into a single 'and' group with unique elements."""
    unique_elements: Dict[Tuple[int, Spec]] = {}
    for and_group in group["elements"]:
        for element in and_group["elements"]:
            # Makes sure that we add the same element only once
            unique_elements.update({element.hash(): element})
    return {
        "_type": "spec_or",
        "elements": [
            {
                "_type": "spec_and",
                "elements": [elem for elem in unique_elements.values()],
            }
        ],
    }


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


def create_flow_instance(
    flow_config: FlowConfig, parent_uid: Optional[str] = None
) -> FlowState:
    loop_uid: Optional[str] = None
    if flow_config.loop_type == InteractionLoopType.NEW:
        loop_uid = new_uid()
    elif flow_config.loop_type == InteractionLoopType.NAMED:
        loop_uid = flow_config.loop_id
    # For type InteractionLoopType.PARENT we keep it None to infer loop_id at run_time from parent

    flow_uid = new_readable_uid(flow_config.id)

    head_uid = new_uid()
    flow_state = FlowState(
        uid=flow_uid,
        parent_uid=parent_uid,
        flow_id=flow_config.id,
        loop_id=loop_uid,
        heads={
            head_uid: FlowHead(
                uid=head_uid,
                position=0,
                flow_state_uid=flow_uid,
                matching_scores=[],
            )
        },
    )

    # Add all the flow parameters
    for idx, param in enumerate(flow_config.parameters):
        flow_state.arguments.append(param.name)
        flow_state.context.update(
            {
                param.name: eval_expression(param.default_value_expr, {}),
            }
        )
    # Add the positional flow parameter identifiers
    for idx, param in enumerate(flow_config.parameters):
        flow_state.arguments.append(f"${idx}")

    return flow_state


def add_new_flow_instance(state, flow_state: FlowState) -> FlowState:
    # Update state structures
    state.flow_states.update({flow_state.uid: flow_state})
    if flow_state.flow_id in state.flow_id_states:
        state.flow_id_states[flow_state.flow_id].append(flow_state)
    else:
        state.flow_id_states.update({flow_state.flow_id: [flow_state]})

    return flow_state


def _create_event_reference(
    state: State, flow_state: FlowState, element: Element, event: Event
) -> dict:
    reference_name = element.spec.ref["elements"][0]["elements"][0].lstrip("$")
    new_event = _get_event_from_element(state, flow_state, element)
    new_event.arguments.update(event.arguments)

    if isinstance(new_event, InternalEvent):
        flow_state_uid = event.arguments.get("source_flow_instance_uid", None)
        if flow_state_uid is not None:
            new_event.flow = state.flow_states[flow_state_uid]
    elif isinstance(new_event, ActionEvent):
        event = cast(ActionEvent, event)
        new_event.action_uid = event.action_uid
        if event.action_uid is not None:
            if event.action_uid not in state.actions:
                user_action = Action.from_event(event)
                assert user_action is not None
                state.actions.update({event.action_uid: user_action})
                new_event.action = user_action
            else:
                new_event.action = state.actions[event.action_uid]
    return {reference_name: new_event}


def _context_log(flow_state: FlowState) -> str:
    return str(
        [
            {key: value}
            for key, value in flow_state.context.items()
            if not isinstance(value, InternalEvent) and not isinstance(value, FlowState)
        ]
    )


def run_to_completion(state: State, external_event: Union[dict, Event]) -> None:
    """
    Computes the next state of the flow-driven system.
    """
    log.info(f"[bold violet]-> External Event[/]: {external_event}")

    if isinstance(external_event, dict):
        converted_external_event = ActionEvent.from_umim_event(external_event)
    elif isinstance(external_event, Event):
        converted_external_event = external_event

    # Initialize the new state
    state.internal_events = deque([converted_external_event])
    state.outgoing_events.clear()

    # Clear all matching scores
    for flow_state in state.flow_states.values():
        for head in flow_state.heads.values():
            head.matching_scores.clear()

    actionable_heads: List[FlowHead] = []

    heads_are_advancing = True
    while heads_are_advancing:
        while state.internal_events:
            event = state.internal_events.popleft()
            log.info(f"Process internal event: {event}")

            # We also record the flow finished events in the history
            if event.name == "FlowFinished":
                state.last_events.append({"type": event.name, **event.arguments})

            # Handle internal events that have no default matchers in flows yet
            # TODO: Let's see if we need this
            # if event.name == InternalEvents.START_SIBLING_FLOW:
            #     # Convert it into a normal START_FLOW event and only switch source flow instance to parent flow uid
            #     event.name = InternalEvents.START_FLOW
            #     parent_state_uid = state.flow_states[
            #         event.arguments["source_flow_instance_uid"]
            #     ].parent_uid
            #     event.arguments["source_flow_instance_uid"] = parent_state_uid
            if event.name == InternalEvents.FINISH_FLOW:
                if "flow_instance_uid" in event.arguments:
                    flow_state = state.flow_states[event.arguments["flow_instance_uid"]]
                    if not _is_inactive_flow(flow_state):
                        _finish_flow(
                            state,
                            flow_state,
                            event.matching_scores,
                        )
                elif "flow_id" in event.arguments:
                    for flow_state in state.flow_id_states[event.arguments["flow_id"]]:
                        if not _is_inactive_flow(flow_state):
                            _finish_flow(
                                state,
                                flow_state,
                                event.matching_scores,
                            )
            elif event.name == InternalEvents.STOP_FLOW:
                if "flow_instance_uid" in event.arguments:
                    flow_state = state.flow_states[event.arguments["flow_instance_uid"]]
                    if not _is_inactive_flow(flow_state):
                        _abort_flow(
                            state=state,
                            flow_state=flow_state,
                            matching_scores=event.matching_scores,
                            deactivate_flow=event.arguments.get("activated", False),
                        )
                elif "flow_id" in event.arguments:
                    for flow_state in state.flow_id_states[event.arguments["flow_id"]]:
                        if not _is_inactive_flow(flow_state):
                            _abort_flow(
                                state=state,
                                flow_state=flow_state,
                                matching_scores=event.matching_scores,
                                deactivate_flow=event.arguments.get("activated", False),
                            )
                # TODO: Add support for all flow instances of same flow with "flow_id"
            # elif event.name == "ResumeFlow":
            #     pass
            # elif event.name == "PauseFlow":
            #     pass

            # Find all heads of flows where event is relevant
            heads_matching: List[FlowHead] = []
            heads_not_matching: List[FlowHead] = []
            heads_failing: List[FlowHead] = []

            # TODO: Create a head dict for all active flows to speed this up
            # Iterate over all flow states to check for the heads to match the event
            for flow_state in state.flow_states.values():
                if not _is_listening_flow(flow_state):
                    continue

                for head in flow_state.active_heads.values():
                    element = _get_element_from_head(state, head)
                    if _is_match_op_element(element):
                        # TODO: Assign matching score
                        matching_score = _compute_event_matching_score(
                            state, flow_state, element, event
                        )

                        if matching_score > 0.0:
                            head.matching_scores = event.matching_scores.copy()
                            head.matching_scores.append(matching_score)

                            heads_matching.append(head)
                            log.info(
                                f"Matching head: {head} context={_context_log(flow_state)}"
                            )
                        elif matching_score < 0.0:
                            heads_failing.append(head)
                            log.info(
                                f"Matching head failed: {head} context={_context_log(flow_state)}"
                            )
                        else:
                            heads_not_matching.append(head)

            # Create internal events for unhandled events
            if (
                len(heads_matching) == 0
                and event.name != InternalEvents.UNHANDLED_EVENT
            ):
                arguments = event.arguments.copy()
                arguments.update({"event": event.name})
                internal_event = create_internal_event(
                    InternalEvents.UNHANDLED_EVENT, arguments, event.matching_scores
                )
                _push_internal_event(state, internal_event)

            # Sort matching heads to prioritize more specific matches over the others
            heads_matching = sorted(
                heads_matching, key=lambda x: x.matching_scores, reverse=True
            )

            # Handle internal event matching
            for head in heads_matching:
                element = _get_element_from_head(state, head)
                flow_state = _get_flow_state_from_head(state, head)

                # Create a potential reference form the match
                if element.spec.ref is not None:
                    flow_state.context.update(
                        _create_event_reference(state, flow_state, element, event)
                    )

                if (
                    event.name == InternalEvents.START_FLOW
                    and event.arguments["flow_id"]
                    == _get_flow_state_from_head(state, head).flow_id
                    and head.position == 0
                ):
                    _start_flow(state, flow_state, head, event.arguments)
                # elif event.name == InternalEvents.FINISH_FLOW:
                #     _finish_flow(new_state, flow_state)
                # TODO: Introduce default matching statements with heads for all flows
                # elif event.name == InternalEvents.ABORT_FLOW:
                #     _abort_flow(new_state, flow_state)
                # elif event.name == "ResumeFlow":
                #     pass
                # elif event.name == "PauseFlow":
                #     pass

            # Update actions status in all active flows by action event
            if isinstance(event, ActionEvent):
                _update_action_status_by_event(state, event)

            # Abort all flows with a mismatch
            for head in heads_failing:
                if head.catch_pattern_failure_label:
                    head.position = _get_flow_config_from_head(
                        state, head
                    ).element_labels[head.catch_pattern_failure_label]
                    heads_matching.append(head)
                else:
                    flow_state = _get_flow_state_from_head(state, head)
                    _abort_flow(state, flow_state, [])

            # Advance front of all matching heads to actionable or match statements
            for new_head in _advance_head_front(state, heads_matching):
                if new_head not in actionable_heads:
                    actionable_heads.append(new_head)

        # All internal events are processed and flow heads are on either action or match statements
        log.debug("All internal event processed -> advance actionable heads:")

        # Remove actionable heads for stopped or finished flows
        actionable_heads = [
            head
            for head in actionable_heads
            if _is_active_flow(_get_flow_state_from_head(state, head))
        ]

        # Check for potential conflicts between actionable heads
        advancing_heads: List[FlowHead] = []
        if len(actionable_heads) == 1:
            # If we have only one actionable head there is no conflict
            advancing_heads = actionable_heads
            _generate_action_event_from_actionable_element(
                state, list(actionable_heads)[0]
            )
        elif len(actionable_heads) > 1:
            # Group all actionable heads by their flows interaction loop
            head_groups: Dict[str, List[FlowHead]] = {}
            for head in actionable_heads:
                flow_state = _get_flow_state_from_head(state, head)
                if flow_state.loop_id in head_groups:
                    head_groups[flow_state.loop_id].append(head)
                else:
                    head_groups.update({flow_state.loop_id: [head]})

            for group in head_groups.values():
                max_length = max(len(head.matching_scores) for head in group)
                ordered_heads = sorted(
                    group,
                    key=lambda head: head.matching_scores
                    + [1.0] * (max_length - len(head.matching_scores)),
                    reverse=True,
                )
                # Check if we have heads with the exact same matching scores and pick one at random (or-group)
                equal_heads_index = next(
                    (
                        i
                        for i, h in enumerate(ordered_heads)
                        if h.matching_scores != ordered_heads[0].matching_scores
                    ),
                    len(ordered_heads),
                )
                picked_head = random.choice(ordered_heads[:equal_heads_index])
                winning_element = _get_flow_config_from_head(
                    state, picked_head
                ).elements[picked_head.position]
                flow_state = _get_flow_state_from_head(state, picked_head)
                winning_event: ActionEvent = _get_event_from_element(
                    state, flow_state, winning_element
                )
                log.info(
                    f"Winning action at head: {picked_head} scores={picked_head.matching_scores}"
                )

                advancing_heads.append(picked_head)
                _generate_action_event_from_actionable_element(state, picked_head)
                for head in ordered_heads:
                    if head == picked_head:
                        continue
                    competing_element = _get_flow_config_from_head(
                        state, head
                    ).elements[head.position]
                    competing_flow_state = _get_flow_state_from_head(state, head)
                    competing_event: ActionEvent = _get_event_from_element(
                        state, competing_flow_state, competing_element
                    )
                    if winning_event.is_equal(competing_event):
                        # All heads that are on the exact same action as the winning head
                        # need to replace their action references with the winning heads action reference
                        for (
                            key,
                            context_variable,
                        ) in competing_flow_state.context.items():
                            if (
                                isinstance(context_variable, Action)
                                and context_variable.uid == competing_event.action_uid
                            ):
                                competing_flow_state.context[key] = state.actions[
                                    winning_event.action_uid
                                ]
                        index = competing_flow_state.action_uids.index(
                            competing_event.action_uid
                        )
                        competing_flow_state.action_uids[
                            index
                        ] = winning_event.action_uid
                        state.actions.pop(competing_event.action_uid, None)

                        advancing_heads.append(head)
                        log.info(
                            f"Co-winning action at head: {head} scores={head.matching_scores}"
                        )
                    elif head.catch_pattern_failure_label:
                        # If a head defines a pattern failure catch label,
                        # it will forward the head to the label rather the aborting the flow
                        head.position = _get_flow_config_from_head(
                            state, head
                        ).element_labels[head.catch_pattern_failure_label]
                        advancing_heads.append(head)
                        log.info(
                            f"Caught loosing action head: {head} scores={head.matching_scores}"
                        )
                    else:
                        # Loosing heads will abort the flow
                        flow_state = _get_flow_state_from_head(state, head)
                        log.info(
                            f"Loosing action at head: {head} scores={head.matching_scores}"
                        )
                        _abort_flow(state, flow_state, head.matching_scores)

        heads_are_advancing = len(advancing_heads) > 0
        actionable_heads = _advance_head_front(state, advancing_heads)

    return state


def _advance_head_front(state: State, heads: List[FlowHead]) -> List[FlowHead]:
    """
    Advances all provided heads to the next blocking elements (actionable or matching) and returns all heads on
    actionable elements.
    """
    actionable_heads: List[FlowHead] = []
    for head in heads:
        log.debug(f"Advancing head: {head}")
        flow_state = _get_flow_state_from_head(state, head)
        flow_config = _get_flow_config_from_head(state, head)

        if flow_state.status == FlowStatus.WAITING:
            flow_state.status = FlowStatus.STARTING

        head.position += 1

        new_heads = slide(state, flow_state, flow_config, head)

        # Advance all new heads from a head fork
        if len(new_heads) > 0:
            for new_head in _advance_head_front(state, new_heads):
                if new_head not in actionable_heads:
                    actionable_heads.append(new_head)

        flow_finished = False
        flow_aborted = False
        if head.position >= len(flow_config.elements):
            if flow_state.status == FlowStatus.STOPPED:
                flow_aborted = True
            else:
                flow_finished = True

        # TODO: Use additional element to finish flow
        if flow_finished:
            log.debug(f"Flow finished: {head.flow_state_uid} with last element")
        elif flow_aborted:
            log.debug(f"Flow aborted: {head.flow_state_uid} by 'abort' statement")

        all_heads_at_real_match_elements = False
        if not flow_finished and not flow_aborted:
            # Check if all all flow heads at a match element
            all_heads_at_real_match_elements = True
            for temp_head in flow_state.active_heads.values():
                element = flow_config.elements[temp_head.position]
                if not _is_match_op_element(element) or "internal" in element.info:
                    all_heads_at_real_match_elements = False
                    break

        if flow_finished or all_heads_at_real_match_elements:
            if flow_state.status == FlowStatus.STARTING:
                flow_state.status = FlowStatus.STARTED
                event = create_internal_flow_event(
                    InternalEvents.FLOW_STARTED, flow_state, head.matching_scores
                )
                _push_internal_event(state, event)
        elif not flow_aborted and _is_action_op_element(
            flow_config.elements[head.position]
        ):
            actionable_heads.append(head)

        # Check if flow has finished or was aborted
        if flow_finished:
            flow_state.status = FlowStatus.FINISHING
            event = create_finish_flow_internal_event(
                flow_state.uid, flow_state.uid, head.matching_scores
            )
            _push_internal_event(state, event)
        elif flow_aborted:
            flow_state.status = FlowStatus.STOPPING
            event = create_stop_flow_internal_event(
                flow_state.uid,
                flow_state.uid,
                head.matching_scores,
            )
            _push_internal_event(state, event)

    # Make sure that all actionable heads still exist in flows, otherwise remove them
    actionable_heads = [
        head
        for head in actionable_heads
        if head in state.flow_states[head.flow_state_uid].active_heads.values()
    ]

    return actionable_heads


def slide(
    state: State, flow_state: FlowState, flow_config: FlowConfig, head: FlowHead
) -> Tuple[Deque[dict], List[FlowHead]]:
    """Tries to slide a flow with the provided head."""
    new_heads: List[FlowHead] = []

    # TODO: Implement global/local flow context handling
    # context = state.context
    # context = flow_state.context

    while True:
        # if we reached the end, we stop
        if head.position == len(flow_config.elements) or head.position < 0:
            break

        # prev_head = head.position
        element = flow_config.elements[head.position]
        log.debug(f"--Sliding element: '{element}'")

        if isinstance(element, SpecOp):
            if element.op == "send":
                event = _get_event_from_element(state, flow_state, element)

                if event.name not in InternalEvents.ALL:
                    break

                event_arguments = event.arguments
                event_arguments.update(
                    {
                        "source_flow_instance_uid": head.flow_state_uid,
                        "source_head_uid": head.uid,
                    }
                )
                new_event = create_internal_event(
                    event.name, event_arguments, head.matching_scores
                )
                _push_internal_event(state, new_event)
                head.position += 1

            elif element.op == "_new_action_instance":
                assert (
                    element.spec.spec_type != SpecType.FLOW
                ), "Flows cannot be instantiated!"

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
                for scope_uid in head.scope_uids:
                    flow_state.scopes[scope_uid][1].append(action.uid)
                reference_name = element.spec.ref["elements"][0]["elements"][0].lstrip(
                    "$"
                )
                flow_state.context.update({reference_name: action})
                head.position += 1
            else:
                # Not a sliding element
                break

        elif isinstance(element, Label):
            if element.name == "start_new_flow_instance":
                new_event = _create_restart_flow_internal_event(
                    state, flow_state, head.matching_scores
                )
                _push_left_internal_event(state, new_event)
                flow_state.new_instance_started = True
            head.position += 1

        elif isinstance(element, Goto):
            if eval_expression(element.expression, flow_state.context):
                if element.label in flow_config.element_labels:
                    head.position = flow_config.element_labels[element.label] + 1
                else:
                    # Still advance by one on invalid label
                    log.warning(f"Invalid label `{element.label}`.")
                    head.position += 1
            else:
                head.position += 1

        elif isinstance(element, ForkHead):
            # We deactivate current head (parent of new heads)
            head.active = False
            # We create the new child heads
            for idx, label in enumerate(element.labels):
                head_uid = (
                    element.head_uids[idx]
                    if len(element.head_uids) > idx
                    else new_uid()
                )
                pos = flow_config.element_labels[label]
                new_head = FlowHead(
                    uid=head_uid,
                    position=pos,
                    flow_state_uid=flow_state.uid,
                    matching_scores=head.matching_scores,
                    catch_pattern_failure_label=head.catch_pattern_failure_label,
                    scope_uids=head.scope_uids,
                )
                flow_state.heads[head_uid] = new_head
                head.child_head_uids.append(new_head.uid)
                new_heads.append(new_head)

            log.debug(f"Head forked: {element.labels}")

            break

        elif isinstance(element, MergeHeads):
            # Compose a list of all head uids and there children that should be merged
            # except for the current head that will continue
            head_uids: List[str] = []
            scope_uids: List[str] = []
            for uid in element.head_uids:
                head_uids.append(uid)
                # TODO: Make sure that child head uids are kept up-to-date
                if uid in flow_state.heads:
                    head_uids.extend(flow_state.heads[uid].get_child_head_uids(state))
                    # Merge scope uids from heads
                    scope_uids.extend(
                        [
                            scope_uid
                            for scope_uid in flow_state.heads[uid].scope_uids
                            if scope_uid not in scope_uids
                        ]
                    )

            head.scope_uids = scope_uids

            # Remove them from the flow
            for uid in head_uids:
                if uid != head.uid:
                    flow_state.heads.pop(uid, None)

            head.position += 1

        elif isinstance(element, WaitForHeads):
            # Check if enough heads are on this element to continue
            waiting_heads = [
                h
                for h in flow_state.active_heads.values()
                if h.position == head.position
            ]
            if len(waiting_heads) >= element.number:
                # Remove all waiting head except for the current
                for key in waiting_heads:
                    if key != head.uid:
                        flow_state.heads.pop(key, None)

                head.position += 1
            else:
                break

        elif isinstance(element, Assignment):
            # We need to first evaluate the expression
            expr_val = eval_expression(element.expression, flow_state.context)
            flow_state.context.update({element.key: expr_val})
            head.position += 1

        elif isinstance(element, Return):
            flow_state.context.update(
                {
                    "_return_value": eval_expression(
                        element.expression, flow_state.context
                    )
                }
            )
            head.position = len(flow_config.elements)

        elif isinstance(element, Abort):
            if head.catch_pattern_failure_label:
                head.catch_pattern_failure_label = element.label
                head.position += 1
            else:
                flow_state.status = FlowStatus.STOPPING
                new_event = create_stop_flow_internal_event(
                    flow_state.uid, flow_state.uid, head.matching_scores
                )
                _push_internal_event(state, new_event)
                head.position = len(flow_config.elements)

        elif isinstance(element, Continue) or isinstance(element, Break):
            if element.label is None:
                head.position += 1
            else:
                head.position = flow_config.element_labels[element.label] + 1

        elif isinstance(element, Priority):
            priority = eval_expression(element.priority_expr, flow_state.context)
            if not isinstance(priority, float) or priority < 0.0 or priority > 1.0:
                raise ColangValueError(
                    "priority must be a float number between 0.0 and 1.0!"
                )
            flow_state.priority = priority
            head.position += 1

        elif isinstance(element, CatchPatternFailure):
            head.catch_pattern_failure_label = element.label
            head.position += 1

        elif isinstance(element, BeginScope):
            if element.name in head.scope_uids:
                raise ColangRuntimeError(
                    f"Scope with name {element.name} already opened in this head!"
                )
            head.scope_uids.append(element.name)
            if element.name not in flow_state.scopes:
                flow_state.scopes.update({element.name: ([], [])})
            head.position += 1

        elif isinstance(element, EndScope):
            if element.name not in flow_state.scopes:
                raise ColangRuntimeError(
                    f"Scope with name {element.name} does not exist!"
                )
            # Remove scope and stop all started flows/actions in scope
            flow_uids, action_uids = flow_state.scopes.pop(element.name)
            for flow_uid in flow_uids:
                child_flow_state = state.flow_states[flow_uid]
                if _is_listening_flow(child_flow_state):
                    child_flow_state.status = FlowStatus.STOPPING
                    event = create_stop_flow_internal_event(
                        child_flow_state.uid,
                        flow_state.uid,
                        head.matching_scores,
                        True,
                    )
                    _push_internal_event(state, event)
            for action_uid in action_uids:
                action = state.actions[action_uid]
                if (
                    action.status == ActionStatus.STARTING
                    or action.status == ActionStatus.STARTED
                ):
                    event = action.stop_event({})
                    action.status = ActionStatus.STOPPING
                    _generate_action_event(state, event)

            # Remove scope from all heads
            for h in flow_state.heads.values():
                if element.name in h.scope_uids:
                    h.scope_uids.remove(element.name)

            head.position += 1

        else:
            # Ignore unknown element
            head.position += 1

    # If we got this far, it means we had a match and the flow advanced
    return new_heads


def _start_flow(
    state: State, flow_state: FlowState, head: FlowHead, arguments: dict
) -> None:
    flow_config = state.flow_configs[flow_state.flow_id]

    if flow_state.uid != state.main_flow_state.uid:
        # Link to parent flow
        parent_flow_uid = arguments["source_flow_instance_uid"]
        parent_flow = state.flow_states[parent_flow_uid]
        flow_state.parent_uid = parent_flow_uid
        parent_flow.child_flow_uids.append(flow_state.uid)
        # Add to parent scopes
        if "source_head_uid" in arguments:
            for scope_uid in parent_flow.heads[arguments["source_head_uid"]].scope_uids:
                if scope_uid in parent_flow.scopes:
                    parent_flow.scopes[scope_uid][0].append(flow_state.uid)

        loop_id = state.flow_configs[flow_state.flow_id].loop_id
        if loop_id is not None:
            if loop_id == "NEW":
                flow_state.loop_id = new_uid()
            else:
                flow_state.loop_id = loop_id
        else:
            flow_state.loop_id = parent_flow.loop_id
        flow_state.activated = arguments.get("activated", False)

        # Update context with event/flow parameters
        # TODO: Check if we really need all arguments int the context
        flow_state.context.update(arguments)
        # Resolve positional flow parameters to their actual name in the flow
        for idx in range(10):
            pos_arg = f"${idx}"
            if pos_arg in arguments:
                flow_state.context[flow_state.arguments[idx]] = arguments[pos_arg]
            else:
                break

    # Initialize new flow instance of flow
    add_new_flow_instance(state, create_flow_instance(flow_config))


def _abort_flow(
    state: State,
    flow_state: FlowState,
    matching_scores: List[float],
    deactivate_flow: bool = False,
) -> None:
    """Aborts a flow instance and all its active child flows."""

    # abort all running child flows
    for child_flow_uid in flow_state.child_flow_uids:
        child_flow_state = state.flow_states[child_flow_uid]
        if _is_listening_flow(child_flow_state):
            child_flow_state.status = FlowStatus.STOPPING
            event = create_stop_flow_internal_event(
                child_flow_state.uid, flow_state.uid, matching_scores
            )
            _push_internal_event(state, event)

    # Abort all stared actions that have not finished yet
    for action_uid in flow_state.action_uids:
        action = state.actions[action_uid]
        if (
            action.status == ActionStatus.STARTING
            or action.status == ActionStatus.STARTED
        ):
            event = action.stop_event({})
            action.status = ActionStatus.STOPPING
            _generate_action_event(state, event)

    # Cleanup all head from flow
    flow_state.heads.clear()

    flow_state.status = FlowStatus.STOPPED

    # Generate FlowFailed event
    event = create_internal_flow_event(
        InternalEvents.FLOW_FAILED, flow_state, matching_scores
    )
    _push_internal_event(state, event)

    log.info(
        f"Flow aborted/failed: '{_get_flow_parent_hierarchy(state, flow_state.uid)}'"
    )

    if (
        not deactivate_flow
        and flow_state.activated
        and not flow_state.new_instance_started
    ):
        event = _create_restart_flow_internal_event(state, flow_state, matching_scores)
        _push_left_internal_event(state, event)
        flow_state.new_instance_started = True


def _finish_flow(
    state: State, flow_state: FlowState, matching_scores: List[float]
) -> None:
    """Finishes a flow instance and all its active child flows."""

    # Deactivate all activated child flows
    for child_flow_uid in flow_state.child_flow_uids:
        child_flow_state = state.flow_states[child_flow_uid]
        if child_flow_state.activated:
            child_flow_state.activated = False
            log.info(
                f"Flow deactivated: {_get_flow_parent_hierarchy(state, child_flow_state.uid)}"
            )

    # Abort all running child flows
    for child_flow_uid in flow_state.child_flow_uids:
        child_flow_state = state.flow_states[child_flow_uid]
        if _is_listening_flow(child_flow_state):
            child_flow_state.status = FlowStatus.STOPPING
            event = create_stop_flow_internal_event(
                child_flow_state.uid, flow_state.uid, matching_scores, True
            )
            _push_internal_event(state, event)

    # Abort all started actions that have not finished yet
    for action_uid in flow_state.action_uids:
        action = state.actions[action_uid]
        if (
            action.status == ActionStatus.STARTING
            or action.status == ActionStatus.STARTED
        ):
            event = action.stop_event({})
            action.status = ActionStatus.STOPPING
            _generate_action_event(state, event)

    # Cleanup all head from flow
    flow_state.heads.clear()

    flow_state.status = FlowStatus.FINISHED

    # Generate FlowFinished event
    event = create_internal_flow_event(
        InternalEvents.FLOW_FINISHED, flow_state, matching_scores
    )
    _push_internal_event(state, event)

    log.info(
        f"Flow finished: '{_get_flow_parent_hierarchy(state, flow_state.uid)}' context={_context_log(flow_state)}"
    )

    if flow_state.activated and not flow_state.new_instance_started:
        event = _create_restart_flow_internal_event(state, flow_state, matching_scores)
        _push_left_internal_event(state, event)
        flow_state.new_instance_started = True


def _update_action_status_by_event(state: State, event: ActionEvent) -> None:
    for flow_state in state.flow_states.values():
        if not _is_listening_flow(flow_state):
            # Don't process flows that are not active
            continue

        for action_uid in flow_state.action_uids:
            # TODO: Make sure that the state.action are deleted so we don't need this check
            if action_uid in state.actions:
                action = state.actions[action_uid]
                if action.status != ActionStatus.FINISHED:
                    action.process_event(event)


def _is_listening_flow(flow_state: FlowState) -> bool:
    return (
        flow_state.status == FlowStatus.WAITING
        or flow_state.status == FlowStatus.STARTED
        or flow_state.status == FlowStatus.STARTING
    )


def _is_active_flow(flow_state: FlowState) -> bool:
    return (
        flow_state.status == FlowStatus.STARTED
        or flow_state.status == FlowStatus.STARTING
    )


def _is_inactive_flow(flow_state: FlowState) -> bool:
    return (
        flow_state.status == FlowStatus.WAITING
        or flow_state.status == FlowStatus.STOPPED
        or flow_state.status == FlowStatus.FINISHED
    )


def _generate_action_event(state: State, event: ActionEvent) -> None:
    umim_event = create_umim_action_event(event, event.arguments)
    state.outgoing_events.append(umim_event)
    log.info(f"[bold violet]<- Action[/]: {event}")

    # Update the status of relevant actions by event
    _update_action_status_by_event(state, event)


def _push_internal_event(state: State, event: Event) -> None:
    state.internal_events.append(event)
    log.debug(f"Created internal event: {event}")


def _push_left_internal_event(state: State, event: dict) -> None:
    state.internal_events.appendleft(event)
    log.debug(f"Created internal event: {event}")


def _get_element_from_head(state: State, head: FlowHead) -> SpecOp:
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
        and element.spec.name not in InternalEvents.ALL
    )


def _evaluate_arguments(arguments: dict, context: dict) -> dict:
    return dict([(key, eval_expression(arguments[key], context)) for key in arguments])


def _is_match_op_element(element: SpecOp) -> bool:
    return isinstance(element, SpecOp) and element.op == "match"


def _get_flow_parent_hierarchy(state: State, flow_state_uid: int) -> str:
    if flow_state_uid not in state.flow_states:
        return ""
    flow_state = state.flow_states[flow_state_uid]
    return (
        _get_flow_parent_hierarchy(state, flow_state.parent_uid)
        + "/"
        + state.flow_configs[flow_state.flow_id].id
    )


def _compute_event_matching_score(
    state: State, flow_state: FlowState, element: SpecOp, event: Event
) -> float:
    """Checks if the given element matches the given event.

    Factors that determine the final score:
    - match event parameter specificity
    - flow priority [0.0-1.0]
    - definition order of flow

    Args:
    Returns:
        1.0: Exact match (all parameters match)
        < 1.0: Fuzzy match (some parameters are missing, but all the others match)
        0.0: No match
        -1.0: Event will fail the current match
    """

    assert _is_match_op_element(element), f"Element '{element}' is not a match element!"

    ref_event = _get_event_from_element(state, flow_state, element)
    if not isinstance(ref_event, type(event)):
        return 0.0

    # Compute matching score based on event argument matching
    match_score: float = 1.0
    if (
        event.name == InternalEvents.START_FLOW
        and ref_event.name == InternalEvents.START_FLOW
    ):
        match_score = _compute_arguments_dict_matching_score(
            event.arguments, ref_event.arguments
        )

        if "flow_id" not in ref_event.arguments:
            match_score *= 0.9
        else:
            match_score = float(
                ref_event.name == InternalEvents.START_FLOW
                and ref_event.arguments["flow_id"] == event.arguments["flow_id"]
            )
    elif event.name in InternalEvents.ALL and ref_event.name in InternalEvents.ALL:
        if (
            "flow_id" in ref_event.arguments
            and "flow_id" in event.arguments
            and ref_event.arguments["flow_id"] != event.arguments["flow_id"]
        ):
            return 0.0

        # TODO: Check if this is needed
        # if isinstance(event, FlowEvent) and event.flow is not None:
        #     event.arguments["flow_arguments"] = event.flow.context

        match_score = _compute_arguments_dict_matching_score(
            event.arguments, ref_event.arguments
        )

        # TODO: Generalize this with mismatch using the 'not' keyword
        if match_score > 0.0:
            if (
                (
                    ref_event.name == InternalEvents.FLOW_FINISHED
                    and event.name == InternalEvents.FLOW_FAILED
                )
                or (
                    ref_event.name == InternalEvents.FLOW_FAILED
                    and event.name == InternalEvents.FLOW_FINISHED
                )
                or (
                    ref_event.name == InternalEvents.FLOW_STARTED
                    and (
                        event.name == InternalEvents.FLOW_FINISHED
                        or event.name == InternalEvents.FLOW_FAILED
                    )
                )
            ):
                # Match failure
                return -1.0
            elif ref_event.name != event.name:
                # Match success
                return 0.0

    else:
        # Its an UMIM event
        if (ref_event.name != event.name) or (
            ref_event.action_uid is not None
            and ref_event.action_uid != event.action_uid
        ):
            return 0.0

        # TODO: Action event matches can also fail for certain events, e.g. match Started(), received Finished()

        if event.action_uid is not None and event.action_uid in state.actions:
            action_arguments = state.actions[event.action_uid].start_event_arguments
            event.arguments["action_arguments"] = action_arguments

        match_score = _compute_arguments_dict_matching_score(
            event.arguments, ref_event.arguments
        )

    # Take into account the priority of the flow
    match_score *= flow_state.priority

    return match_score


def find_all_active_event_matchers(state: State, event: Event) -> List[FlowHead]:
    event_matchers: List[FlowHead] = []
    for flow_state in state.flow_states.values():
        if not _is_listening_flow(flow_state):
            continue

        flow_config = state.flow_configs[flow_state.flow_id]

        for head in flow_state.active_heads.values():
            element = flow_config.elements[head.position]
            score = _compute_event_matching_score(
                state,
                flow_state,
                element,
                event,
            )
            if score > 0.0:
                event_matchers.append(head)

    return event_matchers


def _compute_arguments_dict_matching_score(args: dict, ref_args: dict) -> float:
    # TODO: Find a better way of passing arguments to distinguish the ones that count for matching
    argument_filter = ["return_value", "source_flow_instance_uid"]
    score = 1.0
    for key in args.keys():
        if key in argument_filter:
            continue
        elif key in ref_args:
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

        # Resolve variable and member attributes
        obj = flow_state.context[variable_name]
        member = None
        for member in element_spec.members[:-1]:
            if not hasattr(obj, member.name):
                raise ColangValueError(f"No attribute '{member.name}' in {obj}")
            obj = getattr(obj, member.name)
        if element_spec.members is not None:
            member = element_spec.members[-1]

        if isinstance(obj, Event):
            if element_spec.members is not None:
                raise ColangValueError("Events have no event attributes!")
            return obj
        elif isinstance(obj, Action) or isinstance(obj, FlowState):
            if element_spec.members is None:
                raise ColangValueError(f"Missing event attribute in {obj.name}")
            event_name = member["name"]
            event_arguments = member["arguments"]
            event_arguments = _evaluate_arguments(event_arguments, flow_state.context)
            event = obj.get_event(event_name, event_arguments)

            if isinstance(event, InternalEvent):
                event.flow = obj
            elif isinstance(event, ActionEvent):
                event.action_uid = obj.uid
                event.action = None

            return event
        else:
            raise ColangRuntimeError(f"Unsupported type '{type(obj)}'")

    elif element_spec.members is not None:
        # Case 2)
        if element_spec.spec_type == SpecType.FLOW:
            # Flow object
            flow_config = state.flow_configs[element_spec.name]
            temp_flow_state = create_flow_instance(flow_config)
            flow_event_name = element_spec.members[0]["name"]
            flow_event_arguments = element_spec.members[0]["arguments"]
            flow_event_arguments = _evaluate_arguments(
                flow_event_arguments, flow_state.context
            )
            flow_event: InternalEvent = temp_flow_state.get_event(
                flow_event_name, flow_event_arguments
            )
            if element["op"] == "match":
                # Delete flow reference from event since it is only a helper object
                flow_event.flow = None
            return flow_event
        elif element_spec.spec_type == SpecType.ACTION:
            # Action object
            action_arguments = _evaluate_arguments(
                element_spec.arguments, flow_state.context
            )
            action = Action(element_spec.name, action_arguments, flow_state.flow_id)
            # TODO: refactor the following repetition of code (see above)
            event_name = element_spec.members[0]["name"]
            event_arguments = element_spec.members[0]["arguments"]
            event_arguments = _evaluate_arguments(event_arguments, flow_state.context)
            action_event: ActionEvent = action.get_event(event_name, event_arguments)
            if element["op"] == "match":
                # Delete action_uid from event since the action is only a helper object
                action_event.action_uid = None
            return action_event
    else:
        # Case 1)
        if element_spec.name.islower() or element_spec.name in InternalEvents.ALL:
            # Flow event
            event_arguments = _evaluate_arguments(
                element_spec.arguments, flow_state.context
            )
            flow_event = InternalEvent(element_spec.name, event_arguments)
            return flow_event
        else:
            # Action event
            event_arguments = _evaluate_arguments(
                element_spec.arguments, flow_state.context
            )
            action_event = ActionEvent(element_spec.name, event_arguments)
            return action_event

    return None


def _generate_action_event_from_actionable_element(
    state: State,
    head: FlowHead,
) -> None:
    """Helper to create an outgoing event from the flow head element."""
    flow_state = _get_flow_state_from_head(state, head)
    element = _get_element_from_head(state, head)
    assert _is_action_op_element(
        element
    ), f"Cannot create an event from a non actionable flow element {element}!"

    if element.op == "send":
        event = _get_event_from_element(state, flow_state, element)
        _generate_action_event(state, event)

    # Extract the comment, if any
    # state.next_steps_comment = element.get("_source_mapping", {}).get("comment")


def _create_restart_flow_internal_event(
    state: State, flow_state: FlowState, matching_scores: List[float]
) -> InternalEvent:
    # TODO: Check if this creates unwanted side effects of arguments being passed and keeping their state
    arguments = dict([(arg, flow_state.context[arg]) for arg in flow_state.arguments])
    arguments.update(
        {
            "flow_id": flow_state.context["flow_id"],
            "source_flow_instance_uid": flow_state.context["source_flow_instance_uid"],
            "source_head_uid": flow_state.context["source_head_uid"],
            "activated": flow_state.context["activated"],
        }
    )
    return create_internal_event(InternalEvents.START_FLOW, arguments, matching_scores)


def create_finish_flow_internal_event(
    flow_instance_uid: str,
    source_flow_instance_uid: str,
    matching_scores: List[float],
) -> InternalEvent:
    """Returns 'FinishFlow' internal event"""
    arguments = {
        "flow_instance_uid": flow_instance_uid,
        "source_flow_instance_uid": source_flow_instance_uid,
    }
    return create_internal_event(
        InternalEvents.FINISH_FLOW,
        arguments,
        matching_scores,
    )


def create_stop_flow_internal_event(
    flow_instance_uid: str,
    source_flow_instance_uid: str,
    matching_scores: List[float],
    deactivate_flow: bool = False,
) -> InternalEvent:
    """Returns 'StopFlow' internal event"""
    arguments = {
        "flow_instance_uid": flow_instance_uid,
        "source_flow_instance_uid": source_flow_instance_uid,
    }
    if deactivate_flow:
        arguments["activate"] = False

    return create_internal_event(
        InternalEvents.STOP_FLOW,
        arguments,
        matching_scores,
    )


def create_internal_flow_event(
    event_name: str,
    source_flow_state: FlowState,
    matching_scores: List[float],
    arguments: Optional[dict] = None,
) -> InternalEvent:
    """Creates and returns a internal flow event"""
    if arguments is None:
        arguments = dict()
    arguments.update(
        {
            "source_flow_instance_uid": source_flow_state.uid,
            "flow_id": source_flow_state.flow_id,
            "return_value": source_flow_state.context.get("_return_value", None),
        }
    )
    if "flow_start_uid" in source_flow_state.context:
        arguments["flow_start_uid"] = source_flow_state.context["flow_start_uid"]
    for arg in source_flow_state.arguments:
        if arg in source_flow_state.context:
            arguments.update({arg: source_flow_state.context[arg]})
    return create_internal_event(
        event_name,
        arguments,
        matching_scores,
    )


def create_internal_event(
    event_name: str, event_args: dict, matching_scores: List[float]
) -> InternalEvent:
    """Returns an internal event for the provided event data"""
    event = InternalEvent(
        name=event_name,
        arguments=event_args,
        matching_scores=matching_scores,
    )
    return event


def create_umim_action_event(event: ActionEvent, event_args: dict) -> Dict[str, Any]:
    """Returns an outgoing UMIM event for the provided action data"""
    new_event_args = event_args.copy()
    new_event_args["source_uid"] = "NeMoGuardrails-Colang-1.1"
    if event.action_uid is not None:
        return new_event_dict(event.name, action_uid=event.action_uid, **new_event_args)
    else:
        return new_event_dict(event.name, **new_event_args)
