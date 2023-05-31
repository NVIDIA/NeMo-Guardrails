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

from typing import List

import yaml

import re


def split_markdown_in_topic_chunks(
    content: str, max_chunk_size: int = 400
) -> List[dict]:
    """Splits a markdown content into topic chunks.

    :param content: The markdown content to be split.
    :param max_chunk_size: The maximum size of a chunk.
    """

    chunks = []
    lines = content.strip().split("\n")

    # Meta information for the whole document
    meta = {}

    # If there's a code block at the beginning, with meta data, we parse that first.
    if lines[0].startswith("```"):
        meta_yaml = ""
        lines = lines[1:]
        while not lines[0].startswith("```"):
            meta_yaml += lines[0] + "\n"
            lines = lines[1:]
        lines = lines[1:]

        meta.update(yaml.safe_load(meta_yaml))

    # Every section and subsection title will be part of the title of the chunk.
    chunk_title_parts = []

    # The data for the current chunk.
    chunk_body_lines = []
    chunk_size = 0

    def _record_chunk():
        nonlocal chunk_body_lines, chunk_size

        body = "\n".join(chunk_body_lines).strip()
        lines = body.split("\n")
        chunks_to_add = []

        # Split the body into chunks of sentences
        current_chunk = ""
        for line in lines:
            line = line.strip()
            if line:
                # Exclude periods in abbreviations, words beginning with a capital letter, and split sentences after periods or question marks
                sentences = re.split(r"(?<!\w\.\w.)(?<![A-Z][a-z]\.)(?<=\.|\?)\s", line)
                for sentence in sentences:
                    if len(current_chunk) + len(sentence) <= max_chunk_size:
                        current_chunk += sentence + " "
                    else:
                        if current_chunk:
                            chunks_to_add.append(current_chunk.strip())
                        if len(sentence) <= max_chunk_size:
                            # To prevent the length of a single sentence from exceeding max_chunk_size, the approach here is to directly discard sentences exceeding this length
                            current_chunk = sentence + " "

            elif current_chunk:
                chunks_to_add.append(current_chunk.strip())
                current_chunk = ""

        if current_chunk:
            chunks_to_add.append(current_chunk.strip())

        # Create chunks from the split sentences
        for chunk in chunks_to_add:
            if chunk:
                chunks.append(
                    {
                        "title": " - ".join(chunk_title_parts),
                        "body": chunk,
                        **meta,
                    }
                )

        chunk_body_lines = []
        chunk_size = 0


    i = 0
    while i < len(lines):
        line = lines[i]

        if line.startswith("#"):
            # If we have a chunk up to this point, we need to record it
            if chunk_body_lines:
                _record_chunk()

            # Update the title parts with the new section/subsection
            level = 0
            while len(line) > 0 and line[0] == "#":
                level += 1
                line = line[1:]

            # Remove all title parts greater than the current level
            chunk_title_parts[level - 1 :] = []
            chunk_title_parts.append(line.strip())

        elif line.strip() == "":
            chunk_body_lines.append("")

            # If the chunk is over the desired size, we reset it
            if chunk_size > max_chunk_size:
                _record_chunk()
        else:

            chunk_body_lines.append(line)
            chunk_size += len(line)

        i += 1

    if chunk_body_lines:
        _record_chunk()

    return chunks
