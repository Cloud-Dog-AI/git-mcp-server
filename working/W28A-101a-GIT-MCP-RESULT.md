# W28A-101a Git MCP Python 3.12 Rerun Result

## Prime Directive / Goal

Instruction source: `cloud-dog-ai-platform-standards/working/instructions/W28A-101a-git-mcp-PYTHON-312-RERUN-2026-05-08.md`.

Goal executed: rerun and repair `git-mcp-server` on Python 3.12.13, prove the runtime guard, full applicable UT/ST/IT/AT/QT layers, package build, Docker dev/public builds, server-control smoke, and confirm there are no active Python 3.10/3.11 build/Docker/package/test-runner references. No local DB/container fallback was introduced.

## Runtime

- Repository: `git-mcp-server`
- Branch at evidence capture: `main`
- Base commit before this work: `e06a27e`
- Python executable: `/opt/iac/Development/cloud-dog-ai/git-mcp-server/.venv/bin/python`
- Python version: `3.12.13`
- Runtime guard evidence: `working/w28a-101-ps100-python-runtime-guard.log`
- Runtime guard result: `runtime_guard=pass`

## Changes Made

- Added missing `websocket-client>=1.8,<2.0` dev dependency required for integration collection.
- Fixed local IT/AT startup by removing unresolved optional Vault placeholders from the active local-server env path:
  - JWT test secrets now resolve through `TEST_JWT_SECRET` indirection.
  - Optional GitLab tokens now resolve through blank `TEST_OPTIONAL_GITLAB_TOKEN` indirection.
  - GitLab URL remains blank for the public Gitea boundary fixture.
- Disabled platform log-integrity background verifier in test env overlays and short-lived test audit emitters to remove hidden shutdown noise/hangs while preserving service-level logging configuration.
- Centralised process environment copying for Git clone subprocesses in `git_tools.process_env`.
- Routed cookie-session HTTP validation through the shared `git_mcp_server.http_client` wrapper.
- Fixed QT compliance drift in docs/test traceability, UK spelling checks, and hardcoded URL/path static checks.

## Evidence

| Layer | Command summary | Result | Log |
|---|---:|---:|---|
| PS-100 runtime guard | `.venv/bin/python .../python-runtime-guard.py` | PASS | `working/w28a-101-ps100-python-runtime-guard.log` |
| Diff check | `git diff --check` | PASS | `working/w28a-101-diff-check.log` |
| UT | `pytest tests/unit --env tests/env-UT -q -rs` | `82 passed` | `working/w28a-101-ut.log` |
| ST | `pytest tests/system --env tests/env-ST -q -rs` | `23 passed` | `working/w28a-101-st.log` |
| IT | `pytest tests/integration --env tests/env-IT -q -rs` | `21 passed` | `working/w28a-101-it.log` |
| AT | `pytest tests/application --env tests/env-AT -q -rs` | `9 passed` | `working/w28a-101-at.log` |
| QT | `pytest tests/quality tests/security --env tests/env-QT -q -rs` | `62 passed` | `working/w28a-101-qt.log` |
| Build | `.venv/bin/python -m build --sdist --wheel` | PASS | `working/w28a-101-build.log` |
| Docker dev | `./docker-build.sh w28a-101a-python312 --variant dev` | PASS | `working/w28a-101-docker-build.log` |
| Docker public | `./docker-build.sh w28a-101a-python312-public --variant public` | PASS | `working/w28a-101-docker-build-public.log` |
| Server smoke | `server_control.sh --env tests/env-IT start/status/health/stop all` | PASS | `working/w28a-101-server-smoke.log` |
| Python ref scan | active build/docker/package/test-runner/runtime files | PASS, no matches | `working/w28a-101-python-reference-scan.log` |

## Server Smoke Details

`server_control.sh` was run with `tests/env-IT` because root-owned stale services occupy the default ports on this host. The smoke proved:

- API: `http://127.0.0.1:19031/health -> 200`
- Web: `http://127.0.0.1:19032/ -> 200`
- MCP: `http://127.0.0.1:19033/health -> 200`
- A2A: `http://127.0.0.1:19034/health -> 200`

## Python 3.10/3.11 Scan

No active Python 3.10/3.11 references were found in:

- `Dockerfile*`
- `docker-build.sh`
- `server_control.sh`
- `pyproject.toml`
- `.github`
- `scripts`
- `tests`

The pre-existing untracked `.venv.ps100-backup-20260508T114844Z/` contains Python 3.10 paths, but it is an untracked backup directory outside the active build/Docker/package/test-runner/runtime scope and was not modified or removed.

## Worktree Note

The only known unrelated dirty state is the pre-existing untracked `.venv.ps100-backup-20260508T114844Z/` directory. It was present before this task and is intentionally left untouched.

Root-owned stale `python3 -m git_mcp_server.*` processes remain on the host default ports and could not be killed by this user. Final IT/AT/smoke used isolated test ports and stopped all services they started.
