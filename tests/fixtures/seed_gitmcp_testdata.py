#!/usr/bin/env python3
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

"""W28J-1329 — deterministic, idempotent seed harness for the git-mcp deep-flow e2e suite.

Builds the W28J-1329 test-data catalog (the 6 waived-flow fixtures) into a target root with NO
manual steps. Re-runnable (idempotent): a re-run wipes + rebuilds the catalog to identical content.
Determinism: fixed author/committer identity AND fixed commit timestamps -> stable commit SHAs across
runs (no Math.random / wall-clock). Emits ``catalog.json`` (the manifest the e2e + coverage map read):
each fixture records its path + the GMC(s) it serves + the known-good assertions (commit messages,
diff hunks, conflict regions, job specs, provenance shape).

Usage:
    python -m tests.fixtures.seed_gitmcp_testdata [--root <dir>] [--print-catalog]
    # or: SEED_GITMCP_ROOT=<dir> python tests/fixtures/seed_gitmcp_testdata.py

The closing deep-run that flips the W28J waivers to PASS is W28J-1330; this module only builds the data.
"""

from __future__ import annotations

import argparse
import json
import os
import shutil
from pathlib import Path
from typing import Any

from git import Actor, Repo

# Fixed determinism anchors — DO NOT randomise (replay-safe per AGENT-LESSONS final-evidence gotchas).
_AUTHOR = Actor("Ada Lovelace", "ada@cloud-dog.test")
_COMMITTER = Actor("Cloud-Dog CI", "ci@cloud-dog.test")
_T0 = "2026-01-01T09:00:00"  # base author/committer date; each commit offsets deterministically
_DATES = [
    "2026-01-01T09:00:00",
    "2026-01-02T10:30:00",
    "2026-01-03T11:15:00",
    "2026-01-04T12:45:00",
    "2026-01-05T14:00:00",
]


def _commit(repo: Repo, message: str, idx: int) -> str:
    date = _DATES[idx % len(_DATES)]
    commit = repo.index.commit(message, author=_AUTHOR, committer=_COMMITTER, author_date=date, commit_date=date)
    return commit.hexsha


def _init(path: Path, *, bare: bool = False) -> Repo:
    path.mkdir(parents=True, exist_ok=True)
    repo = Repo.init(path, bare=bare, initial_branch="main")
    if not bare:
        repo.git.config("user.email", _COMMITTER.email)
        repo.git.config("user.name", _COMMITTER.name)
        repo.git.config("commit.gpgsign", "false")
    return repo


# --------------------------------------------------------------------------- C-09
def _build_commits_repo(root: Path) -> dict[str, Any]:
    """GMC-C-09: deterministic multi-commit history with known messages/authors/order."""
    p = root / "commits_repo"
    repo = _init(p)
    messages = [
        "C1: scaffold project (README + LICENSE)",
        "C2: add module alpha",
        "C3: add module beta + tests",
        "C4: document the public API",
    ]
    shas: list[str] = []
    (p / "README.md").write_text("# git-mcp seed: commits\n", encoding="utf-8")
    (p / "LICENSE").write_text("Apache-2.0\n", encoding="utf-8")
    repo.index.add(["README.md", "LICENSE"])
    shas.append(_commit(repo, messages[0], 0))
    (p / "alpha.py").write_text("def alpha():\n    return 'alpha'\n", encoding="utf-8")
    repo.index.add(["alpha.py"])
    shas.append(_commit(repo, messages[1], 1))
    (p / "beta.py").write_text("def beta():\n    return 'beta'\n", encoding="utf-8")
    (p / "test_beta.py").write_text("from beta import beta\n\ndef test_beta():\n    assert beta() == 'beta'\n", encoding="utf-8")
    repo.index.add(["beta.py", "test_beta.py"])
    shas.append(_commit(repo, messages[2], 2))
    (p / "API-REFERENCE.md").write_text("# API\n- alpha()\n- beta()\n", encoding="utf-8")
    repo.index.add(["API-REFERENCE.md"])
    shas.append(_commit(repo, messages[3], 3))
    return {
        "path": str(p),
        "gmc": ["GMC-C-09"],
        "branch": "main",
        "expected_commits": [
            {"message": m, "author": _AUTHOR.name, "author_email": _AUTHOR.email, "date": _DATES[i], "sha": shas[i]}
            for i, m in enumerate(messages)
        ],
        "assertion": "Commits page lists 4 commits newest-first with these exact messages + author 'Ada Lovelace'.",
    }


# --------------------------------------------------------------------------- X-03
def _build_diff_repo(root: Path) -> dict[str, Any]:
    """GMC-X-03: a base commit then a change commit exercising add/modify/delete/rename/binary."""
    p = root / "diff_repo"
    repo = _init(p)
    # base commit
    (p / "keep.txt").write_text("line1\nline2\nline3\n", encoding="utf-8")          # will be MODIFIED
    (p / "remove.txt").write_text("to be deleted\n", encoding="utf-8")               # will be DELETED
    (p / "old_name.txt").write_text("rename me unchanged\n", encoding="utf-8")       # will be RENAMED
    (p / "logo.bin").write_bytes(bytes(range(0, 64)))                                # will be BINARY-modified
    repo.index.add(["keep.txt", "remove.txt", "old_name.txt", "logo.bin"])
    base_sha = _commit(repo, "X1: base tree for diff fixtures", 0)
    # change commit
    (p / "added.txt").write_text("brand new file\n", encoding="utf-8")               # ADD
    (p / "keep.txt").write_text("line1\nline2-CHANGED\nline3\nline4-added\n", encoding="utf-8")  # MODIFY
    (p / "remove.txt").unlink()                                                      # DELETE
    repo.git.mv("old_name.txt", "new_name.txt")                                      # RENAME
    (p / "logo.bin").write_bytes(bytes(range(64, 160)))                              # BINARY modify
    repo.index.add(["added.txt", "keep.txt"])
    repo.index.remove(["remove.txt"])
    repo.index.add(["logo.bin"])
    change_sha = _commit(repo, "X2: add/modify/delete/rename/binary", 1)
    return {
        "path": str(p),
        "gmc": ["GMC-X-03"],
        "base_ref": base_sha,
        "change_ref": change_sha,
        "expected_hunks": {
            "add": "added.txt",
            "modify": "keep.txt (line2 changed, line4 added)",
            "delete": "remove.txt",
            "rename": "old_name.txt -> new_name.txt",
            "binary": "logo.bin (binary, no text hunk)",
        },
        "assertion": "Diff page (base..change) shows added.txt(A), keep.txt(M), remove.txt(D), rename old->new, logo.bin(binary).",
    }


# --------------------------------------------------------------------------- M-04
def _build_conflict_repo(root: Path) -> dict[str, Any]:
    """GMC-M-04: two branches engineered to produce a deterministic conflict in a known region."""
    p = root / "conflict_repo"
    repo = _init(p)
    conflict_file = "settings.conf"
    (p / conflict_file).write_text("name=base\nmode=shared\nvalue=ORIGINAL\nport=8080\n", encoding="utf-8")
    repo.index.add([conflict_file])
    base_sha = _commit(repo, "M1: base settings", 0)
    # main branch changes line 3
    repo.git.checkout("main")
    (p / conflict_file).write_text("name=base\nmode=shared\nvalue=MAIN-EDIT\nport=8080\n", encoding="utf-8")
    repo.index.add([conflict_file])
    main_sha = _commit(repo, "M2: main edits value", 1)
    # feature branch (from base) changes the SAME line differently -> conflict on merge
    repo.git.checkout(base_sha, b="feature/conflict")
    (p / conflict_file).write_text("name=base\nmode=shared\nvalue=FEATURE-EDIT\nport=8080\n", encoding="utf-8")
    repo.index.add([conflict_file])
    feature_sha = _commit(repo, "M3: feature edits value", 2)
    repo.git.checkout("main")
    return {
        "path": str(p),
        "gmc": ["GMC-M-04"],
        "base_branch": "main",
        "merge_branch": "feature/conflict",
        "conflict_file": conflict_file,
        "conflict_region": "line 3 (value=MAIN-EDIT vs value=FEATURE-EDIT)",
        "main_ref": main_sha,
        "feature_ref": feature_sha,
        "assertion": "git_merge main<-feature/conflict yields a conflict; Merge page surfaces settings.conf with the MAIN-EDIT/FEATURE-EDIT region.",
    }


# --------------------------------------------------------------------------- P-06
def _build_source_variants(root: Path) -> dict[str, Any]:
    """GMC-P-06: >=3 git-source variants as concrete profile fixtures."""
    variants_dir = root / "source_variants"
    # 1) local-path working repo
    local_repo = _init(variants_dir / "local_path_repo")
    (variants_dir / "local_path_repo" / "README.md").write_text("local path source\n", encoding="utf-8")
    local_repo.index.add(["README.md"])
    _commit(local_repo, "local-path source initial", 0)
    # 2) file:// bare remote (+ a working clone pushed to it)
    bare = _init(variants_dir / "bare_remote.git", bare=True)
    work = _init(variants_dir / "bare_work")
    (variants_dir / "bare_work" / "README.md").write_text("bare remote source\n", encoding="utf-8")
    work.index.add(["README.md"])
    _commit(work, "bare-remote source initial", 0)
    work.create_remote("origin", (variants_dir / "bare_remote.git").as_posix())
    work.git.push("-u", "origin", "HEAD:main")
    profiles = {
        "seed_local_path": {
            "source_type": "local-path",
            "repo": {"source": str(variants_dir / "local_path_repo"), "default_branch": "main"},
        },
        "seed_file_remote": {
            "source_type": "file-remote",
            "repo": {"source": (variants_dir / "bare_remote.git").as_uri(), "default_branch": "main"},
        },
        "seed_http_remote": {
            "source_type": "http-remote",
            "repo": {"source": "https://github.com/octocat/Hello-World.git", "default_branch": "master"},
        },
    }
    return {
        "path": str(variants_dir),
        "gmc": ["GMC-P-06"],
        "profiles": profiles,
        "assertion": "Profiles page loads each of the 3 source-type profiles and lists/opens its repo.",
    }


# --------------------------------------------------------------------------- J-05
def _build_job_specs(commits_repo: dict[str, Any]) -> dict[str, Any]:
    """GMC-J-05: a sync job and an async job spec, each emitting an audit event."""
    return {
        "gmc": ["GMC-J-05"],
        "sync_job": {
            "kind": "sync",
            "transport": "POST /api/v1/call/git_status (admin session)",
            "expectation": "immediate result envelope; Jobs/Audit shows a completed record with correlation_id.",
        },
        "async_job": {
            "kind": "async",
            "transport": "POST /api/v1/jobs/git-diff -> job_id -> poll /api/v1/jobs/{job_id}",
            "payload_repo": commits_repo["path"],
            "expectation": "job reaches succeeded; Jobs page row + audit-link resolves to the emitted git_mcp.* event.",
        },
        "assertion": "Both a sync (call) and async (job) path complete and each surfaces via the Jobs audit-link.",
    }


# --------------------------------------------------------------------------- SE-02
def _build_provenance_expectation() -> dict[str, Any]:
    """GMC-SE-02: the provenance data shape /settings/config/sources must return (backend = W28J-1328)."""
    return {
        "gmc": ["GMC-SE-02"],
        "endpoint": "GET /api/v1/settings/config/sources (admin session)",
        "shape": {
            "result.sources": "{ '<dot.path[i]>': { source: default|config|env|vault, secret: bool } }",
            "result.counts": "{ total, secret, default, config, env, vault }",
        },
        "invariants": ["counts.total > 0", ">=2 distinct source classes", "every leaf == {source,secret} (NO secret values)"],
        "backend_owner": "W28J-1328 (delivered + live)",
        "assertion": "Settings provenance legend renders the source counts + per-leaf badges from this endpoint.",
    }


def build_catalog(root: Path) -> dict[str, Any]:
    """Build the full catalog into ``root`` (idempotent: wipes + rebuilds). Returns the manifest."""
    if root.exists():
        shutil.rmtree(root)
    root.mkdir(parents=True, exist_ok=True)
    commits = _build_commits_repo(root)
    catalog = {
        "lane": "W28J-1329",
        "root": str(root),
        "determinism": {"author": f"{_AUTHOR.name} <{_AUTHOR.email}>", "fixed_dates": _DATES, "random": "none"},
        "fixtures": {
            "commits_repo": commits,
            "diff_repo": _build_diff_repo(root),
            "conflict_repo": _build_conflict_repo(root),
            "source_variants": _build_source_variants(root),
            "job_specs": _build_job_specs(commits),
            "provenance": _build_provenance_expectation(),
        },
    }
    (root / "catalog.json").write_text(json.dumps(catalog, indent=2, sort_keys=True), encoding="utf-8")
    return catalog


def main() -> int:
    parser = argparse.ArgumentParser(description="W28J-1329 git-mcp deep-flow seed harness")
    parser.add_argument("--root", default=os.environ.get("SEED_GITMCP_ROOT", "/tmp/git-mcp-seed-testdata"))
    parser.add_argument("--print-catalog", action="store_true")
    args = parser.parse_args()
    catalog = build_catalog(Path(args.root))
    gmcs = sorted({g for fx in catalog["fixtures"].values() for g in fx["gmc"]})
    print(f"W28J-1329 seed built at {args.root}: fixtures={list(catalog['fixtures'])} covering {gmcs}")
    if args.print_catalog:
        print(json.dumps(catalog, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
