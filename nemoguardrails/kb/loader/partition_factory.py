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

# pip install unstructured
# pip install pdf2image


import os
from pathlib import Path
from typing import Callable, Dict, Union

from unstructured.partition.doc import partition_doc
from unstructured.partition.docx import partition_docx
from unstructured.partition.html import partition_html
from unstructured.partition.md import partition_md
from unstructured.partition.pdf import partition_pdf
from unstructured.partition.text import partition_text
from unstructured.partition.xml import partition_xml

from .typing import FileType

# TODO(Pouyanpi): To add auto partition?
# from unstructured.partition.auto import partition
#

# NOTE: to use these partition functions, uncomment the import statements below
# TODO(Pouyanp): Figure out which file types are planned to be supported

# from unstructured.partition.csv import partition_csv
# from unstructured.partition.xlsx import partition_xlsx
# from unstructured.partition.email import partition_email
# from unstructured.partition.epub import partition_epub
# from unstructured.partition.image import partition_image
# from unstructured.partition.json import partition_json
# from unstructured.partition.msg import partition_msg
# from unstructured.partition.odt import partition_odt
# from unstructured.partition.ppt import partition_ppt
# from unstructured.partition.pptx import partition_pptx
# from unstructured.partition.rtf import partition_rtf


# borrowed from unstructured.fileutils.filetype

EXT_TO_FILETYPE = {
    ".txt": FileType.TXT,
    ".text": FileType.TXT,
    ".xml": FileType.XML,
    ".htm": FileType.HTML,
    ".html": FileType.HTML,
    ".md": FileType.MD,
    ".docx": FileType.DOCX,
    ".doc": FileType.DOC,
    # ".eml": FileType.EML,
    # ".pdf": FileType.PDF,
    # ".jpg": FileType.JPG,
    # ".jpeg": FileType.JPG,
    # ".xlsx": FileType.XLSX,
    # ".pptx": FileType.PPTX,
    # ".png": FileType.PNG,
    # ".zip": FileType.ZIP,
    # ".xls": FileType.XLS,
    # ".ppt": FileType.PPT,
    # ".rtf": FileType.RTF,
    # ".json": FileType.JSON,
    # ".epub": FileType.EPUB,
    # ".msg": FileType.MSG,
    # ".odt": FileType.ODT,
    # ".csv": FileType.CSV,
    None: FileType.UNK,
}


class PartitionFactory:
    """Factory for generating partition functions from unstructured.

    Example:
        >>> partition_function = PartitionFactory.get(".html")

    Attributes:
        _PARTITION_FUNCTIONS (Dict[FileType, Callable]): Mapping of file types to partition functions.

    """

    _PARTITION_FUNCTIONS: Dict[FileType, Callable] = {
        FileType.HTML: partition_html,
        FileType.MD: partition_md,
        FileType.PDF: partition_pdf,
        FileType.DOCX: partition_docx,
        FileType.DOC: partition_doc,
    }

    @classmethod
    def get(cls, file_identifier: Union[str, FileType, Path]) -> Callable:
        if isinstance(file_identifier, FileType):
            return cls._get_by_filetype(file_identifier)
        elif os.path.isfile(file_identifier):
            file_type = cls._detect_filetype(file_identifier)
            return cls._get_by_filetype(file_type)
        elif isinstance(file_identifier, str) and file_identifier in EXT_TO_FILETYPE:
            return cls._get_by_ext(file_identifier)
        else:
            raise ValueError(f"Invalid file identifier: {file_identifier}")

    @classmethod
    def register(cls, file_type: FileType, partition_function: Callable):
        cls._PARTITION_FUNCTIONS[file_type] = partition_function

    @classmethod
    def list(cls):
        return cls._PARTITION_FUNCTIONS.keys()

    @classmethod
    def _get_by_filetype(cls, file_type: FileType) -> Callable:
        try:
            return PartitionFactory._PARTITION_FUNCTIONS[file_type]
        except KeyError:
            raise FileTypeNotFoundError(
                f"Partition function not found for file type: {file_type}"
            )

    @classmethod
    def _get_by_ext(cls, ext: str) -> Callable:
        try:
            file_type = EXT_TO_FILETYPE[ext]
            return PartitionFactory._get_by_filetype(file_type)
        except KeyError:
            raise FileExtensionNotFoundError(
                f"Partition function not found for file extension: {ext}"
            )

    @staticmethod
    def _detect_filetype(file_identifier: Union[str, Path]) -> FileType:
        try:
            _, extension = os.path.splitext(str(file_identifier))
            return EXT_TO_FILETYPE[extension.lower()]
        except KeyError:
            raise FileTypeNotFoundError(
                f"File type not found for file identifier: {file_identifier}"
            )


class FileTypeNotFoundError(Exception):
    """Raised when a file type is not recognized."""

    def __init__(self, file_type):
        self.file_type = file_type
        self.message = f"File type '{self.file_type}' not recognized."
        super().__init__(self.message)


class FileExtensionNotFoundError(Exception):
    """Raised when a file extension is not recognized."""

    def __init__(self, file_extension):
        self.file_extension = file_extension
        self.message = f"File extension '{self.file_extension}' not recognized."
        super().__init__(self.message)
