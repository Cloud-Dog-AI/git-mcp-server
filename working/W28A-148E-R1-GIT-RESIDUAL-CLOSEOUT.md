# W28A-148E-R1 Git Residual Closeout

Date: 2026-05-11

## Scope

- Confirmed starting commit: `git-mcp-server` at `87cfffe`.
- Confirmed UI monorepo starting commit: `2a6e247`.
- Owned changes only under `git-mcp-server/**` and `cloud-dog-ai-ui-monorepo/apps/git-mcp/**`.
- No DB rerun.
- No LLM/Ragflow/generation.
- No full W28A-102 estate rerun because focused preprod did not pass.

## Changes

Git server:

- Allowed `/admin/*` paths to fall through to the SPA shell instead of returning JSON 404.
- API admin routes are still protected under `/api/v1/admin/*` and `/app/v1/admin/*`.
- Added/updated unit regression coverage for `/admin/users` deep-link delivery.

Git UI Playwright preprod config:

- Added approved preprod `E2E_API_KEY` resolver.
- Resolver reads `git-mcp-server/private/env-PREPROD`, resolves the configured Vault reference through `/opt/iac/Development/cloud-dog-ai/env-vault`, and sets `process.env.E2E_API_KEY` without printing the secret.
- Defaults preprod auth mode to `api_key`.

Changed files:

- `src/git_mcp_server/web_ui.py`
- `tests/unit/UT1.56_WebUiDelivery/test_web_ui_delivery.py`
- `../cloud-dog-ai-ui-monorepo/apps/git-mcp/playwright.preprod.config.ts`

## Redacted Key Proof

Command:

```bash
node -e "import('./playwright.preprod.config.ts').then(()=>{const k=process.env.E2E_API_KEY||''; console.log('source=vault.dev.services.gitmcpserver0.api_key resolved=' + Boolean(k) + ' length=' + k.length + ' prefix=REDACTED');})"
```

Result:

```text
source=vault.dev.services.gitmcpserver0.api_key resolved=true length=35 prefix=REDACTED
```

No secret value was printed.

## Runtime Config Probe

Live preprod `/runtime-config.js` no longer contains `127.0.0.1:5177`:

```text
200 https://gitmcpserver0.cloud-dog.net/runtime-config.js
matches: /git-mcp, gitmcpserver0.cloud-dog.net, window.location.origin
```

## Focused Result

Command:

```bash
npx --no-install playwright test tests/e2e/ui-review2.spec.ts -g 'T10|T11|T12|T13' --config=playwright.preprod.config.ts --reporter=list
```

Result:

```text
4 failed
```

Failures:

- `T10 users entity dialog`: timed out waiting for `Add User`.
- `T11 groups entity dialog`: timed out waiting for `Add Group`.
- `T12 api key entity dialog`: timed out waiting for `Add API Key`.
- `T13 api key relative timestamps`: timed out waiting for `add user`.

Classification:

- The missing `E2E_API_KEY` blocker is cleared.
- Each screenshot shows preprod returned `{"detail":"Not Found"}` for `/admin/...`.
- Preserved contexts include one browser 404 console error and aborted API polls.
- This is the Git server SPA deep-link fallback bug fixed locally in `web_ui.py`, but not deployed.

Evidence paths:

- `cloud-dog-ai-ui-monorepo/apps/git-mcp/test-results/preprod/e2e-ui-review2-T10-users-entity-dialog-chromium/trace.zip`
- `cloud-dog-ai-ui-monorepo/apps/git-mcp/test-results/preprod/e2e-ui-review2-T11-groups-entity-dialog-chromium/trace.zip`
- `cloud-dog-ai-ui-monorepo/apps/git-mcp/test-results/preprod/e2e-ui-review2-T12-api-key-entity-dialog-chromium/trace.zip`
- `cloud-dog-ai-ui-monorepo/apps/git-mcp/test-results/preprod/e2e-ui-review2-T13-api-key-relative-timestamps-chromium/trace.zip`

## Local Verification

Command:

```bash
.venv/bin/pytest tests/unit/UT1.56_WebUiDelivery/test_web_ui_delivery.py -q
```

Result:

```text
4 passed in 5.41s
```

Command:

```bash
npx --no-install tsc -p tsconfig.json --noEmit
```

Result:

```text
failed with pre-existing app type errors in GroupsPage.tsx, RepositoryBrowserPage.tsx, and TagManagerPage.tsx
```

## Full Shard

Not run. Stop condition held because the focused preprod shard did not pass.

## Deploy

No deploy was performed in this pass.

Required deploy to close the live deep-link gap:

- Build/push `registry.cloud-dog.net:443/cloud-dog/git-mcp-server:latest`.
- Apply only `docker_image.gitmcpserver` and `docker_container.gitmcpserver0`.
- Reprobe `https://gitmcpserver0.cloud-dog.net/admin/users` for HTML 200 instead of JSON 404.
- Rerun focused T10/T11/T12/T13, then the full Git W28A-102 shard if focused passes.

## Residual Blockers

- `gitmcpserver0` is still running an image that returns JSON 404 for `/admin/*` SPA routes.
- Focused Git T10-T13 remain red until the SPA fallback fix is deployed.
