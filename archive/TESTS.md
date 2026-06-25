# git-mcp-server — Test Plan

**Version:** 1.1  
**Date:** 2026-03-01  
**Standard:** PS-95  
**Total tests:** 53 UT + 12 ST + 13 IT + 7 AT + 14 QT = 99

---

## Latest W25A-B Status (2026-03-09)

- Instruction file used:
  - `cloud-dog-ai-platform-standards/working/AGENT-INSTRUCTION-W25A-B-FIX-CONFIG-BURNDOWN.md`
- Config drift remediation completed:
  - removed obsolete keys from `tests/env-*`:
    - `CLOUD_DOG__WORKSPACE__BASE_DIR`
    - `GIT_MCP_REMOTE_CLONE_DEPTH`
    - `GIT_MCP_REQUEST_TIMEOUT_SECONDS`
- Strict command summaries:
  - `python3 -m pytest tests/quality --env tests/env-QT -q -rs` -> `30 passed`
  - `python3 -m pytest tests/unit --env tests/env-UT -q -rs` -> `29 passed`
- Evidence paths:
  - `working/w25ab-config-git-qt-after.log`
  - `working/w25ab-config-git-ut-after.log`
  - `working/W25A-B-FIX-CONFIG-BURNDOWN-REPORT.md`

## Latest W15B-04 Status (2026-03-02)

- Instruction file used:
  - `cloud-dog-ai-platform-standards/working/AGENT-INSTRUCTION-W15B-04-GIT-MCP-COMPLIANCE-REVALIDATE-STRICT.md`
- Mandatory precheck:
  - canonical loader present in `src/git_tools/config/loader.py` (`load_config(` detected)
  - no fail-open `${vault... || ...}` patterns and no `sk-or-v1-*` tokens in `tests/env-*`
  - Result: `bad_env_files 0`
- Runtime ensure:
  - `bash local-docker-server.sh --env tests/env-local-docker-server ensure` -> already running healthy with matching env
- Strict backend command summaries:
  - `python3 -m pytest tests/unit/ --env tests/env-UT-local-docker -q` -> `27 passed`
  - `python3 -m pytest tests/system/ --env tests/env-ST-local-docker -q` -> `10 passed`
  - `python3 -m pytest tests/integration/ --env tests/env-IT-local-docker -q` -> `12 passed`
  - `python3 -m pytest tests/application/ --env tests/env-AT-local-docker -q` -> `6 passed`
- Vault note:
  - IT remote tests require reachable authorised remote credentials; IT/AT commands were executed with:
    - `set -a; source /opt/iac/Development/cloud-dog-ai/env-vault; set +a`
  - Without Vault-sourced gitlab credentials, first blocking assertion was:
    - `No authorised reachable remote configured ... Vault gitlab url/token missing`

## Latest W14B Status (2026-03-01)

- Instruction file used: `cloud-dog-ai-platform-standards/working/AGENT-INSTRUCTION-W14B-01-GIT-MCP-A2A-AUTH-CONTRACT-STRICT.md`
- A2A contract status:
  - `GET /a2a/health` enabled on API runtime
  - no auth -> `401`
  - `Authorisation: Bearer 12345678` -> `200`
  - auth validator uses shared `cloud_dog_idam` API key authority (no separate key store)
- Env contract in active local-server/local-docker test env files:
  - `TEST_A2A_BASE_PATH=/a2a`
  - `TEST_A2A_API_KEY=12345678`
- Strict command summaries (local-docker):
  - `python3 -m pytest tests/unit/ --env tests/env-UT-local-docker -q` -> `27 passed in 6.43s`
  - `python3 -m pytest tests/system/ --env tests/env-ST-local-docker -q` -> `10 passed in 12.32s`
  - `python3 -m pytest tests/integration/ --env tests/env-IT-local-docker -q` -> `12 passed in 10.36s`
  - `python3 -m pytest tests/application/ --env tests/env-AT-local-docker -q` -> `6 passed in 9.19s`
  - `npm run lint -- --filter=@cloud-dog/app-git-mcp` -> `Tasks:    8 successful, 8 total`
  - `npm run typecheck -- --filter=@cloud-dog/app-git-mcp` -> `Tasks:    8 successful, 8 total`
  - `npm run e2e -- --filter=@cloud-dog/app-git-mcp` -> `10 passed (44.2s)` + `Tasks:    8 successful, 8 total`
  - `npm run a11y -- --filter=@cloud-dog/app-git-mcp` -> `1 passed (8.8s)` + `Tasks:    8 successful, 8 total`
- Probe evidence:
  - `GET /a2a/health` (no auth) -> `401`, payload `{"detail":"Unauthorised"}`
  - `GET /a2a/health` (Bearer `12345678`) -> `200`, payload includes `"interface":"a2a"`
- Evidence report path: `working/W14B-01-GIT-MCP-A2A-AUTH-CONTRACT-REPORT-2026-03-01.md`
- Current status: `COMPLETE VERIFIED`

---

## Latest W14A Status (2026-03-01)

- Instruction file used: `cloud-dog-ai-platform-standards/working/AGENT-INSTRUCTION-W14A-01-GIT-MCP-ROUTE-PFX-AND-TEST-INTEGRITY-STRICT.md`
- Canonical route-prefix contract adopted:
  - API: `/app/v1`
  - MCP: `/mcp`
  - Web: `/`
  - A2A: `/a2a`
- Compatibility policy:
  - Legacy `/api/v1/*` remains compatibility-only alias during migration.
  - New test coverage includes explicit compatibility probe for `/api/v1/health`.
- Strict command summaries (local-docker):
  - `python3 -m pytest tests/unit/ --env tests/env-UT-local-docker -q` -> `26 passed in 11.69s`
  - `python3 -m pytest tests/system/ --env tests/env-ST-local-docker -q` -> `10 passed in 25.88s`
  - `python3 -m pytest tests/integration/ --env tests/env-IT-local-docker -q` -> `11 passed in 12.87s`
  - `python3 -m pytest tests/application/ --env tests/env-AT-local-docker -q` -> `5 passed in 20.24s`
  - `npm run lint -- --filter=@cloud-dog/app-git-mcp` -> `Tasks:    8 successful, 8 total`
  - `npm run typecheck -- --filter=@cloud-dog/app-git-mcp` -> `Tasks:    8 successful, 8 total`
  - `npm run e2e -- --filter=@cloud-dog/app-git-mcp` -> `10 passed (44.2s)` + `Tasks:    8 successful, 8 total`
  - `npm run a11y -- --filter=@cloud-dog/app-git-mcp` -> `1 passed (8.8s)` + `Tasks:    8 successful, 8 total`
- Probe evidence:
  - `GET /app/v1/health` -> HTTP 200, `{"ok": true, ...}`
  - `GET /mcp/tools` -> HTTP 200, tool catalogue returned
  - `GET /api/v1/health` -> HTTP 200 (compatibility alias only)
- Evidence report path: `working/W14A-01-GIT-MCP-ROUTE-PFX-AND-TEST-INTEGRITY-REPORT-2026-03-01.md`
- Current status: `COMPLETE VERIFIED`

---

## Latest W11D Status (2026-02-28)

- Instruction file used: `cloud-dog-ai-platform-standards/working/AGENT-INSTRUCTION-W11D-01-GIT-MCP-LOCAL-DOCKER-IT-AT-STRICT.md`
- Runtime env/controller env files used:
  - `tests/env-local-docker-server`
  - `tests/env-IT-local-docker`
  - `tests/env-AT-local-docker`
- Runtime image + hash:
  - `cloud-dog/git-mcp-server:latest`
  - `sha256:f4e7ca68cfcbd5bbffbf5de09c1dc210303a58cec0ea558a4d23ce84347a0dfb`
- Exact commands run:
  - `bash local-docker-server.sh --env tests/env-local-docker-server ensure`
  - `curl -fsS http://127.0.0.1:18585/health >/tmp/w11d_git_health_api.json`
  - `curl -fsS http://127.0.0.1:18586/mcp/tools >/tmp/w11d_git_tools.json`
  - `python3 -m pytest tests/integration/ --env tests/env-IT-local-docker -q`
  - `python3 -m pytest tests/application/ --env tests/env-AT-local-docker -q`
  - `python3 -m pytest tests/application/AT1.4_FullWorkflow_AdminProfileCRUD --env tests/env-AT-local-docker -q`
- Exact summary lines:
  - `10 passed in 10.26s`
  - `5 passed in 9.06s`
  - `1 passed in 0.69s`
- Evidence report path: `working/W11D-P1-GIT-MCP-LOCAL-DOCKER-IT-AT-REPORT-2026-02-27.md`
- Current status: `COMPLETE VERIFIED`

---

## Environment Requirements

### Tier env files (required)
- `tests/env-UT`
- `tests/env-ST`
- `tests/env-IT`
- `tests/env-AT`
- `tests/env-QT`

These are loaded by `tests/conftest.py` when `--env <TIER>` is supplied.

### Route-prefix env contract (UT/ST/IT/AT and local-* variants)
- `TEST_API_BASE_PATH=/app/v1`
- `TEST_MCP_BASE_PATH=/mcp`
- `TEST_WEB_BASE_PATH=/`
- `TEST_A2A_BASE_PATH=/a2a`
- `TEST_ENV_TIER=<UT|ST|IT|AT|QT>` (mandatory in each tier env file)

### External services (IT/AT/QT)
- API and MCP processes started by `tests/integration/conftest.py`
- Git network remote (`git daemon` over localhost for local-remote scenarios; `https://git.cloud-dog.net/playgroup/test-project.git` for hosted-remote scenarios)
- Optional Vault/env overlays when running outside local integration harness

---

## Unit Tests (UT) — 53 tests

Mocking allowed. No external services required.

| ID | Test | Module | Description |
|----|------|--------|-------------|
| UT1.1 | ConfigLoaderPrecedence | `git_tools/config/` | Config loads with correct precedence: env → .env → YAML → defaults [Req: FR-02] |
| UT1.2 | ConfigVaultIntegration | `git_tools/config/` | Vault secrets merged into config via `cloud_dog_config` [Req: FR-02] |
| UT1.3 | ConfigValidation | `git_tools/config/` | Invalid config rejected with clear error messages [Req: FR-02] |
| UT1.4 | ProfileModelValidation | `git_tools/config/` | Profile Pydantic models validate all required fields [Req: FR-03] |
| UT1.5 | RefResolverBranch | `git_tools/workspaces/` | Branch ref resolves to working_tree mode [Req: FR-07] |
| UT1.6 | RefResolverTag | `git_tools/workspaces/` | Tag ref resolves to ref_readonly mode [Req: FR-07] |
| UT1.7 | RefResolverCommit | `git_tools/workspaces/` | Commit SHA resolves to ref_readonly mode [Req: FR-07] |
| UT1.8 | WorkspaceLocking | `git_tools/workspaces/` | Concurrent workspace access is serialised by lock [Req: FR-01] |
| UT1.9 | ScopeEnforcement | `git_tools/security/` | Path scope blocks access outside allowed directories [Req: FR-01] |
| UT1.10 | ProtectedBranchPolicy | `git_tools/security/` | Protected branch patterns block writes for non-maintainers [Req: FR-05] |
| UT1.11 | RBACPolicyEval | `git_tools/security/` | `cloud_dog_idam` RBAC correctly evaluates subject/object/action [Req: FR-05] |
| UT1.12 | AuditEventShape | `git_tools/audit/` | Audit events include required fields (timestamp, actor, operation, correlation_id) [Req: FR-14] |
| UT1.13 | AuditRedaction | `git_tools/audit/` | Secrets are redacted from audit entries [Req: FR-14] |
| UT1.14 | GitStatusParsing | `git_tools/git/` | Git status output parsed correctly [Req: FR-10] |
| UT1.15 | GitLogFiltering | `git_tools/git/` | Git log filters (date, author, path, max_count) produce correct commands and max_count output limits [Req: FR-10] |
| UT1.16 | GitDiffGeneration | `git_tools/git/` | Diff between refs produces expected output [Req: FR-10] |
| UT1.17 | TagCRUD | `git_tools/git/` | Tag create/list/delete operations work correctly [Req: FR-10, FR-11] |
| UT1.18 | ConflictDetection | `git_tools/git/` | Conflict markers detected after merge/rebase [Req: FR-10, FR-12] |
| UT1.19 | ConflictResolution | `git_tools/git/` | Ours/theirs/manual resolution produces clean index [Req: FR-10, FR-12] |
| UT1.20 | RecoveryStash | `git_tools/git/` | Recovery via stash preserves working tree changes [Req: FR-10, FR-13] |
| UT1.21 | FileIOAtomicWrite | `git_tools/files/` | Atomic write completes fully or not at all [Req: FR-08] |
| UT1.22 | FileSearchContent | `git_tools/files/` | Content search with regex and glob filters works [Req: FR-08, UC-02] |
| UT1.23 | StructuredEditJSON | `git_tools/files/edit/` | JSON edit via JSON Pointer works correctly [Req: FR-09] |
| UT1.24 | FileValidation | `git_tools/files/` | File validation detects format errors (JSON/YAML/XML) [Req: FR-09] |
| UT1.25 | ToolDefinitionSchemas | `git_tools/tools/` | All tool Pydantic schemas validate correctly [Req: FR-02] |
| UT1.26 | A2AAuthValidatorParity | `git_mcp_server/api_server.py` | `/a2a` bearer validator uses shared API key validation authority and enforces bearer token semantics [Req: FR-04] |
| UT1.27 | DatabaseAbstraction | `git_tools/db/` | Database runtime abstraction initialises engine/session and supports sqlite session lifecycle [Req: FR-17] |
| UT1.28 | FileDownload | `git_tools/files/` | File download returns expected content and errors on missing paths [Req: FR-08, UC-004] |
| UT1.29 | FileMove | `git_tools/files/` | File move preserves content and enforces destination safety checks [Req: FR-08, UC-005] |
| UT1.30 | FileCopy | `git_tools/files/` | File copy preserves source and validates missing input handling [Req: FR-08, UC-006] |
| UT1.31 | FileDelete | `git_tools/files/` | File delete removes files and rejects invalid/protected targets [Req: FR-08, UC-007] |
| UT1.32 | DirCreate | `git_tools/files/` | Directory create supports nested/parent flows and existing-dir behaviour [Req: FR-08, UC-009] |
| UT1.33 | DirRemove | `git_tools/files/` | Directory removal validates empty/non-empty and recursive policy [Req: FR-08, UC-010] |
| UT1.34 | SearchFiles | `git_tools/files/` | File search supports glob/regex matching and empty-result handling [Req: FR-08, UC-011] |
| UT1.35 | StructuredEditYAML | `git_tools/files/edit/` | YAML edit updates/adds/deletes keys and rejects invalid YAML [Req: FR-09, UC-016] |
| UT1.36 | StructuredEditXMLHTML | `git_tools/files/edit/` | XML/HTML edit updates attributes/elements and rejects invalid selectors [Req: FR-09, UC-017] |
| UT1.37 | StructuredEditSedLike | `git_tools/files/edit/` | Sed-like replacement supports single/multi-line cases and no-match reporting [Req: FR-09, UC-018] |
| UT1.38 | GitBranchList | `git_tools/git/` | Branch listing includes default and created branches [Req: FR-10, UC-027] |
| UT1.39 | GitBranchDelete | `git_tools/git/` | Branch delete works for non-protected refs and rejects protected refs [Req: FR-10, UC-029] |
| UT1.40 | GitReset | `git_tools/git/` | Git reset supports HEAD/index reset behaviour and path-scoped operations [Req: FR-10, UC-035] |
| UT1.41 | GitPull | `git_tools/git/` | Git pull updates workspace from remote branch state [Req: FR-10, UC-039] |
| UT1.42 | GitForcePush | `git_tools/git/` | Force-with-lease push handles remote divergence safely [Req: FR-10, UC-041] |
| UT1.43 | GitMergeNoFF | `git_tools/git/` | Non-fast-forward merge creates merge commit when required [Req: FR-10, UC-045] |
| UT1.44 | GitMergeAbortContinue | `git_tools/git/` | Merge abort/continue workflows handle conflict lifecycle correctly [Req: FR-10, FR-12, UC-051] |
| UT1.45 | GitStashList | `git_tools/git/` | Stash list reports entries for saved workspace changes [Req: FR-10, UC-058] |
| UT1.46 | GitTagPush | `git_tools/git/` | Tag push publishes created tag to remote and verifies visibility [Req: FR-11, UC-055] |
| UT1.47 | GitAuthorPolicy | `git_tools/git/` | Author policy enforcement validates commit metadata controls [Req: FR-10, UC-037] |
| UT1.48 | URLAllowlistEnforcement | `git_tools/security/` | URL allowlist enforcement permits authorised remotes and blocks disallowed remotes [Req: FR-06, UC-043] |
| UT1.49 | SessionHeartbeatTimeout | `git_tools/session/` | Session heartbeat updates and timeout expiry behaviour validated [Req: FR-13, UC-062] |
| UT1.50 | RecoveryListGetRestore | `git_tools/git/recovery.py` | Recovery list/get/restore flow validates stash and patch artefact behaviour [Req: FR-13, UC-066, UC-067] |
| UT1.51 | RBACToolCategory | `git_tools/security/` | RBAC policy enforces access by tool category constraints [Req: FR-05, UC-080] |
| UT1.52 | JWTAuthRuntime | `git_mcp_server/auth/middleware.py` | JWT runtime wiring issues/verifies bearer tokens and enforces explicit secret config in JWT mode [Req: FR-04, UC-078] |
| UT1.53 | EnterpriseAuthIntegration | `git_mcp_server/auth/middleware.py` | Enterprise auth provider wiring, role mapping, and middleware enforcement behaviour [Req: FR-04, FR-05, UC-084] |

---

## System Tests (ST) — 12 tests

Real git repos required. No mocking of git operations.

| ID | Test | Description |
|----|------|-------------|
| ST1.1 | WorkspaceCreateEphemeral | Create ephemeral workspace from local repo; verify checkout and isolation [Req: FR-03] |
| ST1.2 | WorkspaceCreatePersistent | Create persistent workspace; verify reuse across sessions [Req: FR-03] |
| ST1.3 | BranchCreateCommitPush | Create branch, perform 20 sequential add+commit cycles, verify `git_log(max_count=25)`, push branch [Req: FR-10] |
| ST1.4 | TagCreateAndList | Create annotated tag, list tags, verify metadata [Req: FR-11, UC-04] |
| ST1.5 | MergeFFOnly | Fast-forward merge succeeds; non-ff merge rejected when ff-only policy [Req: FR-10] |
| ST1.6 | RebaseSimple | Rebase onto target branch; verify linear history [Req: FR-10] |
| ST1.7 | StashSaveAndPop | Stash changes, pop, verify restoration [Req: FR-10] |
| ST1.8 | RecoveryOnCrash | Simulate session crash; verify recovery artefact created per policy [Req: FR-13, UC-06] |
| ST1.9 | RetentionEnforcement | Workspace TTL expiry triggers cleanup [Req: FR-01] |
| ST1.10 | AuditLogPersistence | Audit events persisted to JSONL file with correct format [Req: FR-14] |
| ST1.11a | DatabaseMigration | Migration upgrade and CRUD smoke for sqlite backend [Req: FR-17] |
| ST1.11b | DatabaseMigrationMultiBackend | Migration lifecycle upgrade/downgrade/upgrade and schema-version simulation [Req: FR-17] |

---

## Integration Tests (IT) — 13 tests

Real services required. Tests cross-component interaction.

| ID | Test | Description | Services |
|----|------|-------------|----------|
| IT1.1 | APIHealthEndpoint | `GET /health` and API health endpoints return a live status envelope | FastAPI [Req: FR-01] |
| IT1.1b | APIHealthLegacyAliasCompatibility | Compatibility-only assertion for legacy `/api/v1/health` alias while canonical `/app/v1` is primary | FastAPI [Req: FR-01] |
| IT1.2 | APIAuthReject | Unauthenticated request to protected endpoint returns 401 | FastAPI + `cloud_dog_idam` [Req: FR-04] |
| IT1.3 | APIAuthAccept | Valid API key/JWT grants access to permitted endpoints | FastAPI + `cloud_dog_idam` [Req: FR-04] |
| IT1.4 | APIRBACEnforce | API tool flow performs branch edit/commit/push against a network remote (`git daemon`) | FastAPI + git [Req: FR-05] |
| IT1.5 | MCPToolCatalogue | MCP client lists all tools with correct schemas | MCP transport [Req: FR-01] |
| IT1.6 | MCPToolExecution | MCP executes `repo_open` + `git_fetch` against a network remote (`git daemon`) | MCP transport + git [Req: FR-01] |
| IT1.7 | APIFileOpsRefReadonly | File write via API fails in ref_readonly mode (tag checkout) | FastAPI + git [Req: FR-07] |
| IT1.8 | CorrelationIDPropagation | Correlation ID from request propagates through logs and audit | FastAPI + `cloud_dog_logging` [Req: FR-14] |
| IT1.9 | RemoteCloneAndFetch | Clone from `https://git.cloud-dog.net/playgroup/test-project.git` via repo_open, git_fetch, file_read, repo_close. Fails explicitly if remote unreachable. | FastAPI + git remote [Req: FR-06, FR-10] |
| IT1.10 | RemoteBranchPush | Push a `test/git-mcp-*` branch to `https://git.cloud-dog.net/playgroup/test-project.git`, then delete it. Fails explicitly if remote unreachable. | FastAPI + git remote [Req: FR-06, FR-10] |
| IT1.11 | A2AHealthAuthContract | `/a2a/health` auth matrix: no auth `401`, wrong bearer `401`, bearer `12345678` `200` | FastAPI + `cloud_dog_idam` [Req: FR-04] |
| IT1.12 | JWTAuthContract | Protected API endpoint auth matrix for JWT bearer tokens: valid token `200`, invalid token `401` | FastAPI + `cloud_dog_idam` JWT service [Req: FR-04, UC-078] |

---

## Application Tests (AT) — 7 tests

End-to-end user workflows.

| ID | Test | Description |
|----|------|-------------|
| AT1.1 | FullWorkflow_BranchEditPush | Open repo → create branch → edit file → commit → push → verify remote [Req: FR-08, UC-01, UC-02] |
| AT1.2 | FullWorkflow_TagBrowse | Open repo on tag → list files → read file → verify write blocked [Req: FR-07, UC-03, UC-04] |
| AT1.3 | FullWorkflow_ConflictResolve | Real merge conflict via two branches editing same file, `pytest.raises(GitCommandError)`, resolve via `git_conflict_resolve_manual`, verify `git_log` [Req: FR-12, UC-05] |
| AT1.4 | FullWorkflow_AdminProfileCRUD | Admin creates profile → assigns RBAC → user accesses → admin deletes [Req: FR-05, FR-15, FR-16, UC-07] |
| AT1.5 | FullWorkflow_RecoveryRestore | Stash save/pop with file verification, patch bundle with content check, recovery branch creation and activation [Req: FR-13, UC-06] |
| AT1.6 | A2AHealthAuthContract | API-level `/a2a/health` flow: bearer required, `x-api-key` fallback rejected, bearer `12345678` accepted [Req: FR-04] |
| AT1.7 | JWTAuthContract | Application-level JWT bearer validation against protected API endpoint (`200` valid token, `401` invalid token) [Req: FR-04, UC-078] |

---

## Quality Tests (QT) — 4 tests

Security and quality checks.

| ID | Test | Description |
|----|------|-------------|
| QT1.1 | SecretsNeverLogged | Grep audit and ops logs; no tokens, keys, or passwords present [Req: FR-06] |
| QT1.2 | SymlinkEscapePrevented | Symlink pointing outside workspace root is blocked [Req: FR-01] |
| QT1.3 | GitHooksDisabled | Git hooks in cloned repos are disabled/sandboxed [Req: FR-01] |
| QT1.4 | UKEnglishCompliance | All source files, docs, and error messages use UK English [Req: FR-01] |

### W25A Compliance Quality Tests (QT2) — 10 tests

Static-analysis compliance checks for cross-project platform governance.

| ID | Test | Description |
|----|------|-------------|
| QT2.1 | test_qt_rules_compliance | `tests/quality/QT_COMPLIANCE/test_qt_rules_compliance.py` scans RC-01..RC-06 and RC-10 policy patterns [Req: FR-01] |
| QT2.2 | test_qt_package_adoption | `tests/quality/QT_COMPLIANCE/test_qt_package_adoption.py` verifies platform package adoption and bespoke replacements [Req: FR-01] |
| QT2.3 | test_qt_vault_config_contract | `tests/quality/QT_COMPLIANCE/test_qt_vault_config_contract.py` verifies defaults/env/secret contract rules [Req: FR-01] |
| QT2.4 | test_qt_migration_completeness | `tests/quality/QT_COMPLIANCE/test_qt_migration_completeness.py` checks migration leftovers (raw FastAPI, bespoke auth, config adapters) [Req: FR-01] |
| QT2.5 | test_qt_traceability | `tests/quality/QT_COMPLIANCE/test_qt_traceability.py` performs requirements↔tests↔code traceability and delivery matrix generation [Req: FR-16, FR-17] |
| QT2.6 | test_qt_library_server_separation | `tests/quality/QT_COMPLIANCE/test_qt_library_server_separation.py` enforces library/server separation contract (no transport imports in `git_tools`, no direct GitPython imports in `git_mcp_server`) [Req: FR-01, UC-097] |
| QT2.7 | test_qt1_security_suite | `tests/quality/QT_COMPLIANCE/test_qt1_security_suite.py` validates static security controls and secret-exposure guardrails [Req: FR-01, FR-06] |
| QT2.8 | test_qt26_secrets_separation | `tests/quality/QT_COMPLIANCE/test_qt26_secrets_separation.py` verifies test/code separation from secret material and prohibited credential paths [Req: FR-06] |
| QT2.9 | test_qt27_bespoke_code_scan | `tests/quality/QT_COMPLIANCE/test_qt27_bespoke_code_scan.py` scans for bespoke replacements where platform packages are mandatory [Req: FR-01] |
| QT2.10 | test_qt3_documentation_suite | `tests/quality/QT_COMPLIANCE/test_qt3_documentation_suite.py` verifies required documentation files and structural policy alignment [Req: FR-01, FR-17] |

---

## Test Execution

```bash
cd /opt/iac/Development/cloud-dog-ai/git-mcp-server

# Unit tests
python3 -m pytest tests/unit/ --env UT -v

# System tests
python3 -m pytest tests/system/ --env ST -v

# Integration tests (start/stop server via integration fixture)
python3 -m pytest tests/integration/ --env IT -v

# Application tests
python3 -m pytest tests/application/ --env AT -v

# Security tests
python3 -m pytest tests/security/ --env QT -v

# Full suite
python3 -m pytest tests/ --env UT --env ST --env IT --env AT --env QT -v
```

---
