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

from fastapi.testclient import TestClient

from git_mcp_server.api_server import create_api_app
import pytest
@pytest.mark.AT
@pytest.mark.mcp
@pytest.mark.req("FR-022")  # W28E-1804A semantic rebind


def test_t1_gm_api_health_and_auth_negative_contract() -> None:
    """FR-1.2, CS-1.1, T1-GM-AUTH: health is public and gated tools reject anonymous."""
    app = create_api_app(env_files=["tests/env-UT"])
    client = TestClient(app)

    health = client.get("/api/v1/health")
    unauth = client.post("/api/v1/tools/git_status", json={"workspace_id": "missing"})

    assert health.status_code == 200
    assert unauth.status_code in {401, 403}
@pytest.mark.AT
@pytest.mark.mcp
@pytest.mark.req("FR-022")  # W28E-1804A semantic rebind


def test_t1_gm_api_key_secret_not_listed_after_create() -> None:
    """FR-1.16, UC-1.5, T1-GM-IDAM: create reveals once; list/read omit raw key."""
    app = create_api_app(env_files=["tests/env-UT"])
    runtime = app.state.admin_runtime
    runtime.create_user(user_id="e2e-u1", username="e2e-user", email="e2e@example.invalid")

    created = runtime.create_api_key(
        name="e2e-key",
        owner_user_id="e2e-u1",
        capabilities=["profile:team-repo"],
    )
    listed = runtime.list_api_keys(owner_user_id="e2e-u1")
    read_back = runtime.read_api_key(created["key_id"])

    assert "raw_key" in created
    assert all("raw_key" not in item for item in listed)
    assert "raw_key" not in read_back
