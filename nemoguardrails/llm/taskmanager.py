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
from ast import literal_eval
from typing import Any, List, Optional, Union

from jinja2 import Environment, meta

from nemoguardrails.llm.filters import (
    colang,
    first_turns,
    last_turns,
    remove_text_messages,
    to_messages,
    user_assistant_sequence,
    verbose_v1,
)
from nemoguardrails.llm.output_parsers import (
    bot_intent_parser,
    bot_message_parser,
    user_intent_parser,
    verbose_v1_parser,
)
from nemoguardrails.llm.prompts import get_prompt
from nemoguardrails.llm.types import Task
from nemoguardrails.rails.llm.config import MessageTemplate, RailsConfig


class LLMTaskManager:
    """Interface for interacting with an LLM in a task-oriented way."""

    def __init__(self, config: RailsConfig):
        # Save the config as we need access to instructions and sample conversations.
        self.config = config

        # Initialize the environment for rendering templates.
        self.env = Environment()

        # Register the default filters.
        self.env.filters["colang"] = colang
        self.env.filters["remove_text_messages"] = remove_text_messages
        self.env.filters["first_turns"] = first_turns
        self.env.filters["last_turns"] = last_turns
        self.env.filters["user_assistant_sequence"] = user_assistant_sequence
        self.env.filters["to_messages"] = to_messages
        self.env.filters["verbose_v1"] = verbose_v1

        self.output_parsers = {
            "user_intent": user_intent_parser,
            "bot_intent": bot_intent_parser,
            "bot_message": bot_message_parser,
            "verbose_v1": verbose_v1_parser,
        }

        # The prompt context will hold additional variables that ce also be included
        # in the prompt.
        self.prompt_context = {}

    def _get_general_instruction(self):
        """Helper to extract the general instruction."""
        text = ""
        for instruction in self.config.instructions:
            if instruction.type == "general":
                text = instruction.content

                # We stop at the first one for now
                break

        return text

    def _render_string(
        self,
        template_str: str,
        context: Optional[dict] = None,
        events: Optional[List[dict]] = None,
    ) -> str:
        """Render a template using the provided context information.

        :param template_str: The template to render.
        :param context: The context for rendering the prompt.
        :param events: The history of events so far.
        :return: The rendered template.
        :rtype: str.
        """

        template = self.env.from_string(template_str)

        # First, we extract all the variables from the template.
        variables = meta.find_undeclared_variables(self.env.parse(template_str))

        # This is the context that will be passed to the template when rendering.
        render_context = {
            "history": events,
            "general_instruction": self._get_general_instruction(),
            "sample_conversation": self.config.sample_conversation,
            "sample_conversation_two_turns": self.config.sample_conversation,
        }

        # Copy the context variables to the render context.
        if context:
            for variable in variables:
                if variable in context:
                    render_context[variable] = context[variable]

        # Last but not least, if we have variables from the prompt context, we add them
        # to the render context.
        if self.prompt_context:
            for variable in variables:
                if variable in self.prompt_context:
                    value = self.prompt_context[variable]

                    # If it's a callable, we compute the value, otherwise we just use it
                    # as is.
                    if callable(value):
                        value = value()

                    render_context[variable] = value

        return template.render(render_context)

    def _render_messages(
        self,
        message_templates: List[Union[str, MessageTemplate]],
        context: Optional[dict] = None,
        events: Optional[List[dict]] = None,
    ) -> List[dict]:
        """Render a sequence of messages.

        :param message_templates: The message templates to render.
        :param context: The context for rendering the prompt.
        :param events: The history of events so far.
        :return: The rendered messages.
        """
        messages = []

        # We iterate each template and render it.
        # If it's a string, it must be a list of messages in JSON format.
        # If it's a MessageTemplate, we render it as a message.
        for message_template in message_templates:
            if isinstance(message_template, str):
                str_messages = self._render_string(
                    message_template, context=context, events=events
                )
                try:
                    new_messages = literal_eval(str_messages)
                except SyntaxError:
                    raise ValueError(f"Invalid message template: {message_template}")
                messages.extend(new_messages)
            else:
                content = self._render_string(
                    message_template.content, context=context, events=events
                )

                # Don't add empty messages.
                if content.strip():
                    messages.append(
                        {
                            "type": message_template.type,
                            "content": content,
                        }
                    )

        return messages

    def render_task_prompt(
        self,
        task: Task,
        context: Optional[dict] = None,
        events: Optional[List[dict]] = None,
    ) -> Union[str, List[dict]]:
        """Render the prompt for a specific task.

        :param task: The name of the task.
        :param context: The context for rendering the prompt
        :param events: The history of events so far.

        :return: A string, for completion models, or an array of messages for chat models.
        """
        prompt = get_prompt(self.config, task)

        if prompt.content:
            return self._render_string(prompt.content, context=context, events=events)
        else:
            return self._render_messages(
                prompt.messages, context=context, events=events
            )

    def parse_task_output(self, task: Task, output: str):
        """Parses the output for the provided tasks.

        If an output parser is associated with the prompt, it will be used.
        Otherwise, the output is returned as is.
        """
        prompt = get_prompt(self.config, task)

        output_parser = None
        if prompt.output_parser:
            output_parser = self.output_parsers.get(prompt.output_parser)
            if not output_parser:
                logging.warning("No output parser found for %s", prompt.output_parser)

        if output_parser:
            return output_parser(output)
        else:
            return output

    def register_filter(self, filter_fn: callable, name: Optional[str] = None):
        """Register a custom filter for the rails configuration."""
        name = name or filter_fn.__name__
        self.env.filters[name] = filter_fn

    def register_output_parser(self, output_parser: callable, name: str):
        """Register a custom output parser for the rails configuration."""
        self.output_parsers[name] = output_parser

    def register_prompt_context(self, name: str, value_or_fn: Any):
        """Register a value to be included in the prompt context.

        :name: The name of the variable or function that will be used.
        :value_or_fn: The value or function that will be used to generate the value.
        """
        self.prompt_context[name] = value_or_fn
