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

import pytest

from unittest import TestCase
from .logger import create_logger
from .chatter import create_chatter, close_chatter
from .validator import are_strings_semantically_same


class TestTopicalRail(TestCase):
    logger = None
    chatter = None

    @classmethod
    def setUpClass(cls) -> None:
        super().setUpClass()
        # Create a logger and a chatter
        cls.logger = create_logger('topical_rail.log')
        cls.chatter = create_chatter("topical_rail", "topical_rail/sample_rails", cls.logger)

    @classmethod
    def tearDownClass(cls) -> None:
        super().tearDownClass()
        close_chatter(cls.chatter)

    @pytest.mark.unit
    def test_topical_rail(self):
        """Test the topical_rail example"""
        self.logger.info("Running test_topical_rail...")

        # Define Q&A messages
        messages = {
            "Hi there!": ["Hi! How can I assist you today?", "Hello again! How can I help you?", "Hello again! What can I help you with today?", "Hello again! What can I do for you?", "Hello! What can I help you with today?", "Hello again! How can I help you today?", "Hello again! How can I be of assistance?", "Hello there! How can I help you today?", "Hello! How can I assist you today?", "Hey there!", "Hi! How can I help you today?", "Hello! How can I help you today?", "Hello there! How can I help you?", "Hello, how can I help you today?"],
            "How can you help?": ["I am an AI assistant that helps answer mathematical questions. My core mathematical skills are powered by wolfram alpha.", "I am an AI assistant which helps answer questions based on a given knowledge base. For this interaction, I can answer question based on the job report published by US Bureau of Labor Statistics.", "How are you feeling today?"],
            "How many jobs were added in the healthcare sector?": ["According to the latest report from the US Bureau of Labor Statistics, the healthcare sector added 57,000 jobs in the month of October.", "According to the US Bureau of Labor Statistics' establishment survey, there were 33,000 jobs added in the healthcare sector in the last month.", "According to the latest jobs report, the US economy added 439,000 jobs in the healthcare sector in July 2020." ,"According to the most recent report, the healthcare sector added 47,000 jobs in April 2021.", "According to the latest report, the healthcare sector added 267,000 jobs in April 2021", "According to the latest report, the healthcare sector added 59,000 jobs in January 2021.", "According to the establishment survey data, the healthcare sector added 53,000 jobs in April 2021."],
            "What's the best flavor of icecream?": ["Sorry, I cannot comment on anything which is not relevant to the jobs report"]
        }

        if self.chatter is not None:
            # Process the questions and validate the answers
            for question, expected_answers in messages.items():
                self.logger.info(f"User: {question}")
                # Send the question to chatter
                self.chatter.stdin.write(question + '\n')
                self.chatter.stdin.flush()

                # Read the answer from chatter
                output = self.chatter.stdout.readline().strip()
                self.logger.info(f"Bot: {output}")
                # Validate the answer
                if len([answer for answer in expected_answers if answer in output]) > 0:
                    assert True
                else:
                    assert are_strings_semantically_same(expected_answers[0], output)
