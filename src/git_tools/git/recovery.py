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

import uuid

from cloud_dog_storage import path_utils
from git import Repo

from git_tools.files.io import store_host_text


class RecoveryManager:
    """Recovery artefact helpers for ungraceful session endings."""

    def __init__(self, repo_path: str | object) -> None:
        self.repo = Repo(str(repo_path))

    def stash_changes(self, label: str) -> str:
        """Stash working tree changes."""
        return str(self.repo.git.stash("push", "-u", "-m", label))

    def create_recovery_branch(self, session_id: str) -> str:
        """Create a recovery branch from current HEAD."""
        branch = f"recovery/{session_id}-{uuid.uuid4().hex[:8]}"
        self.repo.git.checkout("-b", branch)
        return branch

    def create_patch_bundle(self, output_dir: str | object, session_id: str):
        """Write a binary patch bundle from working diff."""
        out_dir = path_utils.as_path(str(output_dir)).expanduser().resolve()
        out_dir.mkdir(parents=True, exist_ok=True)
        patch_path = out_dir / f"recovery-{session_id}.patch"
        # Force Git's internal diff to avoid external diff tools from user config.
        patch = self.repo.git.diff("--no-ext-diff", "--binary")
        store_host_text(patch_path, patch)
        return patch_path
