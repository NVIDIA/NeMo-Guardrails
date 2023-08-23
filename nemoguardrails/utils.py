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
from collections import namedtuple
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any, Callable, Dict, Optional, Tuple


def new_uid() -> str:
    """Helper to create a new UID."""

    return str(uuid.uuid4())


# Very basic event validation - will be replaced by validation based on pydantic models
Property = namedtuple("Property", ["name", "type"])
Validator = namedtuple("Validator", ["description", "function"])


def _has_property(e: Dict[str, Any], p: Property) -> bool:
    return p.name in e and type(e[p.name]) == p.type


_event_validators = [
    Validator("Events need to provide 'type'", lambda e: "type" in e),
    Validator(
        "Events need to provide 'uid'", lambda e: _has_property(e, Property("uid", str))
    ),
    Validator(
        "Events need to provide 'event_created_at' of type 'str'",
        lambda e: _has_property(e, Property("event_created_at", str)),
    ),
    Validator(
        "Events need to provide 'source_uid' of type 'str'",
        lambda e: _has_property(e, Property("source_uid", str)),
    ),
    Validator(
        "***Action events need to provide an 'action_uid' of type 'str'",
        lambda e: "Action" not in e["type"]
        or _has_property(e, Property("action_uid", str)),
    ),
    Validator(
        "***ActionFinished events require 'action_finished_at' field of type 'str'",
        lambda e: "ActionFinished" not in e["type"]
        or _has_property(e, Property("action_finished_at", str)),
    ),
    Validator(
        "***ActionFinished events require 'is_success' field of type 'bool'",
        lambda e: "ActionFinished" not in e["type"]
        or _has_property(e, Property("is_success", bool)),
    ),
    Validator(
        "Unsuccessful ***ActionFinished events need to provide 'failure_reason'.",
        lambda e: "ActionFinished" not in e["type"]
        or (e["is_success"] or "failure_reason" in e),
    ),
    Validator(
        "***StartUtteranceBotAction events need to provide 'script' of type 'str'",
        lambda e: e["type"] != "StartUtteranceBotAction"
        or _has_property(e, Property("script", str)),
    ),
    Validator(
        "***UtteranceBotActionScriptUpdated events need to provide 'interim_script' of type 'str'",
        lambda e: e["type"] != "UtteranceBotActionScriptUpdated "
        or _has_property(e, Property("interim_script", str)),
    ),
    Validator(
        "***UtteranceBotActionFinished events need to provide 'final_script' of type 'str'",
        lambda e: e["type"] != "UtteranceBotActionFinished"
        or _has_property(e, Property("final_script", str)),
    ),
    Validator(
        "***UtteranceUserActionTranscriptUpdated events need to provide 'interim_transcript' of type 'str'",
        lambda e: e["type"] != "UtteranceUserActionTranscriptUpdated"
        or _has_property(e, Property("interim_transcript", str)),
    ),
    Validator(
        "***UtteranceUserActionFinished events need to provide 'final_transcript' of type 'str'",
        lambda e: e["type"] != "UtteranceUserActionFinished"
        or _has_property(e, Property("final_transcript", str)),
    ),
]


_action_to_modality_info: Dict[str, Tuple[str, str]] = {
    "UtteranceBotAction": ("bot_speech", "replace"),
    "UtteranceUserAction": ("user_speech", "replace"),
}


def _add_modality_info(event_dict: Dict[str, Any]) -> None:
    """Add modality related information to the action event"""
    for action_name, modality_info in _action_to_modality_info.items():
        modality_name, modality_policy = modality_info
        if action_name in event_dict["type"]:
            event_dict["action_info_modality"] = modality_name
            event_dict["action_info_modality_policy"] = modality_policy


def _update_action_properties(event_dict: Dict[str, Any]) -> None:
    """Update action related even properties and ensure UMIM compliance (very basic)"""

    if "Started" in event_dict["type"]:
        event_dict["action_started_at"] = datetime.now(timezone.utc).isoformat()
    elif "Start" in event_dict["type"]:
        if "action_uid" not in event_dict:
            event_dict["action_uid"] = new_uid()
    elif "Finished" in event_dict["type"]:
        event_dict["action_finished_at"] = datetime.now(timezone.utc).isoformat()
        if event_dict["is_success"] and "failure_reason" in event_dict:
            del event_dict["failure_reason"]


def ensure_valid_event(event: Dict[str, Any]) -> None:
    """Performs basic event validation and throws an AssertionError if any of the validators fail."""
    for validator in _event_validators:
        assert validator.function(event), validator.description


def is_valid_event(event: Dict[str, Any]) -> bool:
    """Performs a basic event validation and returns True if the event conforms."""
    for validator in _event_validators:
        if not validator.function(event):
            return False
    return True


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

    ensure_valid_event(event)
    return event
