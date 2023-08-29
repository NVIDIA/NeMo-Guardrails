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

from __future__ import annotations

from typing import Any, Dict, List

from nemoguardrails.utils import new_event_dict

# TODO: Check if we should have both: flow_id and flow_state_uid in events


# def create_start_flow_internal_event(
#     flow_id: str, parent_flow_state_uid: str, matching_scores: List[float]
# ) -> dict:
#     """Returns 'AbortFlow' internal event"""
#     event = {
#         "type": "StartFlow",
#         "flow_id": flow_id,
#         "parent_flow_uid": parent_flow_state_uid,
#         "matching_scores": matching_scores,
#     }
#     return event


def create_abort_flow_internal_event(
    flow_instance_uid: str, source_flow_instance_uid: str, matching_scores: List[float]
) -> dict:
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
) -> dict:
    """Returns 'FlowStarted' internal event"""
    return create_internal_event(
        "FlowStarted",
        {"source_flow_instance_uid": source_flow_instance_uid},
        matching_scores,
    )


def create_flow_finished_internal_event(
    source_flow_instance_uid: str, matching_scores: List[float]
) -> dict:
    """Returns 'FlowFinished' internal event"""
    return create_internal_event(
        "FlowFinished",
        {"source_flow_instance_uid": source_flow_instance_uid},
        matching_scores,
    )


def create_flow_failed_internal_event(
    source_flow_instance_uid: str, matching_scores: List[float]
) -> dict:
    """Returns 'FlowFailed' internal event"""
    return create_internal_event(
        "FlowFailed",
        {"source_flow_instance_uid": source_flow_instance_uid},
        matching_scores,
    )


def create_internal_event(
    event_type: str, event_args: Any, matching_scores: List[float]
) -> Dict[str, Any]:
    """Returns an internal event for the provided event data"""
    event: Dict[str, Any] = {"type": event_type, "matching_scores": matching_scores}
    # TODO: Find a better way of handling double quotation marks than just stripping them
    # Will probably want to evaluate expressions at some point
    for key in event_args:
        val = event_args[key]
        if isinstance(val, str):
            event_args[key] = val.strip("\"'")
    event = {**event, **event_args}
    return event


def create_umim_action_event(event_type: str, event_args: Any) -> Dict[str, Any]:
    """Returns an outgoing UMIM event for the provided action data"""
    return new_event_dict(event_type, **event_args)
