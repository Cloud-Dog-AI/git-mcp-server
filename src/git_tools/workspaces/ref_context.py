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

from dataclasses import dataclass
from typing import Literal

from git import BadName, Repo

RefType = Literal["branch", "tag", "commit"]
RefMode = Literal["working_tree", "ref_readonly"]


@dataclass(slots=True)
class RefContext:
    """Resolved reference context for workspace operations."""

    ref_type: RefType
    ref_name: str
    resolved_commit: str
    mode: RefMode


class RefResolver:
    """Resolve refs against a git repository."""

    def __init__(self, repo: Repo) -> None:
        self._repo = repo

    def resolve(self, ref_type: RefType, ref_name: str) -> RefContext:
        """Resolve a ref into commit hash and operation mode."""
        if ref_type == "branch":
            if ref_name not in [h.name for h in self._repo.branches]:
                raise ValueError(f"Branch does not exist: {ref_name}")
            commit = self._repo.branches[ref_name].commit.hexsha
            return RefContext(ref_type="branch", ref_name=ref_name, resolved_commit=commit, mode="working_tree")

        if ref_type == "tag":
            if ref_name not in [t.name for t in self._repo.tags]:
                raise ValueError(f"Tag does not exist: {ref_name}")
            tag_ref = self._repo.tags[ref_name]
            commit = tag_ref.commit.hexsha
            return RefContext(ref_type="tag", ref_name=ref_name, resolved_commit=commit, mode="ref_readonly")

        if ref_type == "commit":
            try:
                commit = self._repo.commit(ref_name).hexsha
            except (BadName, ValueError) as exc:
                raise ValueError(f"Commit does not exist: {ref_name}") from exc
            return RefContext(ref_type="commit", ref_name=ref_name, resolved_commit=commit, mode="ref_readonly")

        raise ValueError(f"Unsupported ref type: {ref_type}")
