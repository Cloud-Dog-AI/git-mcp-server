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

import pytest
from git import GitCommandError, Repo

from tests.unit._tool_registry_harness import open_workspace_harness


def _prepare_conflicting_branches(harness) -> None:
    harness.registry.call(
        "git_branch_create",
        {
            "workspace_id": harness.workspace_id,
            "name": "feature/conflict",
            "from_ref": harness.default_branch,
        },
    )
    harness.registry.call("git_checkout", {"workspace_id": harness.workspace_id, "ref": "feature/conflict"})
    harness.registry.call(
        "file_write",
        {"workspace_id": harness.workspace_id, "path": "README.md", "content": "feature-change\n"},
    )
    harness.registry.call("git_add", {"workspace_id": harness.workspace_id, "paths": ["README.md"]})
    harness.registry.call("git_commit", {"workspace_id": harness.workspace_id, "message": "feature change"})

    harness.registry.call("git_checkout", {"workspace_id": harness.workspace_id, "ref": harness.default_branch})
    harness.registry.call(
        "file_write",
        {"workspace_id": harness.workspace_id, "path": "README.md", "content": "main-change\n"},
    )
    harness.registry.call("git_add", {"workspace_id": harness.workspace_id, "paths": ["README.md"]})
    harness.registry.call("git_commit", {"workspace_id": harness.workspace_id, "message": "main change"})


def test_merge_abort_resets_merge_state(tmp_path) -> None:
    """Requirements: FR-10, FR-12. UCs: UC-051."""
    harness = open_workspace_harness(tmp_path)
    try:
        _prepare_conflicting_branches(harness)
        with pytest.raises(GitCommandError):
            harness.registry.call(
                "git_merge",
                {"workspace_id": harness.workspace_id, "ref": "feature/conflict", "ff_only": False},
            )
        harness.registry.call("git_merge_abort", {"workspace_id": harness.workspace_id})
        assert not (harness.workspace_path / ".git" / "MERGE_HEAD").exists()
    finally:
        harness.close()


def test_merge_continue_completes_after_manual_resolution(tmp_path) -> None:
    """Requirements: FR-10, FR-12. UCs: UC-051."""
    harness = open_workspace_harness(tmp_path)
    try:
        _prepare_conflicting_branches(harness)
        with pytest.raises(GitCommandError):
            harness.registry.call(
                "git_merge",
                {"workspace_id": harness.workspace_id, "ref": "feature/conflict", "ff_only": False},
            )

        harness.registry.call(
            "file_write",
            {
                "workspace_id": harness.workspace_id,
                "path": "README.md",
                "content": "resolved\n",
            },
        )
        harness.registry.call("git_add", {"workspace_id": harness.workspace_id, "paths": ["README.md"]})
        harness.registry.call("git_merge_continue", {"workspace_id": harness.workspace_id})

        repo = Repo(harness.workspace_path)
        assert len(repo.head.commit.parents) == 2
        assert not (harness.workspace_path / ".git" / "MERGE_HEAD").exists()
    finally:
        harness.close()
