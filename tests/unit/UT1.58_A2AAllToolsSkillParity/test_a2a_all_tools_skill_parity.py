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

"""W28A-224: Verify A2A exposes all MCP tools as skills."""

from __future__ import annotations

from git_mcp_server.a2a_server import create_a2a_app
import pytest
# FR-1.18 traceability marker for existing git-mcp coverage.
@pytest.mark.UT
@pytest.mark.mcp
@pytest.mark.req("FR-004")  # W28E-1804A semantic rebind


def test_a2a_skills_cover_all_mcp_tools() -> None:
    """Every MCP tool must have a corresponding A2A skill."""
    app = create_a2a_app()

    # Extract skills from the agent card endpoint
    from starlette.testclient import TestClient

    client = TestClient(app)
    resp = client.get("/.well-known/agent.json")
    assert resp.status_code == 200
    card = resp.json()
    skill_ids = {s["id"] for s in card.get("skills", [])}

    # The MCP tool registry has 63 tools
    assert len(skill_ids) >= 63, (
        f"A2A agent card exposes only {len(skill_ids)} skills, expected >= 63"
    )

    # Verify key tools are present
    expected_tools = {
        "repo_open", "repo_close", "repo_set_ref",
        "git_status", "git_log", "git_diff", "git_add", "git_commit",
        "git_push", "git_pull", "git_fetch",
        "git_branch_list", "git_branch_create", "git_branch_delete",
        "git_tag_list", "git_tag_create", "git_tag_delete",
        "file_read", "file_write", "file_delete",
        "dir_list", "dir_mkdir",
        "search_content", "search_files",
        "admin_user_list", "admin_user_create",
        "admin_group_list", "admin_api_key_list",
    }
    missing = expected_tools - skill_ids
    assert not missing, f"A2A missing skills: {sorted(missing)}"
