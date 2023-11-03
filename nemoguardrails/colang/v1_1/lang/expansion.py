import copy
import re
from typing import Dict, List, Optional, Tuple, Union

from nemoguardrails.colang.v1_1.lang.colang_ast import (
    Abort,
    Assignment,
    BeginScope,
    Break,
    CatchPatternFailure,
    Continue,
    EndScope,
    ForkHead,
    Goto,
    If,
    Label,
    MergeHeads,
    Spec,
    SpecOp,
    SpecType,
    WaitForHeads,
    When,
    While,
)
from nemoguardrails.colang.v1_1.runtime.flows import (
    ColangSyntaxError,
    ElementType,
    FlowConfig,
    InternalEvents,
)
from nemoguardrails.colang.v1_1.runtime.utils import new_var_uid


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
            elif isinstance(element, Assignment):
                expanded_elems = _expand_assignment_stmt_element(element, flow_configs)
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
                elements_changed = True
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
                        ref=create_ref_ast_dict_helper(flow_event_ref_uid),
                        spec_type=SpecType.EVENT,
                    ),
                    info={"internal": True},
                )
            )
            # $flow_ref = $_flow_event_ref.flow
            element_ref = element.spec.ref
            if element_ref is None:
                flow_ref_uid = f"_flow_ref_{new_var_uid()}"
                element_ref = create_ref_ast_dict_helper(flow_ref_uid)
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
                element_ref = create_ref_ast_dict_helper(action_event_ref_uid)
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
                element_ref = create_ref_ast_dict_helper(
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
                    element_ref = create_ref_ast_dict_helper(
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
                element_ref = create_ref_ast_dict_helper(f"_ref_{new_var_uid()}")

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
                group_element_copy = copy.deepcopy(group_element)
                element_ref = group_element_copy.ref
                if element_ref is None:
                    element_ref = create_ref_ast_dict_helper(f"_ref_{new_var_uid()}")

                group_element_copy.ref = element_ref
                start_elements[-1].append(
                    SpecOp(
                        op="start",
                        spec=group_element_copy,
                    )
                )
                match_elements[-1].append(
                    Spec(
                        var_name=element_ref["elements"][0]["elements"][0].lstrip("$"),
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
            element_copy = copy.deepcopy(element)
            element_copy.spec.arguments.update(
                {
                    "flow_id": f"'{element.spec.name}'",
                    "flow_start_uid": f"'{new_var_uid()}'",
                    "activated": "True",
                }
            )
            new_elements.append(
                SpecOp(
                    op="start",
                    spec=element_copy.spec,
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


def _expand_assignment_stmt_element(
    element: Assignment, flow_configs: Dict[str, FlowConfig]
) -> List[ElementType]:
    new_elements: List[ElementType] = []

    # Check if the expression is an NLD
    nld_pattern = r"\"\"\"(.*?)\"\"\"|'''(.*?)'''"
    match = re.search(nld_pattern, element.expression)

    if match:
        # Replace the assignment with the GenerateValueAction system action
        new_elements.append(
            SpecOp(
                op="await",
                spec=Spec(
                    name="GenerateValueAction",
                    spec_type=SpecType.ACTION,
                    arguments={
                        "var_name": f'"{element.key}"',
                        "instructions": f'"{match.group(1) or match.group(2)}"',
                    },
                ),
                return_var_name=element.key,
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
                        group_element.ref = create_ref_ast_dict_helper(ref_uid)
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
                when_element.ref = create_ref_ast_dict_helper(flow_ref_uid)
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
                when_element.ref = create_ref_ast_dict_helper(action_ref_uid)
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


def create_ref_ast_dict_helper(ref_name: str) -> dict:
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
