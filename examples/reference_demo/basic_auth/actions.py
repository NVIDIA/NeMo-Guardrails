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
import os
from typing import Optional
from urllib import parse
import aiohttp
from nemoguardrails.actions import action
from nemoguardrails.actions.actions import ActionResult
from nemoguardrails.utils import new_event_dict
from datetime import datetime
import json

LOG_FILENAME = datetime.now().strftime('logs/mylogfile_%H_%M_%d_%m_%Y.log')
log = logging.getLogger(__name__)
logging.basicConfig(filename=LOG_FILENAME,level=logging.DEBUG)
#print(logging.getLoggerClass().root.handlers[0].baseFilename)



data = {}

@action(name="extract_and_save_data")
async def extract_and_save_data(
    query: Optional[str] = None, context: Optional[dict] = None
):
    """Saves the inputs received from the user
    
    :param context: The context for the execution of the action.
    :param query: The query for execution
    """
    # If we don't have an explicit query, we take the last user message
    if query is None and context is not None:
        query = context.get("last_user_message") or "Example First Name"

    if query is None:
        raise Exception("No input name was provided.")

    log.info(f"Received following query: {query}")
    log.info(f"Received following context: {context}")

    data = {}
    log.info(f"Found the following relevant data:")
    if "firstname" in context and "firstname" not in data:
        data["firstname"] = context["firstname"]
    if "lastname" in context and "lastname" not in data:
        data["lastname"] = context["lastname"]
    if "user_id" in context and "user_id" not in data:
        data["user_id"] = context["user_id"]
    #Note: one can also save the details to disk 

@action(name="authenticate_user")
async def authenticate_user(user_id, firstname, lastname):
    """Loads the ground truth database for authentication and compares against the inputs received from the user

    Note that only the values needed to authenticate are passed onto this function
    """
    log.info(f"Received following inputs: {user_id, firstname, lastname}")
    
    with open("ground_truth.json", "r") as infile:
        ground_truth = json.load(infile)

    log.info(f"Received following inputs: {ground_truth}")

    
    if user_id in ground_truth:
        print("success till here")
        #match against first and last name
        if firstname.lower() == ground_truth[user_id]["firstname"].lower() and lastname.lower() == ground_truth[user_id]["lastname"].lower():
            return True
        else:
            return False
    else:
        return False
        