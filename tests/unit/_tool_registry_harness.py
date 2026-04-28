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
from pathlib import Path

from git import Repo

from git_tools.tools.registry import ToolRegistry
from git_tools.workspaces.manager import WorkspaceManager
from tests.helpers import create_repo


@dataclass(slots=True)
class WorkspaceHarness:
    """Convenience wrapper for registry-backed workspace unit tests."""

    registry: ToolRegistry
    workspace_id: str
    workspace_path: Path
    source_repo: Path
    default_branch: str

    def close(self) -> None:
        """Close the workspace via tool API."""
        self.registry.call("repo_close", {"workspace_id": self.workspace_id})


def open_workspace_harness(tmp_path: Path, repo_source: Path | None = None) -> WorkspaceHarness:
    """Create a tool registry and open an ephemeral workspace for tests."""
    source = repo_source
    if source is None:
        source_repo = create_repo(tmp_path / "source")
        source = Path(source_repo.working_tree_dir)
    source = source.resolve()

    manager = WorkspaceManager(tmp_path / "workspaces")
    registry = ToolRegistry(
        manager,
        profile_store={
            "repoA": {
                "repo": {
                    "source": source.as_posix(),
                }
            }
        },
    )

    opened = registry.call(
        "repo_open",
        {
            "profile": "repoA",
            "session_id": "unit",
            "repo_source": source.as_posix(),
        },
    )
    workspace_path = Path(opened["path"]).resolve()
    default_branch = Repo(workspace_path).active_branch.name
    return WorkspaceHarness(
        registry=registry,
        workspace_id=opened["workspace_id"],
        workspace_path=workspace_path,
        source_repo=source,
        default_branch=default_branch,
    )
