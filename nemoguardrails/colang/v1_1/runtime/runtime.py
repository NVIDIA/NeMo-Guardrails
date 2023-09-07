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

import inspect
import logging
from textwrap import indent
from typing import Any, Dict, List, Optional, Tuple
from urllib.parse import urljoin

import aiohttp
from langchain.chains.base import Chain

from nemoguardrails.actions.actions import ActionResult
from nemoguardrails.colang import parse_colang_file
from nemoguardrails.colang.runtime import Runtime
from nemoguardrails.colang.v1_1.runtime.flows import (
    FlowConfig,
    State,
    compute_context,
    compute_next_events,
    compute_next_state,
)
from nemoguardrails.utils import new_event_dict

log = logging.getLogger(__name__)


class RuntimeV1_1(Runtime):
    """Runtime for executing the guardrails."""

    def _init_flow_configs(self):
        """Initializes the flow configs based on the config."""
        self.flow_configs = {}

        for flow in self.config.flows:
            flow_id = flow.name
            self.flow_configs[flow_id] = FlowConfig(id=flow_id, elements=flow.elements)

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

    async def _process_start_action(self, events: List[dict]) -> List[dict]:
        """Starts the specified action, waits for it to finish and posts back the result."""

        event = events[-1]

        action_name = event["action_name"]
        action_params = event["action_params"]
        action_result_key = event["action_result_key"]

        context = {}
        action_meta = {}

        fn = self.action_dispatcher.get_action(action_name)

        # TODO: check action is available in action server
        if fn is None:
            status = "failed"
            result = self._internal_error_action_result(
                f"Action '{action_name}' not found."
            )

        else:
            context = compute_context(events)

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

        # If we have an action result key, we also record the update.
        if action_result_key:
            context_updates[action_result_key] = return_value

        next_steps = []

        if context_updates:
            # We check if at least one key changed
            changes = False
            for k, v in context_updates.items():
                if context.get(k) != v:
                    changes = True
                    break

            if changes:
                next_steps.append(new_event_dict("ContextUpdate", data=context_updates))

        next_steps.append(
            new_event_dict(
                "InternalSystemActionFinished",
                action_name=action_name,
                action_params=action_params,
                action_result_key=action_result_key,
                status=status,
                is_success=status != "failed",
                failure_reason=status,
                return_value=return_value,
                events=return_events,
                is_system_action=action_meta.get("is_system_action", False),
            )
        )

        # If the action returned additional events, we also add them to the next steps.
        if return_events:
            next_steps.extend(return_events)

        return next_steps

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

    async def _process_start_flow(self, events: List[dict]) -> List[dict]:
        """Starts a flow."""

        event = events[-1]

        flow_id = event["flow_id"]

        # Up to this point, the body will be the sequence of instructions.
        # We need to alter it to be an actual flow definition, i.e., add `define flow xxx`
        # and intent the body.
        body = event["flow_body"]
        body = "define flow " + flow_id + ":\n" + indent(body, "  ")

        # We parse the flow
        parsed_data = parse_colang_file("dynamic.co", content=body)

        assert len(parsed_data["flows"]) == 1
        flow = parsed_data["flows"][0]

        # To make sure that the flow will start now, we add a start_flow element at
        # the beginning as well.
        flow["elements"].insert(0, {"_type": "start_flow", "flow_id": flow_id})

        # We add the flow to the list of flows.
        self._load_flow_config(flow)

        # And we compute the next steps. The new flow should match the current event,
        # and start.
        next_steps = await self._compute_next_steps(events)

        return next_steps

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

        if state is None:
            state = State(context={}, flow_states={}, flow_configs=self.flow_configs)
            state.initialize()
        else:
            if isinstance(state, dict):
                state = State.from_dict(state)

        output_events = []
        for event in events:
            state = compute_next_state(state, event)

            # If we have context updates after this event, we first add that.
            if state.context_updates:
                output_events.append(
                    new_event_dict("ContextUpdate", data=state.context_updates)
                )

            for out_event in state.outgoing_events:
                output_events.append(out_event)

        # TODO: serialize the state to dict
        return output_events, state
