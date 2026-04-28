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

from git_tools.git.recovery import RecoveryManager
from git_tools.git.repo import GitRepository
from tests.helpers import create_repo


def test_recovery_list_get_and_restore_flow(tmp_path: Path) -> None:
    """Requirements: FR-13. UCs: UC-066, UC-067."""
    source = create_repo(tmp_path / "repo")
    repo_path = Path(source.working_tree_dir)
    recovery = RecoveryManager(repo_path)
    git_repo = GitRepository(repo_path)

    target = repo_path / "README.md"
    target.write_text("changed-before-stash\n", encoding="utf-8")
    stash_result = recovery.stash_changes("recovery-point")
    assert "Saved working directory" in stash_result

    listed = git_repo.stash_list()
    assert "stash@{0}" in listed
    assert "recovery-point" in listed

    target.write_text("pending-local-change\n", encoding="utf-8")
    patch = recovery.create_patch_bundle(tmp_path / "recovery", session_id="s1")
    assert patch.exists()
    patch_text = patch.read_text(encoding="utf-8")
    assert "README.md" in patch_text
    assert "pending-local-change" in patch_text

    git_repo.repo.git.checkout("--", "README.md")
    pop_result = git_repo.stash_pop()
    assert "Dropped refs/stash@{0}" in pop_result
    assert target.read_text(encoding="utf-8") == "changed-before-stash\n"
