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

from git_tools.tools.registry import ToolRegistry
from git_tools.workspaces.manager import WorkspaceManager
from tests.helpers import create_repo


def test_fullworkflow_tag_browse(tmp_path: Path) -> None:
    """Requirements: FR-07, UC-03, UC-04."""
    repo = create_repo(tmp_path / "repo")
    repo.create_tag("v1.2.0")

    manager = WorkspaceManager(tmp_path / "work")
    tools = ToolRegistry(manager)
    opened = tools.call(
        "repo_open",
        {
            "profile": "repoA",
            "repo_source": repo.working_tree_dir,
            "session_id": "at-2",
            "ref": {"type": "tag", "name": "v1.2.0"},
        },
    )

    workspace = manager.get_workspace(opened["workspace_id"])
    assert workspace.ref_context is not None
    assert workspace.ref_context.mode == "ref_readonly"

    with pytest.raises(PermissionError):
        tools.call(
            "file_write",
            {
                "workspace_id": opened["workspace_id"],
                "path": "README.md",
                "content": "blocked in readonly mode\\n",
            },
        )
