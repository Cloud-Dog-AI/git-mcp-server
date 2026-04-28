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
import yaml

from git_tools.files.edit.json_yaml import edit_yaml_file


def test_yaml_edit_update_add_and_soft_delete(tmp_path: Path) -> None:
    """Requirements: FR-09. UCs: UC-016."""
    target = tmp_path / "config.yaml"
    target.write_text("service:\n  enabled: true\n", encoding="utf-8")

    updated = edit_yaml_file(target, "/service/enabled", False)
    assert updated["service"]["enabled"] is False

    updated = edit_yaml_file(target, "/service/region", "eu-west-2")
    assert updated["service"]["region"] == "eu-west-2"

    updated = edit_yaml_file(target, "/service/region", None)
    assert updated["service"]["region"] is None


def test_yaml_edit_invalid_yaml_raises(tmp_path: Path) -> None:
    """Requirements: FR-09. UCs: UC-016."""
    target = tmp_path / "broken.yaml"
    target.write_text("service: [", encoding="utf-8")
    with pytest.raises(yaml.YAMLError):
        edit_yaml_file(target, "/service/enabled", True)
