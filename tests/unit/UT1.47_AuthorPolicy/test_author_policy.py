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

from git import Repo

from tests.unit._tool_registry_harness import open_workspace_harness


def test_commit_author_uses_repo_policy_config(tmp_path) -> None:
    """Requirements: FR-10. UCs: UC-037."""
    harness = open_workspace_harness(tmp_path)
    try:
        repo = Repo(harness.workspace_path)
        repo.git.config("user.name", "Policy User")
        repo.git.config("user.email", "policy@example.com")

        harness.registry.call(
            "file_write",
            {"workspace_id": harness.workspace_id, "path": "author.txt", "content": "author\n"},
        )
        harness.registry.call("git_add", {"workspace_id": harness.workspace_id, "paths": ["author.txt"]})
        harness.registry.call("git_commit", {"workspace_id": harness.workspace_id, "message": "author policy commit"})

        commit = repo.head.commit
        assert commit.author.name == "Policy User"
        assert commit.author.email == "policy@example.com"
    finally:
        harness.close()
