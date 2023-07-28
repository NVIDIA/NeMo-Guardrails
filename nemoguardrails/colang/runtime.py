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
import uuid
from typing import List, Optional

from nemoguardrails.actions.action_dispatcher import ActionDispatcher
from nemoguardrails.colang.v1_0.runtime.flows import FlowConfig
from nemoguardrails.llm.taskmanager import LLMTaskManager
from nemoguardrails.rails.llm.config import RailsConfig

log = logging.getLogger(__name__)


class Runtime:
    """Base Colang Runtime implementation."""

    def __init__(self, config: RailsConfig, verbose: bool = False):
        self.config = config
        self.verbose = verbose

        # The dictionary of registered actions, initialized with default ones.
        self.registered_actions = {}

        # Register the actions with the dispatcher.
        self.action_dispatcher = ActionDispatcher(config_path=config.config_path)
        for action_name, action_fn in self.registered_actions.items():
            self.action_dispatcher.register_action(action_fn, action_name)

        # The list of additional parameters that can be passed to the actions.
        self.registered_action_params = {}

        self._init_flow_configs()

        # Initialize the prompt renderer as well.
        self.llm_task_manager = LLMTaskManager(config)

    def _load_flow_config(self, flow: dict):
        """Loads a flow into the list of flow configurations."""
        elements = flow["elements"]

        # If we have an element with meta information, we move the relevant properties
        # to top level.
        if elements and elements[0].get("_type") == "meta":
            meta_data = elements[0]["meta"]

            if "priority" in meta_data:
                flow["priority"] = meta_data["priority"]
            if "is_extension" in meta_data:
                flow["is_extension"] = meta_data["is_extension"]
            if "interruptable" in meta_data:
                flow["is_interruptible"] = meta_data["interruptable"]

            # Finally, remove the meta element
            elements = elements[1:]

        # If we don't have an id, we generate a random UID.
        flow_id = flow.get("id") or str(uuid.uuid4())

        self.flow_configs[flow_id] = FlowConfig(
            id=flow_id,
            elements=elements,
            priority=flow.get("priority", 1.0),
            is_extension=flow.get("is_extension", False),
            is_interruptible=flow.get("is_interruptible", True),
            source_code=flow.get("source_code"),
        )

        # We also compute what types of events can trigger this flow, in addition
        # to the default ones.
        for element in elements:
            if element.get("UtteranceUserActionFinished"):
                self.flow_configs[flow_id].trigger_event_types.append(
                    "UtteranceUserActionFinished"
                )

    def _init_flow_configs(self):
        """Initializes the flow configs based on the config."""
        self.flow_configs = {}

        for flow in self.config.flows:
            self._load_flow_config(flow)

    def register_action(self, action: callable, name: Optional[str] = None):
        """Registers an action with the given name.

        :param name: The name of the action.
        :param action: The action function.
        """
        self.action_dispatcher.register_action(action, name)

    def register_actions(self, actions_obj: any):
        """Registers all the actions from the given object."""
        self.action_dispatcher.register_actions(actions_obj)

    def register_action_param(self, name: str, value: any):
        """Registers an additional parameter that can be passed to the actions.

        :param name: The name of the parameter.
        :param value: The value of the parameter.
        """
        self.registered_action_params[name] = value

    async def generate_events(self, events: List[dict]) -> List[dict]:
        """Generates the next events based on the provided history.

        This is a wrapper around the `process_events` method, that will keep
        processing the events until the `listen` event is produced.

        :return: The list of events.
        """
        raise NotImplementedError()
