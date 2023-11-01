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

import logging
import time
from collections import deque
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Callable, Deque, Dict, List, Optional, Tuple, Union

from dataclasses_json import dataclass_json

from nemoguardrails.colang.v1_1.lang.colang_ast import Element, FlowParamDef, SpecOp
from nemoguardrails.colang.v1_1.runtime.utils import new_readable_uid
from nemoguardrails.utils import new_uid

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
    # TODO: Check if we could convert them into just a internal list to track action/intents
    BOT_INTENT_LOG = "BotIntentLog"
    USER_INTENT_LOG = "UserIntentLog"
    BOT_ACTION_LOG = "BotActionLog"
    USER_ACTION_LOG = "UserActionLog"

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
        BOT_INTENT_LOG,
        USER_INTENT_LOG,
        BOT_ACTION_LOG,
        USER_ACTION_LOG,
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
    main_flow_state: Optional[FlowState] = None

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


class ColangSyntaxError(Exception):
    """Raises when there is invalid Colang syntax detected"""

    pass


class ColangValueError(Exception):
    """Raises when there is an invalid value detected in a Colang expression"""

    pass


class ColangRuntimeError(Exception):
    """Raises when there is a Colang related runtime exception."""

    pass
