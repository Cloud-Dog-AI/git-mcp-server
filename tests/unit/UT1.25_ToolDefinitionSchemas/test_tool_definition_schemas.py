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

from git_tools.tools.registry import ToolRegistry
from git_tools.workspaces.manager import WorkspaceManager


def test_tool_definition_schemas_validate() -> None:
    """Requirements: FR-02."""
    manager = WorkspaceManager(Path("working/tool-schemas"))
    registry = ToolRegistry(manager)
    tools = registry.list_tools()

    names = {tool["name"] for tool in tools}
    assert len(tools) >= 49
    required = {
        "repo_open",
        "repo_set_ref",
        "repo_close",
        "git_status",
        "git_push",
        "git_conflict_resolve_manual",
        "file_write",
        "file_upload",
        "dir_list",
        "search_content",
        "admin_profile_create",
        "admin_credentials_set",
    }
    assert required.issubset(names)

    for tool in tools:
        assert "input_schema" in tool
        assert isinstance(tool["input_schema"], dict)
        assert tool["input_schema"].get("type") == "object"
