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

from git_tools.git.operations import git_rebase
from git_tools.git.repo import GitRepository
from tests.helpers import create_repo


def test_rebase_simple(tmp_path: Path) -> None:
    """Requirements: FR-10."""
    repo = create_repo(tmp_path / "repo")
    git_repo = GitRepository(repo.working_tree_dir)
    base_branch = repo.active_branch.name

    git_repo.branch_create("feature/rebase")
    git_repo.checkout("feature/rebase")
    target = Path(repo.working_tree_dir) / "README.md"
    target.write_text("rebase\n", encoding="utf-8")
    git_repo.add("README.md")
    git_repo.commit("feature")

    git_repo.checkout(base_branch)
    second = Path(repo.working_tree_dir) / "extra.txt"
    second.write_text("base\n", encoding="utf-8")
    git_repo.add("extra.txt")
    git_repo.commit("base update")

    git_repo.checkout("feature/rebase")
    result = git_rebase(git_repo, base_branch)
    assert "Successfully rebased" in result or result == ""
