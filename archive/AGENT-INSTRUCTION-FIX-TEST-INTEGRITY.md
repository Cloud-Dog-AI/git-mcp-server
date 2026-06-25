# Agent Instruction — Verify git-mcp-server Test Integrity (Compliance Gate)

**Package:** `git-mcp-server`
**Date:** 2026-02-20 (updated after 15:53 UTC audit)
**Status:** OPEN — **CRITICAL** severity — agent fraud detected
**Audit Reference:** `cloud-dog-ai-platform-standards/AGENT-DISPATCH-TABLE.md` § FRAUD FINDINGS

---

## ⛔ FRAUD FINDING (2026-02-20 15:53 UTC)

**Previous agent claimed IT tests pass. They do NOT test real external systems.**

`tests/env-IT` sets `GIT_MCP_REMOTE_REPO=git://127.0.0.1:19418/sample-repo.git`.
The conftest (`tests/integration/conftest.py`) does the following:

1. Creates a throwaway bare repo on disk (`.tmp-tests/it/local-remote/`)
2. Starts a **local `git daemon`** on localhost:19418
3. Seeds it with a dummy README.md
4. All "remote" tests (IT1.9, IT1.10) clone/push to **THIS LOCAL DAEMON**

**No real GitLab, no real network, no real authentication, no real SSH keys.**
Per RULES.md § 5: IT tests MUST use real external systems. These are system tests misclassified as IT.

### MANDATORY FIX

1. **`tests/env-IT` must set `GIT_MCP_REMOTE_REPO` to a real GitLab URL** (e.g. `https://gitlab.cloud-dog.net/cloud-dog-ai/sample-repo.git` or similar real remote)
2. **IT1.9 and IT1.10 must clone/push to the REAL remote** — not a local daemon
3. **The `local_remote_git_daemon` fixture must be REMOVED or moved to ST** — it is a system test fixture, not integration
4. **If real GitLab is not available**, the tests must `pytest.fail()` with a clear message — NOT silently pass against a fake

---

## INTEGRITY WARRANTY — READ THIS FIRST

This section is copied verbatim from the platform-wide `RULES.md` Section 1. It is **NON-NEGOTIABLE**.

**I WILL NEVER:**
- **LIE** about test results, implementation status, or compliance
- **FUDGE** test data, configuration, or validation results
- **HACK** around problems instead of fixing root causes
- **FALSIFY** test outputs, logs, or status reports
- **STUB** functionality in IT/AT tests when real implementation is required
- **FAKE** success when there are errors, warnings, or failures
- **HIDE** failures, warnings, or non-compliance
- **PRETEND** tests pass when they fail
- **SKIP** validation steps to claim completion
- **BYPASS** rules or requirements for convenience

**IF I CANNOT GUARANTEE 100% COMPLIANCE, I WILL STOP AND SAY SO EXPLICITLY.**

**"ASK. DON'T GUESS. DON'T LIE. DON'T FUDGE."**

---

## MANDATORY READING BEFORE ANY WORK

1. `cloud-dog-ai-platform-standards/RULES.md` — Sections 1, 5 (especially § 5.3 items 9–13, § 5.5)
2. `cloud-dog-ai-platform-standards/migration/AGENT-BEHAVIOUR-RULES.md` — RULES 12 and 13
3. This instruction document — in full, before writing any code

---

## OVERALL ASSESSMENT

git-mcp-server is the **reference implementation** for test infrastructure. The audit rated it **STRUCTURALLY SOUND**:

- IT tests start a real server via `server_control.sh` and make real HTTP requests via `httpx`
- AT tests do the same with AT config
- `pytest.skip()` used ONLY for optional remote repo tests — and even then, env-IT provides the URL
- conftest loads env files properly and resolves tier names
- Server teardown in fixture cleanup

**This instruction is a compliance hardening pass, not a critical fix.** The goal is to bring git-mcp-server into full compliance with the new RULES.md v1.2 (§ 5.3 items 9–13) and serve as the verified reference for other projects.

---

## AUDIT FINDINGS

| ID | Severity | Finding |
|----|----------|---------|
| **GM-1** | LOW | `pytest.skip()` used for `remote_repo_url` fixture when `GIT_MCP_REMOTE_REPO` is not set or remote is unreachable. Since env-IT provides this URL, the skip only fires if the remote is genuinely down. **Acceptable** — but should be `pytest.fail()` if `TEST_ENV_TIER=IT` and the env file provides the URL. |
| **GM-2** | LOW | No `TEST_ENV_TIER` in env files. Adding this enables tier-aware fixture behaviour consistent with RULES.md v1.2. |
| **GM-3** | LOW | No write-path probe before IT tests. The server `/health` endpoint is checked but no git write operation is probed. Minor — git operations are inherently write-tested by the tests themselves. |
| **GM-4** | INFO | All tests are correctly classified. No misclassification found. |

---

## HARD CONSTRAINTS

- **DO NOT** break existing tests.
- **DO NOT** weaken any assertion.
- **DO NOT** add credentials to env files.
- **UK English only.**

---

## PHASE 1 — Add TEST_ENV_TIER to env files (GM-2)

### Step 1.1 — Add to each env file

| File | Add (first line after comment) |
|------|------|
| `tests/env-UT` | `TEST_ENV_TIER=UT` |
| `tests/env-ST` | `TEST_ENV_TIER=ST` |
| `tests/env-IT` | `TEST_ENV_TIER=IT` |
| `tests/env-AT` | `TEST_ENV_TIER=AT` |
| `tests/env-QT` | `TEST_ENV_TIER=QT` |

---

## PHASE 2 — Harden remote_repo_url fixture (GM-1)

### Step 2.1 — Update `tests/integration/conftest.py` `remote_repo_url` fixture

The fixture at line 72-82 currently uses `pytest.skip()`. Change to tier-aware:

```python
@pytest.fixture(scope="session")
def remote_repo_url() -> str:
    """Return the real remote repo URL from env-IT, or fail/skip based on tier."""
    url = os.environ.get("GIT_MCP_REMOTE_REPO", "")
    tier = os.environ.get("TEST_ENV_TIER", "")
    if not url:
        if tier in ("IT", "AT"):
            pytest.fail(
                "GIT_MCP_REMOTE_REPO is required for IT/AT tests. "
                "Check tests/env-IT contains this variable."
            )
        pytest.skip("GIT_MCP_REMOTE_REPO not set -- skipping remote tests")
    result = subprocess.run(
        ["git", "ls-remote", "--exit-code", url],
        capture_output=True,
        timeout=15,
    )
    if result.returncode != 0:
        if tier in ("IT", "AT"):
            pytest.fail(
                f"Remote {url} unreachable for {tier} tier. "
                f"Verify network access to git.cloud-dog.net."
            )
        pytest.skip(f"Remote {url} unreachable -- skipping remote tests")
    return url
```

This means:
- **IT/AT tier:** remote must be configured AND reachable — `pytest.fail()` if not
- **UT/ST/QT tier:** remote is optional — `pytest.skip()` if not configured

---

## PHASE 3 — Verify all test classifications (GM-4)

### Step 3.1 — Verify each test directory matches its actual behaviour

Run this checklist for every test file:

**UT tests:** Verify each test operates on in-memory objects or local temp dirs only. No HTTP calls, no server_control.sh, no external services.

**ST tests:** Verify each test exercises system-level functionality. May use local git repos but should not require external network access.

**IT tests:** Verify each test uses `integration_server` fixture (starts real server) and makes real HTTP requests via `httpx`.

**AT tests:** Verify each test uses `application_server` fixture (starts real server) and exercises end-to-end business scenarios.

**QT tests:** Verify each test exercises security/quality concerns against real behaviour.

### Step 3.2 — Document findings

For each test, record in a table:

```
| Test | Claimed Type | Verified Type | Uses Real Server | Makes HTTP Calls | Status |
```

If any test is misclassified, move it to the correct directory and write a real replacement.

---

## PHASE 4 — Verify env file consumption

### Step 4.1 — Trace every variable in every env file to its consumer

| Env File | Variable | Consumer | Verified |
|----------|----------|----------|----------|
| env-IT | `GIT_MCP_TEST_ROOT` | IT conftest / test code | ? |
| env-IT | `GIT_MCP_AUDIT_PATH` | IT conftest / test code | ? |
| env-IT | `GIT_MCP_REMOTE_REPO` | `remote_repo_url` fixture | ✓ |
| env-IT | `GIT_MCP_SEED_KEY_FILE` | `api_key` fixture | ✓ |
| env-IT | `CLOUD_DOG__SERVER__HOST` | `integration_server` fixture | ✓ |
| env-IT | `CLOUD_DOG__SERVER__PORT` | `integration_server` fixture | ✓ |
| env-IT | `CLOUD_DOG__SERVER__MCP__PORT` | `integration_server` fixture | ✓ |
| ... | ... | ... | ... |

**Any variable with no verified consumer must be removed or its consumer must be documented.**

---

## PHASE 5 — Verification

### Step 5.1 — Run all tiers

```bash
cd /opt/iac/Development/cloud-dog-ai/git-mcp-server

# UT
.venv/bin/pytest tests/unit --env tests/env-UT -v 2>&1 | tail -5

# ST
.venv/bin/pytest tests/system --env tests/env-ST -v 2>&1 | tail -5

# IT (requires real server and git.cloud-dog.net access)
.venv/bin/pytest tests/integration --env tests/env-IT -v 2>&1 | tail -5

# AT
.venv/bin/pytest tests/application --env tests/env-AT -v 2>&1 | tail -5

# QT
.venv/bin/pytest tests/security --env tests/env-QT -v 2>&1 | tail -5
```

### Step 5.2 — Verify IT without remote access produces FAIL not SKIP

Temporarily unset `GIT_MCP_REMOTE_REPO` and run the remote tests to confirm they produce `pytest.fail()`:

```bash
GIT_MCP_REMOTE_REPO="" TEST_ENV_TIER=IT .venv/bin/pytest tests/integration/IT1.9_RemoteCloneAndFetch -v 2>&1 | tail -5
```

**Expected:** `FAILED` (not SKIPPED).

### Step 5.3 — Report honestly

State exact counts per tier: `N passed, N failed, N skipped`.

---

## COMPLETION GATE

This instruction is complete ONLY when:

1. `TEST_ENV_TIER` present in all 5 env files
2. `remote_repo_url` fixture uses `pytest.fail()` for IT/AT tier
3. All test classifications verified — no misclassifications
4. All env file variables traced to consumers — no decoration
5. All tiers run with honest counts reported
6. IT remote tests fail (not skip) when `GIT_MCP_REMOTE_REPO` is unset in IT tier

**DO NOT claim completion without evidence for ALL 6 gates.**
