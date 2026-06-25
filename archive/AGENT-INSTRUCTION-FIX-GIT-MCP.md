# Agent Instruction — Final Fixes for 100% Completion (git-mcp-server)

**Project:** `git-mcp-server`
**Date:** 2026-02-19
**Source:** Independent re-audit — every code snippet verified against the live codebase
**Status:** 2 gaps remain. This document gives EXACT, COPY-PASTE-READY code. Follow it to the letter.

---

## CRITICAL RULES — READ BEFORE YOU TOUCH ANYTHING

These rules come from `RULES.md` and are **NON-NEGOTIABLE**:

1. **UK English throughout** — all source files, docstrings, comments, error messages, and docs.
2. **Library/server separation** — `src/git_tools/` MUST NOT import FastAPI, uvicorn, or MCP transport code. `src/git_mcp_server/` MUST NOT contain git logic beyond dispatch and auth.
3. **Config delegation** — `src/git_tools/` MUST NOT use `os.environ`, `hvac`, or bespoke secret loaders. All config from `cloud_dog_config`.
4. **`--env` enforcement** — every `pytest` invocation MUST pass `--env <TIER>`. Root `tests/conftest.py` enforces this.
5. **No mocking git in ST/IT/AT** — `RULES.md` section 6: "NEVER mock git operations in ST/IT/AT tests."
6. **Integration remote tests MUST use git network transport** — `RULES.md` section 6.
7. **Zero hardcoded credentials** — `RULES.md` section 1.
8. **Test hierarchy** — UT/ST/IT/AT/QT per PS-95 (`TESTS.md`).
9. **File headers** — every `.py` file MUST have the 4-line header block:
   ```
   # git-mcp-server — <short title>
   # Licence: Proprietary — Cloud-Dog AI Platform
   # Owner: Cloud-Dog AI
   # Description: <one-line description>.
   ```
10. **`pyproject.toml`** has `addopts = "-p no:cloud_dog_config"` and marker `integration`. Do NOT change these.
11. **`ruff` line-length=120** — all code must conform.

**If you violate ANY of these, the fix is REJECTED. No exceptions. No workarounds. No "I'll fix it later."**

---

## What is already verified and MUST NOT regress

| Check | Status |
|-------|--------|
| `ruff check src/ tests/` | PASS |
| `ruff format --check src/ tests/` | PASS |
| `mypy src/` | PASS |
| Config delegation (`grep -rn "os\.environ\|import hvac" src/git_tools/`) | Zero hits |
| Library/server separation | No FastAPI/MCP in `git_tools/` |
| Tool registry | 50 tools |
| UT 25/25 | PASS |
| ST 10/10 | PASS |
| AT 5/5 | PASS |
| QT 4/4 | PASS |
| Build wheel | `git_mcp_server-0.1.0` |

**Run the release gate (section 6) after EVERY file change. If any gate fails, fix IMMEDIATELY before proceeding.**

---

## Gap 1 — IT tests MUST exercise the real `git.cloud-dog.net` remote

### Problem (EXACT evidence)

`tests/env-IT` line 4 sets:
```
GIT_MCP_REMOTE_REPO=<operator-authorised-remote>
```

`defaults.yaml` has a `remote_cloud_dog` profile pointing to the same operator-authorised remote.

**But ZERO test files read `GIT_MCP_REMOTE_REPO`. ZERO tests use the `remote_cloud_dog` profile.**

Verified with:
```bash
grep -rn "GIT_MCP_REMOTE_REPO\|remote_cloud_dog" tests/ --include="*.py"
# Output: nothing
```

This violates `RULES.md` section 6: "Integration remote tests MUST use git network transport."

The existing IT1.4 and IT1.6 tests use a local `git daemon`. That is fine and MUST remain. But we MUST ALSO have tests that prove the server works against the real platform remote.

### Step 1a — Edit `tests/integration/conftest.py`

The current file (65 lines) imports `subprocess` but NOT `os`. The root `tests/conftest.py` has an `autouse=True` session fixture `load_env_files` that loads `tests/env-IT` into `os.environ` before any other session fixture runs. So `os.environ.get("GIT_MCP_REMOTE_REPO")` WILL find the value.

**EXACT EDIT 1 — add `import os` after the existing `import subprocess` (line 3):**

Current line 3:
```python
import subprocess
```

Change to:
```python
import os
import subprocess
```

**EXACT EDIT 2 — append the `remote_repo_url` fixture AFTER line 65 (end of file):**

Append these EXACT lines after the last line of the file:

```python


@pytest.fixture(scope="session")
def remote_repo_url() -> str:
    """Return the real remote repo URL from env-IT, or skip if unreachable."""
    url = os.environ.get("GIT_MCP_REMOTE_REPO", "")
    if not url:
        pytest.skip("GIT_MCP_REMOTE_REPO not set -- skipping remote tests")
    result = subprocess.run(
        ["git", "ls-remote", "--exit-code", url],
        capture_output=True,
        timeout=15,
    )
    if result.returncode != 0:
        pytest.skip(f"Remote {url} unreachable -- skipping remote tests")
    return url
```

**Why `--` not `—`:** The em-dash `—` can cause encoding issues in subprocess output. Use `--` in skip messages.

### Step 1b — Create `tests/integration/IT1.9_RemoteCloneAndFetch/test_remote_clone_and_fetch.py`

Create the directory `tests/integration/IT1.9_RemoteCloneAndFetch/`. No `__init__.py` needed.

**EXACT file content** — copy-paste verbatim:

```python
# git-mcp-server -- IT1.9 remote clone and fetch integration test
# Licence: Proprietary -- Cloud-Dog AI Platform
# Owner: Cloud-Dog AI
# Description: Clone from git.cloud-dog.net via the live HTTP API and exercise git_fetch.

from __future__ import annotations

import httpx
import pytest


@pytest.mark.integration
def test_remote_clone_and_fetch(
    integration_server: dict[str, str],
    api_key: str,
    remote_repo_url: str,
) -> None:
    """IT1.9 -- Clone from git.cloud-dog.net via repo_open, then git_fetch."""
    base = integration_server["base_url"]
    headers = {"x-api-key": api_key}

    # 1. Open workspace from real remote using the remote_cloud_dog profile
    open_resp = httpx.post(
        f"{base}/api/v1/tools/repo_open",
        headers=headers,
        json={
            "profile": "remote_cloud_dog",
            "repo_source": remote_repo_url,
            "session_id": "it-remote-clone",
        },
        timeout=120.0,
    )
    assert open_resp.status_code == 200, f"repo_open failed: {open_resp.text}"
    opened = open_resp.json()
    assert opened["ok"] is True, f"repo_open not ok: {opened}"
    workspace_id = opened["result"]["workspace_id"]

    # 2. Verify resolved ref is present and is a branch
    assert opened["result"]["resolved_ref"] is not None, "resolved_ref missing"
    assert opened["result"]["resolved_ref"]["type"] == "branch"

    # 3. Fetch from origin (should succeed even if nothing new)
    fetch_resp = httpx.post(
        f"{base}/api/v1/tools/git_fetch",
        headers=headers,
        json={"workspace_id": workspace_id, "remote": "origin"},
        timeout=60.0,
    )
    assert fetch_resp.status_code == 200, f"git_fetch failed: {fetch_resp.text}"
    assert fetch_resp.json()["ok"] is True, f"git_fetch not ok: {fetch_resp.json()}"

    # 4. Read a file to prove clone has real content
    read_resp = httpx.post(
        f"{base}/api/v1/tools/file_read",
        headers=headers,
        json={"workspace_id": workspace_id, "path": "README.md"},
        timeout=10.0,
    )
    assert read_resp.status_code == 200, f"file_read failed: {read_resp.text}"
    content = read_resp.json()["result"]["content"]
    assert len(content) > 0, "README.md should not be empty after clone"

    # 5. Close workspace
    close_resp = httpx.post(
        f"{base}/api/v1/tools/repo_close",
        headers=headers,
        json={"workspace_id": workspace_id},
        timeout=10.0,
    )
    assert close_resp.status_code == 200, f"repo_close failed: {close_resp.text}"
```

**Fixtures used (all exist already):**
- `integration_server` — from `tests/integration/conftest.py` line 38, returns `{"base_url": str, "mcp_url": str}`
- `api_key` — from `tests/integration/conftest.py` line 57, returns `str`
- `remote_repo_url` — the NEW fixture from Step 1a, returns `str` or skips

### Step 1c — Create `tests/integration/IT1.10_RemoteBranchPush/test_remote_branch_push.py`

Create the directory `tests/integration/IT1.10_RemoteBranchPush/`. No `__init__.py` needed.

**EXACT file content:**

```python
# git-mcp-server -- IT1.10 remote branch push integration test
# Licence: Proprietary -- Cloud-Dog AI Platform
# Owner: Cloud-Dog AI
# Description: Push a test branch to git.cloud-dog.net and clean up.

from __future__ import annotations

import os
import subprocess
import uuid

import httpx
import pytest


@pytest.mark.integration
def test_remote_branch_push(
    integration_server: dict[str, str],
    api_key: str,
    remote_repo_url: str,
) -> None:
    """IT1.10 -- Push a test branch to git.cloud-dog.net and delete it."""
    prefix = os.environ.get("GIT_MCP_REMOTE_BRANCH_PREFIX", "test/git-mcp-")
    branch_name = f"{prefix}{uuid.uuid4().hex[:8]}"
    base = integration_server["base_url"]
    headers = {"x-api-key": api_key}

    # 1. Open workspace from real remote
    open_resp = httpx.post(
        f"{base}/api/v1/tools/repo_open",
        headers=headers,
        json={
            "profile": "remote_cloud_dog",
            "repo_source": remote_repo_url,
            "session_id": "it-remote-push",
        },
        timeout=120.0,
    )
    assert open_resp.status_code == 200, f"repo_open failed: {open_resp.text}"
    assert open_resp.json()["ok"] is True, f"repo_open not ok: {open_resp.json()}"
    workspace_id = open_resp.json()["result"]["workspace_id"]
    workspace_path = open_resp.json()["result"]["path"]

    # 2. Create branch, write file, add, commit, push
    steps: list[tuple[str, dict]] = [
        ("git_branch_create", {"workspace_id": workspace_id, "name": branch_name}),
        ("git_checkout", {"workspace_id": workspace_id, "ref": branch_name}),
        (
            "file_write",
            {
                "workspace_id": workspace_id,
                "path": ".git-mcp-test",
                "content": f"integration test {branch_name}\n",
                "overwrite": True,
            },
        ),
        ("git_add", {"workspace_id": workspace_id, "paths": [".git-mcp-test"]}),
        ("git_commit", {"workspace_id": workspace_id, "message": f"IT push test {branch_name}"}),
        (
            "git_push",
            {
                "workspace_id": workspace_id,
                "remote": "origin",
                "branch": branch_name,
                "force_with_lease": False,
            },
        ),
    ]
    for tool, payload in steps:
        resp = httpx.post(
            f"{base}/api/v1/tools/{tool}",
            headers=headers,
            json=payload,
            timeout=60.0,
        )
        assert resp.status_code == 200, f"{tool} HTTP failed: {resp.text}"
        assert resp.json()["ok"] is True, f"{tool} not ok: {resp.json()}"

    # 3. Cleanup: delete the remote branch via raw git
    #    (independent of tool under test to avoid masking failures)
    subprocess.run(
        ["git", "push", "origin", "--delete", branch_name],
        cwd=workspace_path,
        capture_output=True,
        timeout=30,
    )

    # 4. Close workspace
    httpx.post(
        f"{base}/api/v1/tools/repo_close",
        headers=headers,
        json={"workspace_id": workspace_id},
        timeout=10.0,
    )
```

**Why `os` and `subprocess` are imported here:** `os.environ.get("GIT_MCP_REMOTE_BRANCH_PREFIX")` reads the prefix from `tests/env-IT` line 5. `subprocess` is used for cleanup (deleting the remote branch). These imports are in the TEST file, NOT in `src/git_tools/`, so they do NOT violate config delegation.

### Step 1d — Update `TESTS.md`

Make these EXACT changes to `TESTS.md`:

**Change 1 — line 6:** Replace:
```
**Total tests:** 25 UT + 10 ST + 8 IT + 5 AT + 4 QT = 52
```
with:
```
**Total tests:** 25 UT + 10 ST + 10 IT + 5 AT + 4 QT = 54
```

**Change 2 — line 23:** Replace:
```
- Git network remote (integration tests use `git daemon` transport over localhost)
```
with:
```
- Git network remote (IT1.1--IT1.8 use `git daemon` over localhost; IT1.9--IT1.10 use `git.cloud-dog.net`)
```

**Change 3 — line 81:** Replace:
```
## Integration Tests (IT) — 8 tests
```
with:
```
## Integration Tests (IT) — 10 tests
```

**Change 4 — after the IT1.8 row (line 94), add these two rows:**
```
| IT1.9 | RemoteCloneAndFetch | Clone from `git.cloud-dog.net` via repo_open, git_fetch, file_read, repo_close. Skips if remote unreachable. | FastAPI + git remote |
| IT1.10 | RemoteBranchPush | Push a `test/git-mcp-*` branch to `git.cloud-dog.net`, then delete it. Skips if remote unreachable. | FastAPI + git remote |
```

### Step 1e — Verification commands (run ALL, check ALL expected outputs)

```bash
cd /opt/iac/Development/cloud-dog-ai/git-mcp-server

# 1. Fixture exists
grep -c "def remote_repo_url" tests/integration/conftest.py
# EXPECTED: 1

# 2. IT1.9 file exists
test -f tests/integration/IT1.9_RemoteCloneAndFetch/test_remote_clone_and_fetch.py && echo "OK" || echo "MISSING"
# EXPECTED: OK

# 3. IT1.10 file exists
test -f tests/integration/IT1.10_RemoteBranchPush/test_remote_branch_push.py && echo "OK" || echo "MISSING"
# EXPECTED: OK

# 4. TESTS.md total updated
grep "Total tests:" TESTS.md
# EXPECTED: **Total tests:** 25 UT + 10 ST + 10 IT + 5 AT + 4 QT = 54

# 5. File headers present
head -4 tests/integration/IT1.9_RemoteCloneAndFetch/test_remote_clone_and_fetch.py | grep -c "git-mcp-server"
# EXPECTED: 1

head -4 tests/integration/IT1.10_RemoteBranchPush/test_remote_branch_push.py | grep -c "git-mcp-server"
# EXPECTED: 1

# 6. Lint
ruff check tests/integration/IT1.9_RemoteCloneAndFetch/ tests/integration/IT1.10_RemoteBranchPush/
# EXPECTED: All checks passed!

ruff format --check tests/integration/IT1.9_RemoteCloneAndFetch/ tests/integration/IT1.10_RemoteBranchPush/
# EXPECTED: 2 files already formatted.

# 7. Skip behaviour when remote unreachable
GIT_MCP_REMOTE_REPO= python3 -m pytest tests/integration/IT1.9_RemoteCloneAndFetch/ tests/integration/IT1.10_RemoteBranchPush/ --env IT -v 2>&1 | grep -c "SKIPPED"
# EXPECTED: 2
```

**If ANY verification command gives wrong output, you have a bug. Fix it before proceeding.**

---

## Gap 2 — AT tests MUST exercise deeper end-to-end workflows

### Problem (EXACT evidence)

**AT1.3** (`tests/application/AT1.3_FullWorkflow_ConflictResolve/test_fullworkflow_conflict_resolve.py`) is 17 lines. It writes FAKE conflict markers (`<<<<<<< ours`) directly into a file, then calls `resolve_conflicts()`. It does NOT create a real merge conflict via two branches. This violates `RULES.md` section 6: "NEVER mock git operations in ST/IT/AT tests." Writing fake conflict markers IS mocking — a real conflict comes from `git merge`.

**AT1.5** (`tests/application/AT1.5_FullWorkflow_RecoveryRestore/test_fullworkflow_recovery_restore.py`) is 20 lines. It only creates a patch bundle and checks it exists. It does NOT test stash save/pop or recovery branch creation. The `TESTS.md` description says "simulate crash, list recovery, restore" — none of that happens.

Both tests call library functions directly instead of going through `ToolRegistry`, which is the actual runtime entry point. AT tests are "end-to-end user workflows" per `TESTS.md`.

### CRITICAL: `git_merge` raises an exception on conflict

**I verified this by running the actual code.** When `ToolRegistry.call("git_merge", ...)` encounters a conflict, it raises `git.exc.GitCommandError`. It does NOT return a dict. Your test MUST catch this exception with `pytest.raises()`.

**Verified return shapes (from live execution):**

| Tool | Returns | Shape |
|------|---------|-------|
| `repo_open` | dict | `{"workspace_id": str, "path": str, "mode": str, "resolved_ref": {...}}` |
| `git_status` | dict | `{"entries": [...]}` — list of dicts, empty if clean |
| `git_branch_create` | dict | `{"branch": str, "from_ref": str}` |
| `git_checkout` | dict | `{"checked_out": str}` |
| `file_write` | dict | `{"path": str}` |
| `git_add` | dict | `{"staged": [str]}` |
| `git_commit` | dict | `{"commit": str}` — hex SHA |
| `file_read` | dict | `{"content": str}` |
| `git_log` | dict | `{"log": str}` — oneline format |
| `git_branch_list` | dict | `{"branches": [str]}` |
| `git_stash_save` | dict | `{"result": str}` |
| `git_stash_pop` | dict | `{"result": str}` |
| `git_merge` | **RAISES `GitCommandError` on conflict** | On success: `{"result": str}` |
| `git_conflicts_list` | dict | `{"conflicts": [str]}` — list of file paths |
| `git_conflict_resolve_manual` | dict | `{"resolved": [str], "mode": str}` |
| `repo_close` | dict | `{"workspace_id": str, "closed": True}` |

### Step 2a — Replace `tests/application/AT1.3_FullWorkflow_ConflictResolve/test_fullworkflow_conflict_resolve.py`

Delete the entire current content and replace with this EXACT file:

```python
# git-mcp-server -- AT1.3 full workflow conflict resolve
# Licence: Proprietary -- Cloud-Dog AI Platform
# Owner: Cloud-Dog AI
# Description: Real merge conflict via two branches, resolve via ToolRegistry, verify log.

from __future__ import annotations

from pathlib import Path

import pytest
from git.exc import GitCommandError

from git_tools.tools.registry import ToolRegistry
from git_tools.workspaces.manager import WorkspaceManager
from tests.helpers import create_repo_with_remote


def test_fullworkflow_conflict_resolve(tmp_path: Path) -> None:
    """AT1.3 -- Real merge conflict: two branches edit same line, resolve, commit."""
    local, _ = create_repo_with_remote(tmp_path / "local", tmp_path / "remote.git")
    manager = WorkspaceManager(tmp_path / "work")
    tools = ToolRegistry(manager)
    main_branch = local.active_branch.name

    # Open workspace
    opened = tools.call("repo_open", {
        "profile": "conflict-test",
        "repo_source": local.working_tree_dir,
        "session_id": "at-conflict",
        "ref": {"type": "branch", "name": main_branch},
    })
    wid = opened["workspace_id"]

    # Create feature branch and commit a change to README.md
    tools.call("git_branch_create", {"workspace_id": wid, "name": "feature/conflict"})
    tools.call("git_checkout", {"workspace_id": wid, "ref": "feature/conflict"})
    tools.call("file_write", {
        "workspace_id": wid, "path": "README.md",
        "content": "feature line\n", "overwrite": True,
    })
    tools.call("git_add", {"workspace_id": wid, "paths": ["README.md"]})
    tools.call("git_commit", {"workspace_id": wid, "message": "feature edit"})

    # Switch back to main and make a CONFLICTING change to the same file
    tools.call("git_checkout", {"workspace_id": wid, "ref": main_branch})
    tools.call("file_write", {
        "workspace_id": wid, "path": "README.md",
        "content": "main line\n", "overwrite": True,
    })
    tools.call("git_add", {"workspace_id": wid, "paths": ["README.md"]})
    tools.call("git_commit", {"workspace_id": wid, "message": "main edit"})

    # Attempt merge -- MUST raise GitCommandError because of conflict
    with pytest.raises(GitCommandError):
        tools.call("git_merge", {"workspace_id": wid, "ref": "feature/conflict", "ff_only": False})

    # List conflicts -- README.md must be in the list
    conflicts = tools.call("git_conflicts_list", {"workspace_id": wid})
    assert "README.md" in conflicts["conflicts"], f"Expected README.md in {conflicts['conflicts']}"

    # Resolve manually via tool
    resolve_result = tools.call("git_conflict_resolve_manual", {
        "workspace_id": wid,
        "path": "README.md",
        "content": "resolved line\n",
    })
    assert "README.md" in resolve_result["resolved"]

    # Verify resolution via file_read
    read_result = tools.call("file_read", {"workspace_id": wid, "path": "README.md"})
    assert read_result["content"] == "resolved line\n"

    # Stage and commit the resolution
    tools.call("git_add", {"workspace_id": wid, "paths": ["README.md"]})
    commit_result = tools.call("git_commit", {"workspace_id": wid, "message": "resolve conflict"})
    assert len(commit_result["commit"]) == 40, "Expected 40-char SHA"

    # Verify log contains the resolution commit
    log_result = tools.call("git_log", {"workspace_id": wid, "max_count": 10})
    assert "resolve conflict" in log_result["log"], f"Expected 'resolve conflict' in log: {log_result['log']}"
```

**Key difference from the old version:** `pytest.raises(GitCommandError)` wraps the `git_merge` call. Without this, the test CRASHES instead of asserting. I verified this by running the actual merge on the live codebase — it raises `git.exc.GitCommandError` with exit code 1 and stdout containing "CONFLICT (content): Merge conflict in README.md".

### Step 2b — Replace `tests/application/AT1.5_FullWorkflow_RecoveryRestore/test_fullworkflow_recovery_restore.py`

Delete the entire current content and replace with this EXACT file:

```python
# git-mcp-server -- AT1.5 full workflow recovery restore
# Licence: Proprietary -- Cloud-Dog AI Platform
# Owner: Cloud-Dog AI
# Description: Full recovery cycle: stash save/pop, patch bundle, recovery branch.

from __future__ import annotations

from pathlib import Path

from git import Repo

from git_tools.git.recovery import RecoveryManager
from git_tools.tools.registry import ToolRegistry
from git_tools.workspaces.manager import WorkspaceManager
from tests.helpers import create_repo_with_remote


def test_fullworkflow_recovery_restore(tmp_path: Path) -> None:
    """AT1.5 -- Full recovery: stash, patch bundle, recovery branch."""
    local, _ = create_repo_with_remote(tmp_path / "local", tmp_path / "remote.git")
    manager = WorkspaceManager(tmp_path / "work")
    tools = ToolRegistry(manager)
    main_branch = local.active_branch.name

    # Open workspace
    opened = tools.call("repo_open", {
        "profile": "recovery-test",
        "repo_source": local.working_tree_dir,
        "session_id": "at-recovery",
        "ref": {"type": "branch", "name": main_branch},
    })
    wid = opened["workspace_id"]
    ws_path = opened["path"]

    # --- Phase 1: Stash save/pop ---

    # Make a dirty change via the tool (do NOT commit)
    tools.call("file_write", {
        "workspace_id": wid, "path": "dirty.txt",
        "content": "unsaved work\n", "overwrite": True,
    })

    # Stash it
    stash_result = tools.call("git_stash_save", {"workspace_id": wid, "message": "recovery-stash"})
    assert "recovery-stash" in stash_result["result"], f"Stash message missing: {stash_result}"

    # Verify the file is gone from working tree after stash
    dirty_file = Path(ws_path) / "dirty.txt"
    assert not dirty_file.exists(), "dirty.txt should be removed after stash"

    # Pop the stash
    tools.call("git_stash_pop", {"workspace_id": wid})

    # Verify the file is back with correct content
    read_back = tools.call("file_read", {"workspace_id": wid, "path": "dirty.txt"})
    assert read_back["content"] == "unsaved work\n", f"Wrong content after pop: {read_back['content']}"

    # --- Phase 2: Patch bundle ---

    recovery_mgr = RecoveryManager(ws_path)
    patch = recovery_mgr.create_patch_bundle(tmp_path / "patches", "at-session")
    assert patch.exists(), f"Patch file not created at {patch}"
    patch_content = patch.read_text(encoding="utf-8")
    assert "dirty.txt" in patch_content, "Patch should reference dirty.txt"
    assert "unsaved work" in patch_content, "Patch should contain file content"

    # --- Phase 3: Recovery branch ---

    # Stage and commit so we can create a recovery branch from a clean state
    tools.call("git_add", {"workspace_id": wid, "paths": ["dirty.txt"]})
    tools.call("git_commit", {"workspace_id": wid, "message": "pre-recovery commit"})

    branch = recovery_mgr.create_recovery_branch("at-crash")
    assert branch.startswith("recovery/at-crash-"), f"Unexpected branch name: {branch}"

    # Verify the recovery branch is now the active branch
    ws_repo = Repo(ws_path)
    assert ws_repo.active_branch.name == branch, f"Active branch should be {branch}, got {ws_repo.active_branch.name}"

    # Verify the commit is on the recovery branch
    log_result = tools.call("git_log", {"workspace_id": wid, "max_count": 5})
    assert "pre-recovery commit" in log_result["log"], f"Recovery branch missing commit: {log_result['log']}"
```

**Key differences from the old version:**
1. Uses `create_repo_with_remote` (the helper that exists in `tests/helpers.py` line 24) instead of `create_repo` — consistent with AT1.1.
2. Uses `ToolRegistry.call()` for all tool operations — AT tests are "end-to-end user workflows".
3. Tests ALL three recovery modes: stash save/pop, patch bundle with content check, recovery branch.
4. Verifies stash actually removes the file and pop restores it (not just checking status entries which can be tricky).
5. Verifies recovery branch is active and has the expected commit.

### Step 2c — Update `TESTS.md` AT descriptions

**Change the AT1.3 row (line 106).** Replace:
```
| AT1.3 | FullWorkflow_ConflictResolve | Create conflict → merge → list conflicts → resolve → verify clean |
```
with:
```
| AT1.3 | FullWorkflow_ConflictResolve | Real merge conflict via two branches editing same file, `pytest.raises(GitCommandError)`, resolve via `git_conflict_resolve_manual`, verify `git_log` |
```

**Change the AT1.5 row (line 108).** Replace:
```
| AT1.5 | FullWorkflow_RecoveryRestore | Open repo → make changes → simulate crash → list recovery → restore |
```
with:
```
| AT1.5 | FullWorkflow_RecoveryRestore | Stash save/pop with file verification, patch bundle with content check, recovery branch creation and activation |
```

### Step 2d — Verification commands

```bash
cd /opt/iac/Development/cloud-dog-ai/git-mcp-server

# 1. AT1.3 file line count (should be ~80 lines, not 17)
wc -l tests/application/AT1.3_FullWorkflow_ConflictResolve/test_fullworkflow_conflict_resolve.py
# EXPECTED: ~80 (was 17)

# 2. AT1.5 file line count (should be ~80 lines, not 20)
wc -l tests/application/AT1.5_FullWorkflow_RecoveryRestore/test_fullworkflow_recovery_restore.py
# EXPECTED: ~80 (was 20)

# 3. AT1.3 uses pytest.raises (CRITICAL -- without this the test CRASHES)
grep -c "pytest.raises" tests/application/AT1.3_FullWorkflow_ConflictResolve/test_fullworkflow_conflict_resolve.py
# EXPECTED: 1

# 4. AT1.3 uses ToolRegistry (not direct library calls)
grep -c "tools.call" tests/application/AT1.3_FullWorkflow_ConflictResolve/test_fullworkflow_conflict_resolve.py
# EXPECTED: >= 10

# 5. AT1.5 uses ToolRegistry
grep -c "tools.call" tests/application/AT1.5_FullWorkflow_RecoveryRestore/test_fullworkflow_recovery_restore.py
# EXPECTED: >= 7

# 6. File headers present
head -4 tests/application/AT1.3_FullWorkflow_ConflictResolve/test_fullworkflow_conflict_resolve.py | grep -c "git-mcp-server"
# EXPECTED: 1

head -4 tests/application/AT1.5_FullWorkflow_RecoveryRestore/test_fullworkflow_recovery_restore.py | grep -c "git-mcp-server"
# EXPECTED: 1

# 7. Lint
ruff check tests/application/AT1.3_FullWorkflow_ConflictResolve/ tests/application/AT1.5_FullWorkflow_RecoveryRestore/
# EXPECTED: All checks passed!

ruff format --check tests/application/AT1.3_FullWorkflow_ConflictResolve/ tests/application/AT1.5_FullWorkflow_RecoveryRestore/
# EXPECTED: 2 files already formatted.

# 8. RUN the tests (MUST PASS)
python3 -m pytest tests/application/ --env AT -v --tb=short
# EXPECTED: 5 passed
```

**If the AT tests fail, the MOST LIKELY cause is:**
- Missing `pytest.raises(GitCommandError)` around `git_merge` (test crashes with unhandled exception)
- Missing `from git.exc import GitCommandError` import
- Wrong return shape assumption (check the table above)

---

## Execution Order (MANDATORY — do NOT skip steps, do NOT reorder)

| Step | Action | Verify |
|------|--------|--------|
| 1 | Edit `tests/integration/conftest.py` — add `import os` and `remote_repo_url` fixture | `grep -c "def remote_repo_url" tests/integration/conftest.py` outputs `1` |
| 2 | Create `tests/integration/IT1.9_RemoteCloneAndFetch/test_remote_clone_and_fetch.py` | File exists, has 4-line header, `ruff check` passes |
| 3 | Create `tests/integration/IT1.10_RemoteBranchPush/test_remote_branch_push.py` | File exists, has 4-line header, `ruff check` passes |
| 4 | **Run release gate (section 6)** | ALL gates pass. Existing UT/ST/AT/QT still pass. |
| 5 | Replace `tests/application/AT1.3_.../test_fullworkflow_conflict_resolve.py` | `grep -c "pytest.raises" ...` outputs `1` |
| 6 | Replace `tests/application/AT1.5_.../test_fullworkflow_recovery_restore.py` | `grep -c "tools.call" ...` outputs `>= 7` |
| 7 | **Run AT tests** | `python3 -m pytest tests/application/ --env AT -v` — 5 passed |
| 8 | Update `TESTS.md` — total, IT count, IT1.9/IT1.10 rows, AT1.3/AT1.5 descriptions | `grep "Total tests:" TESTS.md` matches `54` |
| 9 | **Run FULL release gate (section 6)** | ALL gates pass |

---

## Release Gate (run from project root after EVERY change)

```bash
cd /opt/iac/Development/cloud-dog-ai/git-mcp-server

# --- Quality ---
ruff check src/ tests/
ruff format --check src/ tests/
mypy src/

# --- Config delegation ---
grep -rn "os\.environ\|import hvac\|overlay_secrets" src/git_tools/ --include="*.py" | grep -v __pycache__
# Expected: NO OUTPUT

# --- Tests (offline tiers) ---
python3 -m pytest tests/unit/ --env UT -v
# Expected: 25 passed

python3 -m pytest tests/system/ --env ST -v
# Expected: 10 passed

python3 -m pytest tests/application/ --env AT -v
# Expected: 5 passed

python3 -m pytest tests/security/ --env QT -v
# Expected: 4 passed

# --- Build ---
python3 -m build --no-isolation
# Expected: Successfully built ... .whl

# --- Tool count ---
python3 -c "
import sys; sys.path.insert(0, 'src')
from git_tools.tools.registry import ToolRegistry
from git_tools.workspaces.manager import WorkspaceManager
import tempfile, pathlib
wm = WorkspaceManager(pathlib.Path(tempfile.mkdtemp()))
r = ToolRegistry(wm)
n = len(r.list_tools())
assert n >= 50, f'Only {n} tools registered'
print(f'OK: {n} tools registered')
"
# Expected: OK: 50 tools registered
```

---

## Done Criteria (100% — ALL must be true)

- [ ] `tests/integration/conftest.py` has `import os` and `remote_repo_url` fixture
- [ ] `tests/integration/IT1.9_RemoteCloneAndFetch/test_remote_clone_and_fetch.py` exists with 4-line header
- [ ] `tests/integration/IT1.10_RemoteBranchPush/test_remote_branch_push.py` exists with 4-line header
- [ ] IT1.9 uses `integration_server`, `api_key`, `remote_repo_url` fixtures and the `remote_cloud_dog` profile
- [ ] IT1.10 uses `GIT_MCP_REMOTE_BRANCH_PREFIX` from env and cleans up the branch after push
- [ ] Both IT1.9 and IT1.10 SKIP (not FAIL) when `GIT_MCP_REMOTE_REPO` is unset or unreachable
- [ ] AT1.3 creates a REAL merge conflict (two branches, same file), uses `pytest.raises(GitCommandError)`, resolves via `git_conflict_resolve_manual`, verifies `git_log`
- [ ] AT1.5 tests stash save/pop (verifies file removed then restored), patch bundle (verifies content), recovery branch (verifies active)
- [ ] Both AT1.3 and AT1.5 use `ToolRegistry.call()` for all tool operations
- [ ] `TESTS.md` updated: total=54, IT count=10, IT1.9+IT1.10 rows, AT1.3+AT1.5 descriptions
- [ ] `ruff check src/ tests/` — All checks passed
- [ ] `ruff format --check src/ tests/` — All formatted
- [ ] `mypy src/` — No issues
- [ ] UT 25 passed, ST 10 passed, AT 5 passed, QT 4 passed
- [ ] `python3 -m build --no-isolation` — wheel produced
- [ ] Tool count >= 50
- [ ] Config delegation grep — zero hits in `src/git_tools/`

**If ANY checkbox is unchecked, the fix is INCOMPLETE. Do NOT claim completion.**
