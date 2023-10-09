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
import asyncio
import inspect
import logging
import re
from typing import Any, Dict, List, Optional, Tuple
from urllib.parse import urljoin

import aiohttp
from langchain.chains.base import Chain

from nemoguardrails.actions.actions import ActionResult
from nemoguardrails.colang import parse_colang_file
from nemoguardrails.colang.runtime import Runtime
from nemoguardrails.colang.v1_1.runtime.flows import (
    FlowConfig,
    FlowEvent,
    State,
    add_new_flow_instance,
    create_flow_instance,
    expand_elements,
    initialize_flow,
    run_to_completion,
)
from nemoguardrails.rails.llm.config import RailsConfig
from nemoguardrails.utils import new_event_dict

log = logging.getLogger(__name__)


class RuntimeV1_1(Runtime):
    """Runtime for executing the guardrails."""

    def __init__(self, config: RailsConfig, verbose: bool = False):
        super().__init__(config, verbose)

        self.state: Optional[State] = None

        # Register local system actions
        self.register_action(self._add_flows_action, "AddFlowsAction", False)

    async def _add_flows_action(self, **args):
        log.info(f"Start AddFlowsAction! {args}")
        flow_content = args["config"]
        # Parse new flow
        try:
            parsed_flow = parse_colang_file(
                filename="",
                content=flow_content,
                include_source_mapping=False,
                version="1.1",
            )
        except Exception as e:
            log.warning(f"Could not parse the colang content! {e}")
            raise Exception(f"Could not parse the colang content! {e}")

        added_flows: List[str] = []
        for flow in parsed_flow["flows"]:
            if flow.name in self.state.flow_configs:
                log.warning(f"Flow '{flow.name}' already exists!")
                break

            flow_config = FlowConfig(
                id=flow.name,
                loop_id=None,
                elements=expand_elements(flow.elements, self.state.flow_configs),
                parameters=flow.parameters,
            )

            initialize_flow(self, flow_config)

            # Add flow config to state.flow_configs
            self.state.flow_configs.update({flow.name: flow_config})

            # Create an instance of the flow in flow_states
            add_new_flow_instance(
                self.state, create_flow_instance(self.state.flow_configs[flow.name])
            )

            added_flows.append(flow.name)

        return added_flows

    def _init_flow_configs(self):
        """Initializes the flow configs based on the config."""
        self.flow_configs = {}

        for flow in self.config.flows:
            flow_id = flow.name
            self.flow_configs[flow_id] = FlowConfig(
                id=flow_id, elements=flow.elements, parameters=flow.parameters
            )

    async def generate_events(self, events: List[dict]) -> List[dict]:
        raise Exception("Stateless API not supported for Colang 1.1, yet.")

    @staticmethod
    def _internal_error_action_result(message: str):
        """Helper to construct an action result for an internal error."""
        return ActionResult(
            events=[
                {
                    "type": "BotIntent",
                    "intent": "inform internal error occurred",
                },
                {
                    "type": "StartUtteranceBotAction",
                    "script": message,
                },
                # We also want to hide this from now from the history moving forward
                {"type": "hide_prev_turn"},
            ]
        )

    async def _process_start_action(
        self,
        action_name: str,
        action_params: dict,
        context: dict,
        events: List[dict],
        state: "State",
    ) -> Tuple[Any, List[dict], dict]:
        """Starts the specified action, waits for it to finish and posts back the result."""

        fn = self.action_dispatcher.get_action(action_name)

        # TODO: check action is available in action server
        if fn is None:
            result = self._internal_error_action_result(
                f"Action '{action_name}' not found."
            )
        else:
            # We pass all the parameters that are passed explicitly to the action.
            kwargs = {**action_params}

            action_meta = getattr(fn, "action_meta", {})

            parameters = []
            action_type = "class"

            if inspect.isfunction(fn) or inspect.ismethod(fn):
                # We also add the "special" parameters.
                parameters = inspect.signature(fn).parameters
                action_type = "function"

            elif isinstance(fn, Chain):
                # If we're dealing with a chain, we list the annotations
                # TODO: make some additional type checking here
                parameters = fn.input_keys
                action_type = "chain"

            # For every parameter that start with "__context__", we pass the value
            for parameter_name in parameters:
                if parameter_name.startswith("__context__"):
                    var_name = parameter_name[11:]
                    kwargs[parameter_name] = context.get(var_name)

            # If there are parameters which are variables, we replace with actual values.
            for k, v in kwargs.items():
                if isinstance(v, str) and v.startswith("$"):
                    var_name = v[1:]
                    if var_name in context:
                        kwargs[k] = context[var_name]

            # If we have an action server, we use it for non-system/non-chain actions
            if (
                self.config.actions_server_url
                and not action_meta.get("is_system_action")
                and action_type != "chain"
            ):
                result, status = await self._get_action_resp(
                    action_meta, action_name, kwargs
                )
            else:
                # We don't send these to the actions server;
                # TODO: determine if we should
                if "events" in parameters:
                    kwargs["events"] = events

                if "context" in parameters:
                    kwargs["context"] = context

                if "config" in parameters:
                    kwargs["config"] = self.config

                if "llm_task_manager" in parameters:
                    kwargs["llm_task_manager"] = self.llm_task_manager

                if "state" in parameters:
                    kwargs["state"] = state

                # Add any additional registered parameters
                for k, v in self.registered_action_params.items():
                    if k in parameters:
                        kwargs[k] = v

                if (
                    "llm" in kwargs
                    and f"{action_name}_llm" in self.registered_action_params
                ):
                    kwargs["llm"] = self.registered_action_params[f"{action_name}_llm"]

                log.info("Executing action :: %s", action_name)
                # NOTE (schuellc): We need to make this non-blocking with internal events
                result, status = await self.action_dispatcher.execute_action(
                    action_name, kwargs
                )

            # If the action execution failed, we return a hardcoded message
            if status == "failed":
                # TODO: make this message configurable.
                result = self._internal_error_action_result(
                    "I'm sorry, an internal error has occurred."
                )

        return_value = result
        return_events = []
        context_updates = {}

        if isinstance(result, ActionResult):
            return_value = result.return_value
            return_events = result.events
            context_updates.update(result.context_updates)

        # next_steps = []
        #
        # if context_updates:
        #     # We check if at least one key changed
        #     changes = False
        #     for k, v in context_updates.items():
        #         if context.get(k) != v:
        #             changes = True
        #             break
        #
        #     if changes:
        #         next_steps.append(new_event_dict("ContextUpdate", data=context_updates))
        #
        # # If the action returned additional events, we also add them to the next steps.
        # if return_events:
        #     next_steps.extend(return_events)

        return return_value, return_events, context_updates

    async def _get_action_resp(
        self, action_meta: Dict[str, Any], action_name: str, kwargs: Dict[str, Any]
    ) -> Tuple[Dict[str, Any], str]:
        """Interact with actions and get response from action-server and system actions."""
        result, status = {}, "failed"  # default response
        try:
            # Call the Actions Server if it is available.
            # But not for system actions, those should still run locally.
            if (
                action_meta.get("is_system_action", False)
                or self.config.actions_server_url is None
            ):
                result, status = await self.action_dispatcher.execute_action(
                    action_name, kwargs
                )
            else:
                url = urljoin(
                    self.config.actions_server_url, "/v1/actions/run"
                )  # action server execute action path
                data = {"action_name": action_name, "action_parameters": kwargs}
                async with aiohttp.ClientSession() as session:
                    try:
                        async with session.post(url, json=data) as resp:
                            if resp.status != 200:
                                raise ValueError(
                                    f"Got status code {resp.status} while getting response from {action_name}"
                                )

                            resp = await resp.json()
                            result, status = resp.get("result", result), resp.get(
                                "status", status
                            )
                    except Exception as e:
                        log.info(f"Exception {e} while making request to {action_name}")
                        return result, status

        except Exception as e:
            log.info(f"Failed to get response from {action_name} due to exception {e}")
        return result, status

    async def process_events(
        self, events: List[dict], state: Optional[dict] = None
    ) -> Tuple[List[dict], dict]:
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

        output_events = []
        input_events = events.copy()
        local_running_actions = []

        if state is None:
            state = State(context={}, flow_states={}, flow_configs=self.flow_configs)
            state.initialize()
            input_event = FlowEvent(name="StartFlow", arguments={"flow_id": "main"})
            input_events.insert(0, input_event)
            log.info("Start of story!")
        else:
            if isinstance(state, dict):
                state = State.from_dict(state)

        self.state = state

        # While we have input events to process, or there are local running actions
        # we continue the processing.
        while input_events or local_running_actions:
            # First, we process all events
            for event in input_events:
                log.info(f"Processing event {event}")

                # Record the event that we're about to process
                state.last_events.append(event)

                run_to_completion(state, event)

                # If we have context updates after this event, we first add that.
                if state.context_updates:
                    output_events.append(
                        new_event_dict("ContextUpdate", data=state.context_updates)
                    )

                for out_event in state.outgoing_events:
                    # We also record the out events in the recent history.
                    state.last_events.append(out_event)

                    # We need to check if we need to run a locally registered action
                    start_action_match = re.match(r"Start(.*Action)", out_event["type"])
                    if start_action_match:
                        action_name = start_action_match[1]

                        if action_name in self.action_dispatcher.registered_actions:
                            # In this case we need to start the action asynchronously

                            # Start the local action
                            local_action = asyncio.create_task(
                                self._run_action(
                                    action_name,
                                    start_action_event=out_event,
                                    events_history=state.last_events,
                                    state=state,
                                )
                            )
                            local_running_actions.append(local_action)
                        else:
                            output_events.append(out_event)
                    else:
                        output_events.append(out_event)

            # We clear the input events
            input_events = []

            # If we have any local running actions, we need to wait for at least one
            # of them to finish.
            if local_running_actions:
                log.info(
                    f"Waiting for {len(local_running_actions)} local actions to finish."
                )
                done, pending = await asyncio.wait(
                    local_running_actions, return_when=asyncio.FIRST_COMPLETED
                )
                log.info(f"{len(done)} actions finished.")

                for finished_task in done:
                    local_running_actions.remove(finished_task)
                    result = finished_task.result()

                    # We need to create the corresponding action finished event
                    action_finished_event = new_event_dict(
                        f"{result['action_name']}Finished",
                        action_uid=result["start_action_event"]["action_uid"],
                        action_name=result["action_name"],
                        status="success",
                        is_success=True,
                        return_value=result["return_value"],
                        events=result["new_events"],
                        # is_system_action=action_meta.get("is_system_action", False),
                    )
                    input_events.append(action_finished_event)

        # TODO: serialize the state to dict

        # We cap the recent history to the last 100
        state.last_events = state.last_events[-100:]

        return output_events, state

    async def _run_action(
        self,
        action_name: str,
        start_action_event: dict,
        events_history: List[dict],
        state: "State",
    ) -> dict:
        """Runs the locally registered action.

        Args
            action_name: The name of the action to be executed.
            start_action_event: The event that triggered the action.
            events_history: The recent history of events that led to the action being triggerd.
        """

        # NOTE: To extract the actual parameters that should be passed to the local action,
        # we ignore all the keys from "an empty event" of the same type.
        ignore_keys = new_event_dict(start_action_event["type"]).keys()
        action_params = {
            k: v for k, v in start_action_event.items() if k not in ignore_keys
        }

        return_value, new_events, context_updates = await self._process_start_action(
            action_name,
            action_params=action_params,
            context={},
            events=events_history,
            state=state,
        )
        return {
            "action_name": action_name,
            "return_value": return_value,
            "new_events": new_events,
            "context_updates": context_updates,
            "start_action_event": start_action_event,
        }
