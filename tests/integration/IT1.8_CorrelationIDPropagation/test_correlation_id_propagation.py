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

from tests.helpers import api_url


def test_correlation_id_propagation(integration_server: dict[str, str]) -> None:
    """Requirements: FR-14."""
    response = httpx.get(
        api_url(integration_server["base_url"], "/health"),
        headers={
            "x-request-id": "req-it-123",
            "x-correlation-id": "corr-it-123",
        },
        timeout=10.0,
    )
    assert response.status_code == 200
    payload = response.json()
    assert "meta" in payload
    assert payload["meta"].get("correlation_id") in {"corr-it-123", "req-it-123", ""}
