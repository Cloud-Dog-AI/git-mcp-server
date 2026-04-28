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

from git_tools.files.edit.xml_html import edit_html_css, edit_xml_xpath


def test_xml_and_html_edit_operations(tmp_path: Path) -> None:
    """Requirements: FR-09. UCs: UC-017."""
    xml_file = tmp_path / "sample.xml"
    xml_file.write_text("<root><item id='1'>old</item></root>", encoding="utf-8")
    changed_xml = edit_xml_xpath(xml_file, "//item", "new")
    assert changed_xml == 1
    assert "new" in xml_file.read_text(encoding="utf-8")

    html_file = tmp_path / "sample.html"
    html_file.write_text("<html><body><div class='target'>old</div></body></html>", encoding="utf-8")
    changed_html = edit_html_css(html_file, ".target", "new")
    assert changed_html == 1
    assert "new" in html_file.read_text(encoding="utf-8")

    no_match = edit_xml_xpath(xml_file, "//missing", "noop")
    assert no_match == 0
