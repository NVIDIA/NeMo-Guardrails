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

from typing import Any, List, Optional
import logging
import sys
sys.path.append('/workspace/NeMo-Guardrails/examples/hf_falcon')

from nemoguardrails.actions import action
from nemoguardrails.actions.actions import ActionResult

from datetime import datetime
from colorama import Fore
import pytz
log = logging.getLogger(__name__)



def match_any(list_1, item_str):
    item_str=item_str.lower()
    for it in list_1:
        it=it.lower()        
        if it in item_str:
            return True, it
    return False, None

def fetch_time_precision(query):
    months=['January', 'February','March','April','May','June','July','August','September','October','November','December']
    idx2months=dict([(idx,m) for (idx,m) in zip(range(1,13),months)])
    weekdays=['Monday','Tuesday','Wednesday','Thursday','Friday','Saturday','Sunday']
    sixWs=['What','Which']
    time_related_keywords=months+weekdays+['When', 'What time', "Weekend", "holidays","Summer", "Winter", "Fall","Spring","date","today"]
    idx2weekdays=dict([(id,wd) for (id, wd) in zip(range(1,8),weekdays)])
    weekdays2idx= dict([(wd,id) for (wd,id) in zip(range(1,8),weekdays)])
    timezone= pytz.timezone('CET')
    dt=datetime.now(timezone)
    weekday=dt.strftime('%A')
    dayinmonth=dt.strftime('%d')
    time_track=[]
    replace_words=[]
    time_shift=0
    flag1, wd = match_any(weekdays,query)
    flag2, w = match_any(sixWs, query)
    if 'last' in query:
        time_shift=-1
    elif 'previous' in query:
        time_shift=-1
    else:
        pass
    yr=str(dt.year)
    m=idx2months[dt.month]
    wday=dt.strftime('%A')
    day=dt.strftime('%d')
    current_time=dt.strftime("%H:%M")
    if wday=="Friday" and ('next day' in query or 'tomorrow' in query):
        
        additional_inserts="It's {} {}.{}, {}, tomorrow is {}.The time now is {} CET ".format(m,day,yr,wday,"weekend",current_time)
    else:
        additional_inserts="It's {} {}.{}, {}.The current time is {} CET".format(m,day,yr,wday,current_time)
    flag,_= match_any(time_related_keywords, query)
    return flag, additional_inserts

    
   
@action(is_system_action=False)
async def check_if_time_based_query(events: List[dict], context: Optional[dict] = None):
    n = len(events) - 1
    for j in range(n,0, -1):
        if j > 0 and events[j]["type"]=='user_said':
            break
        else:
            j-=1

    user_query=events[j]['content']
    flag, result = fetch_time_precision(user_query)
    
    
    
    log.info(f"time query respond completed!")

    print(Fore.LIGHTWHITE_EX + "============================  result =============================================")
    print(Fore.CYAN+result)
    if flag: 
        return ActionResult(
            events=[
            {
                "type": "bot_said",
                "content": result + "and you asked: "+ user_query,
            }
        ]
    )
    else:
        return  ActionResult(
            events=[
            {
                "type": "bot_said",
                "content": "This is not a question about date time, moving on...",
            }
        ]
    )