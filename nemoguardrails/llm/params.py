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

"""
Module for providing a context manager to temporarily adjust parameters of a language model.

Also allows registration of custom parameter managers for different language model types.
"""
import logging
from typing import Dict, Type

from langchain.base_language import BaseLanguageModel

log = logging.getLogger(__name__)


class LLMParams:
    """Context manager to temporarily modify the parameters of a language model."""

    def __init__(self, llm: BaseLanguageModel, **kwargs):
        self.llm = llm
        self.altered_params = kwargs
        self.original_params = {}

    def __enter__(self):
        # Here we can access and modify the global language model parameters.
        self.original_params = {}
        for param, value in self.altered_params.items():
            if hasattr(self.llm, param):
                self.original_params[param] = getattr(self.llm, param)
                setattr(self.llm, param, value)
            # TODO: Fix the cases where self.llm.model_kwargs is not iterable
            #  https://github.com/NVIDIA/NeMo-Guardrails/issues/92.
            # elif param in getattr(self.llm, "model_kwargs", {}):
            #     self.original_params[param] = self.llm.model_kwargs[param]
            #     self.llm.model_kwargs[param] = value
            else:
                log.warning(
                    "Parameter %s does not exist for %s",
                    param,
                    self.llm.__class__.__name__,
                )

    def __exit__(self, type, value, traceback):
        # Restore original parameters when exiting the context
        for param, value in self.original_params.items():
            if hasattr(self.llm, param):
                setattr(self.llm, param, value)
            elif hasattr(self.llm, "model_kwargs") and param in getattr(
                self.llm, "model_kwargs", {}
            ):
                self.llm.model_kwargs[param] = value


# The list of registered param managers. This will allow us to override the param manager
# for a new LLM.
_param_managers: Dict[Type[BaseLanguageModel], Type[LLMParams]] = {}


def register_param_manager(llm_type: Type[BaseLanguageModel], manager: Type[LLMParams]):
    """
    Register a parameter manager for a specific language model type.

    This function registers a parameter manager for a specific language model type,
    allowing the system to retrieve the appropriate manager when needed.

    Args:
        llm_type (Type[BaseLanguageModel]): The type of the language model.
        manager (Type[LLMParams]): The parameter manager associated with the language model.

    """
    _param_managers[llm_type] = manager


def llm_params(llm: BaseLanguageModel, **kwargs):
    """
    Get a parameter manager for a given language model.

    This function returns a parameter manager for a given language model. If a specific
    manager is registered for the language model type, it will be used; otherwise, a
    default manager (LLMParams) will be returned.

    Args:
        llm (BaseLanguageModel): The language model instance.
        **kwargs: Additional keyword arguments to pass to the parameter manager.

    Returns:
        LLMParams: A parameter manager for the given language model.

    """
    _llm_params = _param_managers.get(llm.__class__, LLMParams)

    return _llm_params(llm, **kwargs)
