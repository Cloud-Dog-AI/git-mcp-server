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
from git.exc import GitCommandError

from git_tools.tools.registry import ToolRegistry
from git_tools.workspaces.manager import WorkspaceManager
from tests.helpers import create_repo_with_remote


def test_fullworkflow_conflict_resolve(tmp_path: Path) -> None:
    """Requirements: FR-12, UC-05."""
    """AT1.3 -- Real merge conflict: two branches edit same line, resolve, commit."""
    local, _ = create_repo_with_remote(tmp_path / "local", tmp_path / "remote.git")
    manager = WorkspaceManager(tmp_path / "work")
    tools = ToolRegistry(manager)
    main_branch = local.active_branch.name

    # Open workspace
    opened = tools.call(
        "repo_open",
        {
            "profile": "conflict-test",
            "repo_source": local.working_tree_dir,
            "session_id": "at-conflict",
            "ref": {"type": "branch", "name": main_branch},
        },
    )
    wid = opened["workspace_id"]

    # Create feature branch and commit a change to README.md
    tools.call("git_branch_create", {"workspace_id": wid, "name": "feature/conflict"})
    tools.call("git_checkout", {"workspace_id": wid, "ref": "feature/conflict"})
    tools.call(
        "file_write",
        {
            "workspace_id": wid,
            "path": "README.md",
            "content": "feature line\n",
            "overwrite": True,
        },
    )
    tools.call("git_add", {"workspace_id": wid, "paths": ["README.md"]})
    tools.call("git_commit", {"workspace_id": wid, "message": "feature edit"})

    # Switch back to main and make a CONFLICTING change to the same file
    tools.call("git_checkout", {"workspace_id": wid, "ref": main_branch})
    tools.call(
        "file_write",
        {
            "workspace_id": wid,
            "path": "README.md",
            "content": "main line\n",
            "overwrite": True,
        },
    )
    tools.call("git_add", {"workspace_id": wid, "paths": ["README.md"]})
    tools.call("git_commit", {"workspace_id": wid, "message": "main edit"})

    # Attempt merge -- MUST raise GitCommandError because of conflict
    with pytest.raises(GitCommandError):
        tools.call("git_merge", {"workspace_id": wid, "ref": "feature/conflict", "ff_only": False})

    # List conflicts -- README.md must be in the list
    conflicts = tools.call("git_conflicts_list", {"workspace_id": wid})
    assert "README.md" in conflicts["conflicts"], f"Expected README.md in {conflicts['conflicts']}"

    # Resolve manually via tool
    resolve_result = tools.call(
        "git_conflict_resolve_manual",
        {
            "workspace_id": wid,
            "path": "README.md",
            "content": "resolved line\n",
        },
    )
    assert "README.md" in resolve_result["resolved"]

    # Verify resolution via file_read
    read_result = tools.call("file_read", {"workspace_id": wid, "path": "README.md"})
    assert read_result["content"] == "resolved line\n"

    # Stage and commit the resolution
    tools.call("git_add", {"workspace_id": wid, "paths": ["README.md"]})
    commit_result = tools.call("git_commit", {"workspace_id": wid, "message": "resolve conflict"})
    assert len(commit_result["commit"]) == 40, "Expected 40-char SHA"

    # Verify log contains the resolution commit
    log_result = tools.call("git_log", {"workspace_id": wid, "max_count": 10})
    assert "resolve conflict" in log_result["log"], f"Expected 'resolve conflict' in log: {log_result['log']}"
