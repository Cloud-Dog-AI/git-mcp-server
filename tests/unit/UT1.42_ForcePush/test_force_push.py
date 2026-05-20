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
from git import GitCommandError, Repo

from tests.helpers import create_repo_with_remote
from tests.unit._tool_registry_harness import open_workspace_harness


def test_force_with_lease_push_after_remote_divergence(tmp_path: Path) -> None:
    """Requirements: FR-10. UCs: UC-041."""
    remote_path = tmp_path / "remote.git"
    create_repo_with_remote(tmp_path / "seed", remote_path)
    harness = open_workspace_harness(tmp_path, repo_source=remote_path)
    try:
        updater_path = tmp_path / "updater"
        updater = Repo.clone_from(remote_path.as_posix(), updater_path)
        updater.git.config("user.email", "updater@example.com")
        updater.git.config("user.name", "Updater")
        (updater_path / "remote-only.txt").write_text("upstream\n", encoding="utf-8")
        updater.index.add(["remote-only.txt"])
        updater.index.commit("upstream commit")
        updater.git.push("origin", harness.default_branch)

        harness.registry.call(
            "file_write",
            {"workspace_id": harness.workspace_id, "path": "local-only.txt", "content": "local\n"},
        )
        harness.registry.call("git_add", {"workspace_id": harness.workspace_id, "paths": ["local-only.txt"]})
        harness.registry.call("git_commit", {"workspace_id": harness.workspace_id, "message": "local commit"})

        with pytest.raises(GitCommandError):
            harness.registry.call(
                "git_push",
                {
                    "workspace_id": harness.workspace_id,
                    "remote": "origin",
                    "branch": harness.default_branch,
                    "force_with_lease": False,
                },
            )

        harness.registry.call("git_fetch", {"workspace_id": harness.workspace_id, "remote": "origin"})
        harness.registry.call(
            "git_push",
            {
                "workspace_id": harness.workspace_id,
                "remote": "origin",
                "branch": harness.default_branch,
                "force_with_lease": True,
            },
        )
    finally:
        harness.close()
