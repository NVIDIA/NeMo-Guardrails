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

import os
import re
import time
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timezone
from typing import List, Optional

from rich.progress import Progress
from rich.text import Text

from nemoguardrails import LLMRails, RailsConfig
from nemoguardrails.actions.llm.utils import llm_call
from nemoguardrails.context import llm_call_info_var
from nemoguardrails.eval.models import (
    ComplianceCheckLog,
    ComplianceCheckResult,
    EvalConfig,
    EvalOutput,
    InteractionLog,
    InteractionOutput,
    InteractionSet,
)
from nemoguardrails.eval.ui.utils import EvalData
from nemoguardrails.llm.params import llm_params
from nemoguardrails.llm.taskmanager import LLMTaskManager
from nemoguardrails.logging.explain import LLMCallInfo
from nemoguardrails.rails.llm.config import Model
from nemoguardrails.utils import console, new_uuid

executor = ThreadPoolExecutor(max_workers=1)


class LLMJudgeComplianceChecker:
    """LLM Judge compliance checker."""

    def __init__(
        self,
        eval_config_path: str,
        output_paths: List[str],
        llm_judge_model: Optional[str] = None,
        policy_ids: Optional[List[str]] = None,
        multi_check: bool = False,
        verbose: bool = False,
        force: bool = False,
        reset: bool = False,
    ):
        """Constructor.

        Args:
            eval_config_path: The path to the evaluation config.
            output_paths: The list of output paths to be checked.
            llm_judge_model: The name of the model to be used as an LLM judge.
            policy_ids: The list of policies to be checked for compliance.
            multi_check: Whether to check compliance for multiple policies at once, in a single LLM call.
            verbose: Whether the output should be verbose.
            force: Whether to force compliance check even when a result exists.
            reset: Whether to reset compliance check data.
        """
        self.eval_config_path = eval_config_path
        self.output_paths = output_paths
        self.llm_judge_model = llm_judge_model
        self.policy_ids = policy_ids
        self.multi_check = multi_check
        self.verbose = verbose
        self.force = force
        self.reset = reset

        # Extract the policies from the configuration
        self.eval_config_path = os.path.abspath(self.eval_config_path)
        self.eval_config = EvalConfig.from_path(eval_config_path)
        self.policies = self.eval_config.policies
        self.policy_by_id = {}

        for policy in self.policies:
            self.policy_by_id[policy.id] = policy

        # If we don't have any policy ids specified, we assume all policies
        if not self.policy_ids:
            self.policy_ids = [policy.id for policy in self.policies]
            console.print(f"Checking all policies: {policy_ids}")

        # Initialize the LLM judge model
        model_config = None
        for _model_config in self.eval_config.models:
            if self.llm_judge_model in [
                _model_config.model,
                f"{_model_config.engine}/{_model_config.model}",
            ]:
                model_config = _model_config
                break

        if model_config is None:
            console.print(
                f"The model `{self.llm_judge_model}` is not defined in the evaluation configuration."
            )
            exit(1)

        model_cls, kwargs = LLMRails.get_model_cls_and_kwargs(model_config)
        self.llm = model_cls(**kwargs)

        # We create a minimal RailsConfig object, so we can initialize an LLMTaskManager.
        # We add a placeholder main model, to avoid some edge case errors when one is not defined.
        _config = RailsConfig(
            models=self.eval_config.models + [Model(type="main", engine="", model="")],
            prompts=self.eval_config.prompts,
        )
        # Initializer the LLMTaskManager
        self.llm_task_manager = LLMTaskManager(config=_config)

        # Global progress bar.
        self.progress = None

        self.eval_data = EvalData(
            eval_config_path=self.eval_config_path,
            eval_config=self.eval_config,
            output_paths=self.output_paths,
            eval_outputs={},
        )

    def print_prompt(self, prompt: str):
        """Helper for printing a prompt."""
        for line in prompt.split("\n"):
            if line.strip() == "[/]":
                continue

            if line.startswith("[cyan]") and line.endswith("[/]"):
                text = Text(line[6:-3], style="maroon")
            else:
                text = Text(
                    line,
                    style="black on #909090",
                )

            text.pad_right(console.width)
            self.progress.print(text)

    def print_completion(self, completion: str):
        """Helper to print a completion."""
        for line in completion.split("\n"):
            text = Text(line, style="black on #006600")
            text.pad_right(console.width)
            self.progress.print(text)

    async def check_interaction_compliance(
        self,
        interaction_output: InteractionOutput,
        interaction_log: InteractionLog,
        interaction_set: InteractionSet,
    ) -> bool:
        """Check the compliance for the provided interaction.

        The interaction output and log are updated in accordance with the check.

        Args:
            interaction_output: The output from the interaction.
            interaction_log: The detailed log for the interaction.
            interaction_set: The corresponding interaction set.

        Returns:
            True if there were any changes.
        """
        has_changed = False

        # Check if we need to reset the compliance check data
        if self.reset:
            interaction_output.compliance_checks = []
            interaction_log.compliance_checks = []
            has_changed = True

        if self.multi_check:
            console.print("Multi-mode not supported yet.")
        else:
            for policy_id in self.policy_ids:
                # First, we check if the policy is applicable to this interaction

                # If a policy has an expected output, we consider it implicitly
                # to be included, even if it has apply_to_all set to False.
                implicitly_include_policies = []
                for item in interaction_set.expected_output:
                    implicitly_include_policies.append(item.policy)

                if (
                    not self.policy_by_id[policy_id].apply_to_all
                    and policy_id not in interaction_set.include_policies
                    and policy_id not in implicitly_include_policies
                ) or policy_id in interaction_set.exclude_policies:
                    # We need to skip the check, but update the status if not already
                    if interaction_output.compliance.get(policy_id) is None:
                        interaction_output.compliance[policy_id] = "n/a"
                        has_changed = True
                    elif interaction_output.compliance[policy_id] != "n/a":
                        self.progress.print(
                            f"[orange][b]Warning[/][/] Policy {policy_id} should not be applicable. "
                            f"However, found compliance value of: {interaction_output.compliance[policy_id]}"
                        )
                    self.progress.print(f"Policy [bold]{policy_id}[/] not applicable.")
                    continue

                if interaction_output.compliance.get(policy_id) is not None:
                    if not self.force:
                        self.progress.print(
                            f"Policy [bold]{policy_id}[/] "
                            f"already checked: {interaction_output.compliance.get(policy_id)}."
                        )
                        continue

                task_name = "llm_judge_check_single_policy_compliance"
                t0 = time.time()

                # Initialize the LLMCallInfo object
                llm_call_info = LLMCallInfo(task=task_name)
                llm_call_info_var.set(llm_call_info)

                # Extract the expected output according to this policy, if any
                expected_output = "\n".join(
                    [
                        " - " + str(item)
                        for item in interaction_set.expected_output
                        if item.policy == policy_id
                    ]
                )
                render_context = {
                    "policy": [p for p in self.policies if p.id == policy_id][0],
                    "expected_output": expected_output or None,
                }

                prompt = self.llm_task_manager.render_task_prompt(
                    task=task_name,
                    events=interaction_log.events,
                    context=render_context,
                )
                self.progress.print(f"Checking compliance for [bold]{policy_id}[/]...")

                if self.verbose:
                    self.print_prompt(prompt)

                # We run this with temperature 0 for deterministic results.
                with llm_params(self.llm, temperature=0):
                    result = await llm_call(self.llm, prompt)

                if self.verbose:
                    self.print_completion(result)

                    self.progress.print(
                        f"LLM judge call took {time.time() - t0:.2f} seconds\n"
                    )

                re_result_compliance = (
                    r'\s*Reason: "?([^"]*)"?\nCompliance: "?([^"]*)"?\s*'
                )
                match = re.match(re_result_compliance, result)

                if match is None:
                    # If we're not in verbose mode, we still print the prompt/completion
                    # to provide enough info.
                    if not self.verbose:
                        self.print_prompt(prompt)
                        self.print_completion(result)

                    self.progress.print("[red]Invalid LLM response. Ignoring.[/]")
                else:
                    reason = match.group(1)
                    compliance = match.group(2)
                    if compliance == "Yes":
                        compliance_val = True
                    elif compliance == "No":
                        compliance_val = False
                    elif compliance == "n/a":
                        compliance_val = "n/a"
                    else:
                        # If we're not in verbose mode, we still print the prompt/completion
                        # to provide enough info.
                        if not self.verbose:
                            self.print_prompt(prompt)
                            self.print_completion(result)

                        self.progress.print(
                            f"[red]Invalid compliance value '{compliance}'. Ignoring.[/]"
                        )
                        continue

                    self.progress.print(f"Compliance: {compliance_val}")

                    compliance_check_id = new_uuid()

                    # We record the compliance check.
                    interaction_output.compliance_checks.append(
                        ComplianceCheckResult(
                            id=compliance_check_id,
                            created_at=datetime.now(timezone.utc).isoformat(),
                            interaction_id=interaction_output.id,
                            method=self.llm_judge_model,
                            compliance={policy_id: compliance_val},
                            details=reason,
                        )
                    )

                    # By default, we override any existing value with the new one.
                    # And if there is a difference, we print a warning as well.
                    if (
                        compliance_val is not None
                        and compliance_val
                        != interaction_output.compliance.get(policy_id)
                    ):
                        if interaction_output.compliance.get(policy_id) is not None:
                            self.progress.print(
                                f"[red][b]WARNING[/][/] The compliance value for policy {policy_id} "
                                f"changed from {interaction_output.compliance.get(policy_id)} "
                                f"to {compliance_val}."
                            )

                        interaction_output.compliance[policy_id] = compliance_val

                    interaction_log.compliance_checks.append(
                        ComplianceCheckLog(
                            id=compliance_check_id, llm_calls=[llm_call_info]
                        )
                    )

                    has_changed = True

        return has_changed

    async def run(self):
        """Run the compliance check."""

        for output_path in self.output_paths:
            t0 = time.time()

            console.print(f"Checking {output_path}")

            eval_output = EvalOutput.from_path(output_path)
            self.eval_data.eval_outputs[output_path] = eval_output

            # Create a mapping from id to logs for all interactions
            id_to_log = {}
            for item in eval_output.logs:
                id_to_log[item.id] = item

            # We also create a mapping to the corresponding interaction set
            id_to_interaction_set = {}
            for item in self.eval_config.interactions:
                id_to_interaction_set[item.id] = item

            self.progress = Progress()
            interactions_count = len(eval_output.results)
            with self.progress:
                for i in self.progress.track(
                    range(interactions_count),
                    description=f"Checking {interactions_count} interactions ...",
                ):
                    interaction_output = eval_output.results[i]

                    self.progress.print(
                        f'[{i}] "{interaction_output.input}" -> "{interaction_output.output}"'
                    )

                    has_changed = await self.check_interaction_compliance(
                        interaction_output=interaction_output,
                        interaction_log=id_to_log[interaction_output.id],
                        interaction_set=id_to_interaction_set[
                            interaction_output.id.split("/")[0]
                        ],
                    )

                    # TODO: send this in a separate thread
                    # Only save changes if something has changed
                    if has_changed:
                        # Running this in a separate thread
                        # executor.submit(
                        #     update_results_and_logs, eval_output, output_path
                        # )
                        self.eval_data.update_results_and_logs(output_path)

            # We also do one final save at the end
            self.eval_data.update_results_and_logs(output_path)
            console.print(
                f"The evaluation for {output_path} took {time.time() - t0:.2f} seconds."
            )
