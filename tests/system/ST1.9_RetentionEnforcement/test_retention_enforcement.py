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

from datetime import datetime, timedelta, timezone
from pathlib import Path

from git_tools.workspaces.manager import WorkspaceManager
from tests.helpers import create_repo


def test_retention_enforcement(tmp_path: Path) -> None:
    """Requirements: FR-01."""
    source_repo = create_repo(tmp_path / "source")
    manager = WorkspaceManager(tmp_path / "workspaces")
    workspace = manager.create_workspace("repoA", source_repo.working_tree_dir, "s1", mode="ephemeral")
    workspace.last_used_at = datetime.now(timezone.utc) - timedelta(hours=2)

    deleted = manager.cleanup_expired(ttl_seconds=10)
    assert workspace.workspace_id in deleted
