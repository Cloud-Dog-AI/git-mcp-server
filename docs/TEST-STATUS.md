---
template-id: T-TSS
template-version: 1.0
project: git-mcp-server
doc-last-updated: 2026-06-25T05:40:27Z
doc-git-commit: 342c8c1b336389e2f3afa5e5400ad3ed9b5d33cd
doc-git-branch: main
doc-age-policy: 30d
doc-conformance-stamp: 2026-06-25T05:40:27Z
---

# git-mcp-server — TEST-STATUS

> **Template version:** T-TSS v1.0 — overwritten by `scripts/update-test-state.py`. Do not hand-edit.

## 1. Latest run

- **Run timestamp:** 2026-06-25T05:40:27Z
- **Commit:** `342c8c1b336389e2f3afa5e5400ad3ed9b5d33cd` (`main`)
- **Totals:** W28E-1804C closeout pack | PASS | 0 blocking failures

Primary raw results:

| Pack | Status | Raw evidence |
|---|---|---|
| Full WebUI local Playwright | PASS (`109 passed, 9 skipped`) | `test-logs/ui-playwright-full-local-r9.log` |
| Focused WebUI adoption | PASS (`15 passed`) | `test-logs/ui-playwright-w28a458-r5.log` |
| UI lint/typecheck/unit/build | PASS | `ui-lint-r12.log`, `ui-typecheck-r16.log`, `ui-vitest-r5.log`, `ui-build-r5.log` |
| Backend focused unit | PASS (`41 passed`) | `backend-focused-unit-r6.log` |
| Backend admin CRUD parity | PASS (`5 passed`) | `backend-admin-crud-parity-r7.log` |
| Backend API/MCP/A2A/jobs on local Docker | PASS (`5 passed`) | `backend-api-mcp-a2a-job-local-docker-r1.log` |
| Audit unit pack | PASS (`7 passed`) | `backend-audit-unit-r1.log` |
| Local Docker image browser proof | PASS (`12 passed`) | `local-docker-ui-playwright-health-r1.log`, `local-docker-ui-playwright-w28j-conformance-r1.log` |
| Live gitmcpserver0 preprod browser proof | PASS (`12 passed`) | `live-preprod-ui-playwright-r2.log` |
| Live gitmcpserver0 cookie front-door smoke | PASS | `live-cookie-browser-smoke-r2.log` |
| Live sibling sentinel browser proof | PASS (`4 passed`) | `live-preprod-sentinels-r1.log` |

## 2. Per-test status

| Test ID | Tier | Status | Last run | Commit | Known issue |
|---|---|---|---|---|---|
| `tests.unit.UT1.65_VestigialGitMcpRoutes.test_vestigial_git_mcp_routes::test_api_git_mcp_prefix_is_not_always_401` | UT/ST/IT | pass | 2026-06-17 | `e7c21dce` | |
| `tests.unit.UT1.65_VestigialGitMcpRoutes.test_vestigial_git_mcp_routes::test_git_mcp_not_advertised_in_web_openapi` | UT/ST/IT | pass | 2026-06-17 | `e7c21dce` | |

## 3. Failures (detail)

_None._
