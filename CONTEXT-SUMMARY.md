# git-mcp-server — Context Summary

**Last updated:** 2026-03-30  
**Status:** Active handoff summary for agent change  
**Current repo state:** Dirty worktree is the authorised baseline from multiple completed W28A instructions; latest completed instruction in this turn is `W28A-511`

---

## Latest Completed Instruction

### W28A-511 — Fix git-mcp E2E Gaps

Instruction:
- `cloud-dog-ai-platform-standards/working/AGENT-INSTRUCTION-W28A-511-FIX-GITMCP-E2E-GAPS.md`

Verdict:
- `PASS`

What was delivered:
- Added dedicated real-remote IT coverage for `git_fetch`:
  - `tests/integration/IT1.16_RemoteFetchRealRemoteRefs/test_remote_fetch_real_remote_refs.py`
- Fixed `git_fetch` so it returns the actual verbose fetch transcript instead of an empty string:
  - `src/git_tools/git/repo.py`
- Added focused UT protection for fetch output:
  - `tests/unit/UT1.41_GitPull/test_git_pull.py`
- Updated traceability mappings:
  - `src/git_mcp_server/traceability_requirements.py`
- Updated test inventory:
  - `docs/TESTS.md`

Authorised remote used:
- `https://git.cloud-dog.net/playgroup/test-project.git`

Focused evidence:
- `working/w28a-511-new-test-results.txt`
- Captured real fetch proof in that log:
  - `POST git-upload-pack (155 bytes)`
  - `From https://git.cloud-dog.net/playgroup/test-project`
  - `* [new branch] main -> origin/main`

Regression results:
- `QT`: `58 passed`
- `UT`: `77 passed`
- `ST`: `19 passed`
- `IT`: `21 passed, 1 warning`
- `AT`: `9 passed, 1 warning`

Evidence logs:
- `working/w28a-511-qt-results.txt`
- `working/w28a-511-ut-results.txt`
- `working/w28a-511-st-results.txt`
- `working/w28a-511-it-results.txt`
- `working/w28a-511-at-results.txt`

Deploy performed because code changed:
- Image: `registry.cloud-dog.net:443/cloud-dog/git-mcp-server:latest`
- Digest: `sha256:e5b729093bfe0b279035cd2821a4911e03afe7b9712b8b7d5d01d01066b36220`
- New preprod container: `9fc9a4cb1d6e8974ad192780e8bde35a3ce5cf3b82c2997450fd6e16ad41047b`

Deploy evidence:
- `working/w28a-511-docker-build.log`
- `working/w28a-511-docker-push.log`
- `working/w28a-511-terraform-plan.log`
- `working/w28a-511-terraform-apply.log`
- `working/w28a-511-preprod-health-checks.txt`

Live health after deploy:
- `GET /health -> 200`
- `GET /api/v1/health -> 200`
- `GET /api/health -> 404`
- `GET /app/v1/health -> 401`

Report:
- `working/W28A-511-FIX-E2E-GAPS-REPORT.md`

Important execution note:
- During W28A-511, one intermediate QT rerun failed because `IT1.16` appeared twice in `docs/TESTS.md`; fixed immediately and the full tier order was rerun from `QT`.
- Two isolated diagnostic reruns were invalid because Vault env was not sourced; they were discarded and rerun correctly with `set -a; source /opt/iac/Development/cloud-dog-ai/env-vault; set +a`.
- The valid evidence set is the final `W28A-511` logs listed above.

---

## Prior Major Completed Instruction

### W28A-489 — UI Review #2 Adoption: git-mcp-server

Verdict:
- `PASS`

Summary:
- Adopted UI-R11 through UI-R25 into backend + UI app
- Local Playwright: `25 passed`
- Preprod Playwright: `25 passed`
- Backend tiers at completion:
  - `QT 58 passed`
  - `UT 76 passed`
  - `ST 19 passed`
  - `IT 20 passed, 1 warning`
  - `AT 9 passed, 1 warning`
- Image pushed at that time:
  - `registry.cloud-dog.net:443/cloud-dog/git-mcp-server:latest`
  - digest superseded later by W28A-511

Key report:
- `working/W28A-489-UI-REVIEW2-GIT-MCP-REPORT.md`

Key fix from that work:
- Preprod Traefik route narrowing was applied in Terraform so SPA routes such as `/api-keys`, `/api-docs`, `/mcp-console`, and `/a2a-console` stop being hijacked by transport path prefixes.

---

## Current Active File Changes In This Repo

The worktree is intentionally dirty and authorised as baseline. `git status --short` currently includes, among others:

Tracked modifications:
- `Dockerfile`
- `defaults.yaml`
- `docs/API-REFERENCE.md`
- `docs/MCP-REFERENCE.md`
- `docs/TESTS.md`
- `pyproject.toml`
- `server_control.sh`
- `src/git_mcp_server/a2a_server.py`
- `src/git_mcp_server/admin/endpoints.py`
- `src/git_mcp_server/api_server.py`
- `src/git_mcp_server/traceability_requirements.py`
- `src/git_mcp_server/web_server.py`
- `src/git_mcp_server/web_ui.py`
- `src/git_tools/config/models.py`
- `src/git_tools/git/repo.py`
- `src/git_tools/security/git_auth.py`
- `tests/application/conftest.py`
- `tests/env-AT`
- `tests/env-IT`
- `tests/env-IT-local-docker`
- `tests/env-IT-local-server`
- `tests/integration/IT1.14_AdminCrudParity/test_admin_crud_parity.py`
- `tests/unit/UT1.1_ConfigLoaderPrecedence/test_config_loader_precedence.py`
- `tests/unit/UT1.2_ConfigVaultIntegration/test_config_vault_integration.py`
- `tests/unit/UT1.41_GitPull/test_git_pull.py`
- `tests/unit/UT1.56_WebUiDelivery/test_web_ui_delivery.py`

Untracked additions:
- `LICENCE`
- `forensic-data/`
- `src/git_mcp_server/http_client.py`
- `src/git_mcp_server/ui_endpoints.py`
- `tests/env-FORENSIC-WEB`
- `tests/integration/IT1.16_RemoteFetchRealRemoteRefs/`
- `tests/unit/UT1.57_UiSupportEndpoints/`
- `vendor/wheels/cloud_dog_config-0.3.1-py3-none-any.whl`
- `vendor/wheels/cloud_dog_logging-0.3.1-py3-none-any.whl`

Do not treat these as unexpected drift. This is the authorised baseline from prior instructions.

---

## Rules/Execution Notes For Next Agent

Mandatory patterns repeatedly enforced in this repo:
- Read both:
  - `RULES.md`
  - `/opt/iac/Development/cloud-dog-ai/cloud-dog-ai-platform-standards/RULES.md`
- Source Vault before any IT/AT/server/deploy work:
  - `set -a; source /opt/iac/Development/cloud-dog-ai/env-vault; set +a`
- Every pytest invocation must include `--env <correct-env-file>`
- Use `./server_control.sh --env <env-file> ...`
- Use `bash docker-build.sh` for builds
- Use Terraform only for preprod container redeploys; no firewall/network shell commands, no SSH

Known contract/path facts:
- Local IT/AT canonical API path is `/app/v1`
- Live preprod still exposes `GET /health -> 200`
- Live authenticated API health is `GET /api/v1/health -> 200`
- `GET /app/v1/health` on preprod is auth-protected and returns `401`
- Authorised remote prefix for real git integration tests:
  - `https://git.cloud-dog.net/playgroup/`

---

## Reports Produced Recently

- `working/W28A-511-FIX-E2E-GAPS-REPORT.md`
- `working/W28A-489-UI-REVIEW2-GIT-MCP-REPORT.md`
- `working/W28A-481-REAL-TEST-GIT-MCP-REPORT.md`
- `working/W28A-458-UI-ADOPT-GIT-MCP-REPORT.md`
- `working/W28A-448-FORENSIC-GIT-MCP-REPORT.md`

---

## Immediate Handoff State

- Latest validated deploy in preprod is from `W28A-511`
- No git commit or push was done in the last turn
- Repo root `CONTEXT-SUMMARY.md` was created in this turn because only `archive/CONTEXT-SUMMARY.md` previously existed
- Next agent should start from this root summary, not the archived one
