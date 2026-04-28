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


def test_stash_list_with_and_without_entries(tmp_path) -> None:
    """Requirements: FR-10. UCs: UC-058."""
    harness = open_workspace_harness(tmp_path)
    try:
        empty = harness.registry.call("git_stash_list", {"workspace_id": harness.workspace_id})["result"]
        assert empty == ""

        harness.registry.call(
            "file_write",
            {"workspace_id": harness.workspace_id, "path": "stash.txt", "content": "pending\n"},
        )
        harness.registry.call(
            "git_stash_save",
            {"workspace_id": harness.workspace_id, "message": "save-for-test"},
        )
        listed = harness.registry.call("git_stash_list", {"workspace_id": harness.workspace_id})["result"]
        assert "stash@{0}" in listed
        assert "save-for-test" in listed
    finally:
        harness.close()
