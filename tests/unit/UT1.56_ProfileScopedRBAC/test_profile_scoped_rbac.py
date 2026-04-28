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

from pathlib import Path

import pytest

from git_tools.admin.runtime import AdminRuntime
from git_tools.tools.registry import ToolRegistry
from git_tools.workspaces.manager import WorkspaceManager
from tests.helpers import create_repo


def _source_repo(path: Path) -> str:
    repo = create_repo(path)
    return Path(repo.working_tree_dir).resolve().as_posix()


def test_repo_open_requires_profile_permission_from_group_role(tmp_path: Path) -> None:
    """Requirements: FR-05. Group-derived `profile:{name}` role gates repo access."""
    source_a = _source_repo(tmp_path / "source-a")
    source_b = _source_repo(tmp_path / "source-b")
    runtime = AdminRuntime(
        profile_store={
            "repoA": {"repo": {"source": source_a}},
            "repoB": {"repo": {"source": source_b}},
        }
    )
    runtime.create_user(user_id="scoped-user", username="scoped-user", email="scoped@example.test")
    runtime.create_group(
        group_id="repo-a-group",
        roles=["profile:repoA"],
        members=["scoped-user"],
    )
    registry = ToolRegistry(
        WorkspaceManager(tmp_path / "workspaces"),
        admin_runtime=runtime,
        profile_store=runtime.profile_store,
    )

    opened = registry.call_with_access(
        "repo_open",
        {"profile": "repoA", "session_id": "ut-rbac-allow"},
        actor_id="scoped-user",
    )
    assert opened["workspace_id"]

    registry.call_with_access(
        "repo_close",
        {"workspace_id": opened["workspace_id"]},
        actor_id="scoped-user",
    )

    with pytest.raises(PermissionError, match="Access denied to profile 'repoB'"):
        registry.call_with_access(
            "repo_open",
            {"profile": "repoB", "session_id": "ut-rbac-deny"},
            actor_id="scoped-user",
        )


def test_repo_open_allows_managed_api_key_capability_for_profile(tmp_path: Path) -> None:
    """Requirements: FR-05. Managed API-key capability `profile:{name}` permits repo access."""
    source_a = _source_repo(tmp_path / "source-a")
    source_b = _source_repo(tmp_path / "source-b")
    runtime = AdminRuntime(
        profile_store={
            "repoA": {"repo": {"source": source_a}},
            "repoB": {"repo": {"source": source_b}},
        }
    )
    runtime.create_user(user_id="key-user", username="key-user", email="key@example.test")
    api_key = runtime.create_api_key(
        name="repo-a-key",
        owner_user_id="key-user",
        capabilities=["profile:repoA"],
    )
    capabilities = set(api_key["capabilities"])
    registry = ToolRegistry(
        WorkspaceManager(tmp_path / "workspaces"),
        admin_runtime=runtime,
        profile_store=runtime.profile_store,
    )

    opened = registry.call_with_access(
        "repo_open",
        {"profile": "repoA", "session_id": "ut-cap-allow"},
        actor_id="key-user",
        capabilities=capabilities,
    )
    assert opened["workspace_id"]

    registry.call_with_access(
        "repo_close",
        {"workspace_id": opened["workspace_id"]},
        actor_id="key-user",
        capabilities=capabilities,
    )

    with pytest.raises(PermissionError, match="Access denied to profile 'repoB'"):
        registry.call_with_access(
            "repo_open",
            {"profile": "repoB", "session_id": "ut-cap-deny"},
            actor_id="key-user",
            capabilities=capabilities,
        )
