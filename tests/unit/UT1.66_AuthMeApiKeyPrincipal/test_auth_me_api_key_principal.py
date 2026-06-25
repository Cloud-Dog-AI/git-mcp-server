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

"""W28C-1705 GM7 — ``/auth/me`` materialises a principal for X-API-Key callers.

Previously ``/auth/me`` returned ``{"user": null}`` for a valid X-API-Key (only a cookie
session materialised a principal), so UI/clients that pivot on ``/auth/me`` saw "logged
out" when authenticating by key. The web tier now returns a service principal for a valid
configured X-API-Key, while remaining null for anonymous / wrong-key callers.
"""

from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

from git_mcp_server.web_server import create_web_app

_KEY = "ut-service-key-1705"


@pytest.fixture()
def client(monkeypatch) -> TestClient:
    monkeypatch.setenv("CLOUD_DOG__GIT__API_KEY", _KEY)
    app = create_web_app(env_files=["tests/env-UT"])
    return TestClient(app, raise_server_exceptions=False)
# FR-1.18 traceability marker for existing git-mcp coverage.
@pytest.mark.UT
@pytest.mark.mcp
@pytest.mark.req("FR-022")  # W28E-1804A semantic rebind


def test_valid_api_key_materialises_service_principal(client: TestClient) -> None:
    """Requirements: W28C-1705 GM7 — X-API-Key caller gets a non-null principal."""
    resp = client.get("/auth/me", headers={"x-api-key": _KEY})
    assert resp.status_code == 200, resp.text
    user = resp.json()["user"]
    assert user is not None, "valid X-API-Key must materialise a principal, not null"
    assert user["type"] == "service"
    assert "admin" in user["roles"]
# FR-1.18 traceability marker for existing git-mcp coverage.
@pytest.mark.UT
@pytest.mark.mcp
@pytest.mark.req("FR-022")  # W28E-1804A semantic rebind


def test_wrong_api_key_stays_null(client: TestClient) -> None:
    resp = client.get("/auth/me", headers={"x-api-key": "not-the-key"})
    assert resp.json()["user"] is None
# FR-1.18 traceability marker for existing git-mcp coverage.
@pytest.mark.UT
@pytest.mark.mcp
@pytest.mark.req("FR-022")  # W28E-1804A semantic rebind


def test_anonymous_stays_null(client: TestClient) -> None:
    resp = client.get("/auth/me")
    assert resp.json()["user"] is None
