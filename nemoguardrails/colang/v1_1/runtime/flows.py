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
from collections import deque
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Callable, Deque, Dict, List, Optional, Set, Tuple, Union

from dataclasses_json import dataclass_json

from nemoguardrails.colang.v1_1.lang.colang_ast import (
    Element,
    FlowParamDef,
    ForkHead,
    Goto,
    Label,
    MergeHeads,
)
from nemoguardrails.colang.v1_1.lang.colang_ast import Set as Set_
from nemoguardrails.colang.v1_1.lang.colang_ast import Spec, SpecOp, WaitForHeads
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
Open points:
* Parser:
  * Assigning references inside e.g. event or action groups does not work yet
  * Does assignment work?
* Colanng flow control:
  * Discuss expansion to fork/merge/wait_for_heads keywords
  * what does 'when else' actually do?
  * We should probably introduce the missatching with e.g. 'not'
"""


@dataclass
class InternalEvents:
    """All internal event types."""

    START_FLOW = "StartFlow"
    FINISH_FLOW = "FinishFlow"
    ABORT_FLOW = "AbortFlow"
    FLOW_STARTED = "FlowStarted"
    FLOW_FINISHED = "FlowFinished"
    FLOW_FAILED = "FlowFailed"

    ALL = {
        START_FLOW,
        FINISH_FLOW,
        ABORT_FLOW,
        FLOW_STARTED,
        FLOW_FINISHED,
        FLOW_FAILED,
    }


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

    def is_equal(self, event: Event) -> bool:
        return self.name == event.name and self.arguments == event.arguments


@dataclass
class ActionEvent(Event):
    """The action event class."""

    # An event can belong to an action
    action_uid: Optional[str] = None

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
            "Start": "start",
            "Change": "change",
            "Stop": "stop",
            "Started": "started_event",
            "Updated": "updated_event",
            "Finished": "finished_event",
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
        assert name in self._event_name_map, f"Event '{name}' not available!"
        func = getattr(self, self._event_name_map[name])
        return func(arguments)

    # Action events to send
    def start(self, args: dict) -> ActionEvent:
        """Starts the action. Takes no arguments."""
        self.status = ActionStatus.STARTING
        return ActionEvent(
            name=f"Start{self.name}",
            arguments=self.start_event_arguments,
            action_uid=self.uid,
        )

    def change(self, args: dict) -> ActionEvent:
        """Changes a parameter of a started action."""
        return ActionEvent(
            name=f"Change{self.name}", arguments=args["arguments"], action_uid=self.uid
        )

    def stop(self, args: dict) -> ActionEvent:
        """Stops a started action. Takes no arguments."""
        self.status = ActionStatus.STOPPING
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

    def __hash__(self):
        return hash(self.uid)


class FlowStatus(Enum):
    """The status of a flow."""

    WAITING = "waiting"
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
    heads: List[FlowHead]

    # All actions that were instantiated since the beginning of the flow
    action_uids: List[str]

    # The current set of variables in the flow state.
    context: dict

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

    # The UID of the flows that interrupted this one
    # interrupted_by = None

    # The flow event name mapping
    _event_name_map: dict = field(init=False)

    def __post_init__(self) -> None:
        self._event_name_map = {
            "Start": "start",
            "Stop": "stop",
            "Pause": "pause",
            "Resume": "resume",
            "Started": "started_event",
            "Paused": "paused_event",
            "Resumed": "resumed_event",
            "Finished": "finished_event",
            "Failed": "failed_event",
        }

    def get_event(self, name: str, arguments: dict) -> Callable[[], FlowEvent]:
        """Returns the corresponding action event."""
        assert name in self._event_name_map, f"Event '{name}' not available!"
        func = getattr(self, self._event_name_map[name])
        return func(arguments)

    # Flow events to send
    def start(self, args: dict) -> FlowEvent:
        """Starts the flow. Takes no arguments."""
        return FlowEvent(InternalEvents.START_FLOW, {"flow_id": self.flow_id})

    def finish(self, args: dict) -> FlowEvent:
        """Finishes the flow. Takes no arguments."""
        return FlowEvent(InternalEvents.FINISH_FLOW, {"flow_id": self.flow_id})

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
        arguments["flow_arguments"] = dict(
            [(arg, self.context[arg]) for arg in self.arguments]
        )
        return FlowEvent(InternalEvents.FLOW_STARTED, arguments)

    def paused_event(self, args: dict) -> FlowEvent:
        """Returns the flow Pause event."""
        arguments = args.copy()
        arguments["flow_id"] = self.flow_id
        arguments["flow_arguments"] = dict(
            [(arg, self.context[arg]) for arg in self.arguments]
        )
        return FlowEvent("FlowPaused", arguments)

    def resumed_event(self, args: dict) -> FlowEvent:
        """Returns the flow Resumed event."""
        arguments = args.copy()
        arguments["flow_id"] = self.flow_id
        arguments["flow_arguments"] = dict(
            [(arg, self.context[arg]) for arg in self.arguments]
        )
        return FlowEvent("FlowResumed", arguments)

    def finished_event(self, args: dict) -> FlowEvent:
        """Returns the flow Finished event."""
        arguments = args.copy()
        arguments["flow_id"] = self.flow_id
        arguments["flow_arguments"] = dict(
            [(arg, self.context[arg]) for arg in self.arguments]
        )
        return FlowEvent(InternalEvents.FLOW_FINISHED, arguments)

    def failed_event(self, args: dict) -> FlowEvent:
        """Returns the flow Failed event."""
        arguments = args.copy()
        arguments["flow_id"] = self.flow_id
        arguments["flow_arguments"] = dict(
            [(arg, self.context[arg]) for arg in self.arguments]
        )
        return FlowEvent(InternalEvents.FLOW_FAILED, arguments)


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
            # Transform and resolve flow configuration element notation (actions, flows, ...)
            flow_config.elements = _expand_elements(
                flow_config.elements, self.flow_configs
            )

            # Extract all the label elements
            for idx, element in enumerate(flow_config.elements):
                if isinstance(element, Label):
                    flow_config.element_labels.update({element["name"]: idx})

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


def _expand_elements(
    elements: List[ElementType], flow_configs: Dict[str, FlowConfig]
) -> List[ElementType]:
    elements_changed = True
    while elements_changed:
        elements_changed = False
        new_elements: List[ElementType] = []
        for element in elements:
            expanded_elems: List[ElementType] = []
            if isinstance(element, SpecOp):
                expanded_elems = _expand_spec_op_element(element, flow_configs)
                if len(expanded_elems) > 0:
                    elements_changed = True
            elif element["_type"] == "while_stmt":
                expanded_elems = _expand_while_stmt_element(element, flow_configs)
            elif element["_type"] == "if_stmt":
                expanded_elems = _expand_if_stmt_element(element, flow_configs)
            elif element["_type"] == "when_stmt":
                expanded_elems = _expand_when_stmt_element(element, flow_configs)

            if len(expanded_elems) > 0:
                new_elements.extend(expanded_elems)
            else:
                new_elements.extend([element])

        elements = new_elements
    return elements


def _expand_spec_op_element(
    element: SpecOp, flow_configs: Dict[str, FlowConfig]
) -> List[ElementType]:
    new_elements: List[ElementType] = []
    if element.op == "await":
        if isinstance(element.spec, Spec):
            # Single element
            if element.spec.name in flow_configs:
                # It's a flow
                new_elements.append(
                    SpecOp(
                        op="start",
                        spec=element.spec,
                    )
                )
                new_elements.append(
                    SpecOp(
                        op="match",
                        spec=element.spec,
                    )
                )
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
                            members=_create_member_ast_dict_helper("Finished", {}),
                        ),
                    )
                )
        else:
            # Element group
            normalized_group = normalize_element_groups(element.spec)
            unique_group = convert_to_single_and_element_group(normalized_group)
            for and_group in unique_group["elements"]:
                for match_element in and_group["elements"]:
                    if match_element.name in flow_configs:
                        # It's a flow
                        new_elements.append(
                            SpecOp(
                                op="start",
                                spec=match_element,
                            )
                        )
                    else:
                        # It's an UMIM action
                        pass
            element.op = "match"
            new_elements.append(element)
    elif element.op == "start":
        if isinstance(element.spec, Spec):
            # Single element
            if element.spec.name in flow_configs:
                # It's a flow
                element.spec.arguments.update({"flow_id": f"'{element.spec.name}'"})
                new_elements.append(
                    SpecOp(
                        op="send",
                        spec=Spec(
                            name=InternalEvents.START_FLOW,
                            arguments=element.spec.arguments,
                        ),
                    )
                )
                new_elements.append(
                    SpecOp(
                        op="match",
                        spec=Spec(
                            name=InternalEvents.FLOW_STARTED,
                            arguments=element.spec.arguments,
                        ),
                    )
                )
            else:
                # It's an UMIM action
                element_ref = element.ref
                if element_ref is None:
                    action_ref_uid = f"_action_ref_{new_uid()}"
                    element_ref = _create_ref_ast_dict_helper(action_ref_uid)
                new_elements.append(
                    SpecOp(
                        op="_new_instance",
                        spec=element.spec,
                        ref=element_ref,
                    )
                )
                spec = element.spec
                spec.members = _create_member_ast_dict_helper("Start", {})
                spec.var_name = element_ref["elements"][0]["elements"][0].lstrip("$")
                new_elements.append(SpecOp(op="send", spec=spec))
        else:
            # Element group
            normalized_group = normalize_element_groups(element.spec)
            if len(normalized_group["elements"]) > 1:
                raise NotImplementedError("Starting 'or' groups not implemented yet!")
            for group_element in normalized_group["elements"][0]["elements"]:
                new_elements.append(
                    SpecOp(
                        op="start",
                        spec=group_element,
                    )
                )

    elif element.op == "match":
        if isinstance(element.spec, Spec):
            # Single match element
            if element.spec.name in flow_configs:
                # It's a flow
                arguments = {"flow_id": f"'{element.spec.name}'"}
                for arg in element.spec.arguments:
                    arguments.update({arg: element.spec.arguments[arg]})

                new_elements.append(
                    SpecOp(
                        op="match",
                        spec=Spec(
                            name=InternalEvents.FLOW_FINISHED,
                            arguments=arguments,
                        ),
                    )
                )
            else:
                # It's an UMIM event
                pass
        elif isinstance(element.spec, dict):
            # Multiple match elements
            normalized_group = normalize_element_groups(element.spec)

            fork_element = ForkHead()
            event_label_elements: List[Label] = []
            event_match_elements: List[SpecOp] = []
            goto_group_elements: List[Goto] = []
            group_label_elements: List[Label] = []
            wait_for_heads_elements: List[WaitForHeads] = []
            end_label_name = f"end_label_{new_uid()}"
            goto_end_element = Goto(label=end_label_name)
            end_label_element = Label(name=end_label_name)

            element_idx = 0
            for group_idx, and_group in enumerate(normalized_group["elements"]):
                group_label_name = f"group_{group_idx}_{new_uid()}"
                group_label_elements.append(Label(name=group_label_name))
                goto_group_elements.append(Goto(label=group_label_name))
                wait_for_heads_elements.append(
                    WaitForHeads(number=len(and_group["elements"]))
                )

                for match_element in and_group["elements"]:
                    label_name = f"event_{element_idx}_{new_uid()}"
                    event_label_elements.append(Label(name=label_name))
                    fork_element.labels.append(label_name)
                    if match_element.name in flow_configs:
                        # It's a flow
                        arguments = {"flow_id": f"'{match_element.name}'"}
                        for arg in match_element.arguments:
                            arguments.update({arg: match_element.arguments[arg]})

                        event_match_elements.append(
                            SpecOp(
                                op="match",
                                spec=Spec(
                                    name=InternalEvents.FLOW_FINISHED,
                                    arguments=arguments,
                                ),
                            )
                        )
                    else:
                        # It's an UMIM event
                        new_match_element = copy.copy(element)
                        new_match_element.spec = match_element
                        event_match_elements.append(new_match_element)
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
                new_elements.append(MergeHeads())
                new_elements.append(goto_end_element)
            new_elements.append(end_label_element)

        else:
            raise ValueError("Unknown element type")

    elif element.op == "activate":
        if isinstance(element.spec, Spec):
            # Single match element
            if element.spec.name in flow_configs:
                # It's a flow
                element.spec.arguments.update(
                    {
                        "flow_id": f"'{element.spec.name}'",
                        "activated": "True",
                    }
                )
                new_elements.append(
                    SpecOp(
                        op="send",
                        spec=Spec(
                            name=InternalEvents.START_FLOW,
                            arguments=element.spec.arguments,
                        ),
                    )
                )
                new_elements.append(
                    SpecOp(
                        op="match",
                        spec=Spec(
                            name=InternalEvents.FLOW_STARTED,
                            arguments=element.spec.arguments,
                        ),
                    )
                )
            else:
                # It's an UMIM event
                raise NotImplementedError("Events cannot be activated!")
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
    element: dict, flow_configs: Dict[str, FlowConfig]
) -> dict:
    label_uid = new_uid()
    begin_label = Label(name=f"_while_begin_{label_uid}")
    end_label = Label(name=f"_while_end_{label_uid}")
    goto_end = Goto(
        label=end_label.name,
        expression=f"({element['elements'][0]['elements'][0]}) == False",
    )
    goto_begin = Goto(
        label=begin_label.name,
        expression="True",
    )
    body_elements = _expand_elements(element["elements"][1]["elements"], flow_configs)

    new_elements = [begin_label, goto_end]
    new_elements.extend(body_elements)
    new_elements.extend([goto_begin, end_label])

    return new_elements


def _expand_if_stmt_element(
    element: dict, flow_configs: Dict[str, FlowConfig]
) -> List[ElementType]:
    raise NotImplementedError()
    return element


def _expand_when_stmt_element(
    element: dict, flow_configs: Dict[str, FlowConfig]
) -> List[ElementType]:
    raise NotImplementedError()
    return element


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
        for idx, and_group in enumerate(results):
            results[idx] = uniquify_element_group(and_group)

        # TODO: Remove duplicated and groups
        return flatten_or_group({"_type": "spec_or", "elements": results})


def flatten_or_group(group: dict):
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
        heads=[
            FlowHead(
                uid=new_uid(),
                position=0,
                flow_state_uid=flow_uid,
                matching_scores=[],
            )
        ],
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


def compute_next_state(state: State, external_event: Union[dict, Event]) -> State:
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
        for head in flow_state.heads:
            head.matching_scores.clear()

    actionable_heads: Set[FlowHead] = set()

    heads_are_advancing = True
    while heads_are_advancing:
        while new_state.internal_events:
            event = new_state.internal_events.popleft()
            logging.info(f"Process internal event: {event}")

            # Handle internal events that have no default matchers in flows yet
            if event.name == InternalEvents.FINISH_FLOW:
                if "flow_id" in event.arguments:
                    for flow_state in new_state.flow_id_states[
                        event.arguments["flow_id"]
                    ]:
                        if _is_active_flow(flow_state):
                            _finish_flow(new_state, flow_state, event.matching_scores)
                elif "flow_instance_uid" in event.arguments:
                    flow_state = new_state.flow_states[
                        event.arguments["flow_instance_uid"]
                    ]
                    if _is_active_flow(flow_state):
                        _finish_flow(new_state, flow_state, event.matching_scores)
            elif event.name == InternalEvents.ABORT_FLOW:
                if "flow_id" in event.arguments:
                    for flow_state in new_state.flow_id_states[
                        event.arguments["flow_id"]
                    ]:
                        if _is_active_flow(flow_state):
                            _abort_flow(new_state, flow_state, event.matching_scores)
                elif "flow_instance_uid" in event.arguments:
                    flow_state = new_state.flow_states[
                        event.arguments["flow_instance_uid"]
                    ]
                    if _is_active_flow(flow_state):
                        _abort_flow(new_state, flow_state, event.matching_scores)
                # TODO: Add support for all flow instances of same flow with "flow_id"
            # elif event.name == "ResumeFlow":
            #     pass
            # elif event.name == "PauseFlow":
            #     pass

            # Find all heads of flows where event is relevant
            heads_matching: List[FlowHead] = []
            heads_not_matching: List[FlowHead] = []
            heads_failing: List[FlowHead] = []
            match_order_score: float = 1.0

            # TODO: Create a head dict for all active flows to speed this up
            # Iterate over all flow states to check for the heads to match the event
            for flow_state in new_state.flow_states.values():
                if not _is_listening_flow(flow_state):
                    continue

                flow_config = new_state.flow_configs[flow_state.flow_id]
                for head in flow_state.heads:
                    element = flow_config.elements[head.position]
                    if _is_match_op_element(element):
                        # TODO: Assign matching score
                        matching_score = _compute_event_matching_score(
                            new_state, flow_state, element, event
                        )
                        # Make sure that we can always resolve conflicts, using the matching score
                        matching_score *= match_order_score
                        match_order_score *= 0.99
                        head.matching_scores = event.matching_scores.copy()
                        head.matching_scores.append(matching_score)

                        if matching_score > 0.0:
                            heads_matching.append(head)
                            logging.info(
                                f"Matching head (score: {matching_score}): {head}"
                            )

                            if element.ref is not None:
                                # Create event and the reference
                                # TODO: Encapsulate this section in a function
                                reference_name = element.ref["elements"][0]["elements"][
                                    0
                                ].lstrip("$")
                                new_event = _get_event_from_element(
                                    new_state, flow_state, element
                                )
                                flow_state.context.update({reference_name: new_event})

                        elif matching_score < 0.0:
                            heads_failing.append(head)
                            logging.info(
                                f"Matching failure head (score: {matching_score}): {head}"
                            )
                        else:
                            heads_not_matching.append(head)

            # Handle internal event matching
            for head in heads_matching:
                if event.name == InternalEvents.START_FLOW:
                    flow_state = _get_flow_state_from_head(new_state, head)
                    _start_flow(new_state, flow_state, event.arguments)
                # elif event.name == InternalEvents.FINISH_FLOW:
                #     _finish_flow(new_state, flow_state)
                # TODO: Introduce default matching statements with heads for all flows
                # elif event.name == InternalEvents.ABORT_FLOW:
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
            for head in heads_failing:
                flow_state = _get_flow_state_from_head(new_state, head)
                _abort_flow(new_state, flow_state, [])

            # Advance front of all matching heads to actionable or match statements
            actionable_heads = actionable_heads.union(
                _advance_head_front(new_state, heads_matching)
            )

        # All internal events are processed and flow heads are on either action or match statements

        # Check for potential conflicts between actionable heads
        advancing_heads = []
        if len(actionable_heads) == 1:
            # If we have only one actionable head there are no conflicts
            advancing_heads = actionable_heads
            _create_outgoing_event_from_actionable_element(
                new_state, list(actionable_heads)[0]
            )
        elif len(actionable_heads) > 1:
            # Group all actionable heads by their flows interaction loop
            head_groups: Dict[str, List[FlowHead]] = {}
            for head in actionable_heads:
                flow_state = _get_flow_state_from_head(new_state, head)
                if flow_state.loop_id in head_groups:
                    head_groups[flow_state.loop_id].append(head)
                else:
                    head_groups.update({flow_state.loop_id: [head]})

            # Find winning and loosing heads for each group
            for group in head_groups.values():
                ordered_heads = _sort_heads_from_matching_scores(group)
                winning_element = _get_flow_config_from_head(
                    new_state, ordered_heads[0]
                ).elements[ordered_heads[0].position]
                flow_state = _get_flow_state_from_head(new_state, ordered_heads[0])
                winning_event: ActionEvent = _get_event_from_element(
                    new_state, flow_state, winning_element
                )

                advancing_heads.append(ordered_heads[0])
                _create_outgoing_event_from_actionable_element(
                    new_state, ordered_heads[0]
                )
                for head in ordered_heads[1:]:
                    competing_element = _get_flow_config_from_head(
                        new_state, head
                    ).elements[head.position]
                    competing_flow_state = _get_flow_state_from_head(new_state, head)
                    competing_event: ActionEvent = _get_event_from_element(
                        new_state, competing_flow_state, competing_element
                    )
                    if winning_event.is_equal(competing_event):
                        # All heads that are on the exact same action as the winning head
                        # need to align their action references to the winning head
                        for context_variable in competing_flow_state.context.values():
                            if (
                                isinstance(context_variable, dict)
                                and "type" in context_variable
                                and context_variable["type"]
                                == ContextVariableType.ACTION_REFERENCE
                                and context_variable["value"]
                                == competing_event.action_uid
                            ):
                                context_variable["value"] = winning_event.action_uid

                        advancing_heads.append(head)
                    else:
                        flow_state = _get_flow_state_from_head(new_state, head)
                        logging.info(f"Conflicting action at head: {head}")
                        _abort_flow(new_state, flow_state, head.matching_scores)

        heads_are_advancing = len(advancing_heads) > 0
        actionable_heads = _advance_head_front(new_state, advancing_heads)

    # Update all external event related actions in all flows that were not updated yet
    for flow_state in new_state.flow_states.values():
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


def _advance_head_front(state: State, heads: List[FlowHead]) -> Set[FlowHead]:
    """
    Advances all provided heads to the next blocking elements (actionable or matching) and returns all heads on
    actionable elements.
    """
    actionable_heads: Set[FlowHead] = set()
    for head in heads:
        flow_state = _get_flow_state_from_head(state, head)
        flow_config = _get_flow_config_from_head(state, head)

        if flow_state.status == FlowStatus.WAITING:
            flow_state.status = FlowStatus.STARTING

        head.position += 1

        internal_events, new_heads = slide(state, flow_state, flow_config, head)
        state.internal_events.extend(internal_events)

        # Advance all new heads from a head fork
        if len(new_heads) > 0:
            actionable_heads = actionable_heads.union(
                _advance_head_front(state, new_heads)
            )

        flow_finished = head.position >= len(flow_config.elements)

        # TODO: Use additional element to finish flow
        if flow_finished:
            logging.info(f"Flow {head.flow_state_uid} finished with last element")
        else:
            logging.info(
                f"Head in flow {head.flow_state_uid} advanced to element: {flow_config.elements[head.position]}"
            )

        # Check if all all flow heads at a match element
        if not flow_finished:
            all_heads_at_match_elements = True
            for temp_head in flow_state.heads:
                if not _is_match_op_element(flow_config.elements[temp_head.position]):
                    all_heads_at_match_elements = False
                    break

        if flow_finished or all_heads_at_match_elements:
            if flow_state.status == FlowStatus.STARTING:
                flow_state.status = FlowStatus.STARTED
                event = create_flow_started_internal_event(
                    flow_state.uid, head.matching_scores
                )
                _push_internal_event(state, event)
        elif _is_action_op_element(flow_config.elements[head.position]):
            actionable_heads.add(head)

        # Check if flow has finished
        # TODO: Refactor to properly finish flow and all its child flows
        if flow_finished:
            _finish_flow(state, flow_state, head.matching_scores)

    return actionable_heads


# TODO: Implement support for more sliding operations
def slide(
    state: State, flow_state: FlowState, flow_config: FlowConfig, head: FlowHead
) -> Tuple[Deque[dict], List[FlowHead]]:
    """Tries to slide a flow with the provided head."""
    head_position = head.position

    internal_events: Deque[dict] = deque()
    new_heads: List[FlowHead] = []

    # TODO: Implement global/local flow context handling
    # context = state.context
    # context = flow_state.context

    while True:
        # if we reached the end, we stop
        if head_position == len(flow_config.elements) or head_position < 0:
            return internal_events, new_heads

        # prev_head = head_position
        element = flow_config.elements[head_position]
        logging.info(f"Sliding element: '{element}'")

        if isinstance(element, SpecOp):
            if element.op == "send" and element.spec.name in InternalEvents.ALL:
                # Evaluate expressions (eliminate all double quotes)
                event_arguments = _evaluate_arguments(
                    element.spec.arguments, flow_state.context
                )
                event_arguments.update(
                    {"source_flow_instance_uid": head.flow_state_uid}
                )
                event = create_internal_event(
                    element.spec.name, event_arguments, head.matching_scores
                )
                internal_events.append(event)
                logging.info(f"Created internal event: {event}")
                head_position += 1
            elif element.op == "_new_instance":
                if element.spec.name in state.flow_configs:
                    # It's a flow
                    raise NotImplementedError()
                    evaluated_arguments = _evaluate_arguments(
                        element.spec.arguments, flow_state.context
                    )
                    flow_config = state.flow_configs[element.spec.name]
                    new_flow_state = _create_flow_instance(flow_config, flow_state)
                    reference_name = element.ref["elements"][0]["elements"][0].lstrip(
                        "$"
                    )
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
                    reference_name = element.ref["elements"][0]["elements"][0].lstrip(
                        "$"
                    )
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
        elif isinstance(element, Label):
            head_position += 1
        elif isinstance(element, Goto):
            if eval_expression(element.expression, flow_state.context):
                if element.label in flow_config.element_labels:
                    head_position = flow_config.element_labels[element.label] + 1
            else:
                head_position += 1
        elif isinstance(element, ForkHead):
            # We create new heads for
            for idx, label in enumerate(element.labels):
                pos = flow_config.element_labels[label]
                if idx == 0:
                    head_position = pos
                else:
                    new_head = FlowHead(
                        new_uid(), pos, flow_state.uid, head.matching_scores
                    )
                    flow_state.heads.append(new_head)
                    new_heads.append(new_head)
        elif isinstance(element, MergeHeads):
            # Delete all heads from the flow except for the current on
            # TODO: Check if these heads are in no another list
            flow_state.heads = [head]
            head_position += 1
        elif isinstance(element, WaitForHeads):
            # Check if enough heads are on this element to continue
            waiting_heads = [h for h in flow_state.heads if h.position == head_position]
            if len(waiting_heads) >= element.number - 1:
                # TODO: Check if these heads are in no another list
                flow_state.heads = [head]
                head_position += 1
            else:
                break

        elif isinstance(element, Set_):
            # We need to first evaluate the expression
            expr_val = eval_expression(element.expression, flow_state.context)
            flow_state.context.update({element.key: expr_val})
            head_position += 1

        else:
            # Ignore unknown element
            head_position += 1

    # If we got this far, it means we had a match and the flow advanced
    head.position = head_position
    return internal_events, new_heads


def _start_flow(state: State, flow_state: FlowState, arguments: dict) -> None:
    flow_config = state.flow_configs[flow_state.flow_id]

    if flow_state.uid != state.main_flow_state.uid:
        # Link to parent flow
        parent_flow_uid = arguments["source_flow_instance_uid"]
        parent_flow = state.flow_states[parent_flow_uid]
        flow_state.parent_uid = parent_flow_uid
        parent_flow.child_flow_uids.append(flow_state.uid)

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
    _add_new_flow_instance(state, _create_flow_instance(flow_config))


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

    if flow_state.activated:
        _restart_flow(state, flow_state, matching_scores)
        logging.info(f"Activated flow '{flow_state.flow_id}' restart")


def _finish_flow(
    state: State, flow_state: FlowState, matching_scores: List[float]
) -> None:
    """Finishes a flow instance and all its active child flows."""
    if not _is_active_flow(flow_state):
        return

    # Generate FlowFinished event
    event = create_flow_finished_internal_event(flow_state, matching_scores)
    _push_internal_event(state, event)

    # Abort all running child flows
    for child_flow_uid in flow_state.child_flow_uids:
        child_flow_state = state.flow_states[child_flow_uid]
        if _is_listening_flow(child_flow_state):
            event = create_abort_flow_internal_event(
                child_flow_state.uid, flow_state.uid, matching_scores
            )
            _push_internal_event(state, event)

    flow_state.status = FlowStatus.COMPLETED

    logging.info(f"Flow '{flow_state.flow_id}' finished")

    if flow_state.activated:
        _restart_flow(state, flow_state, matching_scores)
        logging.info(f"Activated flow '{flow_state.flow_id}' restart")


def _restart_flow(
    state: State, flow_state: FlowState, matching_scores: List[float]
) -> None:
    # TODO: Check if this creates unwanted side effects of arguments being passed and keeping their state
    arguments = dict([(arg, flow_state.context[arg]) for arg in flow_state.arguments])
    arguments.update(
        {
            "flow_id": flow_state.context["flow_id"],
            "source_flow_instance_uid": flow_state.context["source_flow_instance_uid"],
            "activated": flow_state.context["activated"],
        }
    )
    event = create_internal_event(InternalEvents.START_FLOW, arguments, matching_scores)
    state.internal_events.append(event)

    logging.info(f"Created internal event: {event}")


def _is_listening_flow(flow_state: FlowState) -> bool:
    return (
        flow_state.status == FlowStatus.WAITING
        or flow_state.status == FlowStatus.ACTIVE
        or flow_state.status == FlowStatus.STARTED
        or flow_state.status == FlowStatus.STARTING
    )


def _is_active_flow(flow_state: FlowState) -> bool:
    return (
        flow_state.status == FlowStatus.ACTIVE
        or flow_state.status == FlowStatus.STARTED
        or flow_state.status == FlowStatus.STARTING
    )


def _push_internal_event(state: State, event: dict) -> None:
    state.internal_events.append(event)
    logging.info(f"Created internal event: {event}")


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


def _compute_event_matching_score(
    state: State, flow_state: FlowState, element: SpecOp, event: Event
) -> float:
    """Checks if the given element matches the given event.

    Args:
    Returns:
        1.0: Exact match (all parameters match)
        < 1.0: Fuzzy match (some parameters are missing, but all the others match)
        0.0: No match
        -1.0: Event will fail the current match
    """

    assert _is_match_op_element(element), f"Element '{element}' is not a match element!"

    ref_event = _get_event_from_element(state, flow_state, element)

    # Compute matching score based on event argument matching
    if event.name == InternalEvents.START_FLOW:
        for var in event.arguments:
            if (
                var in ref_event.arguments
                and event.arguments[var] != ref_event.arguments[var]
            ):
                return 0.0

        return float(
            ref_event.name == InternalEvents.START_FLOW
            and ref_event.arguments["flow_id"] == event.arguments["flow_id"]
        )
    elif event.name in InternalEvents.ALL and ref_event.name in InternalEvents.ALL:
        if (
            ref_event.arguments["flow_id"]
            == state.flow_states[event.arguments["source_flow_instance_uid"]].flow_id
        ):
            match_score = _compute_arguments_dict_matching_score(
                event.arguments, ref_event.arguments
            )
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
                elif ref_event.name == event.name:
                    # Match success
                    return match_score
        # No match
        return 0.0

    else:
        # Its an UMIM event
        if ref_event.name != event.name:
            return 0.0

        if (
            ref_event.action_uid is not None
            and ref_event.action_uid != event.action_uid
        ):
            return 0.0

        if event.action_uid is not None and event.action_uid in state.actions:
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
            action_event = ActionEvent(element_spec.name, event_arguments)
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
    element = _get_element_from_head(state, head)
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
    history: List[Union[dict, Event]], flow_configs: Dict[str, FlowConfig]
) -> List[dict]:
    """Computes the next step in a flow-driven system given a history of events."""
    state = State(context={}, flow_states={}, flow_configs=flow_configs)
    state.initialize()

    # First, we process the history and apply any alterations e.g. 'hide_prev_turn'
    processed_history = []
    for event in history:
        # First of all, we need to convert the input history to proper Event instances
        if isinstance(event, dict):
            event = Event.from_umim_event(event)

        # NOTE (schuellc): Why is this needed?
        if event.name == "hide_prev_turn":
            # we look up the last `UtteranceUserActionFinished` event and remove everything after
            end = len(processed_history) - 1
            while (
                end > 0 and processed_history[end].name != "UtteranceUserActionFinished"
            ):
                end -= 1

            assert processed_history[end].name == "UtteranceUserActionFinished"
            processed_history = processed_history[0:end]
        else:
            processed_history.append(event)

    for event in processed_history:
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
    if processed_history:
        last_event = processed_history[-1]
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
        InternalEvents.ABORT_FLOW,
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
        InternalEvents.FLOW_STARTED,
        {"source_flow_instance_uid": source_flow_instance_uid},
        matching_scores,
    )


def create_flow_finished_internal_event(
    source_flow_state: FlowState, matching_scores: List[float]
) -> Event:
    """Returns 'FlowFinished' internal event"""
    arguments = {"source_flow_instance_uid": source_flow_state.uid}
    for arg in source_flow_state.arguments:
        if arg in source_flow_state.context:
            arguments.update({arg: source_flow_state.context[arg]})
    return create_internal_event(
        InternalEvents.FLOW_FINISHED,
        arguments,
        matching_scores,
    )


def create_flow_failed_internal_event(
    source_flow_instance_uid: str, matching_scores: List[float]
) -> Event:
    """Returns 'FlowFailed' internal event"""
    return create_internal_event(
        InternalEvents.FLOW_FAILED,
        {"source_flow_instance_uid": source_flow_instance_uid},
        matching_scores,
    )


def create_internal_event(
    event_name: str, event_args: dict, matching_scores: List[float]
) -> Event:
    """Returns an internal event for the provided event data"""
    event = Event(event_name, event_args, matching_scores=matching_scores)
    return event


def create_umim_action_event(event: ActionEvent, event_args: dict) -> Dict[str, Any]:
    """Returns an outgoing UMIM event for the provided action data"""
    if event.action_uid is not None:
        return new_event_dict(event.name, action_uid=event.action_uid, **event_args)
    else:
        return new_event_dict(event.name, **event_args)
