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
import threading
import time


class Styles:
    """The set of standard colors."""

    BLACK = "\033[30m"
    RED = "\033[31m"
    GREEN = "\033[32m"
    YELLOW = "\033[33m"
    BLUE = "\033[34m"
    MAGENTA = "\033[35m"
    CYAN = "\033[36m"
    WHITE = "\033[37m"
    GREY = "\033[38;5;246m"
    WHITE_ON_GREEN = "\033[42m\033[97m"

    RESET = "\033[38m"
    RESET_ALL = "\033[0m"

    PROMPT = "\033[38;5;232m\033[48;5;254m"
    COMPLETION = "\033[38;5;236m\033[48;5;84m"
    COMPLETION_GREEN = "\033[48;5;84m"
    COMPLETION_RED = "\033[48;5;196m"
    EVENT_NAME = "\033[38;5;32m"


# Mapping of colors associated with various sections
SECTION_COLOR = {
    "Phase 1": {"title": Styles.GREEN},
    "Phase 2": {"title": Styles.GREEN},
    "Phase 3": {"title": Styles.GREEN},
    "Event": {"title": Styles.CYAN},
    "Executing action": {"title": Styles.CYAN},
    "Prompt": {
        "title": Styles.BLUE,
        "body": Styles.PROMPT,
    },
    "Prompt Messages": {
        "title": Styles.BLUE,
        "body": Styles.PROMPT,
    },
    "Completion": {"title": Styles.BLUE, "body": Styles.COMPLETION},
    "---": {"title": Styles.GREY, "body": Styles.GREY},
}


class BlinkingCursor:
    """Helper class for a blinking cursor."""

    def __init__(self):
        self._stop_event = threading.Event()
        self._thread = threading.Thread(target=self._blink, daemon=True)

    def _blink(self):
        first = True
        cursors = [f"{Styles.COMPLETION_RED} ", f"{Styles.COMPLETION_GREEN} "]
        i = 0
        while not self._stop_event.is_set():
            i += 1
            if first:
                first = False
            else:
                print("\b", end="", flush=True)

            print(f"{cursors[i%2]}", end="", flush=True)

            for _ in range(25):
                time.sleep(0.01)
                if self._stop_event.is_set():
                    break

        print("\b \b", end="", flush=True)

    def start(self):
        if self._thread.is_alive():
            return
        self._stop_event.clear()
        self._thread = threading.Thread(target=self._blink)
        self._thread.start()

    def stop(self):
        if not self._thread.is_alive():
            return
        self._stop_event.set()
        self._thread.join()


class VerboseHandler(logging.StreamHandler):
    """A log handler for verbose mode."""

    def __init__(self, *args, **kwargs):
        super(VerboseHandler, self).__init__(*args, **kwargs)
        self.blinking_cursor = BlinkingCursor()

    def emit(self, record) -> None:
        msg = self.format(record)

        # We check if we're using the spacial syntax with "::" which denotes a title.
        if "::" in msg:
            title, body = msg.split(" :: ", 1)
            title = title.strip()

            title_style = SECTION_COLOR.get(title, {}).get("title", "")
            body_style = SECTION_COLOR.get(title, {}).get("body", "")

            # We remove the title for completion messages and stop the blinking cursor.
            if title == "Completion":
                self.blinking_cursor.stop()
                print(body_style + body + Styles.RESET_ALL)

            # For prompts, we also start the blinking cursor.
            elif title == "Prompt":
                msg = (
                    title_style
                    + title
                    + Styles.RESET_ALL
                    + "\n"
                    + body_style
                    + body
                    + Styles.RESET_ALL
                )
                print(msg, end="")
                self.blinking_cursor.start()

            elif title == "Event":
                # For events, we also color differently the type of event.
                event_name, body = body.split(" ", 1)
                title = title_style + title + Styles.RESET_ALL
                event_name = Styles.EVENT_NAME + event_name + Styles.RESET_ALL
                body = body_style + body + Styles.RESET_ALL
                msg = title + " " + event_name + " " + body

                print(msg)
            else:
                title = title_style + title + Styles.RESET_ALL
                body = body_style + body + Styles.RESET_ALL
                msg = title + " " + body

                print(msg)


def set_verbose(verbose: bool):
    """Configure the verbose mode."""

    if verbose:
        root_logger = logging.getLogger()

        # We set the root logger to INFO so that we can see the messages from the VerboseHandler.
        root_logger.setLevel(logging.INFO)

        # We make sure the log level for the default root console handler is set to WARNING.
        for handler in root_logger.handlers:
            if isinstance(handler, logging.StreamHandler):
                handler.setLevel(logging.WARNING)

        # Next, we also add an instance of the VerboseHandler.
        verbose_handler = VerboseHandler()
        verbose_handler.setLevel(logging.INFO)
        root_logger.addHandler(verbose_handler)

        # Also, we make sure the sentence_transformers log level is set to WARNING.
        logging.getLogger("sentence_transformers").setLevel(logging.WARNING)

        print("Entered verbose mode.")
