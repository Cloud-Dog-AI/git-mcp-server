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

"""W28A-731-R5 — API/MCP service tier: api-key -> flat-role resolution.

The git-mcp WebUI front-door login is username/password (``AUTH_MODE=cookie``;
see ``test_flat_role_login.py``). Separately, the API/MCP *service* tier uses
api-key auth (``auth.mode=api_key``) for non-browser callers. To prove flat-role
RBAC on that service tier, the API bootstrap-seeds three demo keys — admin /
read-write / read-only — each owned by a user bound to its tool-RBAC role(s).

These tests lock the service-tier behaviour the SPA's ``/auth/me`` X-API-Key
fallback also defers to: the keys are seeded + written to a container-readable
runtime path, ``/whoami`` resolves each key to the right tool roles, and the
read-only key is 403'd on a write tool while admin is not. They do NOT define the
browser login mode — that is username/password.
"""

from __future__ import annotations

from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from git_mcp_server.api_server import create_api_app


@pytest.fixture()
def api_client(monkeypatch, tmp_path: Path):
    seed_file = tmp_path / "seed_api_key.txt"
    monkeypatch.setenv("GIT_MCP_SEED_KEY_FILE", str(seed_file))
    monkeypatch.setenv("CLOUD_DOG__RUNTIME__SEED_KEY_FILE", str(seed_file))
    app = create_api_app(env_files=["tests/env-UT"])
    return TestClient(app, raise_server_exceptions=False), tmp_path


def _read_demo_keys(tmp_path: Path) -> dict[str, str]:
    keys_dir = tmp_path / "flat_role_keys"
    return {p.stem: p.read_text(encoding="utf-8").strip() for p in keys_dir.glob("*.key")}


# Covers: CS-1.2 (W28A-731 api_key 3-key flat-login)
@pytest.mark.UT
@pytest.mark.mcp
@pytest.mark.req("FR-022")  # W28E-1804A semantic rebind
def test_three_demo_keys_seeded_to_disk(api_client) -> None:
    _client, tmp_path = api_client
    keys = _read_demo_keys(tmp_path)
    assert set(keys) == {"admin", "read-write", "read-only"}
    # Distinct, non-empty secrets.
    assert all(v for v in keys.values())
    assert len(set(keys.values())) == 3


# Covers: CS-1.2 (W28A-731 api_key 3-key flat-login)
@pytest.mark.UT
@pytest.mark.mcp
@pytest.mark.req("FR-022")  # W28E-1804A semantic rebind
def test_whoami_resolves_each_key_to_its_tool_roles(api_client) -> None:
    client, tmp_path = api_client
    keys = _read_demo_keys(tmp_path)
    cases = {
        "admin": {"admin"},
        "read-write": {"writer", "reader"},
        "read-only": {"reader"},
    }
    for flat, expected in cases.items():
        r = client.get("/api/v1/whoami", headers={"x-api-key": keys[flat]})
        assert r.status_code == 200, f"{flat}: {r.text}"
        assert set(r.json()["result"]["roles"]) == expected, flat


# Covers: CS-1.2 (W28A-731 api_key 3-key flat-login)
@pytest.mark.UT
@pytest.mark.mcp
@pytest.mark.req("FR-022")  # W28E-1804A semantic rebind
def test_whoami_unknown_key_is_401(api_client) -> None:
    client, _tmp = api_client
    r = client.get("/api/v1/whoami", headers={"x-api-key": "not-a-real-key"})
    assert r.status_code == 401


# Covers: CS-1.2 (W28A-731 api_key 3-key flat-login)
@pytest.mark.UT
@pytest.mark.mcp
@pytest.mark.req("FR-022")  # W28E-1804A semantic rebind
def test_read_only_key_denied_write_tool(api_client) -> None:
    client, tmp_path = api_client
    keys = _read_demo_keys(tmp_path)
    r = client.post(
        "/api/v1/tools/git_commit",
        json={"message": "x"},
        headers={"x-api-key": keys["read-only"]},
    )
    assert r.status_code == 403, r.text  # RBAC denial, not 401/400


# Covers: CS-1.2 (W28A-731 api_key 3-key flat-login)
@pytest.mark.UT
@pytest.mark.mcp
@pytest.mark.req("FR-022")  # W28E-1804A semantic rebind
def test_read_only_key_not_denied_read_tool(api_client) -> None:
    client, tmp_path = api_client
    keys = _read_demo_keys(tmp_path)
    # A read tool is RBAC-permitted for reader; it may fail downstream (e.g. 400
    # for a missing workspace) but must NOT be the 403 RBAC denial or a 401.
    r = client.post(
        "/api/v1/tools/git_status",
        json={},
        headers={"x-api-key": keys["read-only"]},
    )
    assert r.status_code not in (401, 403), r.text


# Covers: CS-1.2 (W28A-731 api_key 3-key flat-login)
@pytest.mark.UT
@pytest.mark.mcp
@pytest.mark.req("FR-022")  # W28E-1804A semantic rebind
def test_admin_key_not_denied_write_tool(api_client) -> None:
    client, tmp_path = api_client
    keys = _read_demo_keys(tmp_path)
    r = client.post(
        "/api/v1/tools/git_commit",
        json={"message": "x"},
        headers={"x-api-key": keys["admin"]},
    )
    assert r.status_code != 403, r.text  # admin is never RBAC-denied
