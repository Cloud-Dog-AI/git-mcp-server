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

import json
from pathlib import Path

from git_tools.files.edit.json_yaml import edit_json_file


def test_structured_edit_json(tmp_path: Path) -> None:
    """Requirements: FR-09, NFR-03."""
    target = tmp_path / "data.json"
    target.write_text(json.dumps({"a": {"b": 1}}), encoding="utf-8")
    updated = edit_json_file(target, "/a/b", 2)
    assert updated["a"]["b"] == 2
