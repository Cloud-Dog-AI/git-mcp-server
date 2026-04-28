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


def test_merge_creates_merge_commit_when_histories_diverge(tmp_path) -> None:
    """Requirements: FR-10. UCs: UC-045."""
    harness = open_workspace_harness(tmp_path)
    try:
        harness.registry.call(
            "git_branch_create",
            {
                "workspace_id": harness.workspace_id,
                "name": "feature/no-ff",
                "from_ref": harness.default_branch,
            },
        )
        harness.registry.call(
            "git_checkout",
            {"workspace_id": harness.workspace_id, "ref": "feature/no-ff"},
        )
        harness.registry.call(
            "file_write",
            {"workspace_id": harness.workspace_id, "path": "feature.txt", "content": "feature\n"},
        )
        harness.registry.call("git_add", {"workspace_id": harness.workspace_id, "paths": ["feature.txt"]})
        harness.registry.call("git_commit", {"workspace_id": harness.workspace_id, "message": "feature commit"})

        harness.registry.call(
            "git_checkout",
            {"workspace_id": harness.workspace_id, "ref": harness.default_branch},
        )
        harness.registry.call(
            "file_write",
            {"workspace_id": harness.workspace_id, "path": "main.txt", "content": "main\n"},
        )
        harness.registry.call("git_add", {"workspace_id": harness.workspace_id, "paths": ["main.txt"]})
        harness.registry.call("git_commit", {"workspace_id": harness.workspace_id, "message": "main commit"})

        harness.registry.call(
            "git_merge",
            {
                "workspace_id": harness.workspace_id,
                "ref": "feature/no-ff",
                "ff_only": False,
            },
        )
        repo = Repo(harness.workspace_path)
        assert len(repo.head.commit.parents) == 2
    finally:
        harness.close()
