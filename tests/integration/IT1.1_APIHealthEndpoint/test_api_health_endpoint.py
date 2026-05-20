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

import httpx

from tests.helpers import api_url, legacy_api_url


def test_api_health_endpoint(integration_server: dict[str, str]) -> None:
    """Requirements: FR-01."""
    response = httpx.get(api_url(integration_server["base_url"], "/health"), timeout=10.0)
    assert response.status_code == 200
    payload = response.json()
    assert payload["ok"] is True
    assert payload["result"]["status"] == "ok"
    assert payload["result"]["service"] == "git-mcp-server"


def test_api_health_endpoint_legacy_alias_compatibility(integration_server: dict[str, str]) -> None:
    """Requirements: FR-01."""
    response = httpx.get(legacy_api_url(integration_server["base_url"], "/health"), timeout=10.0)
    assert response.status_code == 200
    payload = response.json()
    assert payload["ok"] is True
    assert payload["result"]["status"] == "ok"
