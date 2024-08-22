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

import shlex
from typing import Optional

import typer
from rich.table import Table
from rich.tree import Tree

from nemoguardrails.colang.v2_x.lang.colang_ast import SpecOp, SpecType
from nemoguardrails.colang.v2_x.runtime.flows import FlowState, State
from nemoguardrails.colang.v2_x.runtime.runtime import RuntimeV2_x
from nemoguardrails.utils import console

runtime: Optional[RuntimeV2_x] = None
state: Optional[State] = None

app = typer.Typer(name="!!!", no_args_is_help=True, add_completion=False)


def set_runtime(_runtime: RuntimeV2_x):
    """Registers the runtime that will be used by the debugger."""
    global runtime

    runtime = _runtime


def set_output_state(_state: State):
    """Registers the state that will be used by the debugger."""
    global state
    state = _state


@app.command()
def list_flows(
    active: bool = typer.Option(default=False, help="Only show active flows.")
):
    """List the flows from the current state."""

    table = Table(header_style="bold magenta")

    table.add_column("ID", style="dim", width=12)
    table.add_column("Flow Name")
    table.add_column("Source")

    rows = []
    for flow_id, flow_config in state.flow_configs.items():
        source = flow_config.source_file
        if "nemoguardrails" in source:
            source = source.rsplit("nemoguardrails", 1)[1]

        # if active and state.flow_id_states[flow_id]
        rows.append([flow_id, source])

    rows.sort(key=lambda x: x[0])

    for i, row in enumerate(rows):
        table.add_row(f"{i+1}", *row)

    console.print(table)


@app.command()
def tree():
    """Lists the tree of all active flows."""
    main_flow = state.flow_id_states["main"][0]

    root = Tree("main")
    queue = [[main_flow, root]]

    while queue:
        flow_state: FlowState
        node: Tree
        flow_state, node = queue.pop(0)
        flow_config = state.flow_configs[flow_state.flow_id]
        elements = flow_config.elements

        for child_uid in flow_state.child_flow_uids:
            child_flow_state = state.flow_states[child_uid]
            child_uid_short = child_uid.split(")")[1][0:3] + "..."

            # We also want to figure out if the flow is actually waiting on this child
            waiting_on = False

            for head_id, head in flow_state.active_heads.items():
                head_element = elements[head.position]

                if isinstance(head_element, SpecOp):
                    if head_element.op == "match":
                        if head_element.spec.spec_type == SpecType.REFERENCE:
                            var_name = head_element.spec.var_name
                            var = flow_state.context.get(var_name)

                            if var == child_flow_state:
                                waiting_on = True

            child_flow_label = (
                ("[green]>[/] " if waiting_on else "")
                + child_flow_state.flow_id
                + " "
                + child_uid_short
                + " "
                + child_flow_state.status.value
            )

            child_node = node.add(child_flow_label)
            queue.append([child_flow_state, child_node])

    console.print(root)


def run_command(command: str):
    try:
        if command.strip() == "" or command == "help":
            command = "--help"

        app(shlex.split(command))
    except SystemExit as e:
        # Prevent stopping the app
        pass
