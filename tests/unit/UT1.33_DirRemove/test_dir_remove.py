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

from tests.unit._tool_registry_harness import open_workspace_harness


def test_dir_remove_empty_non_empty_and_recursive(tmp_path) -> None:
    """Requirements: FR-08. UCs: UC-010."""
    harness = open_workspace_harness(tmp_path)
    try:
        harness.registry.call("dir_mkdir", {"workspace_id": harness.workspace_id, "path": "empty"})
        harness.registry.call("dir_rmdir", {"workspace_id": harness.workspace_id, "path": "empty"})
        assert not (harness.workspace_path / "empty").exists()

        harness.registry.call("dir_mkdir", {"workspace_id": harness.workspace_id, "path": "nonempty"})
        harness.registry.call(
            "file_write",
            {"workspace_id": harness.workspace_id, "path": "nonempty/a.txt", "content": "x\n"},
        )
        with pytest.raises(OSError):
            harness.registry.call(
                "dir_rmdir",
                {"workspace_id": harness.workspace_id, "path": "nonempty", "recursive": False},
            )

        harness.registry.call(
            "dir_rmdir",
            {"workspace_id": harness.workspace_id, "path": "nonempty", "recursive": True},
        )
        assert not (harness.workspace_path / "nonempty").exists()
    finally:
        harness.close()
