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

"""Security policy and RBAC helpers."""

from git_tools.security.rbac import AccessDeniedError, can_execute_tool, require_tool_access
from git_tools.security.scope import (
    ScopeViolationError,
    can_write_branch,
    enforce_path_scope,
    path_allowed,
    resolve_workspace_path,
)

__all__ = [
    "AccessDeniedError",
    "can_execute_tool",
    "ScopeViolationError",
    "can_write_branch",
    "enforce_path_scope",
    "path_allowed",
    "require_tool_access",
    "resolve_workspace_path",
]
