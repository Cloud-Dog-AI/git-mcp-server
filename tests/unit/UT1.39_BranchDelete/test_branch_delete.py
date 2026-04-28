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
from git import GitCommandError

from tests.unit._tool_registry_harness import open_workspace_harness


def test_branch_delete_non_active_and_active_branch_rejection(tmp_path) -> None:
    """Requirements: FR-10. UCs: UC-029."""
    harness = open_workspace_harness(tmp_path)
    try:
        harness.registry.call(
            "git_branch_create",
            {
                "workspace_id": harness.workspace_id,
                "name": "feature/delete-check",
                "from_ref": harness.default_branch,
            },
        )
        harness.registry.call(
            "git_branch_delete",
            {"workspace_id": harness.workspace_id, "name": "feature/delete-check"},
        )
        listed = harness.registry.call("git_branch_list", {"workspace_id": harness.workspace_id})["branches"]
        assert "feature/delete-check" not in listed

        with pytest.raises(GitCommandError):
            harness.registry.call(
                "git_branch_delete",
                {"workspace_id": harness.workspace_id, "name": harness.default_branch},
            )
    finally:
        harness.close()
