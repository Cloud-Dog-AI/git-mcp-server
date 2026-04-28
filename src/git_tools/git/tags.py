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

from git_tools.git.repo import GitRepository


class TagService:
    """Tag operation helper."""

    def __init__(self, repo: GitRepository) -> None:
        self.repo = repo

    def list_tags(self) -> list[str]:
        """Return sorted tag names."""
        return sorted(tag.name for tag in self.repo.repo.tags)

    def create_tag(self, name: str, message: str | None = None) -> None:
        """Create lightweight or annotated tag."""
        if message:
            self.repo.repo.create_tag(name, message=message)
            return
        self.repo.repo.create_tag(name)

    def delete_tag(self, name: str) -> None:
        """Delete a local tag."""
        self.repo.repo.git.tag("-d", name)

    def push_tag(self, remote: str, name: str) -> str:
        """Push a tag to a remote."""
        return str(self.repo.repo.git.push(remote, name))

    def push_all_tags(self, remote: str = "origin") -> str:
        """Push all local tags to remote."""
        return str(self.repo.repo.git.push(remote, "--tags"))
