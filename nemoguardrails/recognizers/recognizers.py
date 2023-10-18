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
from typing import List, Optional

import requests

from nemoguardrails.actions.actions import ActionResult, action
from nemoguardrails.rails.llm.config import RailsConfig


def recognizer(name: Optional[str] = None):
    """Decorator that sets the meta data
    for identification of PII recognizers
    in modules"""

    def decorator(fn_or_cls):
        fn_or_cls.recognizer_meta = {"name": name or fn_or_cls.__name__}
        return fn_or_cls

    return decorator
