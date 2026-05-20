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

"""ST1.12 — Workspace persistence and reopen after close and server restart.

Verifies the fix for the W28A-502 persistence bug: re-opening a persistent
workspace with the same profile + session_id must return the same workspace
with all previous commits, tags, and files intact.

Requirements: FR-03.
"""

from __future__ import annotations

from pathlib import Path

from git import Repo

from git_tools.workspaces.manager import WorkspaceManager
from tests.helpers import create_repo


def test_reopen_persistent_workspace_after_close(tmp_path: Path) -> None:
    """Close and reopen a persistent workspace — same ID, same data."""
    source = create_repo(tmp_path / "source")
    manager = WorkspaceManager(tmp_path / "workspaces")

    # Create workspace, make a commit and tag.
    ws1 = manager.create_workspace("prof1", source.working_tree_dir, "sess1", mode="persistent")
    repo = Repo(ws1.path)
    test_file = ws1.path / "test.txt"
    test_file.write_text("persistence test content\n", encoding="utf-8")
    repo.index.add(["test.txt"])
    repo.index.commit("add test file")
    repo.create_tag("v1.0.0")
    original_id = ws1.workspace_id

    # Close.
    manager.close_workspace(original_id)
    assert ws1.path.exists(), "persistent workspace directory must survive close"

    # Reopen with same profile + session_id.
    ws2 = manager.create_workspace("prof1", source.working_tree_dir, "sess1", mode="persistent")
    assert ws2.workspace_id == original_id, "same profile+session_id must produce same workspace ID"
    assert ws2.path == ws1.path, "reopened workspace must point to same directory"

    # Verify data survived.
    repo2 = Repo(ws2.path)
    log = repo2.git.log("--oneline")
    assert "add test file" in log, f"commit missing after reopen: {log}"
    tags = repo2.git.tag("-l").splitlines()
    assert "v1.0.0" in tags, f"tag missing after reopen: {tags}"
    assert (ws2.path / "test.txt").read_text(encoding="utf-8") == "persistence test content\n"


def test_reopen_persistent_workspace_after_server_restart(tmp_path: Path) -> None:
    """Requirements: FR-03. Simulate server restart and restore persistent workspace from disk."""
    source = create_repo(tmp_path / "source")
    workspaces_dir = tmp_path / "workspaces"

    # First "server session": create workspace, commit, tag, close.
    mgr1 = WorkspaceManager(workspaces_dir)
    ws1 = mgr1.create_workspace("prof1", source.working_tree_dir, "sess1", mode="persistent")
    repo = Repo(ws1.path)
    (ws1.path / "data.txt").write_text("survives restart\n", encoding="utf-8")
    repo.index.add(["data.txt"])
    repo.index.commit("data commit")
    repo.create_tag("v2.0.0")
    original_id = ws1.workspace_id
    mgr1.close_workspace(original_id)

    # Second "server session": new manager simulates server restart.
    mgr2 = WorkspaceManager(workspaces_dir)
    ws2 = mgr2.create_workspace("prof1", source.working_tree_dir, "sess1", mode="persistent")
    assert ws2.workspace_id == original_id, "workspace ID must be deterministic across restarts"

    repo2 = Repo(ws2.path)
    log = repo2.git.log("--oneline")
    assert "data commit" in log, f"commit missing after restart: {log}"
    tags = repo2.git.tag("-l").splitlines()
    assert "v2.0.0" in tags, f"tag missing after restart: {tags}"
    assert (ws2.path / "data.txt").read_text(encoding="utf-8") == "survives restart\n"


def test_ephemeral_workspace_not_affected(tmp_path: Path) -> None:
    """Requirements: FR-03. Ephemeral workspaces must still be deleted on close."""
    source = create_repo(tmp_path / "source")
    manager = WorkspaceManager(tmp_path / "workspaces")

    ws = manager.create_workspace("prof1", source.working_tree_dir, "sess1", mode="ephemeral")
    assert ws.path.exists()
    manager.close_workspace(ws.workspace_id)
    assert not ws.path.exists(), "ephemeral workspace directory must be deleted on close"


def test_explicit_workspace_id_reopen(tmp_path: Path) -> None:
    """Requirements: FR-03. Caller-provided workspace IDs must reopen the same persistent workspace."""
    source = create_repo(tmp_path / "source")
    manager = WorkspaceManager(tmp_path / "workspaces")

    ws1 = manager.create_workspace(
        "prof1", source.working_tree_dir, "sess1", mode="persistent", workspace_id="my-workspace"
    )
    assert ws1.workspace_id == "my-workspace"
    repo = Repo(ws1.path)
    (ws1.path / "custom.txt").write_text("custom id\n", encoding="utf-8")
    repo.index.add(["custom.txt"])
    repo.index.commit("custom commit")
    manager.close_workspace("my-workspace")

    ws2 = manager.create_workspace(
        "prof1", source.working_tree_dir, "sess1", mode="persistent", workspace_id="my-workspace"
    )
    assert ws2.workspace_id == "my-workspace"
    repo2 = Repo(ws2.path)
    assert "custom commit" in repo2.git.log("--oneline")
