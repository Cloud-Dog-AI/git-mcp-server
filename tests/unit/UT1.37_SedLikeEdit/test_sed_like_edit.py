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

from git_tools.files.edit.text import replace_file_text


def test_sed_like_edit_pattern_multiline_and_no_match(tmp_path: Path) -> None:
    """Requirements: FR-09. UCs: UC-018."""
    target = tmp_path / "notes.txt"
    target.write_text("line1\nline2\nline3\n", encoding="utf-8")

    replaced = replace_file_text(target, "line2", "middle")
    assert "middle" in replaced
    assert target.read_text(encoding="utf-8") == "line1\nmiddle\nline3\n"

    multiline = replace_file_text(target, "line1\nmiddle", "top\ncenter")
    assert "top\ncenter" in multiline

    unchanged = replace_file_text(target, "does-not-exist", "noop")
    assert unchanged == target.read_text(encoding="utf-8")
