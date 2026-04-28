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

from datetime import timedelta
from pathlib import Path

from git_tools.workspaces.manager import WorkspaceManager
from tests.helpers import create_repo


def test_session_heartbeat_and_timeout_cleanup(tmp_path: Path) -> None:
    """Requirements: FR-13. UCs: UC-062."""
    source = create_repo(tmp_path / "source")
    manager = WorkspaceManager(tmp_path / "workspaces")
    workspace = manager.create_workspace(
        profile="repoA",
        repo_source=source.working_tree_dir,
        session_id="heartbeat",
        mode="ephemeral",
    )
    previous_last_used = workspace.last_used_at

    manager.get_workspace(workspace.workspace_id)
    refreshed = manager.get_workspace(workspace.workspace_id)
    assert refreshed.last_used_at >= previous_last_used

    refreshed.last_used_at = refreshed.last_used_at - timedelta(seconds=120)
    deleted = manager.cleanup_expired(ttl_seconds=1)
    assert workspace.workspace_id in deleted
    assert not workspace.path.exists()
