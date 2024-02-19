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
from typing import Any, Dict, List, Optional, Tuple, Union
from urllib.parse import urljoin

import aiohttp
import langchain
from langchain.chains.base import Chain

from nemoguardrails.actions.actions import ActionResult
from nemoguardrails.colang import parse_colang_file
from nemoguardrails.colang.runtime import Runtime
from nemoguardrails.colang.v2_x.lang.colang_ast import Flow
from nemoguardrails.colang.v2_x.runtime.flows import (
    ColangRuntimeError,
    Event,
    FlowStatus,
)
from nemoguardrails.colang.v2_x.runtime.statemachine import (
    FlowConfig,
    InternalEvent,
    State,
    expand_elements,
    initialize_flow,
    initialize_state,
    run_to_completion,
)
from nemoguardrails.rails.llm.config import RailsConfig
from nemoguardrails.utils import new_event_dict

langchain.debug = False

log = logging.getLogger(__name__)


class RuntimeV2_x(Runtime):
    """Runtime for executing the guardrails."""

    def __init__(self, config: RailsConfig, verbose: bool = False):
        super().__init__(config, verbose)

        # Register local system actions
        self.register_action(self._add_flows_action, "AddFlowsAction", False)
        self.register_action(self._remove_flows_action, "RemoveFlowsAction", False)

        # Maps main_flow.uid to a dictionary of actions that are run locally, asynchronously.
        # Dict[main_flow_uid, Dict[action_uid, action_data]]
        self.async_actions: Dict[str, List] = {}

        # A way to disable async function execution. Useful for testing.
        self.disable_async_execution = False

    async def _add_flows_action(self, state: "State", **args: dict) -> List[str]:
        log.info("Start AddFlowsAction! %s", args)
        flow_content = args["config"]
        assert isinstance(flow_content, str)
        # Parse new flow
        try:
            parsed_flow = parse_colang_file(
                filename="",
                content=flow_content,
                version="2.x",
                include_source_mapping=True,
            )
        except Exception:
            log.warning("FAILING-FLOW-PARSING\n%s", flow_content, exc_info=True)
            return []
            # Alternatively, we could through an exceptions
            # raise ColangRuntimeError(f"Could not parse the generated Colang code! {ex}")

        added_flows: List[str] = []
        for flow in parsed_flow["flows"]:
            if flow.name in state.flow_configs:
                log.warning("Flow '%s' already exists!", flow.name)
                break

            flow_config = FlowConfig(
                id=flow.name,
                loop_id=None,
                elements=expand_elements(flow.elements, state.flow_configs),
                parameters=flow.parameters,
                source_code=flow.source_code,
            )

            # Print out expanded flow elements
            # json.dump(flow_config, sys.stdout, indent=4, cls=EnhancedJsonEncoder)

            initialize_flow(state, flow_config)

            # Add flow config to state.flow_configs
            state.flow_configs.update({flow.name: flow_config})

            added_flows.append(flow.name)

        return added_flows

    async def _remove_flows_action(self, state: "State", **args: dict) -> None:
        log.info("Start RemoveFlowsAction! %s", args)
        flow_ids = args["flow_ids"]
        # Remove all related flow states
        for flow_id in flow_ids:
            if flow_id in state.flow_id_states:
                for flow_state in state.flow_id_states[flow_id]:
                    del state.flow_states[flow_state.uid]
                del state.flow_id_states[flow_id]
            if flow_id in state.flow_configs:
                del state.flow_configs[flow_id]

    def _init_flow_configs(self) -> None:
        """Initializes the flow configs based on the config."""
        self.flow_configs = {}

        for flow in self.config.flows:
            assert isinstance(flow, Flow)
            flow_id = flow.name
            self.flow_configs[flow_id] = FlowConfig(
                id=flow_id,
                elements=flow.elements,
                parameters=flow.parameters,
                return_members=flow.return_members,
                source_code=flow.source_code,
            )

    async def generate_events(self, events: List[dict]) -> List[dict]:
        raise NotImplementedError("Stateless API not supported for Colang 2.x, yet.")

    @staticmethod
    def _internal_error_action_result(message: str) -> ActionResult:
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
                # NOTE: This has currently no effect in v 2.x, do we need it?
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
        return_events: List[dict] = []
        context_updates: dict = {}

        if isinstance(result, ActionResult):
            return_value = result.return_value
            if result.events is not None:
                return_events = result.events
            if result.context_updates is not None:
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
    ) -> Tuple[Union[str, Dict[str, Any]], str]:
        """Interact with actions and get response from action-server and system actions."""
        # default response
        result: Union[str, Dict[str, Any]] = {}
        status: str = "failed"
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
                        log.info(
                            "Exception %s while making request to %s", e, action_name
                        )
                        return result, status

        except Exception as e:
            error_message = (
                f"Failed to get response from {action_name} due to exception {e}"
            )
            log.info(error_message)
            raise ColangRuntimeError(error_message) from e
        return result, status

    @staticmethod
    def _get_action_finished_event(result: dict) -> Dict[str, Any]:
        """Helper to return the ActionFinished event from the result of running a local action."""
        return new_event_dict(
            f"{result['action_name']}Finished",
            action_uid=result["start_action_event"]["action_uid"],
            action_name=result["action_name"],
            status="success",
            is_success=True,
            return_value=result["return_value"],
            events=result["new_events"],
            # is_system_action=action_meta.get("is_system_action", False),
        )

    async def _get_async_actions_finished_events(
        self, main_flow_uid: str
    ) -> Tuple[List[dict], int]:
        """Helper to return the ActionFinished events for the local async actions that finished.

        Args
            main_flow_uid: The UID of the main flow.

        Returns
            (action_finished_events, pending_counter)
            The array of *ActionFinished events and the pending counter
        """

        pending_actions = self.async_actions.get(main_flow_uid, [])
        if len(pending_actions) == 0:
            return [], 0

        done, pending = await asyncio.wait(
            pending_actions,
            return_when=asyncio.FIRST_COMPLETED,
            timeout=0,
        )
        if len(done) > 0:
            log.info("%s actions finished.", len(done))

        action_finished_events = []
        for finished_task in done:
            try:
                result = finished_task.result()
            except Exception:
                log.warning(
                    "Local action finished with an exception!",
                    exc_info=True,
                )

            self.async_actions[main_flow_uid].remove(finished_task)

            # We need to create the corresponding action finished event
            action_finished_event = self._get_action_finished_event(result)
            action_finished_events.append(action_finished_event)

        return action_finished_events, len(pending)

    async def process_events(
        self, events: List[dict], state: Union[Optional[dict], State] = None
    ) -> Tuple[List[Dict[str, Any]], State]:
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
        input_events: List[Union[dict, InternalEvent]] = events.copy()
        local_running_actions: List[asyncio.Task[dict]] = []

        if state is None:
            state = State(flow_states={}, flow_configs=self.flow_configs)
            initialize_state(state)
        elif isinstance(state, dict):
            # TODO: Implement dict to State conversion
            raise NotImplementedError()
        #     if isinstance(state, dict):
        #         state = State.from_dict(state)

        assert isinstance(state, State)
        assert state.main_flow_state is not None
        main_flow_uid = state.main_flow_state.uid
        if state.main_flow_state.status == FlowStatus.WAITING:
            input_event = InternalEvent(name="StartFlow", arguments={"flow_id": "main"})
            input_events.insert(0, input_event)
            log.info("Start of story!")

        # Check if we have new finished async local action events to add
        (
            local_action_finished_events,
            pending_local_async_action_counter,
        ) = await self._get_async_actions_finished_events(main_flow_uid)
        input_events.extend(local_action_finished_events)
        local_action_finished_events = []
        return_local_async_action_count = False

        # While we have input events to process, or there are local running actions
        # we continue the processing.
        while input_events or local_running_actions:
            for event in input_events:
                log.info("Processing event %s", event)

                event_name = event["type"] if isinstance(event, dict) else event.name

                if event_name == "CheckLocalAsync":
                    return_local_async_action_count = True
                    continue

                # Record the event that we're about to process
                state.last_events.append(event)

                # Advance the state machine
                new_event: Optional[Union[dict, Event]] = event
                while new_event is not None:
                    try:
                        run_to_completion(state, new_event)
                        new_event = None
                    except Exception as e:
                        log.warning("Colang error!", exc_info=True)
                        new_event = Event(
                            name="ColangError",
                            arguments={
                                "error_type": str(type(e).__name__),
                                "error": str(e),
                            },
                        )
                    await asyncio.sleep(0.001)

                # If we have context updates after this event, we first add that.
                # TODO: Check if this is still needed for e.g. stateless implementation
                # if state.context_updates:
                #     output_events.append(
                #         new_event_dict("ContextUpdate", data=state.context_updates)
                #     )

                for out_event in state.outgoing_events:
                    # We also record the out events in the recent history.
                    state.last_events.append(out_event)

                    # We need to check if we need to run a locally registered action
                    start_action_match = re.match(r"Start(.*Action)", out_event["type"])
                    if start_action_match:
                        action_name = start_action_match[1]

                        if action_name in self.action_dispatcher.registered_actions:
                            # In this case we need to start the action locally
                            action_fn = self.action_dispatcher.get_action(action_name)
                            execute_async = getattr(action_fn, "action_meta", {}).get(
                                "execute_async", False
                            )

                            # Start the local action
                            local_action = asyncio.create_task(
                                self._run_action(
                                    action_name,
                                    start_action_event=out_event,
                                    events_history=state.last_events,
                                    state=state,
                                )
                            )

                            # If the function is not async, or async execution is disabled
                            # we execute the actions as a local action.
                            if not execute_async or self.disable_async_execution:
                                local_running_actions.append(local_action)
                            else:
                                main_flow_uid = state.main_flow_state.uid
                                if main_flow_uid not in self.async_actions:
                                    self.async_actions[main_flow_uid] = []
                                self.async_actions[main_flow_uid].append(local_action)

                            # We need to feedback the start events of the local actions
                            input_events.append(out_event)
                        else:
                            output_events.append(out_event)
                    else:
                        output_events.append(out_event)

                # Check if we have new finished async local action events to add
                (
                    new_local_action_finished_events,
                    pending_local_async_action_counter,
                ) = await self._get_async_actions_finished_events(main_flow_uid)
                local_action_finished_events.extend(new_local_action_finished_events)

            # We clear the input events
            input_events = []

            input_events.extend(local_action_finished_events)
            local_action_finished_events = []

            # If we have any local running actions, we need to wait for at least one
            # of them to finish.
            if local_running_actions:
                log.info(
                    "Waiting for %d local actions to finish.",
                    len(local_running_actions),
                )
                done, _pending = await asyncio.wait(
                    local_running_actions, return_when=asyncio.FIRST_COMPLETED
                )
                log.info("%s actions finished.", len(done))

                for finished_task in done:
                    local_running_actions.remove(finished_task)
                    result = finished_task.result()

                    # We need to create the corresponding action finished event
                    action_finished_event = self._get_action_finished_event(result)
                    input_events.append(action_finished_event)

        if return_local_async_action_count:
            # If we have a "CheckLocalAsync" event, we return the number of
            # pending local async actions that have not yet finished executing
            log.debug(
                "Checking if there are any local async actions that have finished."
            )
            output_events.append(
                new_event_dict(
                    "LocalAsyncCounter", counter=pending_local_async_action_counter
                )
            )

        # TODO: serialize the state to dict

        # We cap the recent history to the last 500
        state.last_events = state.last_events[-500:]

        return output_events, state

    async def _run_action(
        self,
        action_name: str,
        start_action_event: dict,
        events_history: List[Union[dict, Event]],
        state: "State",
    ) -> dict:
        """Runs the locally registered action.

        Args
            action_name: The name of the action to be executed.
            start_action_event: The event that triggered the action.
            events_history: The recent history of events that led to the action being triggered.
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
            context=state.context,
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
