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

"""W28A-731-R4 (Thread a5) — flat WebUI login for git-mcp-server.

Locks the PROGRAM-IDAM-RECOVERY-2 Thread-a contract on the git-mcp web tier:

* the static UI is PUBLIC to an anonymous browser (login box renders — no 401);
* the DATA APIs stay auth-gated (anon -> 401);
* the three flat roles admin / read-write / read-only all log in, and the
  session echoes the shared-idam-derived flat role + permissions;
* a logged-in read-only session is denied writes inline (403, never 401/blank);
* the WebUI front-door login is username/password: the served AUTH_MODE is
  "cookie" so the SPA renders the username/password form that /auth/login
  accepts. (A non-browser X-API-Key still materialises an admin service
  principal on /auth/me — a separate service-account path, not the browser
  login mode.)

Behaviour is proven via the FastAPI TestClient (no live server).
"""

from __future__ import annotations

from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from git_mcp_server.web_server import create_web_app

_ADMIN_PW = "admin-secret-731"
_RW_PW = "rw-secret-731"
_RO_PW = "ro-secret-731"
_API_KEY = "ut-service-key-731"


def _build_ui_dist(root: Path) -> Path:
    """Create a minimal built SPA tree so the static front-door has a shell."""
    ui_root = root / "ui-dist"
    assets_root = ui_root / "assets"
    assets_root.mkdir(parents=True, exist_ok=True)
    (ui_root / "index.html").write_text(
        "<!doctype html><html><head><title>Git MCP UI</title></head>"
        '<body><div id="root"></div>'
        '<script src="/runtime-config.js"></script></body></html>\n',
        encoding="utf-8",
    )
    (assets_root / "app.js").write_text("console.log('ui');\n", encoding="utf-8")
    return ui_root


@pytest.fixture()
def client(monkeypatch, tmp_path: Path) -> TestClient:
    ui_root = _build_ui_dist(tmp_path)
    monkeypatch.setenv("CLOUD_DOG__WEB__UI_DIST_DIR", ui_root.as_posix())
    monkeypatch.setenv("CLOUD_DOG__MCP_SERVER__BASE_PATH", "/mcp")
    monkeypatch.setenv("CLOUD_DOG__RUNTIME__A2A_TEST_API_KEY", "12345678")
    monkeypatch.setenv("CLOUD_DOG__GIT__API_KEY", _API_KEY)
    monkeypatch.setenv("CLOUD_DOG__WEB_LOGIN__PASSWORD", _ADMIN_PW)
    monkeypatch.setenv("CLOUD_DOG__WEB_LOGIN__READ_WRITE_PASSWORD", _RW_PW)
    monkeypatch.setenv("CLOUD_DOG__WEB_LOGIN__READ_ONLY_PASSWORD", _RO_PW)
    app = create_web_app(env_files=["tests/env-UT"])
    return TestClient(app, raise_server_exceptions=False)


def _login(client: TestClient, username: str, password: str):
    return client.post("/auth/login", json={"username": username, "password": password})


# --------------------------------------------------------------------------- #
# Public static front-door (anonymous can load the login box)
# --------------------------------------------------------------------------- #
# Covers: CS-1.2 (W28A-731 flat-role login + RBAC)
@pytest.mark.UT
@pytest.mark.mcp
@pytest.mark.req("FR-022")  # W28E-1804A semantic rebind
def test_static_ui_public_to_anon(client: TestClient) -> None:
    """Anonymous GET of the SPA shell + login route + runtime-config = 200."""
    for path in ("/", "/login", "/dashboard"):
        resp = client.get(path)
        assert resp.status_code == 200, f"{path} -> {resp.status_code}"
        assert "Git MCP UI" in resp.text, f"{path} did not serve the SPA shell"

    rc = client.get("/runtime-config.js")
    assert rc.status_code == 200
    assert rc.headers["content-type"].startswith("application/javascript")
    # Username/password WebUI: the served AUTH_MODE advertises the cookie login
    # form, matching the /auth/login username/password contract (W28A-731-R5).
    assert '"AUTH_MODE": "cookie"' in rc.text
    assert '"api_key"' not in rc.text

    assets = client.get("/assets/app.js")
    assert assets.status_code == 200


# --------------------------------------------------------------------------- #
# Data APIs auth-gated (anon -> 401)
# --------------------------------------------------------------------------- #
# Covers: CS-1.2 (W28A-731 flat-role login + RBAC)
@pytest.mark.UT
@pytest.mark.mcp
@pytest.mark.req("FR-022")  # W28E-1804A semantic rebind
def test_data_apis_gated_for_anon(client: TestClient) -> None:
    """Anonymous data-surface calls are 401 (never served to anon)."""
    for path in ("/api/v1/profiles", "/api/v1/tools", "/app/v1/profiles"):
        resp = client.get(path)
        assert resp.status_code == 401, f"{path} -> {resp.status_code} (expected 401)"


# --------------------------------------------------------------------------- #
# Three flat roles all log in; session echoes shared-derived role/permissions
# --------------------------------------------------------------------------- #
# Covers: CS-1.2 (W28A-731 flat-role login + RBAC)
@pytest.mark.UT
@pytest.mark.mcp
@pytest.mark.req("FR-022")  # W28E-1804A semantic rebind
def test_admin_login_flat_role(client: TestClient) -> None:
    resp = _login(client, "admin", _ADMIN_PW)
    assert resp.status_code == 200, resp.text
    user = resp.json()["user"]
    assert user["roles"] == ["admin"]
    assert user["permissions"] == ["*"]
    me = client.get("/auth/me")
    assert me.json()["user"]["roles"] == ["admin"]


# Covers: CS-1.2 (W28A-731 flat-role login + RBAC)
@pytest.mark.UT
@pytest.mark.mcp
@pytest.mark.req("FR-022")  # W28E-1804A semantic rebind
def test_read_write_login_flat_role(client: TestClient) -> None:
    resp = _login(client, "read-write", _RW_PW)
    assert resp.status_code == 200, resp.text
    user = resp.json()["user"]
    assert user["roles"] == ["read-write"]
    # read-write gets the shared user baseline PLUS git write/execute use-perms.
    perms = set(user["permissions"])
    assert {"git:read", "git:write", "git:execute"} <= perms
    assert "*" not in perms


# Covers: CS-1.2 (W28A-731 flat-role login + RBAC)
@pytest.mark.UT
@pytest.mark.mcp
@pytest.mark.req("FR-022")  # W28E-1804A semantic rebind
def test_read_only_login_flat_role(client: TestClient) -> None:
    resp = _login(client, "read-only", _RO_PW)
    assert resp.status_code == 200, resp.text
    user = resp.json()["user"]
    assert user["roles"] == ["read-only"]
    perms = set(user["permissions"])
    assert "*" not in perms
    assert "git:write" not in perms


# Covers: CS-1.2 (W28A-731 flat-role login + RBAC)
@pytest.mark.UT
@pytest.mark.mcp
@pytest.mark.req("FR-022")  # W28E-1804A semantic rebind
def test_wrong_password_rejected(client: TestClient) -> None:
    assert _login(client, "admin", "wrong-pw").status_code == 401
    assert _login(client, "nobody", "whatever").status_code == 401


# --------------------------------------------------------------------------- #
# read-only -> 403 on writes (inline, never 401/blank)
# --------------------------------------------------------------------------- #
# Covers: CS-1.2 (W28A-731 flat-role login + RBAC)
@pytest.mark.UT
@pytest.mark.mcp
@pytest.mark.req("FR-022")  # W28E-1804A semantic rebind
def test_read_only_write_403(client: TestClient) -> None:
    assert _login(client, "read-only", _RO_PW).status_code == 200
    # A write method on a data surface is denied inline with 403 + a clear reason.
    resp = client.post("/api/v1/profiles", json={"name": "x"})
    assert resp.status_code == 403, resp.text
    body = resp.json()
    assert body["role"] == "read-only"
    assert "read-only" in body["detail"]


# Covers: CS-1.2 (W28A-731 flat-role login + RBAC)
@pytest.mark.UT
@pytest.mark.mcp
@pytest.mark.req("FR-022")  # W28E-1804A semantic rebind
def test_read_write_not_write_blocked(client: TestClient) -> None:
    """read-write must NOT hit the flat-role 403 write-gate (it may pass through)."""
    assert _login(client, "read-write", _RW_PW).status_code == 200
    resp = client.post("/api/v1/profiles", json={"name": "x"})
    # It may fail upstream for other reasons, but never the read-only 403 gate.
    if resp.status_code == 403:
        assert resp.json().get("role") != "read-only"


# --------------------------------------------------------------------------- #
# api_key sign-in: valid X-API-Key -> admin flat principal; logout clears session
# --------------------------------------------------------------------------- #
# Covers: CS-1.2 (W28A-731 flat-role login + RBAC)
@pytest.mark.UT
@pytest.mark.mcp
@pytest.mark.req("FR-022")  # W28E-1804A semantic rebind
def test_api_key_signin_admin_principal(client: TestClient) -> None:
    me = client.get("/auth/me", headers={"x-api-key": _API_KEY})
    assert me.status_code == 200
    user = me.json()["user"]
    assert user is not None
    assert user["roles"] == ["admin"]
    assert user["permissions"] == ["*"]
    assert user.get("type") == "service"


# Covers: CS-1.2 (W28A-731 flat-role login + RBAC)
@pytest.mark.UT
@pytest.mark.mcp
@pytest.mark.req("FR-022")  # W28E-1804A semantic rebind
def test_anonymous_me_is_null(client: TestClient) -> None:
    assert client.get("/auth/me").json()["user"] is None


# Covers: CS-1.2 (W28A-731 flat-role login + RBAC)
@pytest.mark.UT
@pytest.mark.mcp
@pytest.mark.req("FR-022")  # W28E-1804A semantic rebind
def test_logout_clears_session(client: TestClient) -> None:
    assert _login(client, "admin", _ADMIN_PW).status_code == 200
    assert client.get("/auth/me").json()["user"] is not None
    assert client.post("/auth/logout").status_code == 200
    assert client.get("/auth/me").json()["user"] is None
