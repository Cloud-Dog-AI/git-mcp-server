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

from git_tools.files.search import search_content


def test_file_search_content(tmp_path: Path) -> None:
    """Requirements: FR-08, UC-02."""
    (tmp_path / "docs").mkdir()
    (tmp_path / "docs" / "a.md").write_text("TODO: item\n", encoding="utf-8")
    matches = search_content(tmp_path, "TODO", globs=["**/*.md"])
    assert matches
    assert matches[0]["path"].endswith("a.md")
