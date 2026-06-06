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

"""Structured edit helpers by format."""

from git_tools.files.edit.json_yaml import edit_json_file, edit_yaml_file, set_json_pointer
from git_tools.files.edit.markdown import replace_markdown_section
from git_tools.files.edit.text import replace_file_text, replace_text
from git_tools.files.edit.xml_html import edit_html_css, edit_xml_xpath

__all__ = [
    "edit_html_css",
    "edit_json_file",
    "edit_xml_xpath",
    "edit_yaml_file",
    "replace_file_text",
    "replace_markdown_section",
    "replace_text",
    "set_json_pointer",
]
