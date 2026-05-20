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

from tests.helpers import create_repo_with_remote
from tests.unit._tool_registry_harness import open_workspace_harness


def test_git_pull_updates_workspace_from_remote(tmp_path: Path) -> None:
    """Requirements: FR-10. UCs: UC-039."""
    remote_path = tmp_path / "remote.git"
    create_repo_with_remote(tmp_path / "seed", remote_path)
    harness = open_workspace_harness(tmp_path, repo_source=remote_path)
    try:
        updater_path = tmp_path / "updater"
        updater = Repo.clone_from(remote_path.as_posix(), updater_path)
        updater.git.config("user.email", "updater@example.com")
        updater.git.config("user.name", "Updater")
        (updater_path / "from-remote.txt").write_text("remote-change\n", encoding="utf-8")
        updater.index.add(["from-remote.txt"])
        updater.index.commit("remote update")
        updater.git.push("origin", harness.default_branch)

        harness.registry.call(
            "git_pull",
            {
                "workspace_id": harness.workspace_id,
                "remote": "origin",
                "branch": harness.default_branch,
            },
        )
        assert (harness.workspace_path / "from-remote.txt").read_text(encoding="utf-8") == "remote-change\n"
    finally:
        harness.close()


def test_git_fetch_reports_remote_refs(tmp_path: Path) -> None:
    """Requirements: FR-10. UCs: UC-039."""
    remote_path = tmp_path / "remote.git"
    create_repo_with_remote(tmp_path / "seed", remote_path)
    harness = open_workspace_harness(tmp_path, repo_source=remote_path)
    try:
        updater_path = tmp_path / "updater-fetch"
        updater = Repo.clone_from(remote_path.as_posix(), updater_path)
        updater.git.config("user.email", "updater@example.com")
        updater.git.config("user.name", "Updater")
        updater.git.checkout("-b", "feature-fetch")
        (updater_path / "fetch-branch.txt").write_text("remote-branch\n", encoding="utf-8")
        updater.index.add(["fetch-branch.txt"])
        updater.index.commit("remote fetch branch")
        updater.git.push("origin", "feature-fetch")

        fetched = harness.registry.call(
            "git_fetch",
            {
                "workspace_id": harness.workspace_id,
                "remote": "origin",
            },
        )
        result = str(fetched["result"]).strip()
        assert result
        assert "origin/feature-fetch" in result
    finally:
        harness.close()
