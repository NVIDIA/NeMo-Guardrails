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
import json
from typing import Optional
from urllib import parse
from colorama import Fore

from nemoguardrails.actions import action
from nemoguardrails.actions.actions import ActionResult
import wikipedia
log = logging.getLogger(__name__)

def find_keyword(query):
    if 'keyword' in query:
        index=query.find('keyword')+9
        temp=query[index:]
        if temp.endswith('.'):
            temp=temp[:-1]
        else:
            temp=temp
    return temp

def wiki_search_api(query, how_many=800):   
    ny = wikipedia.page(query)
    print(ny.url)
    result=ny.content
    return result[:how_many]

@action(name="query wiki search")
async def query_wiki_search(
    query: Optional[str] = None, context: Optional[dict] = None
):
    """Makes a request to the Wolfram Alpha API

    :param context: The context for the execution of the action.
    :param query: The query for Wolfram.
    """
    # If we don't have an explicit query, we take the last user message
    if query is None and context is not None:
        query = context.get("last_user_message")
        keyword=find_keyword(query)

    if query is None:
        raise Exception("No query was provided to wiki Search.")
    
    if keyword is None:
        return ActionResult(
            return_value=False,
            events=[
                {
                    "type": "bot_said",
                    "content": "Keyword  not found in the environment. Please use keyword:<Keyword used to search on wikipedia>.",
                },
                {"type": "bot_intent", "intent": "stop"},
            ],
        )

    print("####################query=",query)
    print("----"*10)
    log.info(f"wiki Query: executing request for: {query}")

    result = wiki_search_api(keyword)
    print(Fore.LIGHTWHITE_EX + "============================ wiki result =============================================")
    print(Fore.CYAN+result)
    log.info(f"wiki Search completed!")
    return result