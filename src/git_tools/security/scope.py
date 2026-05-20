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

import os
from fnmatch import fnmatch

from cloud_dog_storage import path_utils


class ScopeViolationError(PermissionError):
    """Raised when a path escapes workspace scope."""


def resolve_workspace_path(workspace_root: str | os.PathLike[str], requested_path: str):
    """Resolve and verify a path is inside the workspace root."""
    root = path_utils.as_path(str(workspace_root)).resolve()
    candidate = (root / requested_path).resolve()
    if root not in [candidate, *candidate.parents]:
        raise ScopeViolationError(f"Path escapes workspace root: {requested_path}")
    return candidate


def path_allowed(workspace_root: str | os.PathLike[str], requested_path: str, deny_globs: list[str] | None = None) -> bool:
    """Return whether a path is allowed by deny-glob rules."""
    deny_patterns = deny_globs or ["**/.git/**"]
    path = resolve_workspace_path(workspace_root, requested_path)
    root = path_utils.as_path(str(workspace_root)).resolve()
    relative = path.relative_to(root).as_posix()
    relative_with_dot = f"./{relative}" if relative else "."
    return all(not (fnmatch(relative, pattern) or fnmatch(relative_with_dot, pattern)) for pattern in deny_patterns)


def enforce_path_scope(workspace_root: str | os.PathLike[str], requested_path: str, deny_globs: list[str] | None = None):
    """Resolve path and raise when deny patterns block access."""
    resolved = resolve_workspace_path(workspace_root, requested_path)
    if not path_allowed(workspace_root, requested_path, deny_globs=deny_globs):
        raise ScopeViolationError(f"Path denied by policy: {requested_path}")
    return resolved


def can_write_branch(branch_name: str, protected_patterns: list[str], roles: set[str]) -> bool:
    """Allow writes unless branch is protected and caller lacks elevated role."""
    is_protected = any(fnmatch(branch_name, pattern) for pattern in protected_patterns)
    if not is_protected:
        return True
    return bool({"admin", "maintainer"} & roles)
