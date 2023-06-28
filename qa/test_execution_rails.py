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


class TestExecutionRails(TestCase):
    logger = None
    chatter = None

    @classmethod
    def setUpClass(cls) -> None:
        super().setUpClass()
        # Create a logger and a chatter
        cls.logger = create_logger('execution_rails.log')
        cls.chatter = create_chatter("execution_rails", "execution_rails/sample_rails", cls.logger)

    @classmethod
    def tearDownClass(cls) -> None:
        super().tearDownClass()
        close_chatter(cls.chatter)

    @pytest.mark.unit
    def test_execution_rails(self):
        """Test the execution_rails example"""
        self.logger.info("Running test_execution_rails...")

        # Define Q&A messages
        messages = {
            "Hi there!": ["Hi! How can I assist you today?", "Hello again! How can I help you?", "Hello again! What can I help you with today?", "Hello again! What can I do for you?", "Hello! What can I help you with today?", "Hello again! How can I help you today?", "Hello again! How can I be of assistance?", "Hello there! How can I help you today?", "Hello! How can I assist you today?", "Hey there!", "Hi! How can I help you today?", "Hello! How can I help you today?", "Hello, how can I help you today?", "Hello there! How can I help you?"],
            "How can you help?": ["I am an AI assistant that helps answer mathematical questions. My core mathematical skills are powered by wolfram alpha.", "How are you feeling today?"],
            "What is 434 + 56*7.5?": ["434 + 56*7.5 is equal to 854.", "The result is 854.", "The result of 434 + 56*7.5 is 854.", "The answer is 854.", "434 + 56 * 7.5 is equal to 854."]
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
                assert len([answer for answer in expected_answers if answer in output]) > 0
