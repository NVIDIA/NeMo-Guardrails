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
from abc import abstractmethod
from typing import Any, Callable, List, Optional, Tuple

from nemoguardrails.actions.action_dispatcher import ActionDispatcher
from nemoguardrails.llm.taskmanager import LLMTaskManager
from nemoguardrails.rails.llm.config import RailsConfig

log = logging.getLogger(__name__)


class Runtime:
    """Base Colang Runtime implementation."""

    def __init__(self, config: RailsConfig, verbose: bool = False):
        self.config = config
        self.verbose = verbose

        # Register the actions with the dispatcher.
        self.action_dispatcher = ActionDispatcher(config_path=config.config_path)

        # The list of additional parameters that can be passed to the actions.
        self.registered_action_params: dict = {}

        self._init_flow_configs()

        # Initialize the prompt renderer as well.
        self.llm_task_manager = LLMTaskManager(config)

    @abstractmethod
    def _init_flow_configs(self) -> None:
        pass

    def register_action(
        self, action: Callable, name: Optional[str] = None, override: bool = True
    ) -> None:
        """Registers an action with the given name.

        :param name: The name of the action.
        :param action: The action function.
        :param override: If an action already exists, whether it should be overriden or not.
        """
        self.action_dispatcher.register_action(action, name, override=override)

    def register_actions(self, actions_obj: Any, override: bool = True) -> None:
        """Registers all the actions from the given object."""
        self.action_dispatcher.register_actions(actions_obj, override=override)

    @property
    def registered_actions(self) -> dict:
        """Return registered actions."""
        return self.action_dispatcher.registered_actions

    def register_action_param(self, name: str, value: Any) -> None:
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

    async def process_events(
        self, events: List[dict], state: Optional[dict] = None
    ) -> Tuple[List[dict], Any]:
        """Process a sequence of events in a given state.

        The events will be processed one by one, in the input order.

        Args:
            events: A sequence of events that needs to be processed.
            state: The state that should be used as the starting point. If not provided,
              a clean state will be used.

        Returns:
            (output_events, output_state) Returns a sequence of output events and an output
              state.
        """
        raise NotImplementedError()
