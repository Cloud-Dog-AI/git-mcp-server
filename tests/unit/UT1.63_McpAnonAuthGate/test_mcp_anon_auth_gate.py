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

"""W28C-1705 GM1 — anonymous ``/mcp`` default-deny gate.

The MCP transport (``create_mcp_app``) previously installed NO auth middleware, so an
anonymous caller could ``tools/list`` the full 63-tool catalogue AND ``tools/call`` every
tool — including ``admin_user_create``, ``admin_profile_create`` and ``repo_open``. This
suite proves the gate against the full app (real auth middleware, not the bare router):

* anon ``POST /mcp`` (tools/list, tools/call) is DENIED (401) — default-deny BEFORE dispatch;
* an authenticated caller (seed api-key) still gets the catalogue (200) — no regression;
* the read-only status surface stays reachable without a credential.
"""


from __future__ import annotations
import pytest

from fastapi.testclient import TestClient

from git_mcp_server.mcp_server import create_mcp_app


def _client() -> tuple[TestClient, str]:
    app = create_mcp_app(env_files=["tests/env-UT"])
    return TestClient(app, raise_server_exceptions=False), app.state.seed_api_key
# FR-1.18 traceability marker for existing git-mcp coverage.
@pytest.mark.UT
@pytest.mark.mcp
@pytest.mark.req("FR-003")  # W28E-1804A semantic rebind


def test_anon_mcp_tools_list_denied() -> None:
    """Requirements: CS-01 (W28C-1705 GM1)."""
    client, _ = _client()
    resp = client.post(
        "/mcp", json={"jsonrpc": "2.0", "id": 1, "method": "tools/list", "params": {}}
    )
    assert resp.status_code == 401, resp.text
    assert "result" not in resp.text  # no catalogue leaked to an anonymous caller
# FR-1.18 traceability marker for existing git-mcp coverage.
@pytest.mark.UT
@pytest.mark.mcp
@pytest.mark.req("FR-003")  # W28E-1804A semantic rebind


def test_anon_mcp_tools_call_admin_denied_before_dispatch() -> None:
    """Requirements: CS-01 (W28C-1705 GM1)."""
    client, _ = _client()
    resp = client.post(
        "/mcp",
        json={
            "jsonrpc": "2.0",
            "id": 2,
            "method": "tools/call",
            "params": {
                "name": "admin_user_create",
                "arguments": {"user_id": "x", "username": "x", "email": "x@example.invalid"},
            },
        },
    )
    assert resp.status_code == 401, resp.text
    # default-deny BEFORE dispatch: the tool never runs, so no JSON-RPC result body
    assert "result" not in resp.text
# FR-1.18 traceability marker for existing git-mcp coverage.
@pytest.mark.UT
@pytest.mark.mcp
@pytest.mark.req("FR-003")  # W28E-1804A semantic rebind


def test_authed_mcp_tools_list_serves() -> None:
    """Requirements: CS-01 (W28C-1705 GM1) — authenticated path is not regressed."""
    client, key = _client()
    resp = client.post(
        "/mcp",
        json={"jsonrpc": "2.0", "id": 3, "method": "tools/list", "params": {}},
        headers={"x-api-key": key},
    )
    assert resp.status_code == 200, resp.text
    assert resp.json()["result"]["tools"], "authed tools/list must return the catalogue"
# FR-1.18 traceability marker for existing git-mcp coverage.
@pytest.mark.UT
@pytest.mark.mcp
@pytest.mark.req("FR-003")  # W28E-1804A semantic rebind


def test_status_surface_not_gated() -> None:
    """Read-only service status must stay reachable without a credential (never 401)."""
    client, _ = _client()
    assert client.get("/health").status_code != 401
# FR-1.18 traceability marker for existing git-mcp coverage.
@pytest.mark.UT
@pytest.mark.mcp
@pytest.mark.req("FR-003")  # W28E-1804A semantic rebind


def test_authed_mcp_caller_resolves_admin_role() -> None:
    """GM1: a gated MCP must still AUTHORISE authenticated callers (role_bindings present).

    Without role_bindings on the MCP AdminRuntime, an authenticated key resolved to zero
    roles and every profile-scoped tool returned 'Access denied'. The seed/configured keys
    must resolve to the admin role.
    """
    app = create_mcp_app(env_files=["tests/env-UT"])
    admin_runtime = app.state.admin_runtime
    assert "admin" in set(admin_runtime.resolve_roles("integration-user"))
    assert "admin" in set(admin_runtime.resolve_roles("configured-api-key"))
