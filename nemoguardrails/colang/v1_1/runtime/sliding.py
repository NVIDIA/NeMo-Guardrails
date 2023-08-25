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

import logging
from typing import Optional

from nemoguardrails.colang.v1_1.runtime.eval import eval_expression


def slide(state: "State", flow_config: "FlowConfig", head: "FlowHead") -> Optional[int]:
    """Tries to slide a flow with the provided head.

    Sliding is the operation of moving through "non-matching" elements e.g. check,
    if, jump, expect etc.

    :param state: The current state of the dialog.
    :param flow_config: The config of the flow that should be advanced.
    :param head: The current head.
    :return:
    """
    head_position = head.position

    context = state.context

    # The active label is the label that can be reached going backwards
    # only through sliding elements.
    active_label = None
    active_label_data = None

    # This might get called directly at the end of a flow, in which case
    # we put the prev_head on the last element.
    prev_head = (
        head_position
        if head_position < len(flow_config.elements)
        else head_position - 1
    )

    while True:
        # if we reached the end, we stop
        if head_position == len(flow_config.elements) or head_position < 0:
            # We make a convention to return the last head, multiplied by -1 when the flow finished
            return -1 * (prev_head + 1)

        prev_head = head_position
        pattern_item = flow_config.elements[head_position]

        # Updated the active label if needed
        if "_label" in pattern_item:
            active_label = pattern_item["_label"]
            active_label_data = pattern_item.get("_label_value", None)

        # We make sure the active label is propagated to all the other elements
        if active_label:
            pattern_item["_active_label"] = active_label
            pattern_item["_active_label_data"] = active_label_data

        p_type = pattern_item["_type"]
        logging.info(f"Sliding step: '{p_type}'")

        # CHECK, IF, JUMP
        if p_type in ["check", "if", "jump"]:
            # for check and if, we need to evaluate the expression
            if p_type in ["check", "if"]:
                expr = pattern_item["expression"]
                check = eval_expression(expr, context)

                if p_type == "check":
                    if not check:
                        return None
                    else:
                        head_position += int(pattern_item.get("_next", 1))
                elif p_type == "if":
                    if check:
                        head_position += 1
                    else:
                        head_position += int(pattern_item["_next_else"])

            elif p_type == "jump":
                if not pattern_item.get("_absolute"):
                    head_position += int(pattern_item["_next"])
                else:
                    head_position = int(pattern_item["_next"])

        elif p_type in ["while"]:
            expr = pattern_item["expression"]
            check = eval_expression(expr, context)
            if check:
                head_position += int(pattern_item.get("_next", 1))
            else:
                head_position += int(pattern_item["_next_on_break"])

        # CONTINUE
        elif p_type == "continue":
            head_position += int(pattern_item.get("_next_on_continue", 1))

        # STOP
        elif p_type == "stop":
            return None

        # BREAK
        elif p_type == "break":
            head_position += int(pattern_item.get("_next_on_break", 1))

        # SET
        elif p_type == "set":
            value = eval_expression(pattern_item["expression"], context)

            # We transform tuples into arrays
            if isinstance(value, tuple):
                value = list(value)

            key_name = pattern_item["key"]

            # Update the context with the result of the expression and also record
            # the explicit update.
            context.update({key_name: value})
            state.context_updates.update({key_name: value})

            head_position += int(pattern_item.get("_next", 1))

        # SEND INTERNAL EVENT
        # TODO: Figure out how we can check if it is an internal event or an UMIM Action event from parsing
        elif p_type == "send_internal_event":
            # Push internal event
            # TODO: Create helper function to create internal events
            event = {
                "type": "StartFlow",
                "flow_name": pattern_item["flow_name"],
                "parent_flow_uid": state.flow_states[head.flow_state_uid].uid,
                "matching_scores": head.matching_scores,
                "event_time_uid": head.event_time_uid,
            }
            state.internal_events.append(event)
            logging.info(f"Create internal event: {event}")
            head_position += int(pattern_item.get("_next", 1))
        else:
            break
    # If we got this far, it means we had a match and the flow advanced
    return head_position
