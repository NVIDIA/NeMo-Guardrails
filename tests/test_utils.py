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

from nemoguardrails.utils import new_event_dict


def test_event_generation():
    event_type = "UserIntent"
    user_intent = "user greets bot"
    e = new_event_dict(event_type, intent=user_intent)

    assert "event_created_at" in e
    assert "source_uid" in e
    assert e["type"] == event_type
    assert e["intent"] == user_intent


def test_action_event_generation():
    event_type = "StartUtteranceBotAction"
    script = "Hello. Nice to see you!"
    intensity = 0.5
    e = new_event_dict(event_type, script=script, intensity=intensity)

    assert "event_created_at" in e
    assert "source_uid" in e
    assert e["type"] == event_type
    assert e["script"] == script
    assert e["intensity"] == intensity
    assert e["action_info_modality"] == "bot_speech"
    assert e["action_info_modality_policy"] == "replace"
