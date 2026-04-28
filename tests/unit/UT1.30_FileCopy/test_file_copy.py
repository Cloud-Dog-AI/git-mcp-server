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


def test_file_copy_success_and_missing_source_error(tmp_path) -> None:
    """Requirements: FR-08. UCs: UC-006."""
    harness = open_workspace_harness(tmp_path)
    try:
        harness.registry.call(
            "file_write",
            {"workspace_id": harness.workspace_id, "path": "source.txt", "content": "copy-me\n"},
        )
        copied = harness.registry.call(
            "file_copy",
            {"workspace_id": harness.workspace_id, "src": "source.txt", "dst": "dest.txt"},
        )
        assert copied["path"] == "dest.txt"
        assert (harness.workspace_path / "source.txt").read_text(encoding="utf-8") == "copy-me\n"
        assert (harness.workspace_path / "dest.txt").read_text(encoding="utf-8") == "copy-me\n"

        with pytest.raises(FileNotFoundError):
            harness.registry.call(
                "file_copy",
                {"workspace_id": harness.workspace_id, "src": "missing.txt", "dst": "noop.txt"},
            )
    finally:
        harness.close()
