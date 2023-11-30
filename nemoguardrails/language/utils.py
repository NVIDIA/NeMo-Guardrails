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

import uuid
from typing import List, Optional, Text, Tuple


def split_max(text, separator, max_instances):
    """
    Split a text into parts using a separator, with a maximum number of parts.

    Args:
        text (str): The input text to be split.
        separator (str): The separator used for splitting.
        max_instances (int): The maximum number of parts to create.

    Returns:
        List[str]: A list of parts obtained after splitting the text.

    Note:
        This function splits the input text into parts using the specified separator.
        If the number of resulting parts exceeds the provided `max_instances`, it combines
        the extra parts into the last part.

    """
    parts = text.split(separator)
    if len(parts) > max_instances + 1:
        new_parts = parts[0:max_instances]
        new_parts.append(separator.join(parts[max_instances:]))
        parts = new_parts

    return parts


def split_args(args_str: str) -> List[str]:
    """
    Split a string representing function arguments into individual argument values.

    Args:
        args_str (str): The string with function arguments, potentially containing keywords and complex data types.

    Returns:
        List[str]: A list of individual argument values.

    Note:
        This function correctly handles splitting function arguments, including keyword arguments,
        and nested strings, lists, and dictionaries.

    """

    parts = []
    stack = []

    current = []

    closing_char = {"[": "]", "(": ")", "{": "}", "'": "'", '"': '"'}

    for char in args_str:
        if char in "([{":
            stack.append(char)
            current.append(char)
        elif char in "\"'" and (len(stack) == 0 or stack[-1] != char):
            stack.append(char)
            current.append(char)
        elif char in ")]}\"'":
            if char != closing_char[stack[-1]]:
                raise ValueError(
                    f"Invalid syntax for string: {args_str}; "
                    f"expecting {closing_char[stack[-1]]} and got {char}"
                )
            stack.pop()
            current.append(char)
        elif char == "," and len(stack) == 0:
            parts.append("".join(current))
            current = []
        else:
            current.append(char)

    parts.append("".join(current))

    return [part.strip() for part in parts]


def get_numbered_lines(content: str):
    """
    Extract numbered lines from content, ignoring comments and empty lines.

    Args:
        content (str): The content to extract numbered lines from.

    Returns:
        List[dict]: A list of dictionaries, each containing information about a numbered line.

    Note:
        This function extracts numbered lines from the input content, excluding comments and empty lines.
        It provides information about the text, line number, indentation level, and comments of each line.

    """
    raw_lines = content.split("\n")
    lines = []
    i = 0
    multiline_comment = False
    current_comment = None
    while i < len(raw_lines):
        raw_line = raw_lines[i].strip()

        # If we have a line comment, we record it
        if raw_line.startswith("#"):
            if current_comment is None:
                current_comment = raw_line[1:].strip()
            else:
                # For line comments on consecutive lines, we gather them
                current_comment += "\n" + raw_line[1:].strip()

        # Get rid of empty lines and comments
        if len(raw_line) == 0 or raw_line[0] == "#":
            i += 1
            continue

        # If there is a comment at the end of the line, we first remove it
        parts = word_split(raw_line, "#")
        raw_line = parts[0]

        if not multiline_comment and raw_line.startswith('"""'):
            if raw_line == '"""' or not raw_line.endswith('"""'):
                multiline_comment = True
                current_comment = raw_line[3:]
            else:
                current_comment = raw_line[3:-3]
            i += 1
            continue

        if multiline_comment:
            if raw_line.endswith('"""'):
                current_comment += "\n" + raw_line[0:-3]
                multiline_comment = False
            else:
                current_comment += "\n" + raw_line

            i += 1
            continue

        # Compute indentation level
        ind = 0
        while raw_lines[i][ind] == " ":
            ind += 1

        # As long as the line ends with "\", we also append the next lines
        # but without the indentation.
        # Also, if there's an active "operator" like "or", we also continue to the next line
        text = raw_line
        while i < len(raw_lines) - 1 and text[-1] == "\\" or text.endswith(" or"):
            i += 1
            if text[-1] == "\\":
                text = text[0:-1]
            if text[-1] != " ":
                text = text + " "

            text = text + raw_lines[i].strip()

        lines.append(
            {
                # Get rid of any white space
                "text": text,
                "number": i + 1,
                "indentation": ind,
                "comment": current_comment,
            }
        )
        current_comment = None

        i += 1

    return lines


def remove_token(token: str, line: str):
    """
    Remove a specified token from the beginning of a line.

    Args:
        token (str): The token to be removed.
        line (str): The input line from which the token should be removed.

    Returns:
        str: The modified line with the token removed.

    Raises:
        AssertionError: If the token is not found at the beginning of the line.

    """
    line = line.strip()
    parts = split_max(line, " ", 1)
    assert parts[0] == token

    return parts[1].strip() if len(parts) > 1 else ""


def extract_main_token(text: str):
    """
    Extract the main token from a line of text.

    Args:
        text (str): The input text line.

    Returns:
        str: The main token extracted from the line.

    """    main_token = text.split(" ")[0]

    # For else, we also want to catch the next keyword (if/when)
    if main_token == "else" and text.strip() != "else":
        main_token = "else " + split_max(text, " ", 1)[1].strip().split(" ")[0]

    if main_token == "go":
        main_token = "go " + split_max(text, " ", 1)[1].strip().split(" ")[0]

    return main_token


def char_split(
    text: str, c: str, ignore_parenthesis=False, ignore_strings=False
) -> List[str]:
    """
    Split a string by a specified character, considering parentheses and strings.

    Args:
        text (str): The text to split.
        c (str): The character to use as the separator.
        ignore_parenthesis (bool, optional): If True, parentheses are not considered for splitting.
            Defaults to False.
        ignore_strings (bool, optional): If True, strings enclosed in double quotes are not considered for splitting.
            Defaults to False.

    Returns:
        List[str]: A list of parts obtained after splitting the text.

    """
    parts = []

    # Edge case
    if text == "":
        return [""]

    # The current position
    i = 0

    # The start of the current part
    s = 0
    in_string = False
    parenthesis_counter = 0

    while i < len(text) - 1:
        if in_string:
            if text[i] == '"':
                in_string = False
            i += 1
        else:
            if text[i] == '"' and not ignore_strings:
                in_string = True

            # Only split by character when not inside a parenthesis
            if text[i] == c and parenthesis_counter == 0:
                part = text[s:i].strip()
                if len(part) > 0:
                    parts.append(part)

                i += 1
                s = i
            else:
                if text[i] in ["(", "[", "{"] and not ignore_parenthesis:
                    parenthesis_counter += 1
                elif text[i] in [")", "]", "}"]:
                    parenthesis_counter -= 1

                i += 1

    if s < len(text):
        part = text[s:].strip()
        if len(part) > 0:
            parts.append(part)

    return parts


# This implementation must stay here as it is transpiled into JS, although a
# duplicate of the one in utils.
# noinspection DuplicatedCode
def word_split(text: str, word: str):
    """
    Split a string by a specified word, considering strings enclosed in double quotes.

    Args:
        text (str): The input text to be split.
        word (str): The word to be used as the separator.

    Returns:
        List[str]: A list of parts obtained after splitting the text.

    """    
    parts = []

    # Edge case
    if text == "":
        return [""]

    # The current position
    i = 0

    # The start of the current part
    s = 0
    in_string = False
    while i < len(text) - len(word):
        if in_string:
            if text[i] == '"':
                in_string = False
            i += 1
        else:
            if text[i] == '"':
                in_string = True

            if text[i : i + len(word)] == word:
                part = text[s:i].strip()
                if len(part) > 0:
                    parts.append(part)

                i += len(word)
                s = i
            else:
                i += 1

    if s < len(text):
        part = text[s:].strip()

        # edge case, make sure the part does not end with the actual word
        if part.endswith(word):
            part = part[0 : -1 * len(word)]

        if len(part) > 0:
            parts.append(part)

    return parts


def ws_tokenize(text):
    """
    Tokenize a text by whitespace while considering strings enclosed in double quotes.

    Args:
        text (str): The input text to be tokenized.

    Returns:
        List[str]: A list of tokens obtained after tokenizing the text.

    """    
    return word_split(text, " ")


def params_tokenize(text):
    """
    Tokenize a text specifically for parsing parameters, considering strings enclosed in double quotes.

    Args:
        text (str): The input text to be tokenized for parameter parsing.

    Returns:
        List[str]: A list of tokens obtained after tokenizing the text.

    """    
    tokens = []

    # The current position
    i = 0

    # The start of the current part
    s = 0
    in_string = False
    while i < len(text):
        if in_string:
            if text[i] == '"':
                in_string = False
            i += 1
        else:
            if text[i] == '"':
                in_string = True

            if text[i] in [" ", "-", ":", ",", "="]:
                token = text[s:i].strip()
                if len(token) > 0:
                    tokens.append(token)

                if text[i] != " ":
                    tokens.append(text[i])

                i += 1
                s = i
            else:
                i += 1

    if s < len(text):
        token = text[s:].strip()
        if len(token) > 0:
            tokens.append(token)

    return tokens


def get_stripped_tokens(tokens: List[str]):
    """
    Get a list of tokens with leading and trailing whitespace removed.

    Args:
        tokens (List[str]): The list of tokens to be stripped.

    Returns:
        List[str]: A list of tokens with leading and trailing whitespace removed.

    """
    return [token.strip() for token in tokens]


def get_first_key(d: dict):
    """
    Get the first key from a dictionary.

    Args:
        d (dict): The input dictionary.

    Returns:
        Any: The first key found in the dictionary.

    """
    for k in d.keys():
        return k


def extract_topic_object(text: Text) -> Tuple[Text, Optional[Text]]:
    """
    Extract the object from the definition of a topic.

    Supported expressions:
        - is_open_source
        - is_open_source for @roboself
        - is_open_source for $company
        - is_open_source($roboself)
        - is_open_source(@roboself)

    Args:
        text (Text): The input text containing a topic definition.

    Returns:
        Tuple[Text, Optional[Text]]: A tuple containing the topic name and the object (if present).

    Raises:
        AssertionError: If the input text does not match any of the supported expressions.

    """
    if " " in text:
        parts = ws_tokenize(text)
        assert len(parts) == 3
        assert parts[1] == "for"

        return parts[0], parts[2]
    elif "(" in text:
        parts = split_max(text[0:-1], "(", 1)
        assert len(parts) == 2
        return parts[0], parts[1]
    else:
        return text, None


def parse_package_name(text):
    """
    Extract and normalize a package name from text.

    Args:
        text (str): The input text containing a package name.

    Returns:
        str: The normalized package name.

    """
    # get rid of quotes
    package_name = text
    if package_name[0] == '"' or package_name[0] == "'":
        package_name = package_name[1:-1]

    # Get rid of the "bot/"
    if package_name[0:4] == "bot/":
        package_name = split_max(package_name, "/", 1)[1]

    return package_name


def new_uuid() -> str:
    """
    Generate a new UUID v4.

    In testing mode, it will generate a predictable set of UUIDs to help debugging.

    Returns:
        str: A new UUID v4.

    """
    return str(uuid.uuid4())


def string_hash(s):
    """
    Calculate a simple hash value for a given string.

    This function computes a hash value for the input string using a simple algorithm.
    The equivalent implementation in JavaScript is provided below for reference.

    JavaScript Equivalent:
    ----------------------
    ```javascript
    module.exports.string_hash = function(s){
      let hash = 0;
      if (s.length === 0) return hash;
      for (let i = 0; i < s.length; i++) {
        let char = s.charCodeAt(i);
        hash = ((hash<<5)-hash)+char;
        hash = hash & hash; // Convert to 32bit integer
      }
      if (hash < 0) hash *= -1;

      return hash.toString(16);
    }
    ```

    Args:
        s (str): The input string for which the hash is calculated.

    Returns:
        str: A hexadecimal string representing the calculated hash value.

    """
    _hash = 0
    if len(s) == 0:
        return 0
    for i in range(len(s)):
        _char = ord(s[i])
        _hash = ((_hash << 5) - _hash) + _char
        _hash = _hash & 0xFFFFFFFF

    if _hash >= (1 << 31):
        _hash = -1 * (_hash - (1 << 32))

    return hex(_hash)[2:]
