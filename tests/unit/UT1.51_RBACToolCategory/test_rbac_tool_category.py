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

from cloud_dog_idam import RBACEngine
from git_tools.security.rbac import can_execute_tool


def test_rbac_tool_category_permissions() -> None:
    """Requirements: FR-05. UCs: UC-080."""
    role_patterns = {
        "reader": ["git_status", "git_log", "file_read", "search_*"],
        "writer": ["git_*", "file_*", "dir_*"],
        "admin": ["admin_*"],
    }
    engine = RBACEngine(role_permissions={r: set(p) for r, p in role_patterns.items()})
    engine.assign_role_to_user("alice", "reader")
    engine.assign_role_to_user("bob", "writer")
    engine.assign_role_to_user("carol", "admin")

    assert can_execute_tool(engine, role_patterns, "alice", "git_status")
    assert can_execute_tool(engine, role_patterns, "alice", "search_files")
    assert not can_execute_tool(engine, role_patterns, "alice", "git_push")
    assert not can_execute_tool(engine, role_patterns, "alice", "admin_profile_create")

    assert can_execute_tool(engine, role_patterns, "bob", "git_push")
    assert can_execute_tool(engine, role_patterns, "bob", "file_write")
    assert not can_execute_tool(engine, role_patterns, "bob", "admin_profile_create")

    assert can_execute_tool(engine, role_patterns, "carol", "admin_profile_create")
    assert not can_execute_tool(engine, role_patterns, "carol", "git_push")
