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

from cloud_dog_storage import path_utils
from git import Repo

from git_tools.files.io import store_host_text


def list_conflicts(repo_path: str | object) -> list[str]:
    """List unresolved conflict file paths."""
    repo = Repo(str(repo_path))
    output = repo.git.diff("--name-only", "--diff-filter=U")
    return [line for line in output.splitlines() if line.strip()]


def has_conflict_markers(content: str) -> bool:
    """Return true when conflict markers are present."""
    return "<<<<<<<" in content and "=======" in content and ">>>>>>>" in content


def resolve_conflicts(repo_path: str | object, mode: str, paths: list[str], manual_content: str | None = None) -> None:
    """Resolve conflicts via ours/theirs/manual strategies and stage files."""
    repo = Repo(str(repo_path))
    for path in paths:
        if mode == "ours":
            repo.git.checkout("--ours", path)
        elif mode == "theirs":
            repo.git.checkout("--theirs", path)
        elif mode == "manual":
            if manual_content is None:
                raise ValueError("manual_content is required for manual mode")
            target = path_utils.as_path(str(repo_path)).resolve() / path
            store_host_text(target, manual_content)
        else:
            raise ValueError(f"Unsupported conflict mode: {mode}")
        repo.git.add(path)
