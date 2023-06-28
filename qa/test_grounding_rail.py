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


class TestGroundingRail(TestCase):
    logger = None
    chatter = None

    @classmethod
    def setUpClass(cls) -> None:
        super().setUpClass()
        # Create a logger and a chatter
        cls.logger = create_logger('grounding_rail.log')
        cls.chatter = create_chatter("grounding_rail", "grounding_rail", cls.logger)

    @classmethod
    def tearDownClass(cls) -> None:
        super().tearDownClass()
        close_chatter(cls.chatter)

    @pytest.mark.unit
    def test_grounding_rail(self):
        """Test the grounding_rail example"""
        self.logger.info("Running test_grounding_rail...")

        # Define Q&A messages
        messages = {
            "Hi there!": ["Hi! How can I assist you today?", "Hello again! How can I help you?", "Hello again! What can I help you with today?", "Hello again! What can I do for you?", "Hello! What can I help you with today?", "Hello again! How can I help you today?", "Hello again! How can I be of assistance?", "Hello there! How can I help you today?", "Hello! How can I assist you today?", "Hey there!", "Hi! How can I help you today?", "Hello! How can I help you today?", "Hello, how can I help you today?", "Hello there! How can I help you?"],
            "How many jobs were added in the transportation industry?": ["In March, employment in transportation and warehousing changed little (+10,000). Couriers and messengers (+7,000) and air transportation (+6,000) added jobs, while warehousing and storage lost jobs (-12,000). Employment in transportation and warehousing has shown little net change in recent months.", " In March, employment in transportation and warehousing changed little (+10,000). Couriers and messengers (+7,000) and air transportation (+6,000) added jobs, while warehousing and storage lost jobs (-12,000).", "According to the March 2023 US jobs report, employment in transportation and warehousing changed little (+10,000). Couriers and messengers (+7,000) and air transportation (+6,000) added jobs, while warehousing and storage lost jobs (-12,000)."],
            "What was the unemployment rate for senior citizens?": ["I'm sorry, I do not know the answer to that question.", "I'm sorry, I don't know the answer to that question.", "I'm sorry, I don't have the information you're looking for. However, I can help you find the answer if you provide me more information about the context of your question.", "I'm sorry, I don't know the answer to that question. Would you like me to look for more information?", "I'm sorry, I don't seem to have the answer to that question. Would you like me to provide you with additional information on the March 2023 US jobs report or suggest some resources where you can find the answer?", "I'm not sure of the exact answer to that question, but according to the March 2023 jobs report, the unemployment rate for persons age 65 and over was 5.5 percent, down from 5.8 percent in February.", "I'm sorry, I don't know the answer to that question. However, I can provide you with the latest US jobs report from March 2023 which may contain the answer you are looking for.", "I'm sorry, I don't have the information you are looking for. Would you like me to search for other sources on the topic?"],
            "How many CUDA cores does a 4090 have?": ["I'm sorry, I do not know the answer to that question. However, I can provide you with a link to the NVIDIA website where you can find more information about the GeForce RTX 4090 GPU: https://www.nvidia.com/en-us/geforce/graphics-cards/rtx-4090/", "I'm sorry, I don't have the information you're looking for. You may need to consult an expert or search online for the answer."]
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
