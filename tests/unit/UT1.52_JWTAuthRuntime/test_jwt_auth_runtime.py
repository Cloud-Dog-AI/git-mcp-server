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

import pytest

from git_mcp_server.auth.middleware import build_auth_runtime
from git_tools.config.models import AuthConfig, JWTConfig


def test_jwt_runtime_issues_and_verifies_tokens() -> None:
    """Requirements: FR-04. UCs: UC-078."""
    runtime = build_auth_runtime(
        AuthConfig(
            mode="jwt",
            jwt=JWTConfig(
                issuer="cloud-dog-unit",
                audience="git-mcp-unit",
                secret="unit-jwt-secret-0123456789abcdef0123456789",
            ),
        )
    )
    assert runtime.token_service is not None
    token_pair = runtime.token_service.issue("unit-user", {"roles": ["writer"]})
    claims = runtime.token_service.verify(token_pair.access_token)
    assert claims["sub"] == "unit-user"
    assert claims["roles"] == ["writer"]


def test_jwt_mode_requires_explicit_secret() -> None:
    """Requirements: FR-04. UCs: UC-078."""
    with pytest.raises(ValueError):
        build_auth_runtime(
            AuthConfig(
                mode="jwt",
                jwt=JWTConfig(
                    issuer="cloud-dog-unit",
                    audience="git-mcp-unit",
                    secret="",
                ),
            )
        )
