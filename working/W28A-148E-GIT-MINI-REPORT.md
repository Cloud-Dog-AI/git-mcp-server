# W28A-148E Git Mini Report

Date: 2026-05-11

## Classification

- Root cause fixed in harness/runtime config: preprod Playwright fixtures now default runtime config to `https://gitmcpserver0.cloud-dog.net` instead of `http://127.0.0.1:5177`, preventing local API `ERR_CONNECTION_REFUSED` loops in preprod.
- Root cause fixed in repo-default split: local test repo fallback is honored only for local candidates; remote preprod runs no longer silently use local seed keys without an explicit `E2E_API_KEY`.
- Root cause still blocked: focused preprod admin dialog test now fails immediately with `E2E_API_KEY is required for remote git-mcp runs`, so valid W28A-102-approved Git preprod credentials are required before checking admin dialogs or remote repo flows.
- Harness evidence fixed: Playwright failures now retain trace/video, a redacted screenshot, current spec metadata, and last console/network errors.

## Focused Results

- `npx --no-install playwright test tests/e2e/ui-review2.spec.ts -g "T10|T11|T12|T13" --config=playwright.preprod.config.ts --reporter=list`: initial rerun preserved traces/screenshots and classified sign-in timeout caused by local `127.0.0.1:5177/api/v1/tools` runtime config.
- `npx --no-install playwright test tests/e2e/ui-review2.spec.ts -g "T10" --config=playwright.preprod.config.ts --reporter=list`: `1 failed (1.2s)` with explicit missing `E2E_API_KEY` blocker.
- Evidence paths: `cloud-dog-ai-ui-monorepo/apps/git-mcp/test-results/preprod/e2e-ui-review2-T10-users-entity-dialog-chromium/trace.zip`, `.../video.webm`, and `.../attachments/w28a-timeout-context-ae0e23c74609bc4fb514b0357159243d6c403566.json`.

## Full Shard

- Not run. Stop condition applies because focused Git is credential-blocked.
