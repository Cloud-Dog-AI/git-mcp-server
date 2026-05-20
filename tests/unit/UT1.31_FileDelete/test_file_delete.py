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

from git_tools.security.scope import ScopeViolationError
from tests.unit._tool_registry_harness import open_workspace_harness


def test_file_delete_existing_missing_and_scope_block(tmp_path) -> None:
    """Requirements: FR-08. UCs: UC-007."""
    harness = open_workspace_harness(tmp_path)
    try:
        harness.registry.call(
            "file_write",
            {"workspace_id": harness.workspace_id, "path": "deleteme.txt", "content": "bye\n"},
        )
        harness.registry.call("file_delete", {"workspace_id": harness.workspace_id, "path": "deleteme.txt"})
        assert not (harness.workspace_path / "deleteme.txt").exists()

        # Current implementation is idempotent for missing paths.
        deleted = harness.registry.call("file_delete", {"workspace_id": harness.workspace_id, "path": "missing.txt"})
        assert deleted["deleted"] == "missing.txt"

        with pytest.raises(ScopeViolationError):
            harness.registry.call("file_delete", {"workspace_id": harness.workspace_id, "path": "../outside.txt"})
    finally:
        harness.close()
