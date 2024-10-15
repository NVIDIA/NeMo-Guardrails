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

#
from typing import Any, Dict, List, Optional

from dateutil import parser
from pydantic import BaseModel, Field

from nemoguardrails.colang.v2_x.runtime.flows import ActionEvent
from nemoguardrails.colang.v2_x.runtime.statemachine import InternalEvent
from nemoguardrails.logging.explain import LLMCallInfo
from nemoguardrails.rails.llm.options import (
    ActivatedRail,
    ExecutedAction,
    GenerationLog,
)

# Initialize data structures
activated_rails: List[ActivatedRail] = []
flows: Dict[str, Any] = {}  # flow_instance_uid -> flow data
actions: Dict[str, ExecutedAction] = {}  # action_uid -> ExecutedAction

ignored_flows = [
    # System flows that we can ignore
    "main",
    "wait",
    "repeating timer",
    "llm response polling",
    "llm_response_polling",
    "wait",
    "logging marked bot intent flows",
    "polling llm request response",
    "marking user intent flows",
    "marking bot intent flows",
    "logging marked user intent flows",
    # "bot started saying something",
    # "tracking bot talking state",
    # "bot said something",
    # "bot say",
    # "_bot_say",
    "tracking bot talking state",
    "await_flow_by_name",
    # Any other flows to ignore
]
generation_flows = []
# generation_flows = [
#     "llm generate interaction continuation flow",
#     # "generating user intent for unhandled user utterance",
#     "llm continuation",
#     # Add any other generation flows
# ]


def get_rail_type(flow_id):
    if flow_id in ["input rails", "self check input", "run input rails"]:
        return "input"
    elif flow_id in ["output rails", "self check output", "run output rails"]:
        return "output"
    elif flow_id in generation_flows:
        return "generation"
    elif flow_id not in ignored_flows:
        return "dialog"
    else:
        return None  # Ignored flows


def parse_timestamp(timestamp_str):
    if timestamp_str:
        # print("timestamp_str: ", timestamp_str)
        try:
            dt = parser.isoparse(timestamp_str)
            # print("dt: ", dt)
            # print("dt.timestamp(): ", dt.timestamp())
            return dt.timestamp()
        except Exception as e:
            print(f"Failed to parse timestamp: {e}")
    return None


def compute_generation_log_v2(processing_log: List[dict]) -> GenerationLog:
    # Initialize variables
    activated_rails: List[ActivatedRail] = []
    flows: Dict[str, Any] = {}  # flow_instance_uid -> flow data
    actions: Dict[str, ExecutedAction] = {}
    action_order: List[str] = []  # Keeps track of action_uids in the order they started
    current_action_uid_stack: List[str] = []
    fill_event_created_at(processing_log)

    # Variables to keep track of timestamps
    last_timestamp = None
    input_rails_started_at = None
    input_rails_finished_at = None
    output_rails_started_at = None
    output_rails_finished_at = None

    # Process events
    for event in processing_log:
        if not isinstance(event, dict) and "TimerBotAction" in event.name:
            continue
        # Process InternalEvent
        if isinstance(event, InternalEvent):
            event_name = event.name
            event_arguments = event.arguments
            flow_instance_uid = event_arguments.get("flow_instance_uid")
            flow_id = event_arguments.get("flow_id")
            parent_flow_instance_uid = event_arguments.get("parent_flow_instance_uid")

            timestamp = parse_timestamp(event_arguments.get("event_created_at"))
            if timestamp is not None:
                if last_timestamp is None or timestamp > last_timestamp:
                    last_timestamp = timestamp

            if event_name == "FlowStarted":
                flow_data = {
                    "flow_id": flow_id,
                    "parent_flow_instance_uid": parent_flow_instance_uid,
                    "started_at": timestamp,
                    "flow": None,
                }
                flows[flow_instance_uid] = flow_data

                rail_type = get_rail_type(flow_id)
                if rail_type:
                    activated_rail = ActivatedRail(
                        type=rail_type,
                        name=flow_id,
                        started_at=timestamp,
                    )
                    flow_data["flow"] = activated_rail
                    activated_rails.append(activated_rail)

                    # Update input/output rails started_at
                    if rail_type == "input" and input_rails_started_at is None:
                        input_rails_started_at = timestamp
                    if rail_type == "output" and output_rails_started_at is None:
                        output_rails_started_at = timestamp

            elif event_name == "FlowFinished":
                if flow_instance_uid in flows:
                    flow_data = flows[flow_instance_uid]
                    flow = flow_data["flow"]
                    if flow is not None:
                        flow.finished_at = timestamp
                        if flow.started_at and flow.finished_at:
                            flow.duration = flow.finished_at - flow.started_at

                        # Update input/output rails finished_at
                        rail_type = flow.type
                        if rail_type == "input":
                            input_rails_finished_at = timestamp
                        if rail_type == "output":
                            output_rails_finished_at = timestamp

                    del flows[flow_instance_uid]

        elif isinstance(event, ActionEvent):
            event_name = event.name
            event_arguments = event.arguments
            action_uid = event.action_uid

            timestamp = parse_timestamp(event_arguments.get("event_created_at"))
            if timestamp is not None:
                if last_timestamp is None or timestamp > last_timestamp:
                    last_timestamp = timestamp

            if event_name.startswith("Start"):
                action_name = event_name[len("Start") :]
                action_params = event_arguments
                executed_action = ExecutedAction(
                    action_name=action_name,
                    action_params=action_params,
                    started_at=timestamp,
                )
                actions[action_uid] = executed_action
                action_order.append(action_uid)

                # Find the parent flow
                parent_flow_instance_uid = event_arguments.get(
                    "parent_flow_instance_uid"
                )
                flow_found = False
                current_flow_instance_uid = parent_flow_instance_uid
                visited_flow_uids = set()

                while (
                    current_flow_instance_uid
                    and current_flow_instance_uid not in visited_flow_uids
                ):
                    visited_flow_uids.add(current_flow_instance_uid)
                    if current_flow_instance_uid in flows:
                        flow_data = flows[current_flow_instance_uid]
                        flow = flow_data["flow"]
                        if flow is not None:
                            flow.executed_actions.append(executed_action)
                            flow_found = True
                            break
                        else:
                            next_parent = flow_data.get("parent_flow_instance_uid")
                            if next_parent == current_flow_instance_uid:
                                # Avoid infinite loop
                                break
                            current_flow_instance_uid = next_parent
                    else:
                        current_flow_instance_uid = None  # Cannot find the parent flow

                if not flow_found:
                    # Could not find an ActivatedRail in the parent chain
                    pass  # Or handle accordingly

            elif event_name.endswith("ActionFinished"):
                if action_uid in actions:
                    executed_action = actions[action_uid]
                    executed_action.finished_at = timestamp
                    if executed_action.started_at and executed_action.finished_at:
                        executed_action.duration = (
                            executed_action.finished_at - executed_action.started_at
                        )
                    executed_action.return_value = event_arguments.get("return_value")
                # Do not remove the action_uid from action_order here

        else:
            # Handle llm_call_info events
            llm_call_info = None
            if hasattr(event, "type") and event.type == "llm_call_info":
                llm_call_info = event.data
            elif isinstance(event, dict) and event.get("type") == "llm_call_info":
                llm_call_info = event["data"]

            if llm_call_info:
                # Associate llm_call_info with the most recent action that has not finished
                for action_uid in reversed(action_order):
                    executed_action = actions.get(action_uid)
                    if executed_action and not executed_action.finished_at:
                        executed_action.llm_calls.append(llm_call_info)
                        break
                else:
                    # No action found to associate with; handle accordingly
                    pass

    # Now assign the activated rails to the GenerationLog object
    generation_log = GenerationLog(activated_rails=activated_rails)

    # Start integrating the old logic

    # If we have activated rails, get the last one
    if activated_rails:
        activated_rail = activated_rails[-1]
        if activated_rail.finished_at is None:
            activated_rail.finished_at = last_timestamp
            activated_rail.duration = (
                activated_rail.finished_at - activated_rail.started_at
            )

        if activated_rail.type in ["input", "output"]:
            activated_rail.stop = True
            activated_rail.decisions.append("stop")

    # If we have input rails, we also record the general stats
    if input_rails_started_at:
        # If we don't have a timestamp for when the input rails have finished,
        # we record the last timestamp.
        if input_rails_finished_at is None:
            input_rails_finished_at = last_timestamp

        generation_log.stats.input_rails_duration = (
            input_rails_finished_at - input_rails_started_at
        )

    # For all the dialog/generation rails, we set the finished time and the duration based on
    # the rail right after.
    for i in range(len(generation_log.activated_rails) - 1):
        activated_rail = generation_log.activated_rails[i]

        if (
            activated_rail.type in ["dialog", "generation"]
            and activated_rail.finished_at is None
        ):
            next_rail = generation_log.activated_rails[i + 1]
            activated_rail.finished_at = next_rail.started_at
            activated_rail.duration = (
                activated_rail.finished_at - activated_rail.started_at
            )

    # If we have output rails, we also record the general stats
    if output_rails_started_at:
        # If we don't have a timestamp for when the output rails have finished,
        # we record the last timestamp.
        if output_rails_finished_at is None:
            output_rails_finished_at = last_timestamp

        generation_log.stats.output_rails_duration = (
            output_rails_finished_at - output_rails_started_at
        )

    # We also need to compute the stats for dialog rails and generation.
    # And the stats for the LLM calls.
    for activated_rail in generation_log.activated_rails:
        # TODO: figure out a cleaner way to do this.
        #  the generation should not be inside the `generate user intent`
        # If we have a dialog rail for `generate user intent` and it has an
        # LLM call with the task `general`, then we consider this as a generation rail.
        if activated_rail.name == "generate user intent":
            if len(activated_rail.executed_actions) == 1:
                executed_action = activated_rail.executed_actions[0]

                if (
                    len(executed_action.llm_calls) == 1
                    and executed_action.llm_calls[0].task == "general"
                ):
                    activated_rail.type = "generation"

        if generation_log.stats.dialog_rails_duration is None:
            generation_log.stats.dialog_rails_duration = 0.0

        if generation_log.stats.generation_rails_duration is None:
            generation_log.stats.generation_rails_duration = 0.0

        # Ensure llm_calls_count is initialized
        if generation_log.stats.llm_calls_count is None:
            generation_log.stats.llm_calls_count = 0

        # Ensure llm_calls_duration is initialized
        if generation_log.stats.llm_calls_duration is None:
            generation_log.stats.llm_calls_duration = 0.0

        # Ensure llm_calls_total_prompt_tokens is initialized
        if generation_log.stats.llm_calls_total_prompt_tokens is None:
            generation_log.stats.llm_calls_total_prompt_tokens = 0

        # Ensure llm_calls_total_completion_tokens is initialized
        if generation_log.stats.llm_calls_total_completion_tokens is None:
            generation_log.stats.llm_calls_total_completion_tokens = 0

        # Ensure llm_calls_total_tokens is initialized
        if generation_log.stats.llm_calls_total_tokens is None:
            generation_log.stats.llm_calls_total_tokens = 0
        if activated_rail.type == "dialog" and activated_rail.duration:
            generation_log.stats.dialog_rails_duration += activated_rail.duration

        if activated_rail.type == "generation" and activated_rail.duration:
            generation_log.stats.generation_rails_duration += activated_rail.duration

        for executed_action in activated_rail.executed_actions:
            print("we are here")
            for llm_call in executed_action.llm_calls:
                generation_log.stats.llm_calls_count += 1
                generation_log.stats.llm_calls_duration += llm_call.duration or 0.0
                generation_log.stats.llm_calls_total_prompt_tokens += (
                    llm_call.prompt_tokens or 0
                )
                generation_log.stats.llm_calls_total_completion_tokens += (
                    llm_call.completion_tokens or 0
                )
                generation_log.stats.llm_calls_total_tokens += (
                    llm_call.total_tokens or 0
                )

                print(generation_log.stats)

    # Compute total duration
    if last_timestamp is not None and processing_log:
        first_event_timestamp = None
        for event in processing_log:
            timestamp = None
            if isinstance(event, dict):
                timestamp = event.get("timestamp")
            else:
                event_arguments = event.arguments
                timestamp = parse_timestamp(event_arguments.get("event_created_at"))
            if timestamp is not None:
                first_event_timestamp = timestamp
                break
        if first_event_timestamp is not None:
            generation_log.stats.total_duration = last_timestamp - first_event_timestamp

    print("Final generation_log.stats:", generation_log.stats)
    return generation_log


# def compute_generation_log_v2(processing_log: List[dict]) -> GenerationLog:
#     # Initialize variables
#     activated_rails: List[ActivatedRail] = []
#     flows: Dict[str, Any] = {}  # flow_instance_uid -> flow data
#     actions: Dict[str, ExecutedAction] = {}
#     action_order: List[str] = []  # Keeps track of action_uids in the order they started
#     current_action_uid_stack: List[str] = []
#     fill_event_created_at(processing_log)
#
#     for event in processing_log:
#         if not isinstance(event, dict) and "TimerBotAction" in event.name:
#             continue
#         # Process InternalEvent
#         if isinstance(event, InternalEvent):
#             event_name = event.name
#             event_arguments = event.arguments
#             flow_instance_uid = event_arguments.get("flow_instance_uid")
#             flow_id = event_arguments.get("flow_id")
#             parent_flow_instance_uid = event_arguments.get("parent_flow_instance_uid")
#
#             timestamp = parse_timestamp(event_arguments.get("event_created_at"))
#
#             if event_name == "FlowStarted":
#                 flow_data = {
#                     "flow_id": flow_id,
#                     "parent_flow_instance_uid": parent_flow_instance_uid,
#                     "started_at": timestamp,
#                     "flow": None,
#                 }
#                 flows[flow_instance_uid] = flow_data
#
#                 rail_type = get_rail_type(flow_id)
#                 if rail_type:
#                     activated_rail = ActivatedRail(
#                         type=rail_type,
#                         name=flow_id,
#                         started_at=timestamp,
#                     )
#                     flow_data["flow"] = activated_rail
#                     activated_rails.append(activated_rail)
#
#             elif event_name == "FlowFinished":
#                 if flow_instance_uid in flows:
#                     flow_data = flows[flow_instance_uid]
#                     flow = flow_data["flow"]
#                     if flow is not None:
#                         flow.finished_at = timestamp
#                         if flow.started_at and flow.finished_at:
#                             flow.duration = flow.finished_at - flow.started_at
#
#                     del flows[flow_instance_uid]
#
#         elif isinstance(event, ActionEvent):
#             event_name = event.name
#             event_arguments = event.arguments
#             action_uid = event.action_uid
#
#             timestamp = parse_timestamp(event_arguments.get("event_created_at"))
#
#             if event_name.startswith("Start"):
#                 action_name = event_name[len("Start") :]
#                 action_params = event_arguments
#                 executed_action = ExecutedAction(
#                     action_name=action_name,
#                     action_params=action_params,
#                     started_at=timestamp,
#                 )
#                 actions[action_uid] = executed_action
#                 action_order.append(action_uid)
#
#                 # Find the parent flow
#                 parent_flow_instance_uid = event_arguments.get(
#                     "parent_flow_instance_uid"
#                 )
#                 flow_found = False
#                 current_flow_instance_uid = parent_flow_instance_uid
#                 visited_flow_uids = set()
#
#                 while (
#                     current_flow_instance_uid
#                     and current_flow_instance_uid not in visited_flow_uids
#                 ):
#                     visited_flow_uids.add(current_flow_instance_uid)
#                     if current_flow_instance_uid in flows:
#                         flow_data = flows[current_flow_instance_uid]
#                         flow = flow_data["flow"]
#                         if flow is not None:
#                             flow.executed_actions.append(executed_action)
#                             flow_found = True
#                             break
#                         else:
#                             next_parent = flow_data.get("parent_flow_instance_uid")
#                             if next_parent == current_flow_instance_uid:
#                                 # Avoid infinite loop
#                                 break
#                             current_flow_instance_uid = next_parent
#                     else:
#                         current_flow_instance_uid = None  # Cannot find the parent flow
#
#                 if not flow_found:
#                     # Could not find an ActivatedRail in the parent chain
#                     pass  # Or handle accordingly
#
#             elif event_name.endswith("ActionFinished"):
#                 if action_uid in actions:
#                     executed_action = actions[action_uid]
#                     executed_action.finished_at = timestamp
#                     if executed_action.started_at and executed_action.finished_at:
#                         executed_action.duration = (
#                             executed_action.finished_at - executed_action.started_at
#                         )
#                     executed_action.return_value = event_arguments.get("return_value")
#                 # Do not remove the action_uid from action_order here
#
#         else:
#             # Handle llm_call_info events
#             llm_call_info = None
#             if hasattr(event, "type") and event.type == "llm_call_info":
#                 llm_call_info = event.data
#             elif isinstance(event, dict) and event.get("type") == "llm_call_info":
#                 llm_call_info = event["data"]
#
#             if llm_call_info:
#                 # Associate llm_call_info with the most recent action that has not finished
#                 for action_uid in reversed(action_order):
#                     executed_action = actions.get(action_uid)
#                     if executed_action and not executed_action.finished_at:
#                         print(
#                             f"Associating llm_call_info {llm_call_info.task} with action: {executed_action}"
#                         )
#                         executed_action.llm_calls.append(llm_call_info)
#                         break
#                 else:
#                     # No action found to associate with; handle accordingly
#                     print(
#                         f"No action found to associate with llm_call_info: {llm_call_info}"
#                     )
#                     print(f"existing actions: {executed_action}")
#
#                     pass
#
#     # Now assign the activated rails to the GenerationLog object
#     generation_log = GenerationLog(activated_rails=activated_rails)
#
#     return generation_log


# def compute_generation_log_v2(processing_log: List[dict]) -> GenerationLog:
#     # Initialize variables
#     activated_rails: List[ActivatedRail] = []
#     flows: Dict[str, Any] = {}  # flow_instance_uid -> flow data
#     actions: Dict[str, ExecutedAction] = {}
#     current_action_uid_stack: List[str] = []
#
#     # Now, process the events
#     for event in processing_log:
#         # Process InternalEvent
#         if isinstance(event, InternalEvent):
#             event_name = event.name
#             event_arguments = event.arguments
#             flow_instance_uid = event_arguments.get("flow_instance_uid")
#             flow_id = event_arguments.get("flow_id")
#             parent_flow_instance_uid = event_arguments.get("parent_flow_instance_uid")
#
#             timestamp = parse_timestamp(event_arguments.get("event_created_at"))
#
#             if event_name == "FlowStarted":
#                 flow_data = {
#                     "flow_id": flow_id,
#                     "parent_flow_instance_uid": parent_flow_instance_uid,
#                     "started_at": timestamp,
#                     "flow": None,
#                 }
#                 flows[flow_instance_uid] = flow_data
#
#                 rail_type = get_rail_type(flow_id)
#                 if rail_type:
#                     activated_rail = ActivatedRail(
#                         type=rail_type,
#                         name=flow_id,
#                         started_at=timestamp,
#                     )
#                     flow_data["flow"] = activated_rail
#                     activated_rails.append(activated_rail)
#
#             elif event_name == "FlowFinished":
#                 if flow_instance_uid in flows:
#                     flow_data = flows[flow_instance_uid]
#                     flow = flow_data["flow"]
#                     if flow is not None:
#                         flow.finished_at = timestamp
#                         if flow.started_at and flow.finished_at:
#                             flow.duration = flow.finished_at - flow.started_at
#
#                     del flows[flow_instance_uid]
#
#         elif isinstance(event, ActionEvent):
#             event_name = event.name
#             event_arguments = event.arguments
#             action_uid = event.action_uid
#
#             timestamp = parse_timestamp(event_arguments.get("event_created_at"))
#
#             if event_name.startswith("Start"):
#                 action_name = event_name[len("Start") :]
#                 action_params = event_arguments
#                 executed_action = ExecutedAction(
#                     action_name=action_name,
#                     action_params=action_params,
#                     started_at=timestamp,
#                 )
#                 actions[action_uid] = executed_action
#                 current_action_uid_stack.append(action_uid)
#
#                 # Find the parent flow
#                 parent_flow_instance_uid = event_arguments.get(
#                     "parent_flow_instance_uid"
#                 )
#                 flow_found = False
#                 current_flow_instance_uid = parent_flow_instance_uid
#                 visited_flow_uids = set()
#
#                 while (
#                     current_flow_instance_uid
#                     and current_flow_instance_uid not in visited_flow_uids
#                 ):
#                     visited_flow_uids.add(current_flow_instance_uid)
#                     if current_flow_instance_uid in flows:
#                         flow_data = flows[current_flow_instance_uid]
#                         flow = flow_data["flow"]
#                         if flow is not None:
#                             flow.executed_actions.append(executed_action)
#                             flow_found = True
#                             break
#                         else:
#                             next_parent = flow_data.get("parent_flow_instance_uid")
#                             if next_parent == current_flow_instance_uid:
#                                 # Avoid infinite loop
#                                 break
#                             current_flow_instance_uid = next_parent
#                     else:
#                         current_flow_instance_uid = None  # Cannot find the parent flow
#
#                 if not flow_found:
#                     # Could not find an ActivatedRail in the parent chain
#                     pass  # Or handle accordingly
#
#             elif event_name.endswith("ActionFinished"):
#                 if action_uid in actions:
#                     executed_action = actions[action_uid]
#                     executed_action.finished_at = timestamp
#                     if executed_action.started_at and executed_action.finished_at:
#                         executed_action.duration = (
#                             executed_action.finished_at - executed_action.started_at
#                         )
#                     executed_action.return_value = event_arguments.get("return_value")
#                 if (
#                     current_action_uid_stack
#                     and current_action_uid_stack[-1] == action_uid
#                 ):
#                     current_action_uid_stack.pop()
#
#         elif isinstance(event, dict) and event.get("type") == "llm_call_info":
#             # Associate llm_call_info with the current action
#             if current_action_uid_stack:
#                 current_action_uid = current_action_uid_stack[-1]
#                 if current_action_uid in actions:
#                     executed_action = actions[current_action_uid]
#                     llm_call_info = event["data"]
#                     executed_action.llm_calls.append(llm_call_info)
#             else:
#                 # No current action to associate with, can log or handle accordingly
#                 pass
#
#     # Now assign the activated rails to the GenerationLog object
#     generation_log = GenerationLog(activated_rails=activated_rails)
#
#     return generation_log


# def compute_generation_log_v2(processing_log: List[dict]) -> GenerationLog:
#     # Initialize variables
#     activated_rails: List[ActivatedRail] = []
#     flows: Dict[str, Any] = {}  # flow_instance_uid -> flow data
#     actions: Dict[str, ExecutedAction] = {}
#     current_action_uid_stack: List[str] = []
#
#     # Define ignored_flows and generation_flows
#     ignored_flows = [
#         "main",
#         "wait",
#         "repeating timer",
#         "polling llm request response",
#         "bot started saying something",
#         "tracking bot talking state",
#         "bot said something",
#         "bot say",
#         "_bot_say",
#         "await_flow_by_name",
#         # Add any other flows to ignore
#     ]
#
#     generation_flows = [
#         "llm generate interaction continuation flow",
#         "generating user intent for unhandled user utterance",
#         "llm continuation",
#         # Add any other generation flows
#     ]
#
#     def get_rail_type(flow_id):
#         if flow_id in ["input rails", "self check input", "run input rails"]:
#             return "input"
#         elif flow_id in ["output rails", "self check output", "run output rails"]:
#             return "output"
#         elif flow_id in generation_flows:
#             return "generation"
#         elif flow_id not in ignored_flows:
#             return "dialog"
#         else:
#             return None  # Ignored flows
#
#     def parse_timestamp(timestamp_str):
#         if timestamp_str:
#             try:
#                 dt = parser.isoparse(timestamp_str)
#                 return dt.timestamp()
#             except Exception:
#                 pass
#         return None
#
#     # Now, process the events
#     for event in processing_log:
#         # Process InternalEvent
#         if isinstance(event, InternalEvent):
#             event_name = event.name
#             event_arguments = event.arguments
#             flow_instance_uid = event_arguments.get("flow_instance_uid")
#             flow_id = event_arguments.get("flow_id")
#             parent_flow_instance_uid = event_arguments.get("parent_flow_instance_uid")
#
#             timestamp = parse_timestamp(event_arguments.get("event_created_at"))
#
#             if event_name == "FlowStarted":
#                 flow_data = {
#                     "flow_id": flow_id,
#                     "parent_flow_instance_uid": parent_flow_instance_uid,
#                     "started_at": timestamp,
#                     "flow": None,
#                 }
#                 flows[flow_instance_uid] = flow_data
#
#                 rail_type = get_rail_type(flow_id)
#                 if rail_type:
#                     activated_rail = ActivatedRail(
#                         type=rail_type,
#                         name=flow_id,
#                         started_at=timestamp,
#                     )
#                     flow_data["flow"] = activated_rail
#                     activated_rails.append(activated_rail)
#
#             elif event_name == "FlowFinished":
#                 if flow_instance_uid in flows:
#                     flow_data = flows[flow_instance_uid]
#                     flow = flow_data["flow"]
#                     if flow is not None:
#                         flow.finished_at = timestamp
#                         if flow.started_at and flow.finished_at:
#                             flow.duration = flow.finished_at - flow.started_at
#
#                     del flows[flow_instance_uid]
#
#         elif isinstance(event, ActionEvent):
#             event_name = event.name
#             event_arguments = event.arguments
#             action_uid = event.action_uid
#
#             timestamp = parse_timestamp(event_arguments.get("event_created_at"))
#
#             if event_name.startswith("Start"):
#                 action_name = event_name[len("Start") :]
#                 action_params = event_arguments
#                 executed_action = ExecutedAction(
#                     action_name=action_name,
#                     action_params=action_params,
#                     started_at=timestamp,
#                 )
#                 actions[action_uid] = executed_action
#                 current_action_uid_stack.append(action_uid)
#
#                 # Find the parent flow
#                 parent_flow_instance_uid = event_arguments.get(
#                     "parent_flow_instance_uid"
#                 )
#                 flow_found = False
#                 current_flow_instance_uid = parent_flow_instance_uid
#                 visited_flow_uids = set()
#
#                 while (
#                     current_flow_instance_uid
#                     and current_flow_instance_uid not in visited_flow_uids
#                 ):
#                     visited_flow_uids.add(current_flow_instance_uid)
#                     if current_flow_instance_uid in flows:
#                         flow_data = flows[current_flow_instance_uid]
#                         flow = flow_data["flow"]
#                         if flow is not None:
#                             flow.executed_actions.append(executed_action)
#                             flow_found = True
#                             break
#                         else:
#                             next_parent = flow_data.get("parent_flow_instance_uid")
#                             if next_parent == current_flow_instance_uid:
#                                 # Avoid infinite loop
#                                 break
#                             current_flow_instance_uid = next_parent
#                     else:
#                         break  # Cannot find the parent flow
#
#                 if not flow_found:
#                     # Could not find an ActivatedRail in the parent chain
#                     pass  # Or handle accordingly
#
#             elif event_name.endswith("ActionFinished"):
#                 if action_uid in actions:
#                     executed_action = actions[action_uid]
#                     executed_action.finished_at = timestamp
#                     if executed_action.started_at and executed_action.finished_at:
#                         executed_action.duration = (
#                             executed_action.finished_at - executed_action.started_at
#                         )
#                     executed_action.return_value = event_arguments.get("return_value")
#                 if (
#                     current_action_uid_stack
#                     and current_action_uid_stack[-1] == action_uid
#                 ):
#                     current_action_uid_stack.pop()
#
#         elif isinstance(event, dict) and event.get("type") == "llm_call_info":
#             # Associate llm_call_info with the current action
#             if current_action_uid_stack:
#                 current_action_uid = current_action_uid_stack[-1]
#                 if current_action_uid in actions:
#                     executed_action = actions[current_action_uid]
#                     llm_call_info = event["data"]
#                     executed_action.llm_calls.append(llm_call_info)
#             else:
#                 # No current action to associate with, can log or handle accordingly
#                 pass
#
#     # Now assign the activated rails to the GenerationLog object
#     generation_log = GenerationLog(activated_rails=activated_rails)
#
#     return generation_log


# def compute_generation_log_v2(processing_log: List[dict]) -> GenerationLog:
#     for event in processing_log:
#         # Process InternalEvent
#         if isinstance(event, InternalEvent):
#             event_name = event.name
#             event_arguments = event.arguments
#             flow_instance_uid = event_arguments.get("flow_instance_uid")
#             flow_id = event_arguments.get("flow_id")
#             parent_flow_instance_uid = event_arguments.get("parent_flow_instance_uid")
#
#             # print("ACTIVATED RAIL")
#             timestamp = parse_timestamp(event_arguments.get("event_created_at"))
#             # if not timestamp:
#             # print("No timestamp")
#             # print(event)
#             # print("***" * 100)
#
#             # print(f"timestamp: {timestamp}")
#
#             if event_name == "FlowStarted":
#                 flow_data = {
#                     "flow_id": flow_id,
#                     "parent_flow_instance_uid": parent_flow_instance_uid,
#                     "started_at": timestamp,
#                     "flow": None,
#                 }
#                 flows[flow_instance_uid] = flow_data
#
#                 rail_type = get_rail_type(flow_id)
#                 if rail_type:
#                     activated_rail = ActivatedRail(
#                         type=rail_type,
#                         name=flow_id,
#                         started_at=timestamp,
#                     )
#                     # print(f"timestamp: {timestamp}")
#                     # print(f"activated rail timestamp: {activated_rail.started_at}")
#                     # print("===" * 10)
#                     flow_data["flow"] = activated_rail
#                     activated_rails.append(activated_rail)
#
#             elif event_name == "FlowFinished":
#                 if flow_instance_uid in flows:
#                     flow_data = flows[flow_instance_uid]
#                     flow = flow_data["flow"]
#                     if flow is not None:
#                         flow.finished_at = timestamp
#                         if flow.started_at and flow.finished_at:
#                             flow.duration = flow.finished_at - flow.started_at
#
#                     del flows[flow_instance_uid]
#
#         elif isinstance(event, ActionEvent):
#             event_name = event.name
#             event_arguments = event.arguments
#             action_uid = event.action_uid
#
#             timestamp = parse_timestamp(event_arguments.get("event_created_at"))
#
#             if event_name.startswith("Start"):
#                 action_name = event_name[len("Start") :]
#                 action_params = event_arguments
#                 executed_action = ExecutedAction(
#                     action_name=action_name,
#                     action_params=action_params,
#                     started_at=timestamp,
#                 )
#                 actions[action_uid] = executed_action
#
#                 # Find the parent flow
#                 parent_flow_instance_uid = event_arguments.get(
#                     "parent_flow_instance_uid"
#                 )
#                 flow_found = False
#                 current_flow_instance_uid = parent_flow_instance_uid
#                 visited_flow_uids = set()
#
#                 while (
#                     current_flow_instance_uid
#                     and current_flow_instance_uid not in visited_flow_uids
#                 ):
#                     visited_flow_uids.add(current_flow_instance_uid)
#                     if current_flow_instance_uid in flows:
#                         flow_data = flows[current_flow_instance_uid]
#                         flow = flow_data["flow"]
#                         if flow is not None:
#                             flow.executed_actions.append(executed_action)
#                             flow_found = True
#                             break
#                         else:
#                             next_parent = flow_data.get("parent_flow_instance_uid")
#                             if next_parent == current_flow_instance_uid:
#                                 # Avoid infinite loop
#                                 break
#                             current_flow_instance_uid = next_parent
#                     else:
#                         break  # Cannot find the parent flow
#
#                 if not flow_found:
#                     # Could not find an ActivatedRail in the parent chain
#                     pass  # Or handle accordingly
#
#             elif event_name.endswith("ActionFinished"):
#                 if action_uid in actions:
#                     executed_action = actions[action_uid]
#                     executed_action.finished_at = timestamp
#                     if executed_action.started_at and executed_action.finished_at:
#                         executed_action.duration = (
#                             executed_action.finished_at - executed_action.started_at
#                         )
#                     executed_action.return_value = event_arguments.get("return_value")
#
#     # we can now assign it to the GenerationLog object
#     generation_log = GenerationLog(activated_rails=activated_rails)
#
#     # For demonstration purposes, let's print the activated rails
#     # for rail in generation_log.activated_rails:
#     #     print(
#     #         f"Rail type: {rail.type}, name: {rail.name}, started_at: {rail.started_at}, finished_at: {rail.finished_at}, duration: {rail.duration}"
#     #     )
#     #     for action in rail.executed_actions:
#     #         print(
#     #             f"  Action: {action.action_name}, started_at: {action.started_at}, finished_at: {action.finished_at}, duration: {action.duration}"
#     #         )
#     return generation_log


def fill_event_created_at(events):
    """
    Processes a list of events and fills in the 'event_created_at' for 'FlowStarted' and 'FlowFinished' events
    that are missing it, by using the 'event_created_at' from their corresponding 'UnhandledEvent's.

    Args:
        events (list): A list of event objects.
    """
    # Create mappings from flow_instance_uid to event_created_at for UnhandledEvent where event == 'FlowStarted' or 'FlowFinished'
    unhandled_event_times = {"FlowStarted": {}, "FlowFinished": {}}

    for event in events:
        if isinstance(event, InternalEvent):
            if event.name == "UnhandledEvent":
                event_arguments = event.arguments
                unhandled_event_name = event_arguments.get("event")
                if unhandled_event_name in ("FlowStarted", "FlowFinished"):
                    flow_instance_uid = event_arguments.get("flow_instance_uid")
                    event_created_at = event_arguments.get("event_created_at")
                    if flow_instance_uid and event_created_at:
                        unhandled_event_times[unhandled_event_name][
                            flow_instance_uid
                        ] = event_created_at

    # Now, fill in 'event_created_at' for 'FlowStarted' and 'FlowFinished' events missing it
    for event in events:
        if isinstance(event, InternalEvent):
            if event.name in ("FlowStarted", "FlowFinished"):
                event_arguments = event.arguments
                event_created_at = event_arguments.get("event_created_at")
                if not event_created_at:
                    flow_instance_uid = event_arguments.get("flow_instance_uid")
                    if (
                        flow_instance_uid
                        and flow_instance_uid in unhandled_event_times[event.name]
                    ):
                        # Fill in the missing 'event_created_at' from the UnhandledEvent
                        event.arguments["event_created_at"] = unhandled_event_times[
                            event.name
                        ][flow_instance_uid]
