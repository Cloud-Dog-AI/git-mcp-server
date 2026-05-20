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


def test_dir_create_nested_existing_and_parents_false_error(tmp_path) -> None:
    """Requirements: FR-08. UCs: UC-009."""
    harness = open_workspace_harness(tmp_path)
    try:
        created = harness.registry.call(
            "dir_mkdir",
            {"workspace_id": harness.workspace_id, "path": "one/two/three", "parents": True},
        )
        assert created["path"] == "one/two/three"
        assert (harness.workspace_path / "one" / "two" / "three").is_dir()

        again = harness.registry.call(
            "dir_mkdir",
            {"workspace_id": harness.workspace_id, "path": "one/two/three", "parents": True},
        )
        assert again["path"] == "one/two/three"

        with pytest.raises(FileNotFoundError):
            harness.registry.call(
                "dir_mkdir",
                {"workspace_id": harness.workspace_id, "path": "missing/child", "parents": False},
            )
    finally:
        harness.close()
