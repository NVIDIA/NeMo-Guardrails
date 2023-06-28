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

import os
from typing import Any, List, Optional

import colorama
from colorama import Back, Fore, Style
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib.units import inch
from reportlab.pdfgen import canvas
from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer

from nemoguardrails.actions import action


def create_document(info_ls, field_ls):
    doc = SimpleDocTemplate(
        "./my_form.pdf",
        pagesize=letter,
    )
    styles = getSampleStyleSheet()
    flowables = []
    spacer = Spacer(1, 0.25 * inch)
    # Create a lot of content to make a multipage PDF
    n = len(info_ls)
    for info, field in zip(info_ls, field_ls):
        text = "{} : {}".format(field, info)
        para = Paragraph(text, styles["Normal"])
        flowables.append(para)
        flowables.append(spacer)
    doc.build(flowables)


@action()
async def form_filling(file_name: Optional[str] = None, context: Optional[dict] = None):
    user_query = context.get("last_user_message")
    root_path = os.path.dirname(__file__)
    field_ls = []
    info_ls = []
    colorama.init(autoreset=True)
    print(
        Back.RED
        + Fore.BLUE
        + "====================== Welcome to form filling ========================="
    )

    # taking two inputs at a time
    first_name = input("What is your first name : ")
    field_ls.append("first_name")
    info_ls.append(first_name)
    middle_name = input("Enter your middle name : ")
    field_ls.append("middle_name")
    info_ls.append(middle_name)
    last_name = input("Enter your last name ( or family name) : ")
    field_ls.append("last_name")
    info_ls.append(last_name)
    full_name = [first_name, middle_name, last_name]
    print(Fore.YELLOW + "Your full name entered : ", " ".join(full_name))

    # taking three inputs at a time
    email_entered = input("Enter your email :")
    if "@" not in email_entered:
        print(
            Fore.YELLOW
            + "Entered email : {} is not valid , your email should be in this format maildecoration@domain.countrycode ".format(
                email_entered
            )
        )
        info_ls.append(email_entered)
        field_ls.append("email")
    create_document(info_ls, field_ls)
    print("finish creating my_form.pdf document in your current directory !")
    return True
