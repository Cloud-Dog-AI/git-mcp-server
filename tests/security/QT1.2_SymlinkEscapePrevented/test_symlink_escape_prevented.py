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

from pathlib import Path

import pytest

from git_tools.security.scope import ScopeViolationError, enforce_path_scope


def test_symlink_escape_prevented(tmp_path: Path) -> None:
    """Requirements: FR-01, NFR-02."""
    outside = tmp_path / "outside.txt"
    outside.write_text("secret", encoding="utf-8")

    workspace = tmp_path / "workspace"
    workspace.mkdir()
    symlink = workspace / "escape"
    symlink.symlink_to(outside)

    with pytest.raises(ScopeViolationError):
        enforce_path_scope(workspace, "../outside.txt")
