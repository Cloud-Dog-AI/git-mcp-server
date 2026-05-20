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

from git_tools.workspaces.manager import WorkspaceManager
from tests.helpers import create_repo


def test_workspace_create_ephemeral(tmp_path: Path) -> None:
    """Requirements: FR-03."""
    source_repo = create_repo(tmp_path / "source")
    manager = WorkspaceManager(tmp_path / "workspaces")
    workspace = manager.create_workspace("repoA", source_repo.working_tree_dir, "s1", mode="ephemeral")

    assert workspace.path.exists()
    manager.close_workspace(workspace.workspace_id)
    assert not workspace.path.exists()
