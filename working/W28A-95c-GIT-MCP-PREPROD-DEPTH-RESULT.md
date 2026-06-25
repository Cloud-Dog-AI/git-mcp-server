# W28A-95c Git MCP Preprod Depth Result

## Prime Directive / Goal

Instruction source: `cloud-dog-ai-platform-standards/working/instructions/W28A-95c-GIT-MCP-PREPROD-IT-AT-QT-DEPTH-2026-05-08.md`.

Goal executed: audit and rerun Git MCP IT, AT, and QT depth against the provided preprod-style contracts; use provided services and Vault contracts only; do not invent localhost backends; start/stop managed services only through `server_control.sh`; improve shallow or broken local defects where required; publish logs and a depth coverage classification for git ops, auth, admin, security, MCP, A2A, error paths, and storage variants.

## Reading Proof

- Read repo rules: `RULES.md`.
- Read platform rules: `../cloud-dog-ai-platform-standards/RULES.md`.
- Read lessons: `AGENT-LESSONS.md` and `../cloud-dog-ai-platform-standards/AGENT-LESSONS.md`.
- Read bootstrap directive: `../cloud-dog-ai-platform-standards/AGENT-BOOTSTRAP-DIRECTIVE.md`.
- Read instruction: `../cloud-dog-ai-platform-standards/working/instructions/W28A-95c-GIT-MCP-PREPROD-IT-AT-QT-DEPTH-2026-05-08.md`.

## Runtime And Scope

- Repository: `git-mcp-server`.
- Branch at evidence capture: `main`.
- Base commit before this work: `ae1a306 fix(git-mcp): complete Python 3.12 rerun W28A-101a`.
- Python: `.venv/bin/python` on Python 3.12.13.
- Vault bootstrap: `source /opt/iac/Development/cloud-dog-ai/env-vault`.
- IT contract: `tests/env-IT`.
- AT contract: `tests/env-AT`.
- QT contract: `tests/env-QT`.
- Managed service rule: IT and AT were run through the test harness, which starts/stops services through `server_control.sh` fixtures. Manual cleanup used `./server_control.sh --env tests/env-IT stop all` and `./server_control.sh --env tests/env-AT stop all`.
- Backend rule: no new localhost backend or container fallback was added. The provided IT/AT env files use local Git MCP service ports plus the configured remote Git fixture URLs.

## Changes Made

- Added `pytest-timeout>=2.3,<3.0` to `pyproject.toml` dev dependencies so the mandated `pytest --timeout=...` commands execute instead of failing option parsing.
- Installed `pytest-timeout-2.4.0` into the existing venv for this rerun; install evidence is in `working/w28a-95c-venv-install.log`.
- No runtime fallback, local DB/container backend, or credential workaround was introduced.

## Evidence Summary

| Evidence | Result | Log |
|---|---:|---|
| Test inventory | 36 test files inventoried | `working/w28a-95c-test-inventory.txt` |
| Depth grep | 544 matching lines for depth audit terms | `working/w28a-95c-depth-grep.txt` |
| Vault bootstrap validation | PASS; required variables present, Vault health reachable with HTTP 429 | `working/w28a-95c-vault-validate.log` |
| IT full | `21 passed`, `0 failed`, `0 errors` | `working/it-95c-preprod-full.log` |
| AT full | `9 passed`, `0 failed`, `0 errors` | `working/at-95c-preprod-full.log` |
| QT full | `58 passed`, `0 failed`, `0 errors` | `working/qt-95c-full.log` |
| Security supplemental | `4 passed`, `0 failed`, `0 errors` | `working/security-95c-full.log` |
| Public preprod health smoke | `/health`, `/api/v1/health`, `/mcp/health`, `/a2a/health` all HTTP 200 | `working/w28a-95c-live-preprod-smoke.log` |
| Public WebUI/runtime smoke | `/` and `/runtime-config.js` HTTP 200 | `working/w28a-95c-live-preprod-web-runtime-config.log` |
| Authenticated public preprod contract probe | BLOCKED before HTTP auth calls by unresolved Vault placeholder | `working/w28a-95c-live-preprod-contract-probe.log` |
| Vault shape probe | `dev.services.gitmcpserver0` contains `api_key`, `api_url`, `mcp_url`, `a2a_url`, `web_url` keys | `working/w28a-95c-vault-shape.log` |
| Diff whitespace | PASS | `working/w28a-95c-diff-check.log` |

## Required Commands

The required full-layer commands were run with Vault bootstrap loaded:

```bash
.venv/bin/python -m pytest tests/integration --env tests/env-IT -v --timeout=900
.venv/bin/python -m pytest tests/application --env tests/env-AT -v --timeout=900
.venv/bin/python -m pytest tests/quality --env tests/env-QT -v --timeout=600
git diff --check
```

Supplemental security depth command:

```bash
.venv/bin/python -m pytest tests/security --env tests/env-QT -v --timeout=600
```

## Coverage Classification

| Area | Classification | Evidence |
|---|---|---|
| Git ops | PASS, deep local preprod-contract coverage | IT covers remote clone/fetch, remote branch push, read-only ref protection, managed repo open/diff jobs, and remote-tracking ref recovery. AT covers branch edit/push, tag browse, conflict resolve, and recovery restore. |
| Auth | PASS | IT/AT cover API key accept/reject, JWT bearer accept/reject, A2A bearer health contract, and role-gated HTTP/MCP paths. |
| Admin | PASS | IT covers admin HTTP CRUD parity, admin role enforcement, MCP admin tool parity, and config-change event broadcast. AT covers full admin profile CRUD and repo profile lifecycle. |
| Security | PASS | QT covers no secrets in source/env defaults, Vault expression use, no hardcoded runtime secrets, no internal hostnames, and no skips/xfails/mocks in IT/AT. Security supplemental covers secrets never logged, symlink escape prevention, Git hooks disabled, and UK English compliance. |
| MCP | PASS | IT covers MCP tool catalogue, MCP tool execution against remote fixture, and admin MCP parity. |
| A2A | PASS | IT/AT cover A2A bearer health contracts and config-change event broadcast. Public preprod unauthenticated A2A health returned HTTP 200. |
| Error paths | PASS | Covered rejection paths include missing/invalid API auth, invalid JWT, non-admin admin access, unresolved reader-role repo access, and attempted write to read-only refs. |
| WebUI support endpoints | PASS for public unauthenticated smoke; limited for authenticated flows | Public preprod `/` and `/runtime-config.js` returned HTTP 200. Authenticated live API/MCP/A2A probe is blocked by the Vault resolver gap below. |
| Storage variants | LIMITED | The mandated IT/AT contracts validate the provided Git MCP local service runtime and configured remote Git fixtures. No alternate storage backend matrix is present in W28A-95c, and none was invented. Public preprod health/WebUI smoke passed, but authenticated live-preprod storage/API depth is blocked by the Vault resolver gap below. |

## Live Preprod Contract Gap

Authenticated public preprod probing via `private/env-PREPROD` did not reach HTTP calls. The installed `cloud_dog_config` resolver failed while loading the provided contract:

```text
cloud_dog_config.errors.UnresolvedPlaceholderError: Unresolved placeholder: vault.dev.services.gitmcpserver0.api_key
```

A separate Vault shape probe confirms the expected key path exists in Vault configuration data:

```text
dev.services.gitmcpserver0 keys: ['a2a_url', 'api_key', 'api_url', 'mcp_url', 'web_url']
```

Classification: this is a preprod Vault/config resolver contract gap, not a missing Git MCP test fixture and not a reason to invent local credentials. The local provided `tests/env-IT`, `tests/env-AT`, and `tests/env-QT` contracts are green; authenticated live preprod depth remains blocked until `cloud_dog_config` can resolve the `vault.dev.services.gitmcpserver0.*` placeholders from the provided Vault blob.

## No Skip/Xfail Position

- The required IT, AT, QT, and supplemental security suites completed without skipped or xfailed tests in their pytest summaries.
- QT includes explicit checks against `pytest.skip`, `pytest.mark.skip`, `pytest.mark.xfail`, and mocks in IT/AT.
- The grep audit was retained as raw evidence; binary `__pycache__` stderr was produced by the mandated recursive grep shape but does not affect the pytest no-skip/no-xfail evidence.

## Worktree Note

The pre-existing untracked `.venv.ps100-backup-20260508T114844Z/` directory remains untouched and is intentionally not part of this submission.

## Closing Warrant

W28A-95c IT/AT/QT depth is green against the provided contracts, with explicit coverage classification and logs. The only blocked item is authenticated public preprod probing through `private/env-PREPROD`, because the platform config resolver cannot resolve an existing Vault key path from the provided Vault contract. No localhost backend, container fallback, or secret workaround was introduced.
