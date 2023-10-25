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
import time

import pandas as pd
from tqdm import tqdm

from nemoguardrails import LLMRails, RailsConfig

CONFIGS_FOLDER = os.path.join(os.path.dirname(__file__), "bots")

NUM_TEST_RUNS = 10  # Number of times to average results over

TEST_QUESTIONS = [
    # chit-chat questions
    "Hi",  # throw-away (0th index)
    "Hey, how's the weather in Santa Clara today?",
    "Hello! What can you do for me?",
    # questions about the report in kb
    "What was the unemployment rate in March?",
    "What was the unemployment rate among Asians?",
    "Has the labor force participation rate been trending up?",
    "How many people remained discouraged by the job market?",
    "What percentage of unemployed people have been jobless for a long time?",
    "What industries have shown a continued increase in employment?",
    # general questions
    "What was Barack Obama's age when he was appointed the President of the United States?",
    "What is the recipe to make Aglio Olio pasta?",
]


TEST_CONFIGS = [
    "latency_0_baseline",
    "latency_1_normal",
    "latency_2_single_call",
    "latency_3_embeddings_only",
    "latency_4_compact",
    "latency_5_fact_checking_ask_llm",
    "latency_6_fact_checking_align_score",
]


def run_latency_report():
    latency_report_cols = [
        "config",
        "question_id",
        "question",
        "run_id",
        "response",
        "time",
    ]
    latency_report_rows = []

    sleep_time = 0

    for test_config in tqdm(TEST_CONFIGS):
        config = RailsConfig.from_path(os.path.join(CONFIGS_FOLDER, test_config))

        app = LLMRails(config)

        for test_run_idx in tqdm(range(NUM_TEST_RUNS)):
            for test_question_idx, test_question in enumerate(TEST_QUESTIONS):
                # This is to avoid rate-limiters from LLM APIs affecting measurements
                time.sleep(2)
                sleep_time += 2
                start_time = time.time()
                response = app.generate(
                    messages=[{"role": "user", "content": test_question}]
                )
                end_time = time.time()
                assert response["role"] == "assistant"

                latency_report_rows.append(
                    [
                        test_config,
                        test_question_idx,
                        test_question,
                        test_run_idx,
                        response["content"],
                        end_time - start_time,
                    ]
                )

    latency_report_df = pd.DataFrame(latency_report_rows, columns=latency_report_cols)
    print(latency_report_df)
    latency_report_df.to_csv("latency_report_detailed_openai.tsv", sep="\t")

    latency_report_grouped = latency_report_df.groupby(
        by=["config", "question_id"]
    ).agg({"time": "mean"})
    print()
    print(latency_report_grouped)
    latency_report_pivoted = pd.pivot_table(
        latency_report_grouped,
        values="time",
        index=["question_id"],
        columns=["config"],
    )
    print()
    print(latency_report_pivoted)
    latency_report_pivoted.to_csv("latency_report_openai.tsv", sep="\t")
    return sleep_time


if __name__ == "__main__":
    test_start_time = time.time()
    sleep_time = run_latency_report()
    test_end_time = time.time()

    print(f"Total time taken: {(test_end_time-test_start_time):.2f}")
    print(f"Time spent sleeping: {(sleep_time):.2f}")
