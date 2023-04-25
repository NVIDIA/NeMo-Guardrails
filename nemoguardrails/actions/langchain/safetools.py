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

"""This module contains safer versions for some of the most used LangChain tools.

The same validation logic can be applied to others as well.
"""

from langchain import (
    GoogleSearchAPIWrapper,
    GoogleSerperAPIWrapper,
    SearxSearchWrapper,
    SerpAPIWrapper,
    WikipediaAPIWrapper,
    WolframAlphaAPIWrapper,
)
from langchain.utilities import (
    ApifyWrapper,
    BingSearchAPIWrapper,
    OpenWeatherMapAPIWrapper,
)
from langchain.utilities.zapier import ZapierNLAWrapper

from nemoguardrails.actions.validation import validate_input, validate_response

MAX_QUERY_LEN = 50
MAX_LOCATION_LEN = 50


@validate_input("actor_id", validators=["length"], max_len=MAX_QUERY_LEN)
class ApifyWrapperSafe(ApifyWrapper):
    """Safer version for the ApifyWrapper."""


@validate_input("query", validators=["length"], max_len=MAX_QUERY_LEN)
@validate_response(validators=["ip_filter", "is_default_resp"])
class BingSearchAPIWrapperSafe(BingSearchAPIWrapper):
    """Safer version for the BingSearch API wrapper."""


@validate_input("query", validators=["length"], max_len=MAX_QUERY_LEN)
@validate_response(validators=["ip_filter", "is_default_resp"])
class GoogleSearchAPIWrapperSafe(GoogleSearchAPIWrapper):
    """Safer version for the Google Search API wrapper."""


@validate_input("query", validators=["length"], max_len=MAX_QUERY_LEN)
@validate_response(validators=["ip_filter", "is_default_resp"])
class SearxSearchWrapperSafe(SearxSearchWrapper):
    """Safer version for the Searx Search wrapper"""


@validate_input("query", validators=["length"], max_len=MAX_QUERY_LEN)
@validate_response(validators=["ip_filter", "is_default_resp"])
class GoogleSerperAPIWrapperSafe(GoogleSerperAPIWrapper):
    """Safer version for the Google Serper API wrapper."""


@validate_input("location", validators=["length"], max_len=MAX_LOCATION_LEN)
@validate_response(validators=["ip_filter", "is_default_resp"])
class OpenWeatherMapAPIWrapperSafe(OpenWeatherMapAPIWrapper):
    """Safer version for the OpenWeatherMap API wrapper."""


@validate_input("query", validators=["length"], max_len=MAX_QUERY_LEN)
@validate_response(validators=["ip_filter", "is_default_resp"])
class SerpAPIWrapperSafe(SerpAPIWrapper):
    """Safer version for the SerpAPI wrapper."""


@validate_input("query", validators=["length"], max_len=MAX_QUERY_LEN)
@validate_response(validators=["ip_filter", "is_default_resp"])
class WikipediaAPIWrapperSafe(WikipediaAPIWrapper):
    """Safer version for the Wikipedia API wrapper."""


@validate_input("query", validators=["length"], max_len=MAX_QUERY_LEN)
@validate_response(validators=["ip_filter", "is_default_resp"])
class WolframAlphaAPIWrapperSafe(WolframAlphaAPIWrapper):
    """Safer version for the Wolfram Alpha API wrapper."""


@validate_input("instructions", validators=["length"], max_len=MAX_QUERY_LEN)
@validate_input("action_id")
@validate_response(validators=["ip_filter"])
class ZapierNLAWrapperSafe(ZapierNLAWrapper):
    """Safer version for the Zapier NLA Wrapper."""
