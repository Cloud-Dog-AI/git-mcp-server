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

import tempfile
import types

import pytest

from git_tools.admin.runtime import AdminRuntime
from git_tools.tools.registry import ToolRegistry
from git_tools.workspaces.manager import WorkspaceManager


class _SpyWriter:
    def __init__(self) -> None:
        self.records: list[object] = []

    def emit(self, record: object) -> None:
        self.records.append(record)


def _registry(runtime: AdminRuntime, audit_writer: _SpyWriter | None = None) -> ToolRegistry:
    return ToolRegistry(
        WorkspaceManager(tempfile.mkdtemp()),
        admin_runtime=runtime,
        audit_writer=audit_writer,
    )
@pytest.mark.QT
@pytest.mark.mcp
@pytest.mark.req("FR-016")  # W28E-1804A semantic rebind
@pytest.mark.req("FR-019")  # W28E-1804A semantic rebind


def test_t0_gm_registry_has_tool_audit_chokepoint() -> None:
    """FR-1.16, BR-1.1, T0-GM-AUDIT: call() emits one redacted audit event."""
    runtime = AdminRuntime()
    writer = _SpyWriter()
    registry = _registry(runtime, writer)
    registry._tools["w28a745_secret_tool"] = types.SimpleNamespace(handler=lambda payload: {"ok": True})

    result = registry.call("w28a745_secret_tool", {"token": "do-not-log", "message": "visible"})

    assert result == {"ok": True}
    assert len(writer.records) == 1
    record = writer.records[0]
    assert record.operation == "w28a745_secret_tool"
    assert record.status == "success"
    assert record.params["token"] == "[REDACTED]"
    assert record.params["message"] == "visible"
@pytest.mark.QT
@pytest.mark.mcp
@pytest.mark.req("FR-016")  # W28E-1804A semantic rebind
@pytest.mark.req("FR-019")  # W28E-1804A semantic rebind


def test_t3_gm_cascade_group_profile_grant_add_and_remove() -> None:
    """FR-1.19, UC-1.7, T3-GM-CASCADE: group membership grants and revokes a profile."""
    runtime = AdminRuntime(
        profile_store={
            "team-repo": {"repo": {"source": "https://example.invalid/team.git"}},
            "other-repo": {"repo": {"source": "https://example.invalid/other.git"}},
        }
    )
    runtime.create_user(user_id="u1", username="user-one", email="u1@example.invalid")
    runtime.create_group(group_id="team", roles=["profile:team-repo"], members=[])
    registry = _registry(runtime)

    with pytest.raises(PermissionError):
        registry._require_profile_access(
            "repo_open",
            {"profile": "team-repo"},
            actor_id="u1",
            roles=set(),
            capabilities=set(),
        )

    runtime.update_group(group_id="team", roles=["profile:team-repo"], members=["u1"])
    registry._require_profile_access(
        "repo_open",
        {"profile": "team-repo"},
        actor_id="u1",
        roles=set(),
        capabilities=set(),
    )
    with pytest.raises(PermissionError):
        registry._require_profile_access(
            "repo_open",
            {"profile": "other-repo"},
            actor_id="u1",
            roles=set(),
            capabilities=set(),
        )

    runtime.update_group(group_id="team", roles=["profile:team-repo"], members=[])
    with pytest.raises(PermissionError):
        registry._require_profile_access(
            "repo_open",
            {"profile": "team-repo"},
            actor_id="u1",
            roles=set(),
            capabilities=set(),
        )
@pytest.mark.QT
@pytest.mark.mcp
@pytest.mark.req("FR-016")  # W28E-1804A semantic rebind
@pytest.mark.req("FR-019")  # W28E-1804A semantic rebind


def test_t2_gm_secret_mask_api_key_read_surfaces() -> None:
    """FR-1.16, UC-1.6, T2-GM-SECRET-MASK: non-create API-key reads omit raw secrets."""
    runtime = AdminRuntime()
    runtime.create_user(user_id="u2", username="user-two", email="u2@example.invalid")

    created = runtime.create_api_key(name="matrix-key", owner_user_id="u2", capabilities=["profile:team-repo"])
    listed = runtime.list_api_keys(owner_user_id="u2")
    read_back = runtime.read_api_key(created["key_id"])

    assert "raw_key" in created
    assert all("raw_key" not in item for item in listed)
    assert "raw_key" not in read_back
    assert read_back["capabilities"] == ["profile:team-repo"]
