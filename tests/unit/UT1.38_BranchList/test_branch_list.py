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

from tests.unit._tool_registry_harness import open_workspace_harness


def test_branch_list_includes_created_branch(tmp_path) -> None:
    """Requirements: FR-10. UCs: UC-027."""
    harness = open_workspace_harness(tmp_path)
    try:
        harness.registry.call(
            "git_branch_create",
            {
                "workspace_id": harness.workspace_id,
                "name": "feature/list-check",
                "from_ref": harness.default_branch,
            },
        )
        listed = harness.registry.call("git_branch_list", {"workspace_id": harness.workspace_id})["branches"]
        assert harness.default_branch in listed
        assert "feature/list-check" in listed
    finally:
        harness.close()
