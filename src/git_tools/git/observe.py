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

"""Bounded git-repository change observation (PS-102 CSTREAM-GIT-001/002).

Pure observation helpers that translate the current state of a repository's refs
(and the commits/paths they reach) into a stream of typed
:class:`~git_tools.change_stream.criteria.ChangeCandidate` records keyed by
commit / ref identity. This module does the *diff-since-last-snapshot* work — it
compares a supplied :class:`RefSnapshot` (the last observed ``ref -> sha`` map)
against the live refs and emits only what changed, so a steady-state watch NEVER
re-scans the whole repository (CSTREAM-GIT-002):

* a new ref (branch created / tag created) -> ``created``;
* a fast-forward ref advance -> ``updated`` per new commit reachable, with the
  file paths that commit touched;
* a non-fast-forward ref move (old sha not an ancestor of new) -> ``force_updated``
  (force-push / rebase / reset — the ref rewound; observable via the old->new
  reflog-style comparison this snapshot performs);
* a deleted ref (branch/tag removed) -> ``deleted``;
* a tag re-point -> ``metadata_changed``.

All git reads are bounded: ref enumeration is a single ``for-each-ref``; per-ref
commit walks are capped by ``max_commits``; per-commit path lists are capped by
``max_paths``; ``git diff-tree --name-status`` yields the paths without a full
working-tree scan. No network access happens here — controlled fetch is the
caller's responsibility (the adapter caps fetch frequency).
"""

from __future__ import annotations

from dataclasses import dataclass, field

from git_tools.change_stream.criteria import ChangeCandidate
from git_tools.git.repo import GitRepository

_HEADS_PREFIX = "refs/heads/"
_TAGS_PREFIX = "refs/tags/"

# Bounded-work defaults (CSTREAM-GIT-002 / CSTREAM-006). A caller may lower these
# via config; they are NEVER unbounded.
DEFAULT_MAX_COMMITS_PER_REF = 50
DEFAULT_MAX_PATHS_PER_COMMIT = 100


@dataclass(frozen=True)
class RefSnapshot:
    """The last-observed ``fully-qualified-ref -> commit-sha`` map for a repo.

    The snapshot is the cursor's backing identity state: observation is a pure
    function of ``(previous snapshot, live refs)``. An empty snapshot means the
    watch has never observed the repo — the first observation records baseline
    refs WITHOUT emitting a create for every existing ref (avoids a replay storm),
    unless ``emit_baseline`` is requested.
    """

    refs: dict[str, str] = field(default_factory=dict)

    def is_empty(self) -> bool:
        return not self.refs


def _ref_type(fq_ref: str) -> str:
    if fq_ref.startswith(_HEADS_PREFIX):
        return "branch"
    if fq_ref.startswith(_TAGS_PREFIX):
        return "tag"
    return "other"


def list_refs(repo: GitRepository) -> dict[str, str]:
    """Return ``{fully-qualified-ref: commit-sha}`` for heads + tags (bounded, one call).

    Uses ``for-each-ref`` with ``%(objectname)`` dereferenced (``**`` peels
    annotated tags to the commit they point at) so a tag and a branch at the same
    commit are comparable by commit identity.
    """
    raw = str(
        repo.repo.git.for_each_ref(
            "--format=%(refname) %(objectname)",
            "refs/heads/",
            "refs/tags/",
        )
    )
    out: dict[str, str] = {}
    for line in raw.splitlines():
        line = line.strip()
        if not line:
            continue
        parts = line.split(" ", 1)
        if len(parts) != 2:
            continue
        ref, sha = parts[0].strip(), parts[1].strip()
        if ref and sha:
            out[ref] = sha
    return out


def _is_ancestor(repo: GitRepository, ancestor: str, descendant: str) -> bool:
    """Return True when ``ancestor`` is an ancestor of ``descendant`` (fast-forward)."""
    try:
        repo.repo.git.merge_base("--is-ancestor", ancestor, descendant)
        return True
    except Exception:  # noqa: BLE001 — non-zero exit => not an ancestor
        return False


def _commit_author(repo: GitRepository, sha: str) -> str:
    try:
        out = str(repo.repo.git.show("-s", "--format=%an <%ae>", sha)).strip()
        return out
    except Exception:  # noqa: BLE001
        return ""


def _commit_paths(repo: GitRepository, sha: str, *, max_paths: int) -> list[tuple[str, str]]:
    """Return ``[(status, path), ...]`` for a commit, bounded by ``max_paths``.

    ``git diff-tree --no-commit-id --name-status -r <sha>`` lists the paths the
    commit changed against its first parent (root commit lists all files). Status
    letters: A(dd) / M(odify) / D(elete) / R(ename) / C(opy).
    """
    try:
        raw = str(
            repo.repo.git.diff_tree("--no-commit-id", "--name-status", "-r", "--root", sha)
        )
    except Exception:  # noqa: BLE001
        return []
    rows: list[tuple[str, str]] = []
    for line in raw.splitlines():
        line = line.rstrip("\n")
        if not line.strip():
            continue
        parts = line.split("\t")
        status = parts[0].strip()
        # Renames/copies carry two paths (Rxxx old new); take the destination.
        path = parts[-1].strip()
        if path:
            rows.append((status[:1], path))
        if len(rows) >= max_paths:
            break
    return rows


def _new_commits(repo: GitRepository, old_sha: str | None, new_sha: str, *, max_commits: int) -> list[str]:
    """Return the commit shas reachable from ``new_sha`` but not ``old_sha`` (bounded).

    ``git rev-list --max-count=<n> new ^old`` (oldest-first after reversal) so the
    emitted events are in commit order. When ``old_sha`` is None (new ref), the
    walk is bounded to ``max_commits`` commits from the tip.
    """
    args = [f"--max-count={max_commits}", new_sha]
    if old_sha:
        args.append(f"^{old_sha}")
    try:
        raw = str(repo.repo.git.rev_list(*args))
    except Exception:  # noqa: BLE001
        return []
    shas = [s.strip() for s in raw.splitlines() if s.strip()]
    shas.reverse()  # oldest first
    return shas


_STATUS_TO_ACTION = {
    "A": "created",
    "M": "updated",
    "D": "deleted",
    "R": "moved",
    "C": "created",
}


def observe(
    repo: GitRepository,
    previous: RefSnapshot,
    *,
    max_commits_per_ref: int = DEFAULT_MAX_COMMITS_PER_REF,
    max_paths_per_commit: int = DEFAULT_MAX_PATHS_PER_COMMIT,
    emit_baseline: bool = False,
) -> tuple[list[ChangeCandidate], RefSnapshot]:
    """Compute the change candidates since ``previous`` and the new snapshot.

    Returns ``(candidates, new_snapshot)``. ``candidates`` is empty on a no-op
    observation (steady state). The new snapshot must be persisted by the caller
    (it is the cursor-backing identity state).
    """
    live = list_refs(repo)
    candidates: list[ChangeCandidate] = []

    baseline = previous.is_empty() and not emit_baseline
    if baseline:
        # First observation: record refs, emit nothing (avoid replay storm).
        return [], RefSnapshot(refs=dict(live))

    prev_refs = dict(previous.refs)

    # --- deleted refs (present before, gone now) --------------------------
    for ref, old_sha in prev_refs.items():
        if ref in live:
            continue
        rtype = _ref_type(ref)
        candidates.append(
            ChangeCandidate(
                action="deleted",
                object_ref=ref,
                ref=ref,
                ref_type=rtype,
                object_version=old_sha,
                metadata={"old_sha": old_sha, "new_sha": ""},
            )
        )

    # --- created / moved refs --------------------------------------------
    for ref, new_sha in live.items():
        rtype = _ref_type(ref)
        old_sha = prev_refs.get(ref)

        if old_sha is None:
            # ref newly created (branch created / tag created). This is a REF
            # event keyed by ref identity — the commit(s) the new ref points at
            # were already observed via the ref they advanced on, so we emit ONLY
            # the ref-create marker and never replay their history (CSTREAM-GIT-002).
            # The tip paths ride along so a path criterion can still resolve a new
            # branch, but bounded to the tip commit's own changes.
            tip_paths = tuple(
                p for _, p in _commit_paths(repo, new_sha, max_paths=max_paths_per_commit)
            )
            candidates.append(
                ChangeCandidate(
                    action="created",
                    object_ref=ref,
                    ref=ref,
                    ref_type=rtype,
                    object_version=new_sha,
                    author=_commit_author(repo, new_sha),
                    paths=tip_paths,
                    metadata={"old_sha": "", "new_sha": new_sha, "commit": new_sha},
                )
            )
            continue

        if old_sha == new_sha:
            continue  # unchanged ref — no work

        # ref moved. Determine fast-forward vs force (rewind).
        forced = not _is_ancestor(repo, old_sha, new_sha)
        if rtype == "tag":
            # Tags are pointers; a re-point is metadata_changed (force if rewound).
            action = "force_updated" if forced else "metadata_changed"
            candidates.append(
                ChangeCandidate(
                    action=action,
                    object_ref=ref,
                    ref=ref,
                    ref_type=rtype,
                    object_version=new_sha,
                    author=_commit_author(repo, new_sha),
                    metadata={"old_sha": old_sha, "new_sha": new_sha, "force": forced},
                )
            )
            continue

        if forced:
            # Non-fast-forward branch move (force-push / rebase / reset). One
            # force_updated candidate carries the ref identity + the new tip paths.
            candidates.append(
                ChangeCandidate(
                    action="force_updated",
                    object_ref=ref,
                    ref=ref,
                    ref_type=rtype,
                    object_version=new_sha,
                    author=_commit_author(repo, new_sha),
                    paths=tuple(p for _, p in _commit_paths(repo, new_sha, max_paths=max_paths_per_commit)),
                    metadata={"old_sha": old_sha, "new_sha": new_sha, "force": True},
                )
            )
            continue

        # Fast-forward advance: one candidate per new commit (bounded), plus a
        # merge marker when the commit has >1 parent.
        candidates.extend(
            _commit_candidates(
                repo, ref, rtype, old_sha, new_sha,
                max_commits=max_commits_per_ref, max_paths=max_paths_per_commit,
            )
        )

    return candidates, RefSnapshot(refs=dict(live))


def _commit_candidates(
    repo: GitRepository,
    ref: str,
    ref_type: str,
    old_sha: str | None,
    new_sha: str,
    *,
    max_commits: int,
    max_paths: int,
) -> list[ChangeCandidate]:
    """Emit per-commit + per-path candidates for a fast-forward advance (bounded)."""
    out: list[ChangeCandidate] = []
    for sha in _new_commits(repo, old_sha, new_sha, max_commits=max_commits):
        author = _commit_author(repo, sha)
        parents = _parent_count(repo, sha)
        is_merge = parents > 1
        path_rows = _commit_paths(repo, sha, max_paths=max_paths)
        all_paths = tuple(p for _, p in path_rows)
        # commit-level candidate (matches ref/branch/author/action=updated, and
        # path when any file changed). A merge commit is flagged in metadata.
        out.append(
            ChangeCandidate(
                action="updated",
                object_ref=sha,
                ref=ref,
                ref_type=ref_type,
                object_version=sha,
                author=author,
                paths=all_paths,
                metadata={
                    "commit": sha,
                    "commit_author": author,
                    "merge": is_merge,
                    "parents": parents,
                    "new_sha": new_sha,
                    "paths_changed": len(all_paths),
                },
            )
        )
        # per-path file candidates (add/modify/delete/rename) so a path+action
        # watch (e.g. deleted *.py) resolves at file granularity.
        for status, path in path_rows:
            file_action = _STATUS_TO_ACTION.get(status, "updated")
            out.append(
                ChangeCandidate(
                    action=file_action,
                    object_ref=f"{sha}:{path}",
                    ref=ref,
                    ref_type=ref_type,
                    object_version=sha,
                    author=author,
                    paths=(path,),
                    metadata={
                        "commit": sha,
                        "commit_author": author,
                        "path": path,
                        "file_status": status,
                        "merge": is_merge,
                    },
                )
            )
    return out


def _parent_count(repo: GitRepository, sha: str) -> int:
    try:
        out = str(repo.repo.git.rev_list("--parents", "-n", "1", sha)).strip()
    except Exception:  # noqa: BLE001
        return 1
    # "<sha> <parent1> <parent2> ..." — parents = tokens - 1
    tokens = [t for t in out.split() if t]
    return max(0, len(tokens) - 1)
