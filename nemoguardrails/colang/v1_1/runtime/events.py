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

from typing import TYPE_CHECKING, List

if TYPE_CHECKING:
    from nemoguardrails.colang.v1_1.runtime.flows import FlowState

# TODO: Check if we should have both: flow_id and flow_state_uid in events


def create_start_flow_internal_event(
    flow_id: str, parent_flow_state_uid: str, matching_scores: List[float]
) -> dict:
    """Returns 'AbortFlow' internal event"""
    event = {
        "type": "StartFlow",
        "flow_id": flow_id,
        "parent_flow_uid": parent_flow_state_uid,
        "matching_scores": matching_scores,
    }
    return event


def create_abort_flow_internal_event(
    flow_state_uid: str, matching_scores: List[float]
) -> dict:
    """Returns 'AbortFlow' internal event"""
    event = {
        "type": "AbortFlow",
        "flow_state_uid": flow_state_uid,
        "matching_scores": matching_scores,
    }
    return event


def create_flow_started_internal_event(
    flow_state_uid: str, matching_scores: List[float]
) -> dict:
    """Returns 'FlowStarted' internal event"""
    event = {
        "type": "FlowStarted",
        "flow_state_uid": flow_state_uid,
        "matching_scores": matching_scores,
    }
    return event


def create_flow_finished_internal_event(
    flow_state_uid: str, matching_scores: List[float]
) -> dict:
    """Returns 'FlowFinished' internal event"""
    event = {
        "type": "FlowFinished",
        "flow_state_uid": flow_state_uid,
        "matching_scores": matching_scores,
    }
    return event


def create_flow_failed_internal_event(
    flow_state_uid: str, matching_scores: List[float]
) -> dict:
    """Returns 'FlowFailed' internal event"""
    event = {
        "type": "FlowFailed",
        "flow_state_uid": flow_state_uid,
        "matching_scores": matching_scores,
    }
    return event
