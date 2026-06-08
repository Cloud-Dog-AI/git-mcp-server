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

"""RBAC helpers using cloud_dog_idam.RBACEngine directly (PS-70 UM3).

License: Apache 2.0
Ownership: Cloud-Dog, Viewdeck Engineering Limited
Description: Thin service-layer RBAC functions for git-mcp tool access.
Requirements: CS1.1, UM3
Tasks: W28A-704
"""

from __future__ import annotations

from fnmatch import fnmatch

from cloud_dog_idam import RBACEngine


class AccessDeniedError(PermissionError):
    """Raised when RBAC blocks an operation."""


def can_execute_tool(
    engine: RBACEngine,
    role_patterns: dict[str, list[str]],
    user_id: str,
    tool_name: str,
    *,
    default_deny: bool = True,
) -> bool:
    """Check whether a user may execute a tool via wildcard role patterns."""
    for role in engine.get_effective_roles(user_id):
        for pattern in role_patterns.get(role, []):
            if pattern == "*" or fnmatch(tool_name, pattern):
                return True
    return not default_deny


def require_tool_access(
    engine: RBACEngine,
    role_patterns: dict[str, list[str]],
    user_id: str,
    tool_name: str,
) -> None:
    """Raise AccessDeniedError when tool access is not permitted."""
    if not can_execute_tool(engine, role_patterns, user_id, tool_name):
        raise AccessDeniedError(f"User {user_id!r} cannot execute tool {tool_name!r}")
