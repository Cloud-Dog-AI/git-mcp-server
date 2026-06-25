# W28A-148E-R3 Git Workflow Closeout

Date: 2026-05-11

## Scope

- Service: `git-mcp-server`
- UI app: `cloud-dog-ai-ui-monorepo/apps/git-mcp`
- No DB, LLM, Ragflow, generation, full estate rerun, or public publication was run.

## Changes

- Added explicit SPA deep-link handlers for `/api-docs`, `/mcp-console`, and `/a2a-console`.
- Extended the Git web UI delivery unit test to cover `/api-docs` and `/mcp-console`.
- Improved Git Playwright `runTool` assertions so remaining workflow failures include target/tool/status/code/error/data context.

## Triage

Previous full Git W28A-102 shard residual groups:

```text
36 passed, 16 failed
```

Failure groups:

- Workflow/tool execution: branch edit/commit/push, conflict resolution, MCP catalogue/call, real repository flow, recovery artifacts, tag readonly, W28A-870 sections b-f.
- Workspace-flow UI: recovery page UI, W28A-870 sections l-n, o-p, q-r.
- SPA/API docs/MCP console: T19, T20, T21, W28A-119D rendered API docs.

Confirmed live route residual:

```text
/admin/users status=200 text/html
/mcp-console status=404 application/json
/api-docs status=404 application/json
/repository status=200 text/html
/recovery status=200 text/html
```

## Focused Evidence

Unit:

```text
python3 -m pytest tests/unit/UT1.56_WebUiDelivery/test_web_ui_delivery.py
4 passed in 4.55s
```

Focused preprod deep-link group before deploy:

```text
E2E_BASE_URL=https://gitmcpserver0.cloud-dog.net npx --no-install playwright test tests/e2e/ui-review2.spec.ts -g 'T19|T20|T21' --config=playwright.preprod.config.ts --reporter=list
3 failed
T19/T20/T21 all landed on JSON {"detail":"Not Found"} for undeployed live routes.
```

Focused preprod workflow diagnostic before fixture assertion improvement:

```text
E2E_BASE_URL=https://gitmcpserver0.cloud-dog.net npx --no-install playwright test tests/e2e/w28a870-git-mcp-e2e-testing.spec.ts -g 'sections b-f' --config=playwright.preprod.config.ts --reporter=list
1 failed
Failure remained a generic ok=false assertion; fixture now emits target/tool/status/error detail on rerun.
```

## Full Shard

Not rerun. Focused Git preprod checks remain red until the route fix is deployed; full Git W28A-102 shard remains blocked.

## Residual Blockers

- Git route fix is source-green locally but not deployed to `gitmcpserver0`; `/mcp-console` and `/api-docs` still return live JSON 404.
- Broader workflow failures require a post-deploy focused rerun with the improved assertion diagnostics to identify exact tool/status causes.
