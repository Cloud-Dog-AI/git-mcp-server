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

from git import Repo

from git_tools.git.recovery import RecoveryManager
from git_tools.tools.registry import ToolRegistry
from git_tools.workspaces.manager import WorkspaceManager
from tests.helpers import create_repo_with_remote


def test_fullworkflow_recovery_restore(tmp_path: Path) -> None:
    """Requirements: FR-13, UC-06."""
    """AT1.5 -- Full recovery: stash, patch bundle, recovery branch."""
    local, _ = create_repo_with_remote(tmp_path / "local", tmp_path / "remote.git")
    manager = WorkspaceManager(tmp_path / "work")
    tools = ToolRegistry(manager)
    main_branch = local.active_branch.name

    # Open workspace
    opened = tools.call(
        "repo_open",
        {
            "profile": "recovery-test",
            "repo_source": local.working_tree_dir,
            "session_id": "at-recovery",
            "ref": {"type": "branch", "name": main_branch},
        },
    )
    wid = opened["workspace_id"]
    ws_path = opened["path"]

    # --- Phase 1: Stash save/pop ---

    # Make a dirty change via the tool (do NOT commit)
    tools.call(
        "file_write",
        {
            "workspace_id": wid,
            "path": "README.md",
            "content": "unsaved work\n",
            "overwrite": True,
        },
    )

    # Stash it
    stash_result = tools.call("git_stash_save", {"workspace_id": wid, "message": "recovery-stash"})
    assert "recovery-stash" in stash_result["result"], f"Stash message missing: {stash_result}"

    # Verify the tracked file content is reverted after stash
    read_after_stash = tools.call("file_read", {"workspace_id": wid, "path": "README.md"})
    assert read_after_stash["content"] != "unsaved work\n", "README.md should be reverted after stash"

    # Pop the stash
    tools.call("git_stash_pop", {"workspace_id": wid})

    # Verify the file is back with correct content
    read_back = tools.call("file_read", {"workspace_id": wid, "path": "README.md"})
    assert read_back["content"] == "unsaved work\n", f"Wrong content after pop: {read_back['content']}"

    # --- Phase 2: Patch bundle ---

    recovery_mgr = RecoveryManager(ws_path)
    patch = recovery_mgr.create_patch_bundle(tmp_path / "patches", "at-session")
    assert patch.exists(), f"Patch file not created at {patch}"
    patch_content = patch.read_text(encoding="utf-8")
    assert "README.md" in patch_content, "Patch should reference README.md"
    assert "unsaved work" in patch_content, "Patch should contain file content"

    # --- Phase 3: Recovery branch ---

    # Stage and commit so we can create a recovery branch from a clean state
    tools.call("git_add", {"workspace_id": wid, "paths": ["README.md"]})
    tools.call("git_commit", {"workspace_id": wid, "message": "pre-recovery commit"})

    branch = recovery_mgr.create_recovery_branch("at-crash")
    assert branch.startswith("recovery/at-crash-"), f"Unexpected branch name: {branch}"

    # Verify the recovery branch is now the active branch
    ws_repo = Repo(ws_path)
    assert ws_repo.active_branch.name == branch, f"Active branch should be {branch}, got {ws_repo.active_branch.name}"

    # Verify the commit is on the recovery branch
    log_result = tools.call("git_log", {"workspace_id": wid, "max_count": 5})
    assert "pre-recovery commit" in log_result["log"], f"Recovery branch missing commit: {log_result['log']}"
