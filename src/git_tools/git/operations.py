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

from git_tools.git.repo import GitRepository


@dataclass(slots=True)
class StatusEntry:
    """Parsed `git status --porcelain` line."""

    index_status: str
    worktree_status: str
    path: str


def parse_status_porcelain(raw: str) -> list[StatusEntry]:
    """Parse porcelain output into typed entries."""
    entries: list[StatusEntry] = []
    for line in raw.splitlines():
        if not line.strip():
            continue
        entries.append(
            StatusEntry(
                index_status=line[0],
                worktree_status=line[1],
                path=line[3:],
            )
        )
    return entries


def build_git_log_args(
    author: str | None = None,
    since: str | None = None,
    until: str | None = None,
    path: str | None = None,
    max_count: int | None = None,
) -> list[str]:
    """Build deterministic git log argument list from filters."""
    args: list[str] = ["--oneline"]
    if author:
        args.append(f"--author={author}")
    if since:
        args.append(f"--since={since}")
    if until:
        args.append(f"--until={until}")
    if max_count is not None:
        args.append(f"--max-count={max_count}")
    if path:
        args.extend(["--", path])
    return args


def git_status(repo: GitRepository) -> list[StatusEntry]:
    """Return parsed status for repository."""
    return parse_status_porcelain(repo.status_porcelain())


def git_log(repo: GitRepository, **filters: str | int | None) -> str:
    """Run `git log` with filter arguments."""
    args = build_git_log_args(
        author=filters.get("author"),  # type: ignore[arg-type]
        since=filters.get("since"),  # type: ignore[arg-type]
        until=filters.get("until"),  # type: ignore[arg-type]
        path=filters.get("path"),  # type: ignore[arg-type]
        max_count=filters.get("max_count"),  # type: ignore[arg-type]
    )
    return repo.log(*args)


def git_diff(repo: GitRepository, left: str = "HEAD~1", right: str = "HEAD") -> str:
    """Return diff between two refs."""
    return repo.diff(left, right)


def git_merge(repo: GitRepository, ref: str, ff_only: bool = False) -> str:
    """Merge a branch/ref into current branch."""
    return repo.merge(ref, ff_only=ff_only)


def git_rebase(repo: GitRepository, onto: str) -> str:
    """Rebase current branch onto target ref."""
    return repo.rebase(onto)


def git_fetch(repo: GitRepository, remote: str = "origin") -> str:
    """Fetch refs from a remote."""
    return repo.fetch(remote=remote)


def git_pull(repo: GitRepository, remote: str = "origin", branch: str | None = None) -> str:
    """Pull updates from remote."""
    return repo.pull(remote=remote, branch=branch)


def git_push(
    repo: GitRepository,
    remote: str = "origin",
    branch: str | None = None,
    force_with_lease: bool = False,
) -> str:
    """Push updates to remote."""
    return repo.push(remote=remote, branch=branch, force_with_lease=force_with_lease)


def git_merge_abort(repo: GitRepository) -> str:
    """Abort in-progress merge."""
    return repo.merge_abort()


def git_merge_continue(repo: GitRepository) -> str:
    """Continue in-progress merge."""
    return repo.merge_continue()


def git_rebase_abort(repo: GitRepository) -> str:
    """Abort in-progress rebase."""
    return repo.rebase_abort()


def git_rebase_continue(repo: GitRepository) -> str:
    """Continue in-progress rebase."""
    return repo.rebase_continue()
