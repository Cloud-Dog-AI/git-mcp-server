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

import re
from fnmatch import fnmatch

from cloud_dog_storage import path_utils

from git_tools.files.io import load_host_text
from git_tools.security.scope import resolve_workspace_path


def _match_globs(path: str, globs: list[str] | None) -> bool:
    if not globs:
        return True
    return any(fnmatch(path, pattern) for pattern in globs)


def search_files(workspace_root: str | Path, query: str, globs: list[str] | None = None) -> list[str]:
    """Search for file paths containing a query string."""
    root = resolve_workspace_path(workspace_root, ".")
    matches: list[str] = []
    for item in root.rglob("*"):
        if not item.is_file():
            continue
        rel = item.relative_to(root).as_posix()
        if query in rel and _match_globs(rel, globs):
            matches.append(rel)
    return matches


def search_content(
    workspace_root: str | Path,
    query: str,
    globs: list[str] | None = None,
    regex: bool = False,
    case_sensitive: bool = False,
    max_results: int = 200,
) -> list[dict[str, str]]:
    """Search file content and return matching lines with path metadata."""
    root = resolve_workspace_path(workspace_root, ".")
    flags = 0 if case_sensitive else re.IGNORECASE
    pattern = re.compile(query, flags) if regex else None

    results: list[dict[str, str]] = []
    for current_dir, _, filenames in path_utils.walk(str(root)):
        if len(results) >= max_results:
            break
        current_path = path_utils.as_path(current_dir)
        for name in filenames:
            if len(results) >= max_results:
                break
            item = current_path / name
            rel = item.relative_to(root).as_posix()
            if not _match_globs(rel, globs):
                continue
            try:
                lines = load_host_text(item, errors="ignore").splitlines()
            except OSError:
                continue
            for index, line in enumerate(lines, start=1):
                if pattern:
                    matched = bool(pattern.search(line))
                elif case_sensitive:
                    matched = query in line
                else:
                    matched = query.lower() in line.lower()
                if not matched:
                    continue
                results.append({"path": rel, "line": str(index), "text": line})
                if len(results) >= max_results:
                    break
    return results
