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

import logging
import random
from typing import Optional

from langchain import LLMChain, PromptTemplate
from langchain.llms import BaseLLM

from nemoguardrails.actions.actions import ActionResult, action
from nemoguardrails.kb.kb import KnowledgeBase
from nemoguardrails.recognizers.pii_recognizer import PIIRecognizer
from nemoguardrails.rails.llm.config import RailsConfig


log = logging.getLogger(__name__)


@action(is_system_action=True)
async def detect_sensitive_data_in_query(
    query: str,
    config: Optional[RailsConfig] = None,
    context: Optional[dict] = None,
):
    """detect presence of sensitive data"""

    pii_recognizer = PIIRecognizer(config=config)
    if query and pii_recognizer._detect_sensitive_data(query):
        return True # sensitive data detected
    return False


@action(is_system_action=True)
async def sensitive_data_detection(
    config: Optional[RailsConfig] = None,
):
    """detect presence of sensitive data"""

    if config.sensitive_data_detection:
        return config.sensitive_data_detection
    return False
    

@action(is_system_action=True)
async def detect_sensitive_data_in_user_message(
    context: Optional[dict] = None,
    config: Optional[RailsConfig] = None,
):
    """detect presence of sensitive data, perform redaction"""

    pii_recognizer = PIIRecognizer(config=config)
    user_message = context.get("last_user_message") 
    if user_message and pii_recognizer._detect_sensitive_data(user_message):
        return True # sensitive data detected
    return False


@action(is_system_action=True)
async def detect_sensitive_data_in_bot_message(
    context: Optional[dict] = None,
    config: Optional[RailsConfig] = None,
):
    """detect presence of sensitive data, perform redaction"""

    pii_recognizer = PIIRecognizer(config=config)
    bot_response = context.get("last_bot_message")
    if bot_response and pii_recognizer._detect_sensitive_data(bot_response):
        return True #sensitive data detected
    return False


@action(is_system_action=True)
async def detect_sensitive_data_in_retrieved_chunks(
    context: Optional[dict] = None,
    config: Optional[RailsConfig]= None,
    events: Optional[dict] = None,
):
    """detect presence of sensitive data"""
    
    pii_recognizer = PIIRecognizer(config=config)
    relevant_chunks = context.get("relevant_chunks") 
    if pii_recognizer._detect_sensitive_data(relevant_chunks):
        return True
    return False
    

@action(is_system_action=True)
async def anonymize_sensitive_data_in_retrieved_chunks(
    context: Optional[dict] = None,
    config: Optional[RailsConfig] = None,
):
    """anonymize sensitive data, perform redaction"""
    
    context_updates = {}
    pii_recognizer = PIIRecognizer(config=config)
    relevant_chunks = context.get("relevant_chunks") 
    if pii_recognizer._detect_sensitive_data(relevant_chunks):
        context_updates["relevant_chunks"] = pii_recognizer._anonymize_text(relevant_chunks)
    else:
        context_updates["relevant_chunks"] = relevant_chunks
            
    return ActionResult(
        return_value=context_updates["relevant_chunks"],
        context_updates=context_updates,
    )

