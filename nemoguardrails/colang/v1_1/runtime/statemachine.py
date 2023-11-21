import copy
import logging
import random
import re
import time
from collections import deque
from typing import Any, Deque, Dict, List, Optional, Tuple, Union, cast

from nemoguardrails.colang.v1_1.lang.colang_ast import (
    Abort,
    Assignment,
    BeginScope,
    Break,
    CatchPatternFailure,
    Continue,
    Element,
    EndScope,
    ForkHead,
    Goto,
    Label,
    Log,
    MergeHeads,
    Priority,
    Return,
    Spec,
    SpecOp,
    SpecType,
    WaitForHeads,
)
from nemoguardrails.colang.v1_1.lang.expansion import expand_elements
from nemoguardrails.colang.v1_1.runtime.eval import eval_expression
from nemoguardrails.colang.v1_1.runtime.flows import (
    Action,
    ActionEvent,
    ActionStatus,
    ColangRuntimeError,
    ColangValueError,
    Event,
    FlowConfig,
    FlowHead,
    FlowHeadStatus,
    FlowState,
    FlowStatus,
    InteractionLoopType,
    InternalEvent,
    InternalEvents,
    State,
)
from nemoguardrails.colang.v1_1.runtime.utils import new_readable_uid
from nemoguardrails.utils import new_event_dict, new_uid

log = logging.getLogger(__name__)

random_seed = int(time.time())


def initialize_state(state) -> None:
    """
    Initialize the state to make it ready for the story start.
    """

    state.internal_events = deque()

    assert "main" in state.flow_configs, "No main flow found!"

    state.flow_states = dict()

    # TODO: Think about where to put this
    for flow_config in state.flow_configs.values():
        initialize_flow(state, flow_config)

    # Create main flow state first
    main_flow_config = state.flow_configs["main"]
    main_flow = add_new_flow_instance(state, create_flow_instance(main_flow_config))
    if main_flow_config.loop_id is None:
        main_flow.loop_id = new_readable_uid("main")
    else:
        main_flow.loop_id = main_flow_config.loop_id
    state.main_flow_state = main_flow

    # Create flow states for all other flows and start with head at position 0.
    for flow_config in state.flow_configs.values():
        if flow_config.id != "main":
            add_new_flow_instance(state, create_flow_instance(flow_config))


def initialize_flow(state: State, flow_config: FlowConfig) -> None:
    # Transform and resolve flow configuration element notation (actions, flows, ...)
    flow_config.elements = expand_elements(flow_config.elements, state.flow_configs)

    # Extract flow loop id if available
    if flow_config.source_code:
        match = re.search(r"#\W*meta:\W*loop_id\W*=\W*(\w*)", flow_config.source_code)
        if match:
            flow_config.loop_id = match.group(1)

    # Extract all the label elements
    for idx, element in enumerate(flow_config.elements):
        if isinstance(element, Label):
            flow_config.element_labels.update({element["name"]: idx})


def create_flow_instance(
    flow_config: FlowConfig, parent_uid: Optional[str] = None
) -> FlowState:
    loop_uid: Optional[str] = None
    if flow_config.loop_type == InteractionLoopType.NEW:
        loop_uid = new_uid()
    elif flow_config.loop_type == InteractionLoopType.NAMED:
        assert flow_config.loop_id is not None
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
    new_event = get_event_from_element(state, flow_state, element)
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
        if "Action" in external_event["type"]:
            converted_external_event = ActionEvent.from_umim_event(external_event)
        else:
            converted_external_event = Event.from_umim_event(external_event)
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
    merging_heads: List[FlowHead] = []

    heads_are_advancing = True
    heads_are_merging = True
    while heads_are_advancing:
        while heads_are_merging:
            while state.internal_events:
                event = state.internal_events.popleft()
                log.info(f"Process internal event: {event}")

                # Handle internal events that have no default matchers in flows yet
                handled_event_loops = set()
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
                        flow_instance_uid = event.arguments["flow_instance_uid"]
                        if flow_instance_uid in state.flow_states:
                            flow_state = state.flow_states[
                                event.arguments["flow_instance_uid"]
                            ]
                            if not _is_inactive_flow(flow_state):
                                _finish_flow(
                                    state,
                                    flow_state,
                                    event.matching_scores,
                                )
                                handled_event_loops.add(flow_state.loop_id)
                    elif "flow_id" in event.arguments:
                        flow_id = event.arguments["flow_id"]
                        if flow_id in state.flow_id_states:
                            for flow_state in state.flow_id_states[flow_id]:
                                if not _is_inactive_flow(flow_state):
                                    _finish_flow(
                                        state,
                                        flow_state,
                                        event.matching_scores,
                                    )
                                    handled_event_loops.add(flow_state.loop_id)
                elif event.name == InternalEvents.STOP_FLOW:
                    if "flow_instance_uid" in event.arguments:
                        flow_instance_uid = event.arguments["flow_instance_uid"]
                        if flow_instance_uid in state.flow_states:
                            flow_state = state.flow_states[flow_instance_uid]
                            if not _is_inactive_flow(flow_state):
                                _abort_flow(
                                    state=state,
                                    flow_state=flow_state,
                                    matching_scores=event.matching_scores,
                                    deactivate_flow=flow_state.activated,
                                )
                                handled_event_loops.add(flow_state.loop_id)
                    elif "flow_id" in event.arguments:
                        flow_id = event.arguments["flow_id"]
                        if flow_id in state.flow_id_states:
                            for flow_state in state.flow_id_states[flow_id]:
                                if not _is_inactive_flow(flow_state):
                                    _abort_flow(
                                        state=state,
                                        flow_state=flow_state,
                                        matching_scores=event.matching_scores,
                                        deactivate_flow=flow_state.activated,
                                    )
                                    handled_event_loops.add(flow_state.loop_id)
                    # TODO: Add support for all flow instances of same flow with "flow_id"
                # elif event.name == "ResumeFlow":
                #     pass
                # elif event.name == "PauseFlow":
                #     pass
                elif (
                    event.name == InternalEvents.BOT_INTENT_LOG
                    or event.name == InternalEvents.USER_INTENT_LOG
                    or event.name == InternalEvents.BOT_ACTION_LOG
                    or event.name == InternalEvents.USER_ACTION_LOG
                ):
                    # We also record the flow finished events in the history
                    state.last_events.append(event)
                    handled_event_loops.add("all_loops")

                # Find all heads of flows where event is relevant
                heads_matching: List[FlowHead] = []
                heads_not_matching: List[FlowHead] = []
                heads_failing: List[FlowHead] = []
                active_interaction_loops = set()

                # TODO: Create a head dict for all active flows to speed this up
                # Iterate over all flow states to check for the heads to match the event
                for flow_state in state.flow_states.values():
                    if not _is_listening_flow(flow_state):
                        continue

                    for head in flow_state.active_heads.values():
                        element = get_element_from_head(state, head)
                        if is_match_op_element(element):
                            if (
                                head.position == 0
                                and event.name != InternalEvents.START_FLOW
                            ):
                                # Optimization: Skip matching score computation
                                continue
                            else:
                                if flow_state.loop_id is not None:
                                    active_interaction_loops.add(flow_state.loop_id)

                            matching_score = _compute_event_matching_score(
                                state, flow_state, element, event
                            )

                            if matching_score > 0.0:
                                head.matching_scores = event.matching_scores.copy()
                                head.matching_scores.append(matching_score)

                                heads_matching.append(head)
                                if event.name == InternalEvents.START_FLOW:
                                    handled_event_loops.add("all_loops")
                                else:
                                    handled_event_loops.add(flow_state.loop_id)
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

                # Create internal events for unhandled events for every independent interaction loop
                unhandled_event_loops = active_interaction_loops - handled_event_loops
                if (
                    "all_loops" not in handled_event_loops
                    and len(unhandled_event_loops) > 0
                    and event.name != InternalEvents.UNHANDLED_EVENT
                ):
                    arguments = event.arguments.copy()
                    arguments.update(
                        {"event": event.name, "loop_ids": list(unhandled_event_loops)}
                    )
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
                    element = get_element_from_head(state, head)
                    flow_state = get_flow_state_from_head(state, head)

                    # Create a potential reference from the match
                    if element.spec.ref is not None:
                        flow_state.context.update(
                            _create_event_reference(state, flow_state, element, event)
                        )

                    if (
                        event.name == InternalEvents.START_FLOW
                        and event.arguments["flow_id"]
                        == get_flow_state_from_head(state, head).flow_id
                        and head.position == 0
                    ):
                        _start_flow(state, flow_state, head, event.arguments)
                    elif event.name == InternalEvents.FLOW_STARTED:
                        # Add started flow to active scopes
                        for scope_uid in head.scope_uids:
                            if scope_uid in flow_state.scopes:
                                flow_state.scopes[scope_uid][0].append(
                                    event.arguments["source_flow_instance_uid"]
                                )
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
                        head.position = get_flow_config_from_head(
                            state, head
                        ).element_labels[head.catch_pattern_failure_label[-1]]
                        heads_matching.append(head)
                    else:
                        flow_state = get_flow_state_from_head(state, head)
                        _abort_flow(state, flow_state, [])

                # Advance front of all matching heads to actionable or match statements
                for new_head in _advance_head_front(state, heads_matching):
                    if new_head not in actionable_heads:
                        actionable_heads.append(new_head)

            # Separate merging from actionable heads and remove inactive heads
            merging_heads = [
                head
                for head in actionable_heads
                if head.status == FlowHeadStatus.MERGING
            ]
            actionable_heads = [
                head
                for head in actionable_heads
                if head.status == FlowHeadStatus.ACTIVE
            ]

            # Advance all merging heads and create potential new internal events
            actionable_heads.extend(_advance_head_front(state, merging_heads))

            heads_are_merging = len(merging_heads) > 0

        # All internal events are processed and flow heads are on either action or match statements
        log.debug("All internal event processed -> advance actionable heads:")

        # Remove heads from stopped or finished flows
        actionable_heads = [
            head
            for head in actionable_heads
            if _is_active_flow(get_flow_state_from_head(state, head))
            and head.status == FlowHeadStatus.ACTIVE
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
                flow_state = get_flow_state_from_head(state, head)
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
                winning_element = get_flow_config_from_head(
                    state, picked_head
                ).elements[picked_head.position]
                flow_state = get_flow_state_from_head(state, picked_head)
                winning_event: ActionEvent = get_event_from_element(
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
                    competing_element = get_flow_config_from_head(state, head).elements[
                        head.position
                    ]
                    competing_flow_state = get_flow_state_from_head(state, head)
                    competing_event = get_event_from_element(
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
                        if isinstance(competing_event, ActionEvent):
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
                        head.position = get_flow_config_from_head(
                            state, head
                        ).element_labels[head.catch_pattern_failure_label[-1]]
                        advancing_heads.append(head)
                        log.info(
                            f"Caught loosing action head: {head} scores={head.matching_scores}"
                        )
                    else:
                        # Loosing heads will abort the flow
                        flow_state = get_flow_state_from_head(state, head)
                        log.info(
                            f"Loosing action at head: {head} scores={head.matching_scores}"
                        )
                        _abort_flow(state, flow_state, head.matching_scores)

        heads_are_advancing = len(advancing_heads) > 0
        actionable_heads = _advance_head_front(state, advancing_heads)
        heads_are_merging = True

    return state


def _advance_head_front(state: State, heads: List[FlowHead]) -> List[FlowHead]:
    """
    Advances all provided heads to the next blocking elements (actionable or matching) and returns all heads on
    actionable elements.
    """
    actionable_heads: List[FlowHead] = []
    for head in heads:
        log.debug(f"Advancing head: {head} flow_state_uid: {head.flow_state_uid}")
        flow_state = get_flow_state_from_head(state, head)
        flow_config = get_flow_config_from_head(state, head)

        if head.status == FlowHeadStatus.INACTIVE:
            continue
        elif head.status == FlowHeadStatus.MERGING and len(state.internal_events) > 0:
            # We only advance merging heads if all internal events were processed
            actionable_heads.append(head)
            continue
        elif head.status == FlowHeadStatus.ACTIVE:
            head.position += 1

        if flow_state.status == FlowStatus.WAITING:
            flow_state.status = FlowStatus.STARTING

        new_heads = slide(state, flow_state, flow_config, head)

        # Advance all new heads from a head fork
        if len(new_heads) > 0:
            for new_head in _advance_head_front(state, new_heads):
                if new_head not in actionable_heads:
                    actionable_heads.append(new_head)

        # Add merging heads to the actionable heads since they need to be advanced in the next iteration
        if head.status == FlowHeadStatus.MERGING:
            actionable_heads.append(head)

        flow_finished = False
        flow_aborted = False
        if head.position >= len(flow_config.elements):
            if flow_state.status == FlowStatus.STOPPING:
                flow_aborted = True
            else:
                flow_finished = True

        # TODO: Use additional element to finish flow
        if flow_finished:
            log.debug(f"Flow finished: {head.flow_state_uid} with last element")
        elif flow_aborted:
            log.debug(f"Flow aborted: {head.flow_state_uid} by 'abort' statement")

        all_heads_are_waiting = False
        if not flow_finished and not flow_aborted:
            # Check if all all flow heads are waiting at match or wait_for_heads statements
            all_heads_are_waiting = True
            for temp_head in flow_state.active_heads.values():
                element = flow_config.elements[temp_head.position]
                if not isinstance(element, WaitForHeads) and (
                    not is_match_op_element(element) or "internal" in element.info
                ):
                    all_heads_are_waiting = False
                    break

        if flow_finished or all_heads_are_waiting:
            if flow_state.status == FlowStatus.STARTING:
                flow_state.status = FlowStatus.STARTED
                event = create_internal_flow_event(
                    InternalEvents.FLOW_STARTED, flow_state, head.matching_scores
                )
                _push_internal_event(state, event)
        elif not flow_aborted and is_action_op_element(
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
) -> List[FlowHead]:
    """Tries to slide a flow with the provided head."""
    new_heads: List[FlowHead] = []

    # TODO: Implement global/local flow context handling
    # context = state.context
    # context = flow_state.context

    while True:
        # if we reached the end, we stop
        if (
            head.position >= len(flow_config.elements)
            or head.status == FlowHeadStatus.INACTIVE
        ):
            break

        element = flow_config.elements[head.position]
        log.debug(f"--Sliding element: '{element}'")

        if isinstance(element, SpecOp):
            if element.op == "send":
                event = get_event_from_element(state, flow_state, element)

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
            head.status = FlowHeadStatus.INACTIVE
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
            if head.status == FlowHeadStatus.ACTIVE:
                # Change status of head to allow for other forked heads to process before merging
                head.status = FlowHeadStatus.MERGING
                break
            elif head.status == FlowHeadStatus.MERGING:
                # Compose a list of all head uids and there children that should be merged
                head_uids: List[str] = []
                scope_uids: List[str] = []
                for uid in element.head_uids:
                    head_uids.append(uid)
                    # TODO: Make sure that child head uids are kept up-to-date to remove this check
                    if uid in flow_state.heads:
                        head_uids.extend(
                            flow_state.heads[uid].get_child_head_uids(state)
                        )
                        # Merge scope uids from heads
                        scope_uids.extend(
                            [
                                scope_uid
                                for scope_uid in flow_state.heads[uid].scope_uids
                                if scope_uid not in scope_uids
                            ]
                        )

                # Remove all head_uids that no longer exist in heads
                # TODO: Make sure this is not needed
                head_uids = [
                    head_uid for head_uid in head_uids if head_uid in flow_state.heads
                ]

                # Check that all of the other heads that are on a merging statements do also target the current head
                for head_uid in head_uids:
                    if head_uid != head.uid:
                        other_head = flow_state.heads[head_uid]
                        if other_head.status == FlowHeadStatus.MERGING:
                            merge_element = cast(
                                MergeHeads, flow_config.elements[other_head.position]
                            )
                            if head_uid not in merge_element.head_uids:
                                # If we still have heads that can be merged independently let's wait with this one
                                break

                # Now we are sure that all other related heads had the chance to process
                # Let's resolve competing heads and merge them with the winner

                # Extract all heads that arrived at a merge statement
                merging_heads = [
                    flow_state.heads[head_uid]
                    for head_uid in head_uids
                    if flow_state.heads[head_uid].status == FlowHeadStatus.MERGING
                ]

                picked_head = head
                if len(merging_heads) > 1:
                    # Order the heads in terms of matching scores
                    max_length = max(
                        len(head.matching_scores) for head in merging_heads
                    )
                    ordered_heads = sorted(
                        merging_heads,
                        key=lambda head: head.matching_scores
                        + [1.0] * (max_length - len(head.matching_scores)),
                        reverse=True,
                    )
                    # Check if we have heads with the exact same matching scores and pick one at random
                    equal_heads_index = next(
                        (
                            i
                            for i, h in enumerate(ordered_heads)
                            if h.matching_scores != ordered_heads[0].matching_scores
                        ),
                        len(ordered_heads),
                    )
                    picked_head = random.choice(ordered_heads[:equal_heads_index])

                # If the current had is not the winning head it will be merged
                if picked_head != head:
                    head.status = FlowHeadStatus.INACTIVE
                else:
                    head.status = FlowHeadStatus.ACTIVE
                    head.scope_uids = scope_uids

                    # Remove them from the flow
                    for uid in head_uids:
                        if uid != head.uid:
                            flow_state.heads[uid].status = FlowHeadStatus.INACTIVE
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
                head.position = (
                    flow_config.element_labels[head.catch_pattern_failure_label[-1]] + 1
                )
            else:
                flow_state.status = FlowStatus.STOPPING
                head.position = len(flow_config.elements)

        elif isinstance(element, Continue) or isinstance(element, Break):
            if element.label is None:
                head.position += 1
            else:
                head.position = flow_config.element_labels[element.label] + 1

        elif isinstance(element, Log):
            log.info(
                f"Colang debug info: {eval_expression(element.info,flow_state.context)}"
            )
            head.position += 1

        elif isinstance(element, Priority):
            priority = eval_expression(element.priority_expr, flow_state.context)
            if not isinstance(priority, float) or priority < 0.0 or priority > 1.0:
                raise ColangValueError(
                    "priority must be a float number between 0.0 and 1.0!"
                )
            flow_state.priority = priority
            head.position += 1

        elif isinstance(element, CatchPatternFailure):
            if element.label is None:
                head.catch_pattern_failure_label.pop(-1)
            else:
                head.catch_pattern_failure_label.append(element.label)
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
    state: State, flow_state: FlowState, head: FlowHead, event_arguments: dict
) -> None:
    flow_config = state.flow_configs[flow_state.flow_id]

    if state.main_flow_state is None or flow_state.uid != state.main_flow_state.uid:
        # Link to parent flow
        parent_flow_uid = event_arguments["source_flow_instance_uid"]
        parent_flow = state.flow_states[parent_flow_uid]
        flow_state.parent_uid = parent_flow_uid
        parent_flow.child_flow_uids.append(flow_state.uid)

        loop_id = state.flow_configs[flow_state.flow_id].loop_id
        if loop_id is not None:
            if loop_id == "NEW":
                flow_state.loop_id = new_uid()
            else:
                flow_state.loop_id = loop_id
        else:
            flow_state.loop_id = parent_flow.loop_id
        flow_state.context.update({"loop_id": flow_state.loop_id})
        flow_state.activated = event_arguments.get("activated", False)

        # Update context with event/flow parameters
        # TODO: Check if we really need all arguments int the context
        flow_state.context.update(event_arguments)
        # Resolve positional flow parameters to their actual name in the flow
        last_idx = -1
        for idx, arg in enumerate(flow_state.arguments):
            pos_arg = f"${idx}"
            last_idx = idx
            if pos_arg in event_arguments:
                flow_state.context[arg] = event_arguments[pos_arg]
            else:
                break
        # Check if more parameters were provided than the flow takes
        if f"${last_idx+1}" in event_arguments:
            raise ColangRuntimeError(
                f"To many parameters provided in start of flow '{flow_state.flow_id}'"
            )

    # Initialize new flow instance of flow
    if not flow_config.id == "main" and not flow_config.id.startswith("_dynamic_"):
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
            internal_event = create_stop_flow_internal_event(
                child_flow_state.uid, flow_state.uid, matching_scores
            )
            _push_internal_event(state, internal_event)

    # Abort all stared actions that have not finished yet
    for action_uid in flow_state.action_uids:
        action = state.actions[action_uid]
        if (
            action.status == ActionStatus.STARTING
            or action.status == ActionStatus.STARTED
        ):
            action_event = action.stop_event({})
            action.status = ActionStatus.STOPPING
            _generate_action_event(state, action_event)

    # Cleanup all head from flow
    flow_state.heads.clear()

    flow_state.status = FlowStatus.STOPPED

    # Generate FlowFailed event
    event = create_internal_flow_event(
        InternalEvents.FLOW_FAILED, flow_state, matching_scores
    )
    _push_internal_event(state, event)

    log.info(
        f"Flow aborted/failed: '{_get_readable_flow_state_hierachy(state, flow_state.uid)}'"
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
                f"Flow deactivated: {_get_readable_flow_state_hierachy(state, child_flow_state.uid)}"
            )

    # Abort all running child flows
    for child_flow_uid in flow_state.child_flow_uids:
        child_flow_state = state.flow_states[child_flow_uid]
        if _is_listening_flow(child_flow_state):
            child_flow_state.status = FlowStatus.STOPPING
            internal_event = create_stop_flow_internal_event(
                child_flow_state.uid, flow_state.uid, matching_scores, True
            )
            _push_internal_event(state, internal_event)

    # Abort all started actions that have not finished yet
    for action_uid in flow_state.action_uids:
        action = state.actions[action_uid]
        if (
            action.status == ActionStatus.STARTING
            or action.status == ActionStatus.STARTED
        ):
            action_event = action.stop_event({})
            action.status = ActionStatus.STOPPING
            _generate_action_event(state, action_event)

    # Cleanup all head from flow
    flow_state.heads.clear()

    flow_state.status = FlowStatus.FINISHED

    # Generate FlowFinished event
    event = create_internal_flow_event(
        InternalEvents.FLOW_FINISHED, flow_state, matching_scores
    )
    _push_internal_event(state, event)

    # Check if it was an user/bot intent/action flow a generate internal events
    event_type: Optional[str] = None
    source_code = state.flow_configs[flow_state.flow_id].source_code
    if source_code is not None:
        if "meta: user intent" in source_code:
            event_type = InternalEvents.USER_INTENT_LOG
        elif "meta: bot intent" in source_code:
            event_type = InternalEvents.BOT_INTENT_LOG
        elif "meta: user action" in source_code:
            event_type = InternalEvents.USER_ACTION_LOG
        elif "meta: bot action" in source_code:
            event_type = InternalEvents.BOT_ACTION_LOG

    if (
        event_type == InternalEvents.USER_INTENT_LOG
        or event_type == InternalEvents.BOT_INTENT_LOG
    ):
        event = create_internal_event(
            event_type,
            # TODO: Refactor how we define intents and there relation to flow names
            {
                "flow_id": (
                    flow_state.flow_id
                    if not flow_state.flow_id.startswith("_dynamic_")
                    else flow_state.flow_id[18:]
                ),
                "parameter": flow_state.context.get("$0", None),
            },
            matching_scores,
        )
        _push_internal_event(state, event)

    elif (
        event_type == InternalEvents.USER_ACTION_LOG
        or event_type == InternalEvents.BOT_ACTION_LOG
    ):
        hierarchy = _get_flow_state_hierarchy(state, flow_state.uid)
        # Find next intent in hierarchy
        # TODO: Generalize to multi intents
        intent = None
        for flow_state_uid in reversed(hierarchy):
            flow_config = state.flow_configs[state.flow_states[flow_state_uid].flow_id]
            if flow_config.source_code is not None:
                match = re.search(
                    r'#\W*meta:\W*(bot intent|user intent)(\W*=\W*"([a-zA-Z0-9_ ]*)")?',
                    flow_config.source_code,
                )
                if match:
                    if match.group(3) is not None:
                        intent = match.group(3)
                    else:
                        intent = flow_config.id

        event = create_internal_event(
            event_type,
            {
                "flow_id": flow_state.flow_id,
                "parameter": flow_state.context.get("$0", None),
                "intent_flow_id": intent,
            },
            matching_scores,
        )
        _push_internal_event(state, event)

    log.info(
        f"Flow finished: '{_get_readable_flow_state_hierachy(state, flow_state.uid)}' context={_context_log(flow_state)}"
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


def _generate_action_event(state: State, event: Event) -> None:
    umim_event = create_umim_event(event, event.arguments)
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


def get_element_from_head(state: State, head: FlowHead) -> SpecOp:
    """Returns the element at the flow head position"""
    return get_flow_config_from_head(state, head).elements[head.position]


def get_flow_config_from_head(state: State, head: FlowHead) -> FlowConfig:
    """Returns the flow config of the flow of the head"""
    return state.flow_configs[get_flow_state_from_head(state, head).flow_id]


def get_flow_state_from_head(state: State, head: FlowHead) -> FlowState:
    """Returns the flow state of the flow head"""
    return state.flow_states[head.flow_state_uid]


def is_action_op_element(element: SpecOp) -> bool:
    """Checks if the given element is actionable."""
    return (
        isinstance(element, SpecOp)
        and element.op == "send"
        and element.spec.name not in InternalEvents.ALL
    )


def is_match_op_element(element: SpecOp) -> bool:
    return isinstance(element, SpecOp) and element.op == "match"


def _evaluate_arguments(arguments: dict, context: dict) -> dict:
    return dict([(key, eval_expression(arguments[key], context)) for key in arguments])


def _get_readable_flow_state_hierachy(state: State, flow_state_uid: int) -> str:
    hierarchy = _get_flow_state_hierarchy(state, flow_state_uid)
    result = ""
    for flow_state_uid in hierarchy:
        result += flow_state_uid + "/"
    result.rstrip("/")
    return result


def _get_flow_state_hierarchy(state: State, flow_state_uid: int) -> List[str]:
    if flow_state_uid not in state.flow_states:
        return []
    flow_state = state.flow_states[flow_state_uid]
    if flow_state.parent_uid is None:
        return []
    else:
        result = _get_flow_state_hierarchy(state, flow_state.parent_uid)
        result.append(flow_state.uid)
        return result


def _compute_event_matching_score(
    state: State, flow_state: FlowState, element: SpecOp, event: Event
) -> float:
    """Checks if the element matches with given event."""
    assert is_match_op_element(element), f"Element '{element}' is not a match element!"

    ref_event = get_event_from_element(state, flow_state, element)
    if not isinstance(ref_event, type(event)):
        return 0.0

    return _compute_event_comparison_score(state, event, ref_event, flow_state.priority)


def _compute_event_comparison_score(
    state: State, event: Event, ref_event: Event, priority: Optional[float] = None
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
        assert isinstance(event, InternalEvent) and isinstance(ref_event, InternalEvent)
        if (
            "flow_id" in ref_event.arguments
            and "flow_id" in event.arguments
            and _compute_arguments_dict_matching_score(
                event.arguments["flow_id"], ref_event.arguments["flow_id"]
            )
            != 1.0
        ) or (
            ref_event.flow is not None
            and "source_flow_instance_uid" in event.arguments
            and _compute_arguments_dict_matching_score(
                event.arguments["source_flow_instance_uid"], ref_event.flow.uid
            )
            != 1.0
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
        if ref_event.name != event.name:
            return 0.0

        event_copy = copy.deepcopy(event)

        if hasattr(event, "action_uid") and hasattr(ref_event, "action_uid"):
            if (
                ref_event.action_uid is not None
                and ref_event.action_uid != event.action_uid
            ):
                return 0.0

            # TODO: Action event matches can also fail for certain events, e.g. match Started(), received Finished()

            if event.action_uid is not None and event.action_uid in state.actions:
                action_arguments = state.actions[event.action_uid].start_event_arguments
                event_copy.arguments["action_arguments"] = action_arguments

        match_score = _compute_arguments_dict_matching_score(
            event_copy.arguments, ref_event.arguments
        )

    # Take into account the priority of the flow
    if priority:
        match_score *= priority

    return match_score


def find_all_active_event_matchers(
    state: State, event: Optional[Event] = None
) -> List[FlowHead]:
    event_matchers: List[FlowHead] = []
    for flow_state in state.flow_states.values():
        if not _is_active_flow(flow_state) or not _is_listening_flow(flow_state):
            continue

        flow_config = state.flow_configs[flow_state.flow_id]

        for head in flow_state.active_heads.values():
            if head.status != FlowHeadStatus.INACTIVE:
                element = flow_config.elements[head.position]
                if is_match_op_element(element):
                    if event:
                        element_event = get_event_from_element(
                            state, flow_state, element
                        )
                        score = _compute_event_comparison_score(
                            state,
                            element_event,
                            event,
                        )
                        if score > 0.0:
                            event_matchers.append(head)
                    else:
                        event_matchers.append(head)

    return event_matchers


def _compute_arguments_dict_matching_score(args: Any, ref_args: Any) -> float:
    # TODO: Find a better way of passing arguments to distinguish the ones that count for matching
    score = 1.0
    if isinstance(ref_args, re.Pattern) and (
        isinstance(args, str) or isinstance(args, int) or isinstance(args, float)
    ):
        args = str(args)
        if not ref_args.search(args):
            return 0.0
    elif not isinstance(ref_args, type(args)):
        return 0.0
    elif isinstance(ref_args, dict):
        argument_filter = ["return_value", "activated", "source_flow_instance_uid"]
        if len(ref_args) > len(args):
            return 0.0
        for val in ref_args.keys():
            if val in argument_filter:
                continue
            elif val in args:
                score *= _compute_arguments_dict_matching_score(
                    args[val], ref_args[val]
                )
                if score == 0.0:
                    return 0.0
            else:
                return 0.0

        # Fuzzy match since number of arguments are not the same
        score *= 0.9 ** (len(args) - len(ref_args))
    elif isinstance(ref_args, list):
        if len(ref_args) > len(args):
            return 0.0
        for idx, ref_val in enumerate(ref_args):
            score *= _compute_arguments_dict_matching_score(args[idx], ref_val)
            if score == 0.0:
                return 0.0
        # Fuzzy match since number of arguments are not the same
        score *= 0.9 ** (len(args) - len(ref_args))
    elif isinstance(ref_args, set):
        for ref_val in ref_args:
            temp_score = 0.0
            for val in args:
                temp_score = _compute_arguments_dict_matching_score(val, ref_val)
                if temp_score > 0.0:
                    break
            score *= temp_score
            if temp_score == 0.0:
                return 0.0
        # Fuzzy match since number of arguments are not the same
        score *= 0.9 ** (len(args) - len(ref_args))
    elif args != ref_args:
        return 0.0

    return score


def get_event_from_element(
    state: State, flow_state: FlowState, element: SpecOp
) -> Event:
    """
    Converts the element into the corresponding event if possible.

    Cases:
    1) Bare event: send/match UtteranceBotActionFinished(args)
    2) Event as member of a action or flow constructor: send/match UtteranceBotAction(args).Finished(args)
    3) Event as member of a action or flow reference: send/match $ref.Finished(args) (This is action/flow specific)
    """

    assert isinstance(element.spec, Spec)
    element_spec: Spec = element.spec

    action: Action
    if element_spec["var_name"] is not None:
        # Case 3)
        variable_name = element_spec["var_name"]
        if variable_name not in flow_state.context:
            raise ColangRuntimeError((f"Unkown variable: '{variable_name}'!"))

        # Resolve variable and member attributes
        obj = flow_state.context[variable_name]
        member = None
        if element_spec.members is not None:
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
            flow_event = InternalEvent(
                name=element_spec.name, arguments=event_arguments
            )
            return flow_event
        elif "Action" in element_spec.name:
            # Action event
            event_arguments = _evaluate_arguments(
                element_spec.arguments, flow_state.context
            )
            action_event = ActionEvent(
                name=element_spec.name, arguments=event_arguments
            )
            return action_event
        else:
            # Event
            event_arguments = _evaluate_arguments(
                element_spec.arguments, flow_state.context
            )
            event = Event(name=element_spec.name, arguments=event_arguments)
            return event

    return None


def _generate_action_event_from_actionable_element(
    state: State,
    head: FlowHead,
) -> None:
    """Helper to create an outgoing event from the flow head element."""
    flow_state = get_flow_state_from_head(state, head)
    element = get_element_from_head(state, head)
    assert is_action_op_element(
        element
    ), f"Cannot create an event from a non actionable flow element {element}!"

    if element.op == "send":
        event = get_event_from_element(state, flow_state, element)
        assert isinstance(event, ActionEvent) or isinstance(event, Event)
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


def create_umim_event(event: Event, event_args: dict) -> Dict[str, Any]:
    """Returns an outgoing UMIM event for the provided action data"""
    new_event_args = event_args.copy()
    new_event_args["source_uid"] = "NeMoGuardrails-Colang-1.1"
    if isinstance(event, ActionEvent) and event.action_uid is not None:
        return new_event_dict(event.name, action_uid=event.action_uid, **new_event_args)
    else:
        return new_event_dict(event.name, **new_event_args)
