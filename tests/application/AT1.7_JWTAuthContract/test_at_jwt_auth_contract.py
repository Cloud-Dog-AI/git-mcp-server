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

import os
from pathlib import Path

import httpx
from cloud_dog_idam.tokens import JWTTokenService

from git_tools.config.loader import bind_global_config, load_raw_config
from tests.helpers import api_url


def _config_from_env_file(env_file: str):
    """Load typed config from an env overlay path."""
    return bind_global_config(load_raw_config(env_files=[env_file]))


def _jwt_service_from_runtime(default_env_file: str = "tests/env-AT") -> JWTTokenService:
    config = None
    for env_file in (os.environ.get("TEST_ENV_FILE", "").strip(), default_env_file):
        if not env_file:
            continue
        path = Path(env_file)
        if not path.exists():
            continue
        if path.name.lower().startswith("env-at"):
            candidate = _config_from_env_file(env_file)
        elif env_file == default_env_file:
            candidate = _config_from_env_file(env_file)
        else:
            continue
        if candidate.auth.jwt.secret.strip():
            config = candidate
            break
        if config is None:
            config = candidate
    assert config is not None, "JWT application contract test env file could not be resolved"
    secret = config.auth.jwt.secret.strip()
    issuer = config.auth.jwt.issuer.strip() or "cloud-dog"
    audience = config.auth.jwt.audience.strip() or "cloud-dog-services"
    assert secret, "CLOUD_DOG__AUTH__JWT__SECRET must be configured for JWT application contract tests"
    return JWTTokenService(secret=secret, issuer=issuer, audience=audience)


def test_application_jwt_auth_accepts_valid_bearer_token(application_server: str) -> None:
    """Requirements: FR-04. UCs: UC-078."""
    service = _jwt_service_from_runtime()
    token = service.issue("jwt-application-user", {"roles": ["writer"]}).access_token

    response = httpx.get(
        api_url(application_server, "/tools"),
        headers={"Authorization": f"Bearer {token}"},
        timeout=10.0,
    )
    assert response.status_code == 200
    payload = response.json()
    assert payload["ok"] is True
    assert len(payload["result"]["items"]) >= 49


def test_application_jwt_auth_rejects_invalid_bearer_token(application_server: str) -> None:
    """Requirements: FR-04. UCs: UC-078."""
    response = httpx.get(
        api_url(application_server, "/tools"),
        headers={"Authorization": "Bearer invalid-token"},
        timeout=10.0,
    )
    assert response.status_code == 401
