# W28A-148E-R2 Git Deploy Rerun Closeout

Date: 2026-05-11

## Scope

- Service repo: `git-mcp-server`
- Required source commit: `7583cb9 fix: serve git admin spa deep links`
- Confirmed starting HEAD: `7583cb9`
- Deployment target: `gitmcpserver0` only
- No DB, LLM, Ragflow, generation, full estate rerun, or public publication was run.

## Deploy

Pre-deploy live residual:

```text
GET https://gitmcpserver0.cloud-dog.net/admin/users
HTTP 404 application/json size=22
```

Build and push:

- Image tag: `registry.cloud-dog.net:443/cloud-dog/git-mcp-server:w28a-148e-r2-7583cb9`
- Latest tag: `registry.cloud-dog.net:443/cloud-dog/git-mcp-server:latest`
- Local config digest: `sha256:10e7d88d71cf9deb3fea61240c81f259d2f6a95d2310e3b0a60c18ba0b6dd5cc`
- Python runtime proof: `PYTHON_VERSION=3.12.13`
- Immutable manifest digest: `sha256:18cd2df3645ba52343559b067daf95a24ae3258d9d3a3add782638064d657a13`
- Latest manifest digest: `sha256:18cd2df3645ba52343559b067daf95a24ae3258d9d3a3add782638064d657a13`

Targeted Terraform:

```text
terraform plan -target=docker_image.gitmcpserver -target=docker_container.gitmcpserver0 -out=w28a-148e-r2-gitmcpserver.tfplan
Plan: 2 to add, 0 to change, 2 to destroy.

terraform apply -auto-approve w28a-148e-r2-gitmcpserver.tfplan
Apply complete! Resources: 2 added, 0 changed, 2 destroyed.
```

Runtime proof:

- Container: `gitmcpserver0.app.vpc0.cloud-dog.net`
- Container ID: `c630a5d880d4`
- State: `running`
- Started at: `2026-05-11T16:04:03.498601916Z`
- Runtime image config: `sha256:10e7d88d71cf9deb3fea61240c81f259d2f6a95d2310e3b0a60c18ba0b6dd5cc`

## Live Route Verification

Post-deploy route fix:

```text
GET https://gitmcpserver0.cloud-dog.net/admin/users
HTTP 200 text/html; charset=utf-8 size=487
```

Body markers include `<script` and `<div id="root"`, confirming SPA delivery instead of JSON 404.

## Focused Result

Command:

```bash
E2E_BASE_URL=https://gitmcpserver0.cloud-dog.net npx --no-install playwright test tests/e2e/ui-review2.spec.ts -g 'T10|T11|T12|T13' --config=playwright.preprod.config.ts --reporter=list
```

Result:

```text
4 passed (11.1s)
```

Passed focused cases:

- `T10 users entity dialog`
- `T11 groups entity dialog`
- `T12 api key entity dialog`
- `T13 api key relative timestamps`

Evidence:

- `working/W28A-148E-R2/focused-t10-t13.log`

## Full Git W28A-102 Shard

Command:

```bash
E2E_BASE_URL=https://gitmcpserver0.cloud-dog.net npx --no-install playwright test tests/a11y.spec.ts tests/e2e --config=playwright.preprod.config.ts --reporter=list
```

Result:

```text
36 passed
16 failed
Duration: 8.6m
```

Failed cases:

- `branch-edit-commit-push.spec.ts` / `open, branch, edit, commit and push`
- `conflict-resolution.spec.ts` / `create conflict, list and resolve manually`
- `forensic-w28a-448.spec.ts` / `W28A-448 forensic WebUI flow`
- `mcp-catalogue-and-call.spec.ts` / `catalogue refresh and api+mcp tool execution`
- `real-functional-w28a-481.spec.ts` / `W28A-481 real repository WebUI flow`
- `recovery-artifacts.spec.ts` / `stash save/list/pop workflow`
- `recovery-page-ui.spec.ts` / `recovery page exposes non-destructive actions with on-screen status`
- `tag-readonly-browse.spec.ts` / `tag ref enters readonly mode and blocks file writes`
- `ui-review2.spec.ts` / `T19 MCP tool browser search`
- `ui-review2.spec.ts` / `T20 MCP execution panel`
- `ui-review2.spec.ts` / `T21 API docs panel and links`
- `w28a119d-rendered-assertions.spec.ts` / `W28A-119D API docs render MCP and A2A discovery surfaces in the browser`
- `w28a870-git-mcp-e2e-testing.spec.ts` / `sections b-f api workflow covers workspace lifecycle, file operations, search, status, log, diff, and pull`
- `w28a870-git-mcp-e2e-testing.spec.ts` / `sections l-n web ui covers repository browser, commit log viewer, and diff viewer`
- `w28a870-git-mcp-e2e-testing.spec.ts` / `sections o-p web ui covers branch management and merge conflict resolution`
- `w28a870-git-mcp-e2e-testing.spec.ts` / `sections q-r web ui covers tag management and stash management`

Failure themes:

- Several direct tool calls returned `ok=false` where tests expected success.
- Several WebUI workspace flows did not populate/open a workspace.
- MCP/API docs UI assertions timed out waiting for expected browser-visible content.

Evidence:

- `working/W28A-148E-R2/full-w28a-102-git-shard.log`
- `../cloud-dog-ai-ui-monorepo/apps/git-mcp/test-results/preprod/`

## Evidence Files

- `working/W28A-148E-R2/docker-build-w28a-148e-r2-7583cb9.log`
- `working/W28A-148E-R2/local-image-inspect-w28a-148e-r2-7583cb9.json`
- `working/W28A-148E-R2/push-immutable.log`
- `working/W28A-148E-R2/push-latest.log`
- `working/W28A-148E-R2/terraform-plan-targeted-gitmcpserver0.log`
- `working/W28A-148E-R2/terraform-apply-targeted-gitmcpserver0.log`
- `working/W28A-148E-R2/runtime-container-inspect.json`
- `working/W28A-148E-R2/live-admin-users.html`

## Residual Blockers

- Git live `/admin/*` SPA deep-link residual is fixed.
- Focused Git T10-T13 is green.
- Full Git W28A-102 shard remains red: `36 passed, 16 failed`.
