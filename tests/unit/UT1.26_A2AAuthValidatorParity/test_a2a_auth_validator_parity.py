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

from dataclasses import dataclass

from cloud_dog_idam import RBACEngine

from git_mcp_server.api_server import validate_a2a_bearer_token
from git_mcp_server.auth.middleware import AuthRuntime


@dataclass
class _SpyAPIKeyManager:
    calls: list[str]

    def validate(self, raw_key: str) -> object | None:
        self.calls.append(raw_key)
        if raw_key == "12345678":
            return object()
        return None


def test_a2a_bearer_uses_shared_api_key_validator() -> None:
    """Requirements: FR-04."""
    spy = _SpyAPIKeyManager(calls=[])
    runtime = AuthRuntime(api_key_manager=spy, rbac_engine=RBACEngine())  # type: ignore[arg-type]

    assert validate_a2a_bearer_token("Bearer 12345678", runtime) is True
    assert spy.calls == ["12345678"]

    assert validate_a2a_bearer_token("Bearer wrong-key", runtime) is False
    assert spy.calls[-1] == "wrong-key"

    assert validate_a2a_bearer_token("", runtime) is False
    assert validate_a2a_bearer_token("Bearer", runtime) is False
