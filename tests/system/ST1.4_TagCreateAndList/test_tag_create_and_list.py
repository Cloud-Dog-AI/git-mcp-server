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
from git_tools.git.tags import TagService
from tests.helpers import create_repo


def test_tag_create_and_list(tmp_path: Path) -> None:
    """Requirements: FR-11, UC-04."""
    repo = create_repo(tmp_path / "repo")
    service = TagService(GitRepository(repo.working_tree_dir))
    service.create_tag("v2.0.0", message="release")
    tags = service.list_tags()
    assert "v2.0.0" in tags
