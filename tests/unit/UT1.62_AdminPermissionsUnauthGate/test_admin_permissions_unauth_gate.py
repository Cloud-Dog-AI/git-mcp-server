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

"""W28A-889-A-R2 — admin permission catalogue + unauthenticated negative-auth gate.

Two contracts proven here against the full deployed-equivalent app (real auth
middleware, not the bare router):

* §0C negative-auth: an UNAUTHENTICATED caller (no api-key, no cookie, no bearer)
  is DENIED (401) on the protected admin surface — so CI catches a regression
  locally if the front door is ever left open (the index-retriever incident).
* The new ``GET /api/v1/admin/permissions`` catalogue used by the shared
  ``@cloud-dog/idam`` Roles page returns the assignable-permission set for an
  authenticated admin (200), eliminating the live 404 the WebUI fired.
"""


from __future__ import annotations
import pytest

from fastapi.testclient import TestClient

from git_mcp_server.api_server import create_api_app
@pytest.mark.UT
@pytest.mark.mcp
@pytest.mark.req("CS-020")  # W28E-1804A semantic rebind


def test_unauth_admin_surface_is_denied_and_authed_permissions_catalogue_serves() -> None:
    """Requirements: CS-01, CFG-09, UI-R7 (W28A-889-A-R2)."""
    app = create_api_app(env_files=["tests/env-UT"])
    client = TestClient(app)
    admin_headers = {"x-api-key": app.state.seed_api_key}

    # --- §0C negative-auth: unauthenticated callers are rejected (NOT blanket-open) ---
    for path in ("/api/v1/admin/permissions", "/api/v1/admin/roles", "/api/v1/admin/users"):
        unauth = client.get(path)
        assert unauth.status_code == 401, f"unauth {path} must be 401, got {unauth.status_code}"
        body = unauth.json()
        # never a populated/admin principal to an anonymous caller
        assert body.get("result") is None
        assert "*" not in str(body)

    # --- new permission catalogue serves for an authenticated admin ---
    authed = client.get("/api/v1/admin/permissions", headers=admin_headers)
    assert authed.status_code == 200, authed.text
    items = authed.json()["result"]["items"]
    assert isinstance(items, list) and items, "permission catalogue must be a non-empty list"
    # baseline RBAC permissions must be present in the catalogue
    assert "*" in items
    assert "git:read" in items
    assert "git:write" in items

    # sanity: roles list still serves for admin (regression guard)
    roles = client.get("/api/v1/admin/roles", headers=admin_headers)
    assert roles.status_code == 200, roles.text
