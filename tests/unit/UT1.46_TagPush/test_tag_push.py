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


def test_tag_push_to_remote(tmp_path: Path) -> None:
    """Requirements: FR-11. UCs: UC-055."""
    remote_path = tmp_path / "remote.git"
    create_repo_with_remote(tmp_path / "seed", remote_path)
    harness = open_workspace_harness(tmp_path, repo_source=remote_path)
    try:
        harness.registry.call(
            "git_tag_create",
            {"workspace_id": harness.workspace_id, "tag": "v2.0.0"},
        )
        harness.registry.call(
            "git_tag_push",
            {"workspace_id": harness.workspace_id, "remote": "origin", "tag": "v2.0.0"},
        )

        verify = Repo.clone_from(remote_path.as_posix(), tmp_path / "verify")
        assert "v2.0.0" in [tag.name for tag in verify.tags]
    finally:
        harness.close()
