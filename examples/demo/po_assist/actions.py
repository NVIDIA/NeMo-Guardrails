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

from nemoguardrails.actions import action


@action(name="GetUserProfileAction")
async def get_user_profile():
    return {"name": "John Doe", "email": "john@abc.com"}


@action(name="GetWeatherInfoAction")
async def get_weather_info():
    return {"temperature": "28", "conditions": "cloudy"}


@action(name="GetVendorAction")
async def get_vendor(vendor_name: str):
    vendors = [
        {"name": "Avantel - Berlin", "id": "1"},
        {"name": "Avantel - Chicago", "id": "2"},
        {"name": "NVIDIA", "id": "3"},
        {"name": "Target CW", "id": "4"},
        {"name": "Target XY", "id": "5"},
    ]
    return list(filter(lambda v: vendor_name.lower() in v["name"].lower(), vendors))


@action(name="CreatePurchaseRequisitionAction")
async def create_purchase_requisition(vendor_id: str):
    return {"pr_id": str(uuid.uuid4())[0:6], "vendor_id": vendor_id}


@action(name="CreatePurchaseOrderAction")
async def create_purchase_order(pr_id: str, target_date: str):
    return {"po_id": str(uuid.uuid4())[0:6], "pr_id": pr_id, "target_date": target_date}
