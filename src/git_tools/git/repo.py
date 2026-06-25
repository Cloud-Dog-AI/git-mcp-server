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

import subprocess

from git import Actor, GitCommandError, Repo

from git_tools.process_env import current_process_env
from git_tools.security.git_auth import prime_git_https_credentials


class GitRepository:
    """High-level wrapper over GitPython Repo."""

    def __init__(self, repo_path: str | object) -> None:
        self.repo = Repo(str(repo_path))

    def _remote_url(self, remote: str) -> str:
        try:
            return str(self.repo.remote(remote).url)
        except (ValueError, AttributeError):
            return ""

    def _network_env(self, remote: str) -> dict[str, str]:
        env = current_process_env()
        remote_url = self._remote_url(remote)
        if remote_url:
            prime_git_https_credentials(env, remote_url)
        env["GIT_TERMINAL_PROMPT"] = "0"
        return env

    def status_porcelain(self) -> str:
        """Return git status in porcelain format."""
        return str(self.repo.git.status("--porcelain"))

    def log(self, *args: str) -> str:
        """Return git log output."""
        return str(self.repo.git.log(*args))

    def diff(self, left: str, right: str) -> str:
        """Return textual diff between two refs."""
        return str(self.repo.git.diff("--no-ext-diff", left, right))

    def add(self, *paths: str) -> None:
        """Stage file paths."""
        # Use native git add to correctly resolve unmerged paths during
        # merge/rebase conflict workflows.
        self.repo.git.add(*paths)

    def reset(self, *paths: str, hard: bool = False) -> str:
        """Reset index or working tree for optional paths."""
        if hard:
            return str(self.repo.git.reset("--hard"))
        if paths:
            return str(self.repo.git.reset("HEAD", "--", *paths))
        return str(self.repo.git.reset("HEAD"))

    def commit(
        self,
        message: str,
        author_name: str | None = None,
        author_email: str | None = None,
        committer_name: str | None = None,
        committer_email: str | None = None,
    ) -> str:
        """Create commit and return hash.

        W28M-1602: when author_name/author_email (and optionally committer
        fields) are supplied, stamp the commit with those identities so the
        agentic audit-log carries the real kickoff principal (cloud_dog_idam),
        not the service identity. When omitted, falls back to the repository's
        git config defaults (back-compat)."""
        author: Actor | None = None
        committer: Actor | None = None
        if author_name and author_email:
            author = Actor(author_name, author_email)
        if committer_name and committer_email:
            committer = Actor(committer_name, committer_email)
        elif author is not None:
            committer = author
        return self.repo.index.commit(
            message, author=author, committer=committer
        ).hexsha

    def branch_list(self) -> list[str]:
        """List local branch names."""
        return [branch.name for branch in self.repo.branches]

    def branch_create(self, name: str, from_ref: str = "HEAD") -> None:
        """Create a branch from a ref."""
        self.repo.git.branch(name, from_ref)

    def branch_delete(self, name: str, force: bool = False) -> None:
        """Delete a branch."""
        args = ["-D" if force else "-d", name]
        self.repo.git.branch(*args)

    def checkout(self, ref: str) -> None:
        """Checkout a branch/tag/commit."""
        self.repo.git.checkout(ref)

    def fetch(self, remote: str = "origin") -> str:
        """Fetch remote refs."""
        result = subprocess.run(
            ["git", "fetch", "--verbose", remote],
            cwd=self.repo.working_tree_dir,
            text=True,
            capture_output=True,
            timeout=180,
            check=False,
            env=self._network_env(remote),
        )
        if result.returncode != 0:
            raise GitCommandError(
                ["git", "fetch", "--verbose", remote],
                result.returncode,
                stderr=result.stderr,
                stdout=result.stdout,
            )
        return "\n".join(part.strip() for part in [result.stdout, result.stderr] if part.strip()).strip()

    def pull(self, remote: str = "origin", branch: str | None = None) -> str:
        """Pull from remote branch."""
        with self.repo.git.custom_environment(**self._network_env(remote)):
            if branch:
                return str(self.repo.git.pull(remote, branch))
            return str(self.repo.git.pull(remote))

    def push(self, remote: str = "origin", branch: str | None = None, force_with_lease: bool = False) -> str:
        """Push branch to remote."""
        args: list[str] = [remote]
        if branch:
            args.append(branch)
        if force_with_lease:
            args.append("--force-with-lease")
        with self.repo.git.custom_environment(**self._network_env(remote)):
            return str(self.repo.git.push(*args))

    def merge(self, ref: str, ff_only: bool = False) -> str:
        """Merge a branch/ref into current checkout."""
        if ff_only:
            return str(self.repo.git.merge("--ff-only", ref))
        return str(self.repo.git.merge(ref))

    def merge_abort(self) -> str:
        """Abort an in-progress merge."""
        return str(self.repo.git.merge("--abort"))

    def merge_continue(self) -> str:
        """Continue merge by creating merge commit."""
        return str(self.repo.git.commit("--no-edit"))

    def rebase(self, onto: str) -> str:
        """Rebase current branch onto target ref."""
        return str(self.repo.git.rebase(onto))

    def rebase_abort(self) -> str:
        """Abort an in-progress rebase."""
        return str(self.repo.git.rebase("--abort"))

    def rebase_continue(self) -> str:
        """Continue an in-progress rebase."""
        return str(self.repo.git.rebase("--continue"))

    def stash_save(self, message: str) -> str:
        """Stash local changes and return git output."""
        return str(self.repo.git.stash("push", "-u", "-m", message))

    def stash_list(self) -> str:
        """List stash entries."""
        return str(self.repo.git.stash("list"))

    def stash_pop(self) -> str:
        """Pop latest stash entry."""
        return str(self.repo.git.stash("pop"))
