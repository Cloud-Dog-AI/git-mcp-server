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

from git_tools.git.operations import git_log
from git_tools.git.repo import GitRepository
from tests.helpers import create_repo_with_remote


def test_branch_create_commit_push(tmp_path: Path) -> None:
    """Requirements: FR-10."""
    local, _ = create_repo_with_remote(tmp_path / "local", tmp_path / "remote.git")
    repo = GitRepository(local.working_tree_dir)

    repo.branch_create("feature/x")
    repo.checkout("feature/x")

    for index in range(1, 21):
        name = f"doc_{index}.md"
        target = Path(local.working_tree_dir) / name
        target.write_text(f"Document {index}\n", encoding="utf-8")
        repo.add(name)
        repo.commit(f"Add document {index}")

    log_output = git_log(repo, max_count=25)
    document_entries = [line for line in log_output.splitlines() if "Add document " in line]
    assert len(document_entries) == 20

    local.git.push("origin", "feature/x")

    assert "feature/x" in repo.branch_list()
