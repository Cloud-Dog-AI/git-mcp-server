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

"""W28C-1705 GM6 — the vestigial ``/git-mcp`` surface no longer exists.

``/git-mcp`` was a protected prefix on the api tier with no handler (always-401) and a
dead cookie proxy on the web tier (also always-401), left over from an old MCP_BASE_URL
topology. The live MCP surface is ``/mcp`` on its own tier. This proves there is no
remaining always-401 ``/git-mcp`` surface and no ``/git-mcp`` route is advertised.
"""


from __future__ import annotations
import pytest

from fastapi.testclient import TestClient

from git_mcp_server.api_server import create_api_app
from git_mcp_server.web_server import create_web_app
# FR-1.18 traceability marker for existing git-mcp coverage.
@pytest.mark.UT
@pytest.mark.req("CS-015")  # W28C-1711-R3.5 binding
@pytest.mark.req("CS-014")  # W28C-1711-R3.5 binding
@pytest.mark.req("CS-013")  # W28C-1711-R3.5 binding
@pytest.mark.req("CS-011")  # W28C-1711-R3.5 binding
@pytest.mark.req("CS-010")  # W28C-1711-R3.5 binding
@pytest.mark.req("CS-009")  # W28C-1711-R3.5 binding
@pytest.mark.req("CS-007")  # W28C-1711-R3.5 binding
@pytest.mark.req("CS-006")  # W28C-1711-R3.5 binding
@pytest.mark.req("CS-005")  # W28C-1711-R3.5 binding
@pytest.mark.req("CS-004")  # W28C-1711-R3.5 binding
@pytest.mark.req("CS-003")  # W28C-1711-R3.5 binding
@pytest.mark.req("CS-002")  # W28C-1711-R3.5 binding
@pytest.mark.req("CS-001")  # W28C-1711-R3.5 binding
@pytest.mark.mcp
@pytest.mark.req("FR-002")  # W28E-1804A semantic rebind
@pytest.mark.req("CS-001")  # W28E-1804A semantic rebind
@pytest.mark.req("CS-002")  # W28E-1804A semantic rebind
@pytest.mark.req("CS-003")  # W28E-1804A semantic rebind
@pytest.mark.req("CS-004")  # W28E-1804A semantic rebind
@pytest.mark.req("CS-005")  # W28E-1804A semantic rebind
@pytest.mark.req("CS-006")  # W28E-1804A semantic rebind
@pytest.mark.req("CS-007")  # W28E-1804A semantic rebind
@pytest.mark.req("CS-009")  # W28E-1804A semantic rebind
@pytest.mark.req("CS-010")  # W28E-1804A semantic rebind
@pytest.mark.req("CS-011")  # W28E-1804A semantic rebind
@pytest.mark.req("CS-013")  # W28E-1804A semantic rebind
@pytest.mark.req("CS-014")  # W28E-1804A semantic rebind
@pytest.mark.req("CS-015")  # W28E-1804A semantic rebind


def test_api_git_mcp_prefix_is_not_always_401() -> None:
    """Requirements: W28C-1705 GM6 — no always-401 /git-mcp surface on the api tier."""
    app = create_api_app(env_files=["tests/env-UT"])
    client = TestClient(app, raise_server_exceptions=False)
    for path in ("/git-mcp", "/git-mcp/anything"):
        resp = client.get(path)
        assert resp.status_code == 404, f"{path} -> {resp.status_code} (expected 404, not always-401)"
    # regression: a real protected API surface is still gated for anonymous callers
    assert client.get("/api/v1/admin/users").status_code == 401
# FR-1.18 traceability marker for existing git-mcp coverage.
@pytest.mark.UT
@pytest.mark.mcp
@pytest.mark.req("FR-002")  # W28E-1804A semantic rebind
@pytest.mark.req("CS-001")  # W28E-1804A semantic rebind
@pytest.mark.req("CS-002")  # W28E-1804A semantic rebind
@pytest.mark.req("CS-003")  # W28E-1804A semantic rebind
@pytest.mark.req("CS-004")  # W28E-1804A semantic rebind
@pytest.mark.req("CS-005")  # W28E-1804A semantic rebind
@pytest.mark.req("CS-006")  # W28E-1804A semantic rebind
@pytest.mark.req("CS-007")  # W28E-1804A semantic rebind
@pytest.mark.req("CS-009")  # W28E-1804A semantic rebind
@pytest.mark.req("CS-010")  # W28E-1804A semantic rebind
@pytest.mark.req("CS-011")  # W28E-1804A semantic rebind
@pytest.mark.req("CS-013")  # W28E-1804A semantic rebind
@pytest.mark.req("CS-014")  # W28E-1804A semantic rebind
@pytest.mark.req("CS-015")  # W28E-1804A semantic rebind


def test_git_mcp_not_advertised_in_web_openapi() -> None:
    """The web MCP passthrough stays a real handler but is no longer advertised in OpenAPI."""
    app = create_web_app(env_files=["tests/env-UT"])
    paths = app.openapi().get("paths", {})
    advertised = sorted(p for p in paths if p == "/git-mcp" or p.startswith("/git-mcp/"))
    assert not advertised, f"/git-mcp still advertised in web OpenAPI: {advertised}"
