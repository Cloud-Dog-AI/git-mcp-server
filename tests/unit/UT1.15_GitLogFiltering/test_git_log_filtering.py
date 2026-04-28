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

from git_tools.git.operations import build_git_log_args, git_log
from git_tools.git.repo import GitRepository
from tests.helpers import create_repo


def test_git_log_filtering_builds_expected_args() -> None:
    """Requirements: FR-10, NFR-04."""
    args = build_git_log_args(author="alice", since="2026-01-01", path="README.md", max_count=5)
    assert "--author=alice" in args
    assert "--since=2026-01-01" in args
    assert "--max-count=5" in args
    assert args[-2:] == ["--", "README.md"]


def test_git_log_max_count_limits_output(tmp_path: Path) -> None:
    """Requirements: FR-10, NFR-04."""
    repo = create_repo(tmp_path / "repo")
    git_repo = GitRepository(repo.working_tree_dir)

    for index in range(1, 10):
        name = f"doc_{index}.md"
        target = Path(repo.working_tree_dir) / name
        target.write_text(f"Document {index}\n", encoding="utf-8")
        git_repo.add(name)
        git_repo.commit(f"Add document {index}")

    limited = [line for line in git_log(git_repo, max_count=3).splitlines() if line.strip()]
    assert len(limited) == 3

    all_entries = [line for line in git_log(git_repo, max_count=100).splitlines() if line.strip()]
    assert len(all_entries) == 10
