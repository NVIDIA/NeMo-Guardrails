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

import uuid
from datetime import datetime, timezone
from typing import Any, Dict, Optional, Tuple

import yaml


def new_uid() -> str:
    """Helper to create a new UID."""

    return str(uuid.uuid4())


_action_to_modality_info: Dict[str, Tuple[str, str]] = {
    "UtteranceBotAction": ("bot_speech", "replace"),
    "UtteranceUserAction": ("user_speech", "replace"),
}


def _add_modality_info(event_dict: Dict[str, Any]) -> Dict[str, Any]:
    """Add modality related information to the action event"""
    for action_name, modality_info in _action_to_modality_info.items():
        modality_name, modality_policy = modality_info
        if action_name in event_dict["type"]:
            event_dict["action_info_modality"] = modality_name
            event_dict["action_info_modality_policy"] = modality_policy


def _update_action_properties(event_dict: Dict[str, Any]) -> Dict[str, Any]:
    if "Finished" in event_dict["type"]:
        event_dict["event_created_at"] = datetime.now(timezone.utc).isoformat()
        assert (
            "is_success" in event_dict
        ), "***ActionFinished events require is_success field"
        assert (
            event_dict["is_success"] or "failure_reason" in event_dict
        ), "Unsuccessful ***ActionFinished events need to provide 'failure_reason'."

        if event_dict["is_success"] and event_dict["failure_reason"]:
            del event_dict["failure_reason"]


def new_event_dict(event_type: str, **payload) -> Dict[str, Any]:
    """Helper to create a generic event structure."""

    event: Dict[str, Any] = {
        "type": event_type,
        "uid": new_uid(),
        "event_created_at": datetime.now(timezone.utc).isoformat(),
        "source_uid": "NeMoGuardrails",
    }

    event = {**event, **payload}

    if "Action" in event_type:
        _add_modality_info(event)
        _update_action_properties(event)

    return event


class CustomDumper(yaml.SafeDumper):
    def ignore_aliases(self, data):
        return True

    def increase_indent(self, flow=False, indentless=False):
        return super(CustomDumper, self).increase_indent(flow, False)
