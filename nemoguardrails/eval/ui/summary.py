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

import pandas as pd
import plotly.express as px
import streamlit as st

from nemoguardrails.eval.ui.utils import load_eval_data
from nemoguardrails.eval.utils import collect_interaction_metrics


def main():
    """Show a summary of the evaluation results."""

    st.title("Evaluation Results")

    # Load the evaluation data
    eval_data = load_eval_data()
    eval_config = eval_data.eval_config

    output_names = list(eval_data.eval_outputs.keys())
    with st.sidebar:
        with st.sidebar.expander("Results", expanded=True):
            for output_path in output_names:
                st.checkbox(output_path, True)

        eval_output = eval_data.eval_outputs[output_names[0]]

    policy_options = [policy.id for policy in eval_config.policies]

    with st.sidebar.expander("Policies", expanded=True):
        for policy in policy_options:
            st.checkbox(policy, True)

    # Policies
    st.header("Policies")
    policies = pd.DataFrame(
        [[policy.id, policy.description] for policy in eval_config.policies],
        columns=["Policy ID", "Description"],
    )
    st.dataframe(policies, use_container_width=True)

    # Compute the compliance rate for all outputs
    compliance_info = {}
    general_compliance = {}

    # Sample data
    data = {
        "Category": ["Overall Compliance Rate"],
    }
    data_per_policy = {"Policy": policy_options}

    for output_name in output_names:
        compliance_info[output_name] = eval_data.eval_outputs[
            output_name
        ].compute_compliance()

        data_per_policy[output_name] = [
            compliance_info[output_name][policy_id]["rate"]
            for policy_id in policy_options
        ]

        # We also compute the general compliance rate
        compliance_rate = sum(
            compliance_info[output_name][policy_id]["rate"]
            for policy_id in policy_options
        ) / len(policy_options)
        general_compliance[output_name] = compliance_rate

        data[output_name] = compliance_rate

    st.subheader("Overall Compliance Rate")

    df = pd.DataFrame(data)

    # Create a bar chart using Plotly
    fig = px.bar(
        df,
        x="Category",
        y=output_names,
        barmode="group",
        title="Overall Compliance Rate",
    )

    # Display the plot in Streamlit
    st.plotly_chart(fig, use_container_width=True)

    df = pd.DataFrame(data_per_policy)

    # Create a bar chart using Plotly
    fig = px.bar(
        df,
        x=policy_options,
        y=output_names,
        barmode="group",
        title="Compliance Rate per Policy",
    )

    # Display the plot in Streamlit
    st.plotly_chart(fig, use_container_width=True)

    # compliance = {}
    # for policy in eval_config.policies:
    #     # Display a static progress bar for each percentage
    #     percentage = 0.5 + random.random() / 2
    #     compliance[policy.id] = percentage
    #     st.progress(
    #         percentage, text=f"{percentage * 100:.2f}% compliance for {policy.id}"
    #     )

    # st.header("Compliance")

    # # Sample data
    # df = pd.DataFrame(
    #     {
    #         "Value1": [38, 1.5, 30],
    #         "Value2": [29, 10, 5],
    #         "Value3": [8, 39, 23],
    #         "Value4": [7, 31, 33],
    #         "Value5": [28, 15, 32],
    #     }
    # )
    #
    # fig = px.line_polar(
    #     df,
    #     r=["Value1", "Value2", "Value3", "Value4", "Value5"],
    #     theta=df.columns,
    #     line_close=True,
    #     template="plotly",
    #     line_shape="linear",
    # )
    #
    # # Display the chart
    # st.plotly_chart(fig)

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

    for output_name in output_names:
        st.subheader(f"Total Latency - {output_name}")

        total_latency_metrics = {
            k: v for k, v in metrics[output_name].items() if "_seconds_total" in k
        }
        chart_data = pd.DataFrame(
            {
                "Metric": list(total_latency_metrics.keys()),
                "Value": list(total_latency_metrics.values()),
            }
        )
        st.bar_chart(chart_data, x="Metric", y="Value")


if __name__ == "__main__":
    main()
