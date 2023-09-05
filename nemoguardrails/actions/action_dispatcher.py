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

"""Module for the calling proper action endpoints based on events received at action server endpoint """

import importlib.util
import inspect
import logging
import os
from typing import Any, Dict, List, Optional, Tuple, Union

from langchain.chains.base import Chain

from nemoguardrails.logging.callbacks import logging_callbacks

log = logging.getLogger(__name__)


class ActionDispatcher:
    def __init__(
        self, load_all_actions: bool = True, config_path: Optional[str] = None
    ):
        """Initializes an actions dispatcher.

        :param load_all_actions: When set, it will load all actions in the `actions` folder
          both in the current working directory and in the package.
        :param config_path: The path from which the configuration was loaded. If there are
          actions at the specified path, we load them as well.
        """
        log.info("Initializing action dispatcher")

        self._registered_actions = {}

        if load_all_actions:
            # TODO: check for better way to find actions dir path or use constants.py

            # First, we load all actions from the library
            self.load_actions_from_path(os.path.join(os.path.dirname(__file__), ".."))

            # Next, we load all actions from the current working directory
            # TODO: add support for an explicit ACTIONS_PATH
            self.load_actions_from_path(os.getcwd())

            # Last, but not least, if there was a config path, we try to load actions
            # from there as well.
            if config_path:
                self.load_actions_from_path(config_path)

        log.info(f"Registered Actions: {self._registered_actions}")
        log.info("Action dispatcher initialized")

    @property
    def registered_actions(self):
        return self._registered_actions

    def load_actions_from_path(self, path: str):
        """Loads all actions from the specified path.

        It will load all actions in the `actions.py` file if it exists and all actions
        inside the `actions` folder if it exists.
        """
        actions_path = os.path.join(path, "actions")
        if os.path.exists(actions_path):
            self._registered_actions.update(self._find_actions(actions_path))

        actions_py_path = os.path.join(path, "actions.py")
        if os.path.exists(actions_py_path):
            self._registered_actions.update(
                self._load_actions_from_module(actions_py_path)
            )

    def register_action(
        self, action: callable, name: Optional[str] = None, override: bool = True
    ):
        """Registers an action with the given name.

        :param name: The name of the action.
        :param action: The action function.
        :param override: If an action already exists, whether it should be overriden or not.
        """
        if name is None:
            action_meta = getattr(action, "action_meta", None)
            name = action_meta["name"] if action_meta else action.__name__

        # If we're not allowed to override, we stop.
        if name in self._registered_actions and not override:
            return

        self._registered_actions[name] = action

    def register_actions(self, actions_obj: any, override: bool = True):
        """Registers all the actions from the given object."""
        # Register the actions
        for attr in dir(actions_obj):
            val = getattr(actions_obj, attr)

            if hasattr(val, "action_meta"):
                self.register_action(val, override=override)

    def get_action(self, name: str) -> callable:
        return self._registered_actions.get(name)

    async def execute_action(
        self, action_name: str, params: Dict[str, Any]
    ) -> Tuple[Union[str, Dict[str, Any]], str]:
        """Endpoint called from action server to execute an action.
        This endpoint interacts with different supported actions
        """

        if action_name in self._registered_actions:
            log.info(f"Executing registered action: {action_name}")
            fn = self._registered_actions.get(action_name, None)

            # Actions that are registered as classes are initialized lazy, when
            # they are first used.
            if inspect.isclass(fn):
                fn = fn()
                self._registered_actions[action_name] = fn

            if fn is not None:
                try:
                    # We support both functions and classes as actions
                    if inspect.isfunction(fn) or inspect.ismethod(fn):
                        result = await fn(**params)
                    elif isinstance(fn, Chain):
                        try:
                            chain = fn

                            # For chains with only one output key, we use the `arun` function
                            # to return directly the result.
                            if len(chain.output_keys) == 1:
                                result = await chain.arun(
                                    **params, callbacks=logging_callbacks
                                )
                            else:
                                # Otherwise, we return the dict with the output keys.
                                result = await chain.acall(
                                    inputs=params,
                                    return_only_outputs=True,
                                    callbacks=logging_callbacks,
                                )
                        except NotImplementedError:
                            # Not ideal, but for now we fall back to sync execution
                            # if the async is not available
                            result = fn.run(**params)
                    else:
                        # TODO: there should be a common base class here
                        result = fn.run(**params)
                    return result, "success"
                except Exception as e:
                    log.exception(f"Error {e} while execution {action_name}")

        return None, "failed"

    def get_registered_actions(self) -> List[str]:
        """Endpoint called from action server to get the list of available actions"""
        return list(self._registered_actions.keys())

    @staticmethod
    def _load_actions_from_module(filepath: str):
        """Loads the actions from the specified python module."""
        action_objects = {}
        filename = os.path.basename(filepath)

        try:
            log.debug(f"Analyzing file {filename}")
            # Import the module from the file

            spec = importlib.util.spec_from_file_location(filename, filepath)
            module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(module)

            # Loop through all members in the module and check for the `@action` decorator
            # If class has action decorator is_action class member is true
            for name, obj in inspect.getmembers(module):
                if inspect.isfunction(obj) and hasattr(obj, "action_meta"):
                    log.info(f"Adding {obj.__name__} to actions")
                    action_objects[obj.action_meta["name"]] = obj

                if inspect.isclass(obj) and hasattr(obj, "action_meta"):
                    try:
                        action_objects[obj.action_meta["name"]] = obj
                        log.info(f"Added {obj.action_meta['name']} to actions")
                    except Exception as e:
                        log.debug(
                            f"Failed to register {obj.action_meta['name']} in action dispatcher due to exception {e}"
                        )
        except Exception as e:
            log.debug(
                f"Failed to register {filename} in action dispatcher due to exception {e}"
            )

        return action_objects

    @staticmethod
    def _find_actions(directory) -> Dict:
        """Loop through all the subdirectories and check for the class with @action
        decorator and add in action_classes dict
        """
        action_objects = {}

        if not os.path.exists(directory):
            return action_objects

        # Loop through all files in the directory and its subdirectories
        for root, dirs, files in os.walk(directory):
            for filename in files:
                if filename.endswith(".py"):
                    filepath = os.path.join(root, filename)
                    action_objects.update(
                        ActionDispatcher._load_actions_from_module(filepath)
                    )

        return action_objects
