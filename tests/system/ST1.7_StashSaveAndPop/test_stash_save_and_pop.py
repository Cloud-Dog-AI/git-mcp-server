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

from git_tools.git.repo import GitRepository
from tests.helpers import create_repo


def test_stash_save_and_pop(tmp_path: Path) -> None:
    """Requirements: FR-10."""
    repo = create_repo(tmp_path / "repo")
    git_repo = GitRepository(repo.working_tree_dir)
    target = Path(repo.working_tree_dir) / "README.md"
    target.write_text("stash\n", encoding="utf-8")

    saved = git_repo.stash_save("stash-test")
    popped = git_repo.stash_pop()
    assert ("Saved" in saved or "No local changes" in saved) and ("Dropped" in popped or "Applied" in popped)
