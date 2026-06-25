# AGENT-INSTRUCTION-UNBLOCK-IT-HTTPS-REMOTE

> **DIRECTIVE:** You must read and follow each instruction diligently and accurately. You must ensure you understand and 100% follow your Rules.md. You will NOT avoid completing 100% of your tests, to demonstrate 100% delivery of functionality to full depth, quality and accuracy. You will not lie, fudge, avoid, ignore or hack test results. Tests will always be against real test systems. Ignoring, avoiding, faking or lying is 100% failure.

## Objective
Unblock git-mcp-server IT remote tests (HTTPS path) by removing stale conflicting runtime processes and revalidating IT1.9 + IT1.10 against real remotes.

## Scope
- Project: `git-mcp-server`
- In scope: process cleanup, env validation, real test execution, evidence capture
- Out of scope: chat-client, file-mcp-server, platform-wide migration tasks

## Required Inputs
- `tests/env-IT` must define:
  - `GIT_MCP_REMOTE_REPO` (HTTPS remote)
  - `GIT_MCP_REMOTE_REPOS` (comma-separated HTTPS candidates)
  - `GIT_MCP_ALLOWED_REMOTE_PREFIXES` (HTTPS allowlist)

## Mandatory Steps
1. Move to project root:
   - `cd /opt/iac/Development/cloud-dog-ai/git-mcp-server`
2. Stop local managed services:
   - `./server_control.sh --env tests/env-IT stop all`
3. Stop conflicting containerized instance if present:
   - `docker stop git-mcp-server || true`
4. Verify no stale listeners remain on IT ports:
   - `ss -ltnp | grep -E ':18585|:18586' || true`
   - Expected: no output
5. Verify env is HTTPS-only and populated:
   - `grep -nE 'GIT_MCP_REMOTE_REPO|GIT_MCP_REMOTE_REPOS|GIT_MCP_ALLOWED_REMOTE_PREFIXES' tests/env-IT`
6. Execute real integration tests:
   - `./.venv/bin/pytest tests/integration/IT1.9_RemoteCloneAndFetch/test_remote_clone_and_fetch.py --env tests/env-IT -v`
   - `./.venv/bin/pytest tests/integration/IT1.10_RemoteBranchPush/test_remote_branch_push.py --env tests/env-IT -v`
7. Persist evidence:
   - Save command outputs to `working/reports/IT-HTTPS-UNBLOCK-REPORT-<YYYY-MM-DD>.md`
   - Include pass/fail status and any remediation applied.

## Success Criteria
- No process/container conflict on `18585/18586`
- IT1.9 passes
- IT1.10 passes
- Evidence report committed to `working/reports/`

## Failure Handling
- If any command fails, stop and document exact command, exit code, and stderr.
- Do not skip failing tests.
- Do not replace failures with fallbacks that hide defects.
