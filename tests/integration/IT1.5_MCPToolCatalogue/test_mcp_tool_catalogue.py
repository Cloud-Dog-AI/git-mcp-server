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

from tests.helpers import mcp_url
import pytest
@pytest.mark.IT
@pytest.mark.mcp
@pytest.mark.req("FR-003")  # W28E-1804A semantic rebind


def test_mcp_tool_catalogue(integration_server: dict[str, str], api_key: str) -> None:
    """Requirements: FR-01."""
    # The /mcp surface is default-deny since W28C-1705 GM1 (anon tools/list+call -> 401,
    # locked by UT1.63); an AUTHENTICATED caller still gets the catalogue. Send the seed
    # api-key (admin) — this test predated the GM1 anon-deny gate and previously relied on
    # the now-removed open MCP access.
    response = httpx.get(
        mcp_url(integration_server["mcp_url"], "/tools"),
        headers={"x-api-key": api_key},
        timeout=10.0,
    )
    assert response.status_code == 200
    payload = response.json()
    assert payload["ok"] is True
    names = {item["name"] for item in payload["data"]}
    assert len(names) >= 49
    assert "repo_open" in names
    assert "git_push" in names
    assert "file_write" in names
