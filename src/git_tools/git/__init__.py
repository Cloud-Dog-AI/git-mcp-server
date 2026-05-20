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

"""Git repository primitives and safety helpers."""

from git_tools.git.conflicts import has_conflict_markers, list_conflicts, resolve_conflicts
from git_tools.git.operations import (
    StatusEntry,
    build_git_log_args,
    git_diff,
    git_fetch,
    git_log,
    git_merge,
    git_merge_abort,
    git_merge_continue,
    git_pull,
    git_push,
    git_rebase,
    git_rebase_abort,
    git_rebase_continue,
    git_status,
    parse_status_porcelain,
)
from git_tools.git.recovery import RecoveryManager
from git_tools.git.repo import GitRepository
from git_tools.git.tags import TagService

__all__ = [
    "GitRepository",
    "RecoveryManager",
    "StatusEntry",
    "TagService",
    "build_git_log_args",
    "git_diff",
    "git_fetch",
    "git_log",
    "git_merge",
    "git_merge_abort",
    "git_merge_continue",
    "git_pull",
    "git_push",
    "git_rebase",
    "git_rebase_abort",
    "git_rebase_continue",
    "git_status",
    "has_conflict_markers",
    "list_conflicts",
    "parse_status_porcelain",
    "resolve_conflicts",
]
