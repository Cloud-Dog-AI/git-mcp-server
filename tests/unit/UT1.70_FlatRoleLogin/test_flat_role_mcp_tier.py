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

"""W28A-731-R5 — flat-role enforcement on the MCP tier (read-only write -> 403 everywhere).

The 3 flat demo keys are seeded DETERMINISTICALLY (derived from the shared configured
``git.api_key``) so the MCP server — a separate process — registers the SAME keys as the
API server. A read-only key therefore resolves to ``reader`` on the MCP tier too, so a
read-only WRITE via ``/mcp/tools/*`` is denied (403), matching the API tier. anon /mcp
stays 401 (W28C-1705 GM1 gate, UT1.63).
"""

from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

from git_mcp_server.flat_demo_keys import derive_flat_demo_keys
from git_mcp_server.mcp_server import create_mcp_app

_SEED = "ut-flat-mcp-seed-731"


@pytest.fixture()
def mcp_client(monkeypatch) -> TestClient:
    monkeypatch.setenv("CLOUD_DOG__GIT__API_KEY", _SEED)
    app = create_mcp_app(env_files=["tests/env-UT"])
    return TestClient(app, raise_server_exceptions=False)


def _keys() -> dict[str, str]:
    return derive_flat_demo_keys(_SEED)


# Covers: CS-1.2 (W28A-731 flat-role enforcement on the MCP tier)
@pytest.mark.UT
@pytest.mark.mcp
@pytest.mark.req("FR-022")  # W28E-1804A semantic rebind
def test_anon_mcp_tool_call_denied(mcp_client: TestClient) -> None:
    resp = mcp_client.post("/mcp/tools/git_commit", json={"message": "x"})
    assert resp.status_code == 401, resp.text  # GM1 anon-deny


# Covers: CS-1.2 (W28A-731 flat-role enforcement on the MCP tier)
@pytest.mark.UT
@pytest.mark.mcp
@pytest.mark.req("FR-022")  # W28E-1804A semantic rebind
def test_read_only_key_denied_write_on_mcp(mcp_client: TestClient) -> None:
    resp = mcp_client.post(
        "/mcp/tools/git_commit",
        json={"message": "x"},
        headers={"x-api-key": _keys()["read-only"]},
    )
    assert resp.status_code == 403, resp.text  # reader role -> RBAC denial, not 401


# Covers: CS-1.2 (W28A-731 flat-role enforcement on the MCP tier)
@pytest.mark.UT
@pytest.mark.mcp
@pytest.mark.req("FR-022")  # W28E-1804A semantic rebind
def test_admin_key_not_denied_write_on_mcp(mcp_client: TestClient) -> None:
    resp = mcp_client.post(
        "/mcp/tools/git_commit",
        json={"message": "x"},
        headers={"x-api-key": _keys()["admin"]},
    )
    assert resp.status_code != 403, resp.text  # admin authorised (may 4xx downstream for args)
    assert resp.status_code != 401, resp.text


# Covers: CS-1.2 (W28A-731 flat-role enforcement on the MCP tier)
@pytest.mark.UT
@pytest.mark.mcp
@pytest.mark.req("FR-022")  # W28E-1804A semantic rebind
def test_read_write_key_not_denied_write_on_mcp(mcp_client: TestClient) -> None:
    resp = mcp_client.post(
        "/mcp/tools/git_commit",
        json={"message": "x"},
        headers={"x-api-key": _keys()["read-write"]},
    )
    assert resp.status_code != 403, resp.text
    assert resp.status_code != 401, resp.text
