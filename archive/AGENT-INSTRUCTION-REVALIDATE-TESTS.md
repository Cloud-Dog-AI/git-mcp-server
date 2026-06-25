# Agent Instruction — Revalidate git-mcp-server Tests

**Package:** `git-mcp-server`
**Date:** 2026-02-20
**Status:** OPEN — **CRITICAL** — IT all 10 failing, server won't start
**Audit Reference:** `cloud-dog-ai-platform-standards/AGENT-DISPATCH-TABLE.md`

---

## INTEGRITY WARRANTY — READ THIS FIRST

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

## CURRENT STATE (2026-02-20 17:16 UTC audit)

| Tier | Pass | Fail | Command |
|------|------|------|---------|
| UT | 25 | 0 | `.venv/bin/pytest tests/unit/ --env tests/env-UT --tb=no -q` |
| ST | 10 | 0 | `.venv/bin/pytest tests/system/ --env tests/env-ST --tb=no -q` |
| IT | 0 | 10 | `.venv/bin/pytest tests/integration/ --env tests/env-IT --tb=no -q` |

**IT failure:** ALL 10 IT tests fail with `httpx.ConnectError: [Errno 111] Connection refused`. The `integration_server` fixture in `tests/integration/conftest.py` calls `server_control.sh --env tests/env-IT start all` but the server does not start.

### KNOWN FRAUD FROM PRIOR AUDIT

`tests/env-IT` sets `GIT_MCP_REMOTE_REPO=git://127.0.0.1:19418/sample-repo.git`. The conftest starts a **local `git daemon`** on localhost — NOT a real GitLab server. IT1.9 "RemoteCloneAndFetch" and IT1.10 "RemoteBranchPush" test against this local daemon. Per RULES.md, IT tests MUST use real external systems. This is a system test masquerading as IT.

---

## INSTRUCTIONS

### Pre-flight

```bash
set -a; source /opt/iac/Development/cloud-dog-ai/env-vault; set +a
cd /opt/iac/Development/cloud-dog-ai/git-mcp-server
```

### Step 1 — Confirm UT + ST baseline

```bash
.venv/bin/pytest tests/unit/ --env tests/env-UT --tb=no -q
.venv/bin/pytest tests/system/ --env tests/env-ST --tb=no -q
```

**Expected: UT 25P, ST 10P. STOP if either regressed.**

### Step 2 — Fix IT server startup

The IT tests depend on `integration_server` fixture which runs:
```
./server_control.sh --env tests/env-IT start all
```

Debug why the server won't start:

1. Run `server_control.sh` manually and capture output:
   ```bash
   ./server_control.sh --env tests/env-IT start all 2>&1
   ```
2. Check the server logs for startup errors
3. Verify the ports in `tests/env-IT` (18585, 18586) are not in use
4. Verify all Python dependencies are installed in `.venv`
5. Fix whatever is preventing startup

**Do NOT work around the startup failure.** Fix the root cause.

### Step 3 — Verify IT tests against running server

Once the server starts:

```bash
.venv/bin/pytest tests/integration/ --env tests/env-IT -v --tb=short
```

IT1.1 through IT1.8 should pass if the server is running correctly.

### Step 4 — Address remote test fraud (IT1.9, IT1.10)

The `local_remote_git_daemon` fixture in `tests/integration/conftest.py` starts a local git daemon. This is valid for **ST** but NOT for **IT**.

**Options (choose one, document which you chose and why):**

**Option A — Real remote:** Update `tests/env-IT` to point `GIT_MCP_REMOTE_REPO` to a real GitLab/Gitea server. If no real server is available, document this and move to Option B.

**Option B — Reclassify:** Move IT1.9 and IT1.10 to `tests/system/` since they only test against a local daemon. Update the `remote_repo_url` fixture to live in `tests/system/conftest.py`. The IT directory then only contains tests that use the real running server (IT1.1–IT1.8).

**Option C — Fail honestly:** If a real remote is required but not available, make IT1.9/IT1.10 call `pytest.fail("GIT_MCP_REMOTE_REPO must point to a real remote for IT — currently using local daemon")`.

**DO NOT leave the local daemon pretending to be a real remote in IT tests.**

### Step 5 — Final verification

```bash
echo "--- UT ---"
.venv/bin/pytest tests/unit/ --env tests/env-UT --tb=no -q
echo "--- ST ---"
.venv/bin/pytest tests/system/ --env tests/env-ST --tb=no -q
echo "--- IT ---"
.venv/bin/pytest tests/integration/ --env tests/env-IT --tb=no -q
```

### Step 6 — Report

Append exact results under `## COMPLETION REPORT` at the bottom of this file. Include:
- Exact pytest summary line per tier (paste, do NOT paraphrase)
- Which option you chose for IT1.9/IT1.10 and why
- What fixed the server startup failure

---

## RULES

- **DO NOT** delete or weaken any existing test
- **DO NOT** add `pytest.skip()` to hide failures
- **DO NOT** leave a local git daemon pretending to be a real remote in IT
- If a test genuinely cannot run, use `pytest.fail("reason")` — NEVER `pytest.skip()`
- If you cannot fix a test, leave it failing and document why

## COMPLETION REPORT

### Step 5 exact pytest summaries

- UT: `25 passed in 1.17s`
- ST: `10 passed in 0.84s`
- IT: `10 passed in 637.66s (0:10:37)`

### IT1.9 / IT1.10 option chosen

- **Option A — Real remote**
- `tests/env-IT` now requires `GIT_MCP_REMOTE_REPO` to be set to an operator-authorised remote.
- Rationale: this satisfies RULES.md integrity for IT by validating against an external remote instead of a local daemon.

### Startup failure fix

- Startup reliability was restored by fixing environment handling and IT server wiring:
- `tests/conftest.py` now preserves pre-existing environment variables from `env-vault` instead of overwriting them from `tests/env-*`.
- `tests/integration/conftest.py` now reads both API and MCP ports explicitly from `tests/env-IT` and validates the configured remote in a strict fail-fast path for IT/AT.
- With these fixes in place, `server_control.sh --env tests/env-IT start all` starts correctly and the IT suite reaches a clean pass.

### Revalidation run (2026-02-23)

#### Step 5 exact pytest summaries

- UT: `25 passed in 5.72s`
- ST: `10 passed in 10.43s`
- IT: `10 passed in 46.93s`

#### IT1.9 / IT1.10 option chosen

- **Option A — Real remote**
- Runtime env was set to an authorised real remote:
  - `GIT_MCP_REMOTE_REPO=https://git.cloud-dog.net/cloud-dog-ai/git-mcp-server.git`
  - `GIT_MCP_ALLOWED_REMOTE_PREFIXES=https://git.cloud-dog.net/cloud-dog-ai/`
- Rationale: keeps `tests/env-IT` safe-by-default (empty remote) while enforcing real external remote for IT remote tests.

#### Startup failure fix

- No new startup code change was required in this revalidation run; the historical startup issue was not reproducible.
- `./server_control.sh --env tests/env-IT start all` started API and MCP successfully during Step 2.
- Current behaviour is:
  - API/MCP startup is healthy.
  - IT without remote env fails honestly for IT1.9/IT1.10 (`GIT_MCP_REMOTE_REPO is required...`), while IT1.1–IT1.8 pass.
  - IT with authorised remote env passes 10/10.
