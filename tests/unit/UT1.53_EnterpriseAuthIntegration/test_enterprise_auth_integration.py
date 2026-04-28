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

from typing import Any

import pytest
from cloud_dog_idam import APIKeyManager, RBACEngine
from fastapi import FastAPI, Request
from fastapi.testclient import TestClient

from git_mcp_server.auth.middleware import (
    AuthRuntime,
    _normalise_enterprise_roles,
    build_auth_runtime,
    install_auth_middleware,
)
from git_tools.config.models import AuthConfig, EnterpriseAuthConfig


class _FakeEnterpriseProvider:
    async def validate_id_token(self, token: str, *, expected_nonce: str | None = None) -> dict[str, Any]:
        _ = expected_nonce
        if token == "valid-with-role":
            return {"sub": "enterprise-user", "realm_access": {"roles": ["developer"]}}
        if token == "valid-no-role":
            return {"sub": "enterprise-user", "realm_access": {"roles": []}}
        raise ValueError("invalid token")

    def map_claims_to_roles(self, claims: dict[str, Any]) -> list[str]:
        realm_access = claims.get("realm_access", {})
        return list(realm_access.get("roles", []))


def test_enterprise_runtime_requires_keycloak_settings() -> None:
    """Requirements: FR-04. UCs: UC-084."""
    with pytest.raises(ValueError):
        build_auth_runtime(
            AuthConfig(
                mode="enterprise",
                enterprise=EnterpriseAuthConfig(
                    provider="keycloak",
                    keycloak_base_url="",
                    keycloak_realm="",
                    keycloak_client_id="",
                ),
            )
        )


def test_enterprise_runtime_builds_keycloak_provider() -> None:
    """Requirements: FR-04. UCs: UC-084."""
    runtime = build_auth_runtime(
        AuthConfig(
            mode="enterprise",
            enterprise=EnterpriseAuthConfig(
                provider="keycloak",
                keycloak_base_url="https://keycloak.example.test",
                keycloak_realm="cloud-dog",
                keycloak_client_id="git-mcp",
                keycloak_client_secret="test-secret",
            ),
        )
    )
    assert runtime.enterprise_provider is not None


def test_enterprise_middleware_enforces_token_and_role_mapping() -> None:
    """Requirements: FR-04. UCs: UC-084."""
    app = FastAPI()
    runtime = AuthRuntime(
        api_key_manager=APIKeyManager(),
        rbac_engine=RBACEngine(),
        token_service=None,
        enterprise_provider=_FakeEnterpriseProvider(),  # type: ignore[arg-type]
    )
    install_auth_middleware(
        app,
        runtime,
        auth_mode="enterprise",
        api_base_path="/api/v1",
        legacy_api_base_path="/app/v1",
        a2a_base_path="/a2a",
    )

    @app.get("/api/v1/tools")
    async def _tools(request: Request) -> dict[str, Any]:
        return {
            "ok": True,
            "roles": getattr(request.state, "enterprise_roles", []),
        }

    client = TestClient(app)

    assert client.get("/api/v1/tools").status_code == 401
    assert client.get("/api/v1/tools", headers={"Authorization": "Bearer invalid"}).status_code == 401
    assert client.get("/api/v1/tools", headers={"Authorization": "Bearer valid-no-role"}).status_code == 403

    response = client.get("/api/v1/tools", headers={"Authorization": "Bearer valid-with-role"})
    assert response.status_code == 200
    payload = response.json()
    assert payload["ok"] is True
    assert payload["roles"] == ["maintainer"]


def test_enterprise_role_normalisation_maps_canonical_roles() -> None:
    """Requirements: FR-05. UCs: UC-084."""
    roles = _normalise_enterprise_roles(["developer", "realm-admin", "viewer"])
    assert roles == {"maintainer", "admin", "reader"}
