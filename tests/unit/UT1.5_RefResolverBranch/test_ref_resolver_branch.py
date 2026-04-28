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

from git_tools.workspaces.ref_context import RefResolver
from tests.helpers import create_repo


def test_ref_resolver_branch(tmp_path: Path) -> None:
    """Requirements: FR-07."""
    repo = create_repo(tmp_path / "repo")
    repo.git.checkout("-b", "feature/test")
    resolver = RefResolver(Repo(repo.working_tree_dir))
    resolved = resolver.resolve("branch", "feature/test")
    assert resolved.mode == "working_tree"
    assert resolved.ref_type == "branch"
