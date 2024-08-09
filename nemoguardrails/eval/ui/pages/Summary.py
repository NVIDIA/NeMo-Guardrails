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
from typing import List

import pandas as pd
import plotly.express as px
import streamlit as st

from nemoguardrails.eval.ui.utils import EvalData, load_eval_data
from nemoguardrails.eval.utils import collect_interaction_metrics


def _render_sidebar(output_names: List[str], policy_options: List[str]):
    _output_names = []
    _policy_options = []

    with st.sidebar:
        with st.sidebar.expander("Results", expanded=True):
            for output_path in output_names:
                if st.checkbox(output_path, True):
                    _output_names.append(output_path)

    with st.sidebar.expander("Policies", expanded=True):
        for policy in policy_options:
            if st.checkbox(policy, True):
                _policy_options.append(policy)

    return _output_names, _policy_options


def _render_compliance_data(
    output_names: List[str], policy_options: List[str], eval_data: EvalData
):
    # Compute the compliance rate for all outputs
    compliance_info = {}
    general_compliance = {}

    overall_compliance = []
    compliance_rate_per_policy = {"Policy": policy_options}
    violations_per_policy = {"Policy": policy_options}
    interactions_per_policy = {"Policy": policy_options}

    for output_name in output_names:
        compliance_info[output_name] = eval_data.eval_outputs[
            output_name
        ].compute_compliance()

        compliance_rate_per_policy[output_name] = [
            round(compliance_info[output_name][policy_id]["rate"] * 100, 2)
            for policy_id in policy_options
        ]
        violations_per_policy[output_name] = [
            compliance_info[output_name][policy_id]["interactions_violation_count"]
            for policy_id in policy_options
        ]
        interactions_per_policy[output_name] = [
            compliance_info[output_name][policy_id]["interactions_count"]
            for policy_id in policy_options
        ]

        # We also compute the general compliance rate
        compliance_rate = round(
            sum(
                compliance_info[output_name][policy_id]["rate"]
                for policy_id in policy_options
            )
            / len(policy_options)
            * 100,
            2,
        )
        general_compliance[output_name] = compliance_rate

        overall_compliance.append(["Overall Compliance", output_name, compliance_rate])

    st.subheader("Overall Compliance Rate")
    df = pd.DataFrame(
        overall_compliance,
        columns=["Overall Compliance", "Results", "Compliance Rate"],
    )
    st.dataframe(df)

    # Create a bar chart using Plotly
    fig = px.bar(
        df,
        x="Overall Compliance",
        y="Compliance Rate",
        color="Results",
        barmode="group",
        title="Overall Compliance Rate",
    )

    # Display the plot in Streamlit
    st.plotly_chart(fig, use_container_width=True)

    # Compliance Rate per policy
    fig = px.bar(
        pd.DataFrame(compliance_rate_per_policy),
        x=policy_options,
        y=output_names,
        barmode="group",
        title="Compliance Rate per Policy",
    )
    st.plotly_chart(fig, use_container_width=True)

    # Violations per policy
    fig = px.bar(
        pd.DataFrame(violations_per_policy),
        x=policy_options,
        y=output_names,
        barmode="group",
        title="Violations per Policy",
    )
    st.plotly_chart(fig, use_container_width=True)

    # Interactions per policy
    fig = px.bar(
        pd.DataFrame(interactions_per_policy),
        x=policy_options,
        y=output_names,
        barmode="group",
        title="Interactions per Policy",
    )
    st.plotly_chart(fig, use_container_width=True)


def _render_resource_usage_and_latencies(output_names: List[str], eval_data: EvalData):
    """Render the resource usage part."""
    resource_usage_table = []
    latencies_table = []

    def _append_value(table, metric, value):
        for row in table:
            if row[0] == metric:
                row.append(value)
                return
        table.append([metric, value])

    metrics = {}
    for output_name in output_names:
        metrics[output_name] = collect_interaction_metrics(
            eval_data.eval_outputs[output_name].results
        )

        for metric, value in metrics[output_name].items():
            if "_seconds" in metric:
                # latencies_table.append([metric, value])
                _append_value(latencies_table, metric, value)
            else:
                # resource_usage_table.append([metric, value])
                _append_value(resource_usage_table, metric, value)

    st.header("Resource Usage")
    st.dataframe(
        pd.DataFrame(resource_usage_table, columns=["Metric"] + output_names),
        use_container_width=True,
        hide_index=True,
    )

    # Latencies
    st.header("Latencies")
    st.dataframe(
        pd.DataFrame(latencies_table, columns=["Metric"] + output_names),
        use_container_width=True,
        hide_index=True,
    )

    unique_latency_labels = []
    for output_name in output_names:
        for label in metrics[output_name]:
            if label not in unique_latency_labels and "_seconds_total" in label:
                unique_latency_labels.append(label[0:-14])

    total_latency = []

    for output_name in output_names:
        for metric in unique_latency_labels:
            total_latency.append(
                [
                    output_name,
                    metric,
                    metrics[output_name].get(metric + "_seconds_total"),
                ]
            )
    fig = px.bar(
        pd.DataFrame(total_latency, columns=["Results", "Action", "Total Latency"]),
        x="Action",  # Column name for the x-axis
        y="Total Latency",  # Column name for the y-axis
        color="Results",  # Differentiating the series by time of day
        barmode="group",  # Can be "group" or "stack" for different visual styles
        title="Total Latency by Action",
    )
    st.plotly_chart(fig, use_container_width=True)


def main():
    """Show a summary of the evaluation results."""

    st.title("Evaluation Results")

    # Load the evaluation data
    eval_data = load_eval_data()
    eval_config = eval_data.eval_config
    output_names = list(eval_data.eval_outputs.keys())
    policy_options = [policy.id for policy in eval_config.policies]

    # Sidebar
    output_names, policy_options = _render_sidebar(output_names, policy_options)

    # Compliance data
    _render_compliance_data(output_names, policy_options, eval_data)

    # Resource Usage and Latencies
    _render_resource_usage_and_latencies(output_names, eval_data)


if __name__ == "__main__":
    main()
