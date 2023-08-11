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
import uuid
from time import time
from typing import Any, Dict, List, Optional, Union
from uuid import UUID

from langchain.callbacks import StdOutCallbackHandler
from langchain.callbacks.base import AsyncCallbackHandler, BaseCallbackManager
from langchain.callbacks.manager import AsyncCallbackManagerForChainRun
from langchain.schema import AgentAction, AgentFinish, BaseMessage, LLMResult

from nemoguardrails.logging.stats import llm_stats
from nemoguardrails.logging.verbose import Styles

log = logging.getLogger(__name__)


class LoggingCallbackHandler(AsyncCallbackHandler, StdOutCallbackHandler):
    """Async callback handler that can be used to handle callbacks from langchain."""

    # The timestamp when the last prompt was sent to the LLM.
    last_prompt_timestamp: Optional[float] = 0

    async def on_llm_start(
        self,
        serialized: Dict[str, Any],
        prompts: List[str],
        *,
        run_id: UUID,
        parent_run_id: Optional[UUID] = None,
        **kwargs: Any,
    ) -> None:
        """Run when LLM starts running."""
        log.info("Invocation Params :: %s", kwargs.get("invocation_params", {}))
        log.info("Prompt :: %s", prompts[0])
        self.last_prompt_timestamp = time()
        llm_stats.inc("total_calls")

    async def on_chat_model_start(
        self,
        serialized: Dict[str, Any],
        messages: List[List[BaseMessage]],
        *,
        run_id: UUID,
        parent_run_id: Optional[UUID] = None,
        **kwargs: Any,
    ) -> Any:
        """Run when a chat model starts running."""

        prompt = "\n" + "\n".join(
            [
                Styles.CYAN
                + (
                    "User"
                    if msg.type == "human"
                    else "Bot"
                    if msg.type == "ai"
                    else "System"
                )
                + Styles.PROMPT
                + "\n"
                + msg.content
                for msg in messages[0]
            ]
        )

        log.info("Invocation Params :: %s", kwargs.get("invocation_params", {}))
        log.info("Prompt Messages :: %s", prompt)
        self.last_prompt_timestamp = time()
        llm_stats.inc("total_calls")

    async def on_llm(self, *args, **kwargs) -> Any:
        """NOTE: this needs to be implemented to avoid a warning by LangChain."""
        pass

    async def on_llm_new_token(
        self,
        token: str,
        *,
        run_id: UUID,
        parent_run_id: Optional[UUID] = None,
        **kwargs: Any,
    ) -> None:
        """Run on new LLM token. Only available when streaming is enabled."""

    async def on_llm_end(
        self,
        response: LLMResult,
        *,
        run_id: UUID,
        parent_run_id: Optional[UUID] = None,
        **kwargs: Any,
    ) -> None:
        """Run when LLM ends running."""
        log.info("Completion :: %s", response.generations[0][0].text)

        # If there are additional completions, we show them as well
        if len(response.generations[0]) > 1:
            for i, generation in enumerate(response.generations[0][1:]):
                log.info("--- :: Completion %d", i + 2)
                log.info("Completion :: %s", generation.text)

        log.info("Output Stats :: %s", response.llm_output)
        took = time() - self.last_prompt_timestamp
        log.info("--- :: LLM call took %.2f seconds", took)
        llm_stats.inc("total_time", took)

        # Update the token usage stats as well
        if response.llm_output:
            token_usage = response.llm_output.get("token_usage", {})
            llm_stats.inc("total_tokens", token_usage.get("total_tokens", 0))
            llm_stats.inc("total_prompt_tokens", token_usage.get("prompt_tokens", 0))
            llm_stats.inc(
                "total_completion_tokens", token_usage.get("completion_tokens", 0)
            )

    async def on_llm_error(
        self,
        error: Union[Exception, KeyboardInterrupt],
        *,
        run_id: UUID,
        parent_run_id: Optional[UUID] = None,
        **kwargs: Any,
    ) -> None:
        """Run when LLM errors."""

    async def on_chain_start(
        self,
        serialized: Dict[str, Any],
        inputs: Dict[str, Any],
        *,
        run_id: UUID,
        parent_run_id: Optional[UUID] = None,
        **kwargs: Any,
    ) -> None:
        """Run when chain starts running."""

    async def on_chain_end(
        self,
        outputs: Dict[str, Any],
        *,
        run_id: UUID,
        parent_run_id: Optional[UUID] = None,
        **kwargs: Any,
    ) -> None:
        """Run when chain ends running."""

    async def on_chain_error(
        self,
        error: Union[Exception, KeyboardInterrupt],
        *,
        run_id: UUID,
        parent_run_id: Optional[UUID] = None,
        **kwargs: Any,
    ) -> None:
        """Run when chain errors."""

    async def on_tool_start(
        self,
        serialized: Dict[str, Any],
        input_str: str,
        *,
        run_id: UUID,
        parent_run_id: Optional[UUID] = None,
        **kwargs: Any,
    ) -> None:
        """Run when tool starts running."""

    async def on_tool_end(
        self,
        output: str,
        *,
        run_id: UUID,
        parent_run_id: Optional[UUID] = None,
        **kwargs: Any,
    ) -> None:
        """Run when tool ends running."""

    async def on_tool_error(
        self,
        error: Union[Exception, KeyboardInterrupt],
        *,
        run_id: UUID,
        parent_run_id: Optional[UUID] = None,
        **kwargs: Any,
    ) -> None:
        """Run when tool errors."""

    async def on_text(
        self,
        text: str,
        *,
        run_id: UUID,
        parent_run_id: Optional[UUID] = None,
        **kwargs: Any,
    ) -> None:
        """Run on arbitrary text."""

    async def on_agent_action(
        self,
        action: AgentAction,
        *,
        run_id: UUID,
        parent_run_id: Optional[UUID] = None,
        **kwargs: Any,
    ) -> None:
        """Run on agent action."""

    async def on_agent_finish(
        self,
        finish: AgentFinish,
        *,
        run_id: UUID,
        parent_run_id: Optional[UUID] = None,
        **kwargs: Any,
    ) -> None:
        """Run on agent end."""


handlers = [LoggingCallbackHandler()]
logging_callbacks = BaseCallbackManager(
    handlers=handlers, inheritable_handlers=handlers
)

logging_callback_manager_for_chain = AsyncCallbackManagerForChainRun(
    run_id=uuid.uuid4(),
    parent_run_id=None,
    handlers=handlers,
    inheritable_handlers=handlers,
    tags=[],
    inheritable_tags=[],
)
