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

import contextvars

streaming_handler_var = contextvars.ContextVar("streaming_handler", default=None)

# The object that holds additional explanation information.
explain_info_var = contextvars.ContextVar("explain_info", default=None)

# The current LLM call.
llm_call_info_var = contextvars.ContextVar("llm_call_info", default=None)

# All the generation options applicable to the current context.
generation_options_var = contextvars.ContextVar("generation_options", default=None)

# The stats about the LLM calls.
llm_stats_var = contextvars.ContextVar("llm_stats", default=None)

# The raw LLM request that comes from the user.
# This is used in passthrough mode.
raw_llm_request = contextvars.ContextVar("raw_llm_request", default=None)
