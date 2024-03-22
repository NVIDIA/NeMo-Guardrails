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
import json
import logging
from ast import literal_eval

from rich.logging import RichHandler
from rich.text import Text

from nemoguardrails.logging.simplify_formatter import SimplifyFormatter
from nemoguardrails.utils import console

# Global state variable to track if the verbose mode has already been enabled
verbose_mode_enabled = False

# Whether to log the LLM calls verbosely.
verbose_llm_calls = False

# Whether the debug mode is enabled or not.
debug_mode_enabled = False


class VerboseHandler(logging.StreamHandler):
    """A log handler for verbose mode."""

    def __init__(self, *args, **kwargs):
        super(VerboseHandler, self).__init__(*args, **kwargs)

    def emit(self, record) -> None:
        msg = self.format(record)

        # We check if we're using the spacial syntax with "::" which denotes a title.
        if "::" in msg:
            title, body = msg.split(" :: ", 1)
            title = title.strip()

            # We remove the title for completion messages and stop the blinking cursor.
            if title == "Completion":
                if verbose_llm_calls:
                    for line in body.split("\n"):
                        text = Text(line, style="black on #006600", end="\n")
                        text.pad_right(console.width)
                        console.print(text)

                    console.print("")

            # For prompts, we also start the blinking cursor.
            elif title == "Prompt":
                if verbose_llm_calls:
                    console.print(f"[cyan]{title}[/]")
                    console.print("")
                    for line in body.split("\n"):
                        text = Text(line, style="black on #909090", end="\n")
                        text.pad_right(console.width)
                        console.print(text)

            elif title == "Event":
                # For events, we also color differently the type of event.
                event_name, body = body.split(" ", 1)
                msg = f"[blue]{title}[/] [bold]{event_name}[/] {body}"

                console.print(msg, highlight=False)
            else:
                skip_print = False

                if title == "Processing event":
                    try:
                        event_dict = literal_eval(body)
                        event_type = event_dict["type"]

                        if "ActionStarted" in event_type:
                            skip_print = True
                        elif event_dict["type"] not in [
                            "CheckLocalAsync",
                            "LocalAsyncCounter",
                        ]:
                            del event_dict["type"]
                            del event_dict["uid"]
                            body = json.dumps(event_dict)

                            # We're adding a new line before action events, to
                            # make it more readable.
                            if event_type.startswith("Start") and event_type.endswith(
                                "Action"
                            ):
                                console.print(
                                    f"[magenta][bold]Start[/]{event_type[5:]}[/]"
                                )
                            elif event_type.startswith("Stop") and event_type.endswith(
                                "Action"
                            ):
                                console.print(
                                    f"[magenta][bold]Stop[/]{event_type[4:]}[/]"
                                )
                            elif event_type.endswith("ActionUpdated"):
                                console.print(
                                    f"[magenta]{event_type[:-7]}[bold]Updated[/][/]"
                                )
                            elif event_type.endswith("ActionFinished"):
                                if event_type == "UtteranceUserActionFinished":
                                    console.print(
                                        f"\n[magenta]{event_type[:-8]}[bold]Finished[/][/]"
                                    )
                                else:
                                    console.print(
                                        f"[magenta]{event_type[:-8]}[bold]Finished[/][/]"
                                    )
                            elif event_type.endswith("ActionFailed"):
                                console.print(
                                    f"[magenta{event_type[:-6]}][bold]Failed[/][/]"
                                )
                            else:
                                console.print(f"[magenta]{event_type}[/]")
                            msg = f"{body}"
                        else:
                            skip_print = True
                    except Exception:
                        msg = f"[red]{title}[/] {body}"
                elif title == "Running action":
                    skip_print = True
                elif title == "Matching head":
                    skip_print = True
                    # TODO: activate this once the source line is sorted
                    # flow_name = re.findall(r"flow='(.*?)'", body)[0]
                    # flow_pos = re.findall(r"pos=(\d+)", body)[0]
                    # msg = f"[yellow][bold]{flow_name}[/]:{flow_pos}[/]"
                    #
                    # ignored_flows = ["_bot_say", "await_flow_by_name"]
                    # if flow_pos == "0" or flow_name in ignored_flows:
                    #     skip_print = True
                else:
                    if title == "---":
                        msg = f"[#555555]{body}[/]"
                    else:
                        msg = f"[#707070]{title}[/] [#555555]{body}[/]"

                if not skip_print:
                    console.print(msg, highlight=False)


def set_verbose(
    verbose: bool,
    llm_calls: bool = False,
    debug: bool = False,
    debug_level: str = "INFO",
    simplify: bool = False,
):
    """Configure the verbose mode.

    The verbose mode is meant to be user-friendly. It provides additional information
    about what is happening under the hood.

    The verbose debug mode provides detailed logs, and it's meant for debugging purposes.

    Args:
        verbose: Whether the verbose mode should be enabled or not.
        llm_calls: Whether to log the prompt and response from the LLM calls (default False).
        debug: Whether the debug mode should be enabled or not (default False).
        debug_level: The log level to be used for debug mode (default INFO).
        simplify: Whether the output should be simplified to optimize for readability.
    """
    global verbose_mode_enabled
    global debug_mode_enabled
    global verbose_llm_calls

    if verbose and not verbose_mode_enabled:
        root_logger = logging.getLogger()

        # We make sure that the root logger is at least INFO so that we can see the messages from the VerboseHandler.
        if root_logger.level > logging.INFO:
            root_logger.setLevel(logging.INFO)

        # We make sure the log level for the default root console handler is set to WARNING.
        for handler in root_logger.handlers:
            if isinstance(handler, logging.StreamHandler):
                handler.setLevel(logging.WARNING)

        # In debug mode we add the RichHandler, otherwise we add the VerboseHandler.
        if debug:
            root_logger = logging.getLogger()
            rich_handler = RichHandler(markup=True)

            # If needed, simplify further the verbose output
            if simplify:
                rich_handler.setFormatter(SimplifyFormatter())

            root_logger.addHandler(rich_handler)
            root_logger.setLevel(debug_level)
        else:
            # Next, we also add an instance of the VerboseHandler.
            verbose_handler = VerboseHandler()
            verbose_handler.setLevel(logging.INFO)
            verbose_handler.setFormatter(SimplifyFormatter())
            root_logger.addHandler(verbose_handler)

        # Also, we make sure the sentence_transformers log level is set to WARNING.
        logging.getLogger("sentence_transformers").setLevel(logging.WARNING)

        verbose_mode_enabled = True
        verbose_llm_calls = llm_calls
        debug_mode_enabled = debug
        print("Entered verbose mode.")
