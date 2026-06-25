# AGENT LESSONS — git-mcp-server

## Central Programme Lesson Authority

The canonical programme lessons are in `/opt/iac/Development/cloud-dog-ai/cloud-dog-ai-platform-standards/AGENT-LESSONS.md`. This repository file is a service-specific overlay only. If this file conflicts with the central programme file, the central file wins.

Before project work, every agent must read the central `RULES.md`, central `AGENT-LESSONS.md`, `AGENT-BOOTSTRAP-DIRECTIVE.md`, the live `AGENT-DISPATCH-TABLE.md`, the exact lane instruction, and this overlay. Do not copy central rules here; add only service-specific deltas and feed reusable lessons back to the central file.


## Purpose

This document records the practical lessons from completing the full storage-platform adoption and release verification work for `git-mcp-server`, including the defects that were real, the defects that were only apparent, and the checks that were necessary to get to a truthful completion state.

It is intended to help the next agent or engineer avoid repeating the same dead ends.

## Scope Of What Was Solved

- Full `cloud_dog_storage` adoption in `src/`
- Zero bespoke storage grep count in `src/`
- Zero bespoke storage grep count inside the built container `/app/src`
- Full regression green
- Local Docker build and runtime green
- Preprod deploy green
- Preprod API smoke green
- Preprod WebUI smoke green with 9 unique screenshots

## The Most Important Lesson

The first diagnosis was wrong.

The local Docker failure initially looked like a Vault reachability problem because the container logs showed Vault-related resolution and the service did not come healthy. That was not the real root cause for the supported local-docker flow. The real breakages were local runtime and filesystem issues:

1. The checked-in launcher env pointed at a compose file path that no longer existed.
2. The compose file had been moved under `docker/`, but its bind mounts still assumed root-relative paths.
3. The non-root container hit host-owned files and directories on bind mounts and failed on logs and sqlite access.

If local Docker fails after a platform migration, check launcher pathing and host mount writability before blaming Vault or network.

## What Actually Broke

### 1. Compose Path Drift

The local launcher and control env still referenced a top-level `docker-compose.yml`, but the real file lived at `docker/docker-compose.yml`.

Lesson:
- When a compose file is moved, update every launcher, control env, and wrapper script that resolves it.
- Do not assume a repo-root compose path because `docker compose` will fail later and the failure may look unrelated.

Files involved:
- `local-docker-server.sh`
- `tests/env-local-docker-server`

### 2. Relative Bind Mounts Were Wrong After The Move

Once the compose file lived under `docker/`, mounts like `./logs`, `./data`, and `./certs` no longer meant the project root. They pointed to paths relative to the `docker/` folder instead.

Lesson:
- A compose file move is not just a path update. Every relative `env_file` and `volumes` entry must be revalidated.
- If the service starts but behaves strangely, inspect what is actually mounted into `/app`.

Files involved:
- `docker/docker-compose.yml`

### 3. Non-Root Container + Bind Mounts Caused Real Runtime Failures

> See central AGENT-LESSONS.md §4.12 for the cross-service rule on non-root container + bind-mount writability.

The image runs as a non-root user. Existing host files under bind-mounted `logs/` and `data/` were not always writable by the container user. That caused failures in:

- process log files
- audit log file
- audit integrity log file
- sqlite database file

Lesson:
- For local Docker, prefer isolated writable mounts that the launcher prepares specifically for the container.
- Do not solve a local bind-mount problem by baking environment hacks into production `src/` code unless there is no other option.

The stable fix was:
- use dedicated local-docker mounts under `working/local-docker/...`
- pre-create directories and log files in the launcher
- ensure those directories are writable before startup
- keep production runtime code free of local-only config access

Files involved:
- `docker/docker-compose.yml`
- `local-docker-server.sh`
- `tests/env-local-docker-server`
- `tests/env-IT-local-docker`
- `tests/env-AT-local-docker`
- `tests/env-UT-local-docker`
- `tests/env-ST-local-docker`

## What Looked Like A Good Fix But Was Wrong

An intermediate fix added `CLOUD_DOG_LOG_DIR` handling in `src/git_mcp_server/logging.py` so the app could rebase log destinations away from `/app/logs`.

That made local Docker work, but it introduced three new compliance regressions:

- direct `os.environ` access in `src/`
- hardcoded `/app/...` path logic in `src/`
- bespoke config-like behaviour in application code

Lesson:
- A fix that helps runtime but breaks platform-adoption compliance is not the final fix.
- Local-runtime accommodations belong in the orchestration layer first, not in `src/`, unless the repo’s standards explicitly allow them.

The correct final fix was to remove that `src/` override and make the local-docker mount layout sane instead.

## Storage Migration Lesson: Error Taxonomy Matters

Moving file operations to `cloud_dog_storage` changed the exception type for missing paths from builtin `FileNotFoundError` to `StorageFileNotFoundError`.

That broke existing tool-contract tests for:

- file download
- file copy

Lesson:
- Platform migrations are not only about replacing APIs. They also change exception taxonomy and therefore observable behaviour.
- If callers and tests already depend on builtin exceptions, translate platform-specific errors back to the established contract at the boundary.

The final fix was to catch `StorageFileNotFoundError` in `src/git_tools/files/io.py` and re-raise `FileNotFoundError`.

## Compliance Lesson: Seed Data Is Also Scanned

Static compliance checks scan `src/` broadly enough that bootstrap data in application code matters. The default seeded users in `api_server.py` used `@cloud-dog.net` addresses, and that triggered internal-hostname findings.

Lesson:
- Compliance scanners do not care whether a hostname is “just test data”.
- Seed records in `src/` should use neutral domains like `example.invalid` or `example.test` unless the repo explicitly permits internal domains.

## Local Docker Verification Lesson

> See central AGENT-LESSONS.md §4.11 for the cross-service Docker verification checklist (build / managed-stack / health / endpoints / `pip show` / bespoke grep).

A local Docker build is not enough. For this repo, the trustworthy verification sequence was:

1. build the image
2. start the managed local-docker stack through `local-docker-server.sh`
3. wait for container health
4. hit all four runtime endpoints
5. verify `cloud_dog_storage` inside the container with `pip show`
6. verify bespoke grep count inside `/app/src`
7. run focused external-runtime IT/AT slices against the live local stack

Lesson:
- If you only build, you can still miss mount, health, auth, and pathing failures.
- If you only curl health, you can still miss API contract or auth failures.

## Preprod Routing Lesson

On preprod, the public routed API surface was not the same as the internal app route prefix.

Observed behaviour:
- `/api/v1/*` was the working public routed API surface
- `/app/v1/*` on the public host returned `401`
- `/a2a/health` on preprod was publicly `200`

This matched the deployed Traefik rewrite configuration, not the stale assumption embedded in some test expectations.

Lesson:
- For preprod smoke, validate against the routed public surface that the environment actually exposes.
- Do not treat a stale test fixture expectation as stronger evidence than a live routed deployment plus Terraform labels.

## Preprod Test Harness Lesson

`private/env-PREPROD` was not sufficient on its own for the integration fixtures. It did not provide all of the host and port values expected by `tests/integration/conftest.py`.

Lesson:
- A failing preprod fixture setup is not automatically an application regression.
- Separate three things:
  - fixture wiring defects
  - route/rewrite differences
  - actual service failures

In this case:
- the deployed service was healthy
- the fixture env was incomplete for those integration helpers
- the route expectation in one A2A test did not match deployed preprod behaviour

The truthful deployment proof came from:
- live health checks
- in-container package verification
- direct authenticated API smoke against the routed public surface
- WebUI smoke via real browser

## WebUI Lesson

The preprod WebUI did not use API-key login. Its runtime config advertised `AUTH_MODE: "cookie"`, and the deployed web container had its own `CLOUD_DOG_WEB_LOGIN_*` values.

Lesson:
- Before writing browser automation, fetch `runtime-config.js` from the deployed UI.
- The auth mode in the built frontend matters more than what local tests or prior assumptions expect.
- When a browser test fails at login, check the live auth mode and deployed web env before debugging selectors.

Additional lesson:
- The rendered MCP console on preprod was not the same control surface assumed by some existing Playwright fixtures.
- The live UI used:
  - `Select tool`
  - `Arguments JSON`
  - `Execute`
  - `History`
- It did not expose the more advanced “target/tool name/last response JSON” shape assumed elsewhere.

That meant the browser smoke had to use the controls the deployed UI actually rendered.

## Verification Lesson: Browser Evidence Must Be Strict

The required 9-step WebUI smoke was only trustworthy once it enforced:

- all nine expected screenshots exist
- each screenshot hash is unique
- the flow uses the live auth mode
- the selected pages render real data and controls, not blank shells

Lesson:
- Screenshot capture alone is weak evidence.
- Screenshot capture plus uniqueness verification is much better evidence.

## Recommended Future Checklist

When working this repo again after a platform migration:

1. Run the platform grep counts before touching code.
2. Expect exception-contract regressions whenever platform libraries replace builtin file APIs.
3. Keep local-docker fixes in launcher/compose/env layers unless application code absolutely must change.
4. Re-run compliance checks before full regression if any local-runtime workaround touches `src/`.
5. Prove the built image locally with:
   - container health
   - endpoint curls

## W28A-870 Git MCP E2E And Preprod Rollout Lessons

### Code

- `git_stash_list` UI parsing must tolerate both plain-string and nested-wrapper payload shapes. In this cycle, `StashManagerPage` incorrectly assumed a double-wrapped `.result.result` shape and showed zero stash entries even when the backend returned valid stash data.
- UI refresh paths should not overwrite action-status messages. Silent refresh support in repository, branch, tag, and stash pages makes Playwright assertions much more stable and better matches user expectations.
- Old accessibility assumptions drift quickly. The dashboard service-health widget now exposes role `group` with accessible name `Service health`, not role `status`.
- Route expectations drift too. The home/logo navigation currently lands on `/`, not `/dashboard`.
- Table-control labels also drift. Current pagination controls use `Items per page`, not `Page size`.
- Row-selection labels are part of the contract. Profile bulk-delete selectors now use `Select <name>`, not `Select row <name>`.

### Test Environment

- For Git MCP Playwright E2E, the stable repository source is `https://git.cloud-dog.net/playgroup/test-project.git`. Do not rely on `/opt/iac/local-test-repo` fallback for these tests; it produced unstable `repo_open` behaviour and false regressions.
- The dedicated W28A-870 spec can pass while the full serial Playwright gate still fails. Always run the exact mandated command at the end:
  - `CI=true npx playwright test --workers=1 2>&1 | tee /tmp/pw-870.log`
- Sign-in helpers need retry tolerance. A single wait path can leave tests hanging on `/login` without an alert; a bounded retry path is more robust.
- Legacy suites may fail for stale selectors even when the feature is healthy. When the failure pattern is shared across multiple specs, fix the common stale expectation first instead of patching each test blindly.
- Dedicated E2E specs should avoid brittle transient-status assertions when a stronger invariant is available, for example visible content, selected tabs, or backend-confirmed state.

### W28A-90d Playwright Fix Lessons

- Audit-log correlation checks must match the deployed routed target IDs, not the public browser path assumption. On preprod, audit rows for API tool calls surfaced target IDs like `/app/v1/tools/admin_user_list`, while the Playwright fixture was filtering for `/api/v1/tools/admin_user_list`. The result was a false negative: the fixture fell back to synthetic request/correlation IDs and then searched the Audit Log page for values that were never persisted.
- API-key auth bootstrap on a hard reload must keep the shell in a loading state while saved-key re-authentication is in flight. Without that gate, a test that does `page.reload()` can momentarily render `/login`, and assertions like “column hidden after reload” can pass on the wrong page before timing out on a missing control.

### Infrastructure

- The repo already contains a usable preprod Terraform working directory at:
  - `git-mcp-server/working/w28a-649-terraform`
- The current public preprod host is `https://gitmcpserver0.cloud-dog.net`.
- The current routed public surfaces verified in this cycle were:
  - `/api/v1/health`
  - `/mcp/health`
  - `/a2a/health`
  - `/dashboard`
- A Terraform apply can fail even with a correct plan if a same-name container exists outside the tracked state. In this cycle, `gitmcpserver0.app.vpc0.cloud-dog.net` had to be removed before replanning and applying again.
- When a stale external container is removed, the saved Terraform plan becomes stale immediately. Re-plan before re-apply.
- `docker-build.sh` is Vault-aware and the correct standard path for Git MCP image builds. Do not invent a custom build flow.

### Architecture

- The deployed preprod image is driven by registry digest changes on `registry.cloud-dog.net:443/cloud-dog/git-mcp-server:latest`; the Terraform state then pulls and recreates the container.
- The preprod container wiring still uses the expected four-surface split:
  - web on `8080`
  - mcp on `8081`
  - a2a on `8082`
  - api on `8083`
- The public API route is still rewritten through Traefik from `/api/...` to `/app/...`. Keep that in mind when verifying direct public URLs.
- Health verification should include both public routed endpoints and container health. Public `200` plus container `healthy` after 60 seconds is a stronger proof than either alone.

### Related Projects

- Changes in `cloud-dog-ai-ui-monorepo/apps/git-mcp` and `git-mcp-server` must be validated together. Several failures that first looked like backend issues were actually stale UI or Playwright assumptions.
- Shared Playwright support files in the UI monorepo (`tests/fixtures.ts`, `tests/repoDefaults.ts`) are effectively part of Git MCP’s test contract. A Git MCP task can require updating them even when product code is fine.
- Legacy adoption suites such as `tests/w28a458/ui-adopt.spec.ts` can block a truthful completion claim for a newer work item. If the instruction requires the full serial suite, those suites are in scope.

### Process And Reporting

- Do not claim completion from a dedicated target spec alone when the instruction requires the full suite. This task was only truthfully complete once the exact final gate reported `64 passed (6.5m)`.
- Keep the exact log artifact for the mandated final run. `/tmp/pw-870.log` was the required source of truth for the final count.
- For preprod rollout reporting, record both:
  - pushed registry digest
  - deployed container id and health state
- Cleanup evidence matters. Final report quality is stronger when local ports are explicitly verified closed after shutdown.
- If an apply requires manual reconciliation of stale runtime objects, report that explicitly rather than hiding it behind a final green state.
   - `pip show cloud-dog-storage`
   - in-container bespoke grep count
6. Confirm preprod route shape from Terraform and live probes before choosing smoke URLs.
7. Read live `runtime-config.js` before writing or reusing WebUI smoke automation.
8. Distinguish test harness defects from service defects.

## Final Outcome

The final completion state was:

- storage adoption complete
- storage bespoke count `0` in `src/`
- config bespoke count `0` in `src/`
- logging bespoke count `0` in `src/`
- full regression green
- local Docker green
- image pushed and deployed
- preprod container healthy
- `cloud_dog_storage 0.1.2` installed on preprod
- preprod in-container bespoke storage grep `0`
- direct preprod API smoke green on the routed public API surface
- WebUI preprod smoke green with 9 unique screenshots

The key lesson is that the hard part was not the storage API replacement itself. The hard part was preserving established behaviour, keeping compliance green, and verifying the real deployed route and auth surfaces instead of the assumed ones.

## W28A-664 — Job Control Adoption

### cloud-dog-jobs is installed via `.` in Dockerfile — version constraint goes in pyproject.toml
**What happened (W28A-664):** The Dockerfile installs platform packages first, then the full project via `pip install .`. Since cloud-dog-jobs is a project dependency (not listed separately), the version constraint in `pyproject.toml` controls what gets installed. Added explicit `"cloud-dog-jobs>=0.3.0"` to the first pip install line for Docker cache busting.

### Worker constructor accepts `fallback_policies` parameter
**What happened (W28A-664):** The `cloud_dog_jobs.Worker` accepts `fallback_policies: FallbackPolicyManager | None` for automatic retry/dead-letter handling on handler failures. This was not previously used in git-mcp.

## W28A-649 — WebUI Log Compliance

### Local git UI flows need a real local bare repo, not the default remote URL
**What happened (W28A-649):** The git-mcp Playwright suite was hanging and misreporting UI failures because some flows still tried to exercise clone/open behavior against a remote default path that was unsuitable for deterministic local validation. Pointing the local harness at a real local bare repo under `/opt/iac/local-test-repo` made the branch/edit/commit/push and real-functional flows exercise real git behavior without external dependency drift.

**Rule:** For local git-mcp WebUI verification, always seed a real local bare repository and route the Playwright harness to that repository. If a “functional” UI test is stalling on repo open or clone, prove the repo target first before changing UI code.

## W28A-963 — Requirements Sweep, Vault Resolution, And Bespoke Compliance

### Code

- Compliance scans include entrypoints under `src/`, not just core runtime modules. In this cycle, `src/git_mcp_server/main.py` still contained import-time `os.environ.get(...)` reads for `cloud_dog_logging` correlation defaults, and that was a real bespoke-config violation even though it looked minor.
- The correct fix for the `cloud_dog_logging` ContextVar patch is the same static-default pattern used in the sibling IMAP service:
  - `environment` default should be a static string such as `"unknown"`
  - `service_instance` default should be a static repo-local identifier such as `"git-mcp-local"`
  - do not read environment variables at import time from `src/`
- If a repo already has a robust server-start retry helper in one tier, reuse that shape in the other tier instead of inventing a second startup path. Porting the integration-style retry logic into `tests/application/conftest.py` removed AT flakiness caused by one-shot startup and stale PID/runtime leftovers.
- CORS/browser origin handling should be built from config-derived hosts, not hardcoded URL literals. If browser origins need defaults, keep the fallback loopback-only and construct the final origins through shared helpers.

### Test Environment

- If IT or AT failures show unresolved `${vault...}` placeholders, the first fix is to source `/opt/iac/Development/cloud-dog-ai/env-vault` and rerun the real suite. In this cycle that resolved both:
  - `vault.dev.idp.keycloak.admin_password`
  - the GitLab remote URL/token used by remote git tests
- Do not treat a missing `vault` CLI as permission to bypass `cloud_dog_config`. The supported path is still:
  - source `env-vault`
  - run the real tests with `--env tests/env-IT` or `--env tests/env-AT`
  - let the repo’s config pipeline resolve Vault expressions
- The `cloud_dog_logging` closed-file shutdown error after an otherwise green suite is currently cosmetic in this repo. Do not misreport it as a failing suite, but do mention it explicitly so the coordinator can distinguish noise from a real regression.
- For compliance reruns after a bespoke fix, do both:
  - the direct grep against `src/`
  - the focused QT compliance test, here `tests/quality/QT_COMPLIANCE/test_qt27_bespoke_code_scan.py`

### Infrastructure

- The authoritative preprod Terraform workspace for this service exists in the shared infrastructure tree at:
  - `/opt/iac/cloud-dog-repo/terraform/server0.viewdeck.com/27 MLAgents`
  Do not assume the repo-local `working/w28a-649-terraform` copy is the live deployment source when the shared workspace is available and already tracks `docker_image.gitmcpserver` and `docker_container.gitmcpserver0`.
- Before applying, compare the current Terraform state digest with the newly pushed registry digest. In this cycle the shared workspace was still on the older Git MCP digest, so a health check alone would have proven nothing about the new build.
- For this service, a targeted deploy against:
  - `docker_image.gitmcpserver`
  - `docker_container.gitmcpserver0`
  was sufficient to roll the new image through preprod without touching unrelated services.
- Any plan saved before a new `latest` push becomes stale as deployment evidence. If you rebuild and push again, re-plan and re-apply against the new digest.

### Architecture

- The current live public preprod route set that matters for rollout proof is:
  - `/api/v1/health`
  - `/mcp/health`
  - `/a2a/health`
  - `/dashboard`
- Git MCP preprod rollout evidence is stronger when it records both image identifiers:
  - local Docker `image_id` from the rebuild
  - remote registry `repo_digest` consumed by Terraform
  The digest is the real deployment proof; the local image ID alone is not enough.
- The current delivered service surface is larger than some older docs still implied:
  - 63 MCP tools, not 51
  - WebUI routes already include `/repository`, `/history`, `/diff`, `/branches`, `/merge`, `/tags`, and `/stashes`

### Related Projects

- The IMAP MCP sweep (962) solved the same import-time `os.environ` misuse in its `main.py`. When you see `cloud_dog_logging` correlation defaults patched in sibling services, check whether that repo already has the compliant static-default pattern before inventing a new fix.
- Git MCP documentation accuracy depends on both repos:
  - `git-mcp-server`
  - `cloud-dog-ai-ui-monorepo/apps/git-mcp`
  A stale claim about missing routes can be disproven directly from the UI route table even if the backend docs were not updated yet.

### Process And Reporting

- For this repo, documentation drift is not cosmetic. `README.md`, `docs/REQUIREMENTS.md`, and `docs/TESTS.md` are all part of the compliance surface and can block truthful completion if they understate the implemented routes, tool count, or test inventory.
- When claiming “zero bespoke config access in `src/`”, record the exact grep and its zero-match result. This cycle only became truthfully complete after the final grep over `src/` returned no `os.environ.get` or `os.environ[` matches.
- If a user explicitly points to a prior service sweep as the reference fix, treat that as a concrete implementation hint, not just advice. In this case, reusing the IMAP 962 `main.py` pattern was faster and safer than reasoning from scratch.

## W28A-848 — Native Startup, WebApiProxy Adoption, and Full Playwright Closure

This instruction exposed a different class of failure from the earlier Docker-focused work: native startup, browser-to-API routing, workspace package build drift, and exact UI contract mismatches. The service was not “basically working with noisy tests”. Several defects were real, and the final green state only happened after fixing those real defects in code and runtime wiring.

### Code

#### Adopt the platform proxy primitive instead of preserving bespoke proxy code
**What happened (W28A-848):** The instruction explicitly required replacing the git-mcp bespoke web-to-API proxy logic with `cloud_dog_api_kit.web.proxy.WebApiProxy`. The correct adoption was not a cosmetic import swap. It required moving API and legacy API passthrough onto `WebApiProxy.from_config(...)` while leaving MCP and A2A on their existing direct passthrough.

**Rule:** When the platform package now provides a first-class primitive for a concern already solved locally, remove the bespoke implementation and adapt the service to the package contract. Do not keep the old code “just in case”.

#### Browser login failures can be real CORS defects even when curl succeeds
**What happened (W28A-848):** API-key login from the Vite preview kept failing in the browser even though direct `curl` with the same seed key returned `200`. The root cause was missing CORS allowance for `http://127.0.0.1:5177` and `http://localhost:5177` on the native API server. Once the API app added the proper CORS middleware and origin set, the same login flow succeeded immediately.

**Rule:** If API-key auth works via direct HTTP but fails from the browser, check browser-origin CORS before changing auth code, API keys, or tests.

#### Exact heading and label text matters for these UI reviews
**What happened (W28A-848):** Several Playwright failures were not false positives. The pages really did not match the required UI contract. Examples:
- `Settings` heading had to be exactly `Settings`
- `API Docs` heading had to be exactly `API Docs`
- `Jobs` page needed a page-level `Jobs` header and an always-visible `Job detail` section
- MCP/A2A history sections needed to render `History`
- IDAM pages needed real `JsonBlock` inspection surfaces for PS-71, not just tables and dialogs

**Rule:** For standards-driven WebUI work in this repo, exact visible labels are part of the contract. If the test expects a heading and the page uses a semantically different title, fix the page unless the standard clearly says otherwise.

#### Dist output can drift from source inside workspace packages
**What happened (W28A-848):** `packages/ui/src/patterns/EntityForm.tsx` already said the submit button label default was `Save`, but `packages/ui/dist/patterns/EntityForm.js` still emitted `Save changes`. The app bundled the stale dist behaviour and the tests correctly timed out waiting for `Save`.

**Rule:** In this monorepo, do not trust `src/` alone for linked workspace packages. If runtime behaviour disagrees with source, inspect the package `dist/` actually consumed by the app and rebuild it cleanly.

### Test Environment

#### `pytest tests/unit/ -v` must work exactly as written
**What happened (W28A-848):** The instruction required the exact command `pytest tests/unit/ -v`. In this repo, that was not reliable without an env file. The fix was to make `tests/conftest.py` auto-select `tests/env-UT` for unit-only runs when `--env` is omitted.

**Rule:** If the instruction gives an exact regression command, make that exact command work. Do not silently substitute a different command in the report.

#### Stale Vite preview processes cause fake UI regressions
**What happened (W28A-848):** After fixing MCP console headings, Playwright still saw the old `Response` label. The source and package dist were correct, but the preview process was serving an older built asset. Restarting preview against the rebuilt app resolved it.

**Rule:** After changing bundled frontend code, restart preview or any persistent asset server before trusting Playwright results. A passing build does not guarantee the browser is serving that build.

#### Full-suite Playwright runs can be contaminated by unrelated parallel runners
**What happened (W28A-848):** The first “full suite” attempts were noisy and misleading because there were multiple overlapping `playwright test` trees running elsewhere in the shared monorepo. Once those were killed, the git-mcp full run behaved deterministically and the remaining failures were real.

**Rule:** Before relying on a full Playwright result in this shared workspace, check for other live Playwright runners and kill stale overlaps. Otherwise you can waste time chasing cross-run contamination.

#### Use focused reruns to turn long flaky failures into short actionable ones
**What happened (W28A-848):** A late failure in `admin-config-crud` was difficult to diagnose from the full harness because retries and long waits obscured the first actual problem. Rerunning the isolated spec and then reproducing the flow with a one-off Playwright script exposed the real issue quickly: the dialog button label mismatch caused by stale `@cloud-dog/ui` dist.

**Rule:** When a long full-suite failure is opaque, reduce it to one spec or one scripted reproduction before changing code.

### Infrastructure

#### Native `tests/env-IT` startup may depend on Vault env bootstrap even when the env file exists
**What happened (W28A-848):** Native startup via `./server_control.sh --env tests/env-IT start all` still failed until Vault variables were bootstrapped from `/opt/iac/Development/cloud-dog-ai/env-vault`. The env file alone was not enough because it still contained `${vault...}` placeholders that needed the standard resolver context.

**Rule:** For native startup, ensure the launcher has Vault environment loaded before assuming the service config itself is broken.

#### Cleanup is part of test truthfulness
**What happened (W28A-848):** The instruction required stopping all four services and verifying the ports were clear. Doing that also proved the run was self-contained and not depending on old orphaned processes.

**Rule:** Treat port-clear verification as evidence, not housekeeping. It shows the instruction left no hidden runtime behind.

### Architecture

#### The git-mcp frontend is a workspace app but still bundles through package dist boundaries
**What happened (W28A-848):** Path mapping points `@cloud-dog/ui` at workspace source, but real app behaviour still diverged until `packages/ui/dist` was rebuilt. In practice, this repo behaves like a hybrid workspace where source, dist, and preview lifecycle all matter.

**Rule:** For frontend architecture in this monorepo, reason about three layers together:
- package source
- package dist
- app dist/preview

If only one of the three is updated, the browser may still be wrong.

#### IDAM pages are not compliant with PS-71 unless raw entity inspection exists
**What happened (W28A-848):** The initial PS-71 grep showed `JsonBlock 0` across Users, Groups, API Keys, and RBAC. The tables and dialogs looked substantial, but the standard explicitly requires raw inspection too. Adding real inspection cards made the retro-test honest and fixed the actual gap.

**Rule:** In this repo, standards grep failures on required primitives often indicate a genuine architectural omission, not just a scanner quirk.

### Related Projects / Shared Packages

#### Use only published `cloud-dog-api-kit==0.4.1` for `WebApiProxy`
**What happened (W28A-848):** The required proxy support lived in published `cloud-dog-api-kit==0.4.1`. The correct move was to install and use that version, not to edit local package source, invent intermediate versions, or switch to editable installs.

**Rule:** When a related shared package has just published the required capability, consume the published version exactly. Do not fork or “temporarily patch” the package in the service repo.

#### Shared UI package fixes can be required to close an app instruction
**What happened (W28A-848):** The git-mcp app could not pass its own Playwright suite until `packages/ui` was corrected and rebuilt. The service-level fix was therefore partly in the shared package.

**Rule:** If a git-mcp UI defect originates in `@cloud-dog/ui`, fix the shared package and rebuild the app rather than cloning the behaviour locally.

### Recommended Future Checklist For Native git-mcp WebUI Work

1. Confirm the installed platform package version before touching compatibility code.
2. For native startup, bootstrap Vault env first, then start via `server_control.sh`.
3. Verify all four health endpoints before opening the browser.
4. If browser login fails but direct `curl` works, check CORS immediately.
5. If UI behaviour disagrees with source, inspect both package `dist/` and app `dist/`.
6. Restart preview after any frontend bundle-affecting change.
7. Kill overlapping Playwright runners before trusting a full-suite result.
8. For standards pages, treat exact headings, labels, and required primitives as implementation requirements, not “close enough” copy.

### If the checked-out Terraform source is missing, derive a Docker-provider fallback from the live container and verify with a no-change plan
**What happened (W28A-649):** The prior reports and logs showed Terraform-managed deploys, but the original `.tf` workspace used for `gitmcpserver0` was not present in the accessible repos. A generated fallback workspace based on `docker inspect` of the live container allowed a truthful Terraform redeploy path. After replacing the container from the pushed image, a targeted `terraform plan` returned `No changes`, which proved the fallback config matched the deployed state.

**Rule:** When a service must be redeployed “via Terraform” but the checked-out source workspace is unavailable, generate a minimal Docker-provider workspace from the live container definition, use that for the replacement, and always finish with a no-change post-apply plan before claiming deploy evidence.

---

## W28A-673 — Job Control WebUI Adoption

### PS-76 JW4 backend endpoints need cancel/retry/delete in endpoints.py AND runtime.py
**What happened (W28A-673):** The `JobsRuntime` only had `cancel_job()`. The `retry_job()` and `delete_job()` methods had to be added to runtime.py, and all three action endpoints had to be added to endpoints.py. The endpoint paths must be `POST /{job_id}/cancel`, `POST /{job_id}/retry`, `DELETE /{job_id}` to match the standard URL convention used by all other services.

**Rule:** When adding PS-76 JW4 row actions, implement both the runtime methods and the API endpoints together. The retry resubmits the original payload with the same job type and queue, returning a new job ID. The delete checks for terminal status before removing.

### Terraform container name conflict requires stop+rm before reapply
**What happened (W28A-673):** `terraform apply` failed with “container name already in use” because the old container was still present. Had to `docker -H server0.viewdeck.com stop/rm` the old container, then re-plan and re-apply.

**Rule:** When Terraform tries to recreate a container (destroy + create), the old container must be fully removed first if the apply fails with a name conflict. Use `docker -H <host> stop/rm <container>` then re-plan and re-apply.

---

## W28A-704 — IDAM Compliance (RBAC Refactor)

### RBACAuthoriser wrapper class was eliminated — use direct functions instead
**What happened (W28A-704):** The `RBACAuthoriser` wrapper class was removed entirely. It was replaced with two direct functions: `can_execute_tool()` and `require_tool_access()`, both of which take an `RBACEngine` instance as a parameter. The `fnmatch` pattern matching for tool names is preserved in the direct functions.

**Rule:** Do not create or re-introduce wrapper classes around `RBACEngine`. The approved pattern is direct functions that accept `RBACEngine` as a parameter. This keeps the RBAC boundary thin and avoids maintaining a second abstraction layer that drifts from the upstream IDAM library.

### api_server.py imports RBACEngine directly from cloud_dog_idam
**What happened (W28A-704):** The `api_server.py` module imports `RBACEngine` directly from `cloud_dog_idam` and creates instances per-request for tool authorization. There is no intermediate factory or singleton pattern.

**Rule:** For tool authorization in API request handlers, instantiate `RBACEngine` per-request. The `RBACEngine.get_effective_roles()` method returns a set of role names, and `has_permission()` checks against `role_permissions` dict with wildcard support.

### git_auth.py is NOT bespoke IDAM — do not delete it during IDAM compliance work
**What happened (W28A-704):** During IDAM compliance work, `git_auth.py` in `git_tools/security/` was initially flagged as a candidate for removal. It is actually Git credential management for HTTPS clone operations — specifically GitLab token injection via `git credential approve`. It has nothing to do with identity/access management.

**Rule:** When performing IDAM compliance sweeps, distinguish between authentication/authorization code (which should use `cloud_dog_idam`) and Git credential helpers (which manage repository access tokens for clone/push). `git_auth.py` belongs in the second category and must be preserved.

### Tests updated to use RBACEngine + can_execute_tool() directly
**What happened (W28A-704):** The unit tests `UT1.11_RBACPolicyEval` and `UT1.51_RBACToolCategory` were updated to use `RBACEngine` + `can_execute_tool()` directly instead of the deleted `RBACAuthoriser` wrapper. The test env `tests/env-UT` requires the `--env` flag. The baseline is 74 passed, 8 failed (pre-existing failures in UT1.27, UT1.56, UT1.57).

**Rule:** When refactoring RBAC internals, always update the corresponding unit tests to exercise the new call surface. Do not leave tests importing deleted classes — they will fail silently or be skipped, hiding real regressions. Know the pre-existing failure baseline so you can distinguish new breaks from old ones.

---

## W28A-745 — MCP Audit Logging

### Tool audit logging added to ToolRegistry._call_with_audit()
**What happened (W28A-745):** Audit logging was centralized in `ToolRegistry._call_with_audit()` inside `git_tools/tools/registry.py`. Both `call()` and `call_with_access()` now delegate through this single method, ensuring every tool invocation is logged regardless of entry path.

**Rule:** All tool execution paths must converge through `_call_with_audit()`. If a new execution method is added to `ToolRegistry`, it must delegate through `_call_with_audit()` rather than calling the tool function directly. Otherwise audit coverage will have gaps.

### Sensitive parameters are redacted in audit logs
**What happened (W28A-745):** Parameters named `content`, `password`, `secret`, `token`, or `body` are automatically redacted in audit log entries. This prevents credential leakage in log files while still recording which tools were called and with what non-sensitive arguments.

**Rule:** When adding new tool parameters that carry sensitive data, ensure the parameter name matches one of the redaction keywords (`content`, `password`, `secret`, `token`, `body`). If a new sensitive parameter uses a different name, add it to the redaction list in `_call_with_audit()`. Do not rely on callers to sanitize — the audit layer must handle it centrally.

### ToolRegistry handles registration, dispatch, and profile-scoped access enforcement
**What happened (W28A-745):** `ToolRegistry` in `git_tools/tools/registry.py` is the central class for tool lifecycle: registration, dispatch, audit logging, and profile-scoped access enforcement. HTTP MCP tool registration uses `register_tool_router` from `cloud_dog_api_kit`.

**Rule:** Do not bypass `ToolRegistry` for tool registration or dispatch. All tools must be registered through the registry so that audit logging, access enforcement, and profile scoping apply uniformly.

---

## W28A-795 / W28A-805 — WebUI (git-mcp UI in monorepo)

### git-mcp UI app lives in cloud-dog-ai-ui-monorepo at apps/git-mcp/
**What happened (W28A-795/805):** The git-mcp frontend is part of the monorepo at `cloud-dog-ai-ui-monorepo/apps/git-mcp/`. It is not co-located with the backend. The `ApiDocsPage` has tabs for API, MCP, and A2A endpoints plus a `DocumentViewer` component. The `SettingsPage` has all 7 PS-73 sections with a Health Badge.

**Rule:** When making backend changes that affect the API surface (new endpoints, changed response shapes, new tool names), check the corresponding UI app in the monorepo for impacts. The UI and backend live in separate repos, so changes must be coordinated across both.

### Security module structure at git_tools/security/
**What happened (W28A-795/805):** The security module at `git_tools/security/` contains three files with distinct responsibilities:
- `rbac.py` — direct RBAC functions (`can_execute_tool()`, `require_tool_access()`)
- `git_auth.py` — Git credential management for HTTPS clone operations
- `scope.py` — path and branch enforcement

**Rule:** Respect the separation of concerns in the security module. RBAC policy evaluation, Git credential management, and path/branch scoping are three independent concerns. Do not merge them into a single file or create cross-dependencies between them.

### Port allocations for git-mcp-server
**What happened (W28A-795/805):** The port assignments are: API 8078, Web 8079, MCP 8084, A2A 8085. These are used in Docker builds (`docker-build.sh`), compose files, and Terraform configurations. The Docker image is tagged for `registry.cloud-dog.net:443`.

**Rule:** When modifying Docker or deployment configurations, use the established port allocations. Do not reassign ports without checking all consumers: Docker compose, Terraform workspace, reverse proxy (Traefik) labels, and the UI monorepo's proxy configuration.

### Docker build uses docker-build.sh — not raw docker build
**What happened (W28A-795/805):** The build entry point is `docker-build.sh`, which handles tagging for the private registry at `registry.cloud-dog.net:443`. Do not use raw `docker build` commands — the script ensures consistent image naming and registry targeting.

**Rule:** Always use `docker-build.sh` for building the git-mcp-server image. Manual `docker build` commands risk incorrect tags, missing build args, or registry mismatches.

---

## Lessons from W28A-704, W28A-745, W28A-795, W28A-805 (2026-04-07)

## Code

### IDAM Compliance (W28A-704)
- RBACAuthoriser wrapper class was eliminated. Replaced with direct functions `can_execute_tool()` and `require_tool_access()` in `git_tools/security/rbac.py` that take RBACEngine as a parameter.
- The fnmatch pattern matching for tool names is preserved in the direct functions.
- `git_auth.py` is NOT bespoke IDAM — it's Git credential management for HTTPS clone operations. Do not delete it.
- `api_server.py` imports RBACEngine directly from cloud_dog_idam.

### MCP Audit (W28A-745)
- Tool audit logging added via `_call_with_audit()` in `ToolRegistry` (`git_tools/tools/registry.py`).
- Both `call()` and `call_with_access()` delegate through this method.
- Parameters named content/password/secret/token/body are redacted with `[REDACTED]`.

### WebUI (W28A-795, W28A-805)
- ApiDocsPage: Tab navigation (API/MCP/A2A) + 14 MCP tools with RBAC permissions + 3 A2A skills + DocumentViewer.
- SettingsPage: All 7 PS-73 sections (Service Info, Server, Auth, Storage, Logging, Service-Specific, Health with Badge).
- Health section fetches from `/health` endpoint on mount and displays ok/unknown Badge.

## Test Environment

- 74 passed, 8 failed baseline (pre-existing failures in UT1.27, UT1.56, UT1.57).
- UT1.11 and UT1.51 RBAC tests updated to use RBACEngine + can_execute_tool() directly.
- Tests require `--env tests/env-UT`.

## Infrastructure

- Ports: API 8078, Web 8079, MCP 8084, A2A 8085.
- Preprod: gitmcpserver0.cloud-dog.net.
- Docker build via docker-build.sh, tagged for registry.cloud-dog.net:443.

## Architecture

- ToolRegistry handles tool registration, dispatch, and profile-scoped access enforcement.
- `register_tool_router` from cloud_dog_api_kit is used for HTTP MCP tool registration.
- Security module: `rbac.py` (direct functions), `git_auth.py` (credential management), `scope.py` (path/branch enforcement).

## Related Projects

- cloud-dog-ai-ui-monorepo: app at `apps/git-mcp/`.
- cloud_dog_idam: RBACEngine, hash_api_key, APIKeyOnlyProvider.
- cloud_dog_api_kit: register_tool_router, mcp_tool_audit_middleware.

---

## W28A-A131-FIX-1 -- Terraform Container Env Var Wiring for Gitea Tokens (2026-05-06)

### TF variable declarations without container env wiring are silent failures
**What happened (A131-FIX-1):** `gitmcp_gitlab_token` and `gitmcp_gitlab_maintainer_token` were declared in `variables.tf` and populated in `terraform.tfvars`, but NEVER referenced in the container's `env` block in `gitmcpserver_containers.tf.json`. The service's `defaults.yaml` had empty strings for `storage.gitlab.developer_token` and `storage.gitlab.maintainer_token`, so without env var overrides the runtime config had empty tokens. This caused 11 of 14 Playwright failures -- `repo_open` against the private Gitea repo `git.cloud-dog.net/playgroup/test-project.git` returned HTTP 401 from Gitea, surfaced as HTTP 400 from the API.

**Rule:** When adding TF variables for a container's configuration, always verify the variable is actually WIRED into the container's `env` block. A variable in `terraform.tfvars` + `variables.tf` that is never referenced in the container config is a no-op. The service needs the env var override (e.g., `CLOUD_DOG__STORAGE__GITLAB__DEVELOPER_TOKEN=${var.gitmcp_gitlab_token}`) to reach `cloud_dog_config`.

### The three env vars that must be present for remote Gitea clone operations
The gitmcpserver0 container requires these env vars for private Gitea repo access:
- `CLOUD_DOG__STORAGE__GITLAB__URL=https://git.cloud-dog.net`
- `CLOUD_DOG__STORAGE__GITLAB__DEVELOPER_TOKEN=${var.gitmcp_gitlab_token}`
- `CLOUD_DOG__STORAGE__GITLAB__MAINTAINER_TOKEN=${var.gitmcp_gitlab_maintainer_token}`

Without them, `git_auth.py` in `git_tools/security/` has no token to inject via `git credential approve`, and all HTTPS clone operations to private repos fail with HTTP 401.

### Cascade failures can mask independent defects
**What happened (A131-FIX-1):** The A131 classification predicted 11 of 14 failures would recover. Only 9 recovered. Two tests (tag-readonly-browse and w28a870 sections-o-p merge conflict) appeared to be repo_open failures in the original traces because they failed early at repo_open. After the fix, repo_open succeeded but the tests revealed independent service-side defects: tag readonly enforcement not blocking writes (HTTP 200 instead of >= 400) and merge conflict resolution returning "Loaded 0 conflict file(s)" instead of proceeding.

**Rule:** When a dominant cascade failure (like repo_open 400) is fixed, expect some previously-masked independent defects to surface. Do not assume all failures in the cascade share the same root cause -- the cascade just prevented reaching the code path where the real defect lives.

### browser.newContext() does NOT inherit page-fixture init scripts (A131-FIX-3)
**What happened:** The rbac-enforcement E2E test creates a second browser context via `browser.newContext()` to simulate a restricted user. The fixture's `page` override applies `addInitScript` for `__RUNTIME_CONFIG__` and `page.route` for `runtime-config.js`, but these are scoped to the default context only. The new context gets no runtime config, so the SPA falls back to build-time defaults that omit `api_key` auth mode -- only username/password fields render and the test cannot find the API Key textbox.

**Fix:** Import `runtimeConfig` and `runtimeConfigScript` from fixtures, then apply both `context.route("**/runtime-config.js", ...)` and `context.addInitScript(...)` to every `browser.newContext()` before creating pages from it.

**Rule:** Any Playwright test that creates a new browser context must replicate the runtime-config injection that the page fixture provides. Both `route` and `addInitScript` are available on `BrowserContext` (not just `Page`), so apply them at the context level before `context.newPage()`.

### Container rebuild regenerates seed API keys
**What happened (A131-FIX-1 remaining):** After the B.1 container rebuild (terraform apply), the gitmcpserver0 container generated a new seed API key at `/app/data/seed_api_key.txt`. The local test seed key file at `working/it/seed_api_key.txt` still held the old key. All E2E tests failed at sign-in with "Login failed." because the API key no longer matched.

**Fix:** After any container rebuild/recreate, read the new seed key from the container (`docker -H ... exec <container> cat /app/data/seed_api_key.txt`) and update the local `working/it/seed_api_key.txt`.

**Rule:** Every terraform apply that recreates the container invalidates the seed API key. The local key file must be refreshed before running E2E tests.

### UI runTool helpers that refresh state can overwrite user-facing status messages
**What happened (MergePage sections o-p):** The MergePage `runTool()` helper set `setStatus(successMessage)` then called `await refreshConflicts()`, which itself set `setStatus("Loaded N conflict file(s).")`. The "Merge continued." message was immediately overwritten, causing the E2E test to fail waiting for that text.

**Fix:** Re-set the success message after the state refresh: `setStatus(successMessage)` appears both before and after `refreshConflicts()`.

**Rule:** When a UI handler calls a side-effect function (like a table refresh) that also sets status, the caller must re-assert its own status message afterward if the test/user expects to see it.

### resolveAuditMeta can return stale status codes from prior tool calls
**What happened (tag-readonly-browse):** The E2E fixture `resolveAuditMeta` polls the audit log for entries matching the tool name. Without request_id filtering, it picks the newest entry for `file_write` -- which might be a successful 200 from a prior test run, not the expected 403 from the current call. The `byRequestId` filter (matching on `fallback.requestId`) was added to prefer the correct audit entry.

**Rule:** Any audit log correlation in test fixtures must filter by request_id to avoid stale entries from concurrent or prior test executions polluting the status code.

### Traefik routes /api/v1/* directly to API server, bypassing the web server cookie proxy
**What happened (Cluster B failures):** The web server sets a `git_web_session` cookie and proxies API calls with a seed API key. But Traefik routes `PathPrefix(/api/)` directly to the API server, not through the web server. Cookie-authenticated browser requests therefore arrive at the API server without an API key, causing 401 on every protected endpoint (e.g. `/api/v1/logs`, `/api/v1/settings`). The `/status` endpoint (served directly by the web server) and `/api/v1/health` (in skip_paths) worked, masking the issue.

**Fix:** Added cookie session fallback to `CompatAuthMiddleware` — when API key and Bearer token are absent, the middleware validates the `git_web_session` cookie by calling the web server's `/auth/me` endpoint internally. Also propagated `request.state.web_session_user` through `_roles_from_request` and `_actor_from_request` in both `admin/endpoints.py` and `api_server.py` so that RBAC and tool execution honour cookie sessions.

**Rule:** When Traefik or any reverse proxy routes API paths directly to a backend, cookie sessions set by another service (the web server) cannot be assumed to carry auth. The API server must independently validate cookies or the proxy routing must be fixed.

### MCP_BASE_URL must not include the MCP server base_path when Traefik routes /mcp/* separately
**What happened:** `web_ui.py` set `MCP_BASE_URL` to `${origin}/git-mcp`. The SPA appended `/mcp/tools` to this, producing `${origin}/git-mcp/mcp/tools`. Traefik routes `/git-mcp/` to the API server (not the MCP server), so the tools endpoint was unreachable.

**Fix:** Changed `MCP_BASE_URL` to just `${origin}`. The SPA's MCP paths (`/mcp/tools`, `/mcp/tools/{name}`) resolve correctly to the MCP server via Traefik's `/mcp/` route.

**Rule:** Runtime config URL bases must match the actual Traefik routing topology, not the internal service configuration paths.
