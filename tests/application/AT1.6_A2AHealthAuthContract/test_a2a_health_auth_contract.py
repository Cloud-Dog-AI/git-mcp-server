# Copyright 2026 Cloud-Dog, Viewdeck Engineering Limited
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

from __future__ import annotations

import os

import httpx

from tests.helpers import a2a_url


def test_application_a2a_health_requires_bearer_contract(application_server: str) -> None:
    """Requirements: FR-04."""
    expected_key = "12345678"
    configured_key = os.environ.get("TEST_A2A_API_KEY", "").strip()
    assert configured_key == expected_key

    no_auth = httpx.get(a2a_url(application_server, "/health"), timeout=10.0)
    assert no_auth.status_code == 401

    x_api_key_only = httpx.get(
        a2a_url(application_server, "/health"),
        headers={"x-api-key": configured_key},
        timeout=10.0,
    )
    assert x_api_key_only.status_code == 401

    wrong_key = httpx.get(
        a2a_url(application_server, "/health"),
        headers={"Authorization": "Bearer wrong-key"},
        timeout=10.0,
    )
    assert wrong_key.status_code == 401

    valid_auth = httpx.get(
        a2a_url(application_server, "/health"),
        headers={"Authorization": f"Bearer {configured_key}"},
        timeout=10.0,
    )
    assert valid_auth.status_code == 200
    payload = valid_auth.json()
    assert payload["ok"] is True
    assert payload["result"]["interface"] == "a2a"
