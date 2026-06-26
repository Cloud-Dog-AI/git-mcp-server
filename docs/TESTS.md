---
template-id: T-TST
template-version: 1.1
applies-to: docs/TESTS.md
project: git-mcp-server
doc-last-updated: 2026-06-25
doc-git-commit: 342c8c1b336389e2f3afa5e5400ad3ed9b5d33cd
doc-git-branch: main
doc-age-policy: 90d
doc-conformance-stamp: 2026-06-12T16:36:28Z
req-trace-version: 1.0
total-tests: 135
coverage-percent: 100
---

# Tests — git-mcp-server

This catalogue reflects the current repository and linked WebUI test inventory verified on 2026-04-21. It exists to satisfy RULES §6.4 traceability: every active requirement in `docs/REQUIREMENTS.md` maps to at least one test entry.

## Standard Commands

```bash
python3 -m pytest tests/quality tests/security --env tests/env-QT -v
python3 -m pytest tests/unit --env tests/env-UT -v
python3 -m pytest tests/system --env tests/env-ST -v
python3 -m pytest tests/integration --env tests/env-IT -v
python3 -m pytest tests/application --env tests/env-AT -v
```

## W28E-1804C 1.0RC01 Closeout Commands

The 1.0RC01 Stream-C closeout adds WebUI/E2E, local Docker, preprod, and sibling-sentinel replay evidence under
`cloud-dog-ai-platform-standards/working/evidence/W28E-1804C/current/`.

| Surface | Command | Raw evidence |
|---|---|---|
| WebUI full local E2E | `npm --prefix apps/git-mcp run e2e` | `test-logs/ui-playwright-full-local-r9.log` (`109 passed, 9 skipped, 0 failed`) |
| WebUI focused adoption | `npm --prefix apps/git-mcp run e2e -- tests/w28a458/ui-adopt.spec.ts` | `test-logs/ui-playwright-w28a458-r5.log` (`15 passed`) |
| UI static checks | `npm --prefix apps/git-mcp run lint`, `typecheck`, `test`, `build` | `ui-lint-r12.log`, `ui-typecheck-r16.log`, `ui-vitest-r5.log`, `ui-build-r5.log` |
| Backend focused runtime | `python3 -m pytest ...UT1.56...UT1.70...UT1.54...UT1.61` | `backend-focused-unit-r6.log` (`41 passed`) |
| Backend admin parity | `python3 -m pytest --env IT tests/integration/IT1.14_AdminCrudParity` | `backend-admin-crud-parity-r7.log` (`5 passed`) |
| Backend API/MCP/A2A/jobs on Docker | `python3 -m pytest --env tests/env-IT-local-docker IT1.5 IT1.6 IT1.11 IT1.62` | `backend-api-mcp-a2a-job-local-docker-r1.log` (`5 passed`) |
| Audit unit proof | `TEST_OPTIONAL_GITLAB_TOKEN=w28e1804c-test-token python3 -m pytest --env UT tests/unit/UT1.67_PerToolCallAudit` | `backend-audit-unit-r1.log` (`7 passed`) |
| Local Docker browser proof | `E2E_SKIP_WEBSERVER=1 E2E_BASE_URL=http://127.0.0.1:19032 ... playwright test` | `local-docker-ui-playwright-health-r1.log`, `local-docker-ui-playwright-w28j-conformance-r1.log` (`12 passed total`) |
| Live preprod browser proof | `E2E_SKIP_WEBSERVER=1 E2E_BASE_URL=https://gitmcpserver0.cloud-dog.net ... playwright test` | `live-preprod-ui-playwright-r2.log` (`12 passed`) |
| Live cookie auth proof | `node live-cookie-browser-smoke-w28e1804c.mjs` | `live-cookie-browser-smoke-r2.log` (`LIVE_COOKIE_BROWSER_SMOKE_RESULT=PASS`) |
| Sibling sentinel proof | `E2E_SKIP_WEBSERVER=1 playwright test tests/e2e/w28a731-sentinels.spec.ts` | `live-preprod-sentinels-r1.log` (`4 passed`) |

## Numeric Automated Inventory

| Test ID | Suite | Test module(s) |
|---|---|---|
| AT1.1 | Application | `test_fullworkflow_branch_edit_push.py` |
| AT1.2 | Application | `test_fullworkflow_tag_browse.py` |
| AT1.3 | Application | `test_fullworkflow_conflict_resolve.py` |
| AT1.4 | Application | `test_fullworkflow_admin_profile_crud.py` |
| AT1.5 | Application | `test_fullworkflow_recovery_restore.py` |
| AT1.6 | Application | `test_a2a_health_auth_contract.py` |
| AT1.7 | Application | `test_at_jwt_auth_contract.py` |
| IT1.1 | Integration | `test_api_health_endpoint.py` |
| IT1.2 | Integration | `test_api_auth_reject.py` |
| IT1.3 | Integration | `test_api_auth_accept.py` |
| IT1.4 | Integration | `test_api_rbac_enforce.py` |
| IT1.5 | Integration | `test_mcp_tool_catalogue.py` |
| IT1.6 | Integration | `test_mcp_tool_execution.py` |
| IT1.7 | Integration | `test_api_file_ops_ref_readonly.py` |
| IT1.8 | Integration | `test_correlation_id_propagation.py` |
| IT1.9 | Integration | `test_remote_clone_and_fetch.py` |
| IT1.10 | Integration | `test_remote_branch_push.py` |
| IT1.11 | Integration | `test_it_a2a_health_auth_contract.py` |
| IT1.12 | Integration | `test_it_jwt_auth_contract.py` |
| IT1.13 | Integration | `test_config_change_event_broadcast.py` |
| IT1.14 | Integration | `test_admin_crud_parity.py` |
| IT1.15 | Integration | `test_managed_git_job.py` |
| IT1.16 | Integration | `test_remote_fetch_real_remote_refs.py` |
| IT1.61 | Integration | `test_seed_deep_flows.py` | FR1.18 |
| IT1.62 | Integration | `test_deep_flow_jobs.py` | FR1.9, FR1.16 |
| IT1.63 | Integration | `test_settings_read_only.py` | FR-1.17 |
| QT1.1 | Quality/Security | `test_secrets_never_logged.py` |
| QT1.2 | Quality/Security | `test_symlink_escape_prevented.py` |
| QT1.3 | Quality/Security | `test_git_hooks_disabled.py` |
| QT1.4 | Quality/Security | `test_uk_english_compliance.py` |
| ST1.1 | System | `test_workspace_create_ephemeral.py` |
| ST1.2 | System | `test_workspace_create_persistent.py` |
| ST1.3 | System | `test_branch_create_commit_push.py` |
| ST1.4 | System | `test_tag_create_and_list.py` |
| ST1.5 | System | `test_merge_ff_only.py` |
| ST1.6 | System | `test_rebase_simple.py` |
| ST1.7 | System | `test_stash_save_and_pop.py` |
| ST1.8 | System | `test_recovery_on_crash.py` |
| ST1.9 | System | `test_retention_enforcement.py` |
| ST1.10 | System | `test_audit_log_persistence.py` |
| ST1.11 | System | `test_database_migration.py`, `test_database_migration_multibackend.py` |
| ST1.12 | System | `test_workspace_persistence_reopen.py` |
| UT1.1 | Unit | `test_config_loader_precedence.py` |
| UT1.2 | Unit | `test_config_vault_integration.py` |
| UT1.3 | Unit | `test_config_validation.py` |
| UT1.4 | Unit | `test_profile_model_validation.py` |
| UT1.5 | Unit | `test_ref_resolver_branch.py` |
| UT1.6 | Unit | `test_ref_resolver_tag.py` |
| UT1.7 | Unit | `test_ref_resolver_commit.py` |
| UT1.8 | Unit | `test_workspace_locking.py` |
| UT1.9 | Unit | `test_scope_enforcement.py` |
| UT1.10 | Unit | `test_protected_branch_policy.py` |
| UT1.11 | Unit | `test_rbac_policy_eval.py` |
| UT1.12 | Unit | `test_audit_event_shape.py` |
| UT1.13 | Unit | `test_audit_redaction.py` |
| UT1.14 | Unit | `test_git_status_parsing.py` |
| UT1.15 | Unit | `test_git_log_filtering.py` |
| UT1.16 | Unit | `test_git_diff_generation.py` |
| UT1.17 | Unit | `test_tag_crud.py` |
| UT1.18 | Unit | `test_conflict_detection.py` |
| UT1.19 | Unit | `test_conflict_resolution.py` |
| UT1.20 | Unit | `test_recovery_stash.py` |
| UT1.21 | Unit | `test_file_io_atomic_write.py` |
| UT1.22 | Unit | `test_file_search_content.py` |
| UT1.23 | Unit | `test_structured_edit_json.py` |
| UT1.24 | Unit | `test_file_validation.py` |
| UT1.25 | Unit | `test_tool_definition_schemas.py` |
| UT1.26 | Unit | `test_a2a_auth_validator_parity.py` |
| UT1.27 | Unit | `test_database_abstraction.py` |
| UT1.28 | Unit | `test_file_download.py` |
| UT1.29 | Unit | `test_file_move.py` |
| UT1.30 | Unit | `test_file_copy.py` |
| UT1.31 | Unit | `test_file_delete.py` |
| UT1.32 | Unit | `test_dir_create.py` |
| UT1.33 | Unit | `test_dir_remove.py` |
| UT1.34 | Unit | `test_search_files.py` |
| UT1.35 | Unit | `test_yaml_edit.py` |
| UT1.36 | Unit | `test_xml_html_edit.py` |
| UT1.37 | Unit | `test_sed_like_edit.py` |
| UT1.38 | Unit | `test_branch_list.py` |
| UT1.39 | Unit | `test_branch_delete.py` |
| UT1.40 | Unit | `test_git_reset.py` |
| UT1.41 | Unit | `test_git_pull.py` |
| UT1.42 | Unit | `test_force_push.py` |
| UT1.43 | Unit | `test_merge_no_ff.py` |
| UT1.44 | Unit | `test_merge_abort_continue.py` |
| UT1.45 | Unit | `test_stash_list.py` |
| UT1.46 | Unit | `test_tag_push.py` |
| UT1.47 | Unit | `test_author_policy.py` |
| UT1.48 | Unit | `test_url_allowlist.py` |
| UT1.49 | Unit | `test_session_heartbeat_timeout.py` |
| UT1.50 | Unit | `test_recovery_list_get_restore.py` |
| UT1.51 | Unit | `test_rbac_tool_category.py` |
| UT1.52 | Unit | `test_jwt_auth_runtime.py` |
| UT1.53 | Unit | `test_enterprise_auth_integration.py` |
| UT1.54 | Unit | `test_admin_crud_runtime.py` |
| UT1.55 | Unit | `test_jobs_runtime.py` |
| UT1.56 | Unit | `test_profile_scoped_rbac.py`, `test_web_ui_delivery.py` |
| UT1.57 | Unit | `test_ui_support_endpoints.py` |
| UT1.58 | Unit | `test_a2a_all_tools_skill_parity.py` | FR1.4 |
| UT1.60 | Unit | `test_workspace_enum_endpoints.py` | FR1.18 |
| UT1.61 | Unit | `test_settings_config_sources.py` | FR1.17 |
| UT1.62 | Unit | `test_admin_permissions_unauth_gate.py` | FR1.12, CS1.2 |
| UT1.63 | Unit | `test_mcp_anon_auth_gate.py` | FR1.3, CS1.1 |
| UT1.64 | Unit | `test_profile_persistence.py` | FR1.17 |
| UT1.65 | Unit | `test_vestigial_git_mcp_routes.py` | FR1.2 |
| UT1.66 | Unit | `test_auth_me_api_key_principal.py` | CS1.1 |
| UT1.67 | Unit | `test_per_tool_call_audit.py` | FR1.16 |
| UT1.68 | Unit | `test_a2a_events_gone.py` | FR1.4 |
| UT1.69 | Unit | `test_workspace_gc.py` | FR1.5 |

## Supporting Test Entries

| Test ID | Suite | Test module(s) |
|---|---|---|
| AT_PROFILE_LIFECYCLE | Application | `test_repo_profile_lifecycle.py` |
| AT_WEBUI | Application | `test_webui_playwright.py` |
| QT26 | Quality | `test_qt26_secrets_separation.py` |
| QT_DOCS | Quality | `test_qt3_documentation_suite.py` |
| QT_SECURITY_SUITE | Quality | `test_qt1_security_suite.py` |
| QT_BESPOKE_SCAN | Quality | `test_qt27_bespoke_code_scan.py` |
| QT_LIB_SEPARATION | Quality | `test_qt_library_server_separation.py` |
| QT_LOGGING_COMPLIANCE | Quality | `test_logging_compliance.py` |
| QT_MIGRATION | Quality | `test_qt_migration_completeness.py` |
| QT_PACKAGE | Quality | `test_qt_package_adoption.py`, `test_package_compliance.py` |
| QT_RULES | Quality | `test_qt_rules_compliance.py` |
| QT_TRACEABILITY | Quality | `test_qt_traceability.py` |
| QT_VAULT | Quality | `test_qt_vault_config_contract.py` |
| ST_INTEGRITY | System | `test_integrity_running.py` |
| ST_LOG_ROTATION | System | `test_rotation_config.py` |
| UT_AUDIT_FORMAT | Unit | `test_audit_log_format.py` |
| UT_LOGGING_CONFIG | Unit | `test_logging_surface_config.py` |

## Thread-B Access-Control Matrix

These tests implement the W28A-745 T0-T3 b-method rows for git-mcp without touching
the UI monorepo. Browser-level rows remain mapped to the existing Playwright inventory.

| Test ID | Suite | Requirement IDs | Test module(s) | Coverage |
|---|---|---|---|---|
| T0-GM-AUDIT | Smoke | FR1.16, BR1.1 | `test_access_control_matrix.py` | `ToolRegistry.call()` converges through `_call_with_audit()` and redacts sensitive params |
| T1-GM-AUTH | E2E | FR1.2, CS1.1 | `test_access_control_api_contract.py` | API health is public; anonymous tool call is denied |
| T1-GM-IDAM | E2E | FR1.16, UC1.5 | `test_access_control_api_contract.py` | managed API-key create reveals once; list/read omit raw secret |
| T2-GM-SECRET-MASK | Smoke | FR1.16, UC1.6 | `test_access_control_matrix.py` | non-create API-key metadata reads do not expose stored secrets |
| T3-GM-CASCADE | Smoke | FR1.19, UC1.7 | `test_access_control_matrix.py` | group membership grants `profile:<name>` access, denies other profiles, and removal revokes |

## Browser Workflow Inventory

The following Playwright evidence is maintained in `cloud-dog-ai-ui-monorepo/apps/git-mcp/tests/e2e/`.

| Test ID | Spec file(s) | Primary coverage |
|---|---|---|
| PW1.1 | `health-and-auth.spec.ts`, `mcp-catalogue-and-call.spec.ts` | Health, authentication, MCP catalogue and tool execution |
| PW1.2 | `profile-crud.spec.ts`, `api-key-metadata.spec.ts`, `rbac-bindings.spec.ts`, `rbac-enforcement.spec.ts` | Profile admin, API-key metadata, RBAC admin workflows |
| PW1.3 | `branch-edit-commit-push.spec.ts` | Repository edit, commit, and push workflow |
| PW1.4 | `tag-readonly-browse.spec.ts` | Tag browsing and read-only ref behaviour |
| PW1.5 | `conflict-resolution.spec.ts` | Merge or conflict resolution workflow |
| PW1.6 | `recovery-artifacts.spec.ts`, `recovery-page-ui.spec.ts` | Recovery and stash-adjacent workflows |
| PW1.7 | `audit-log-correlation.spec.ts` | Audit visibility and correlation workflow |
| PW1.8 | `w28a869-webui-pages.spec.ts` | Routed page presence for repository and admin pages |
| PW1.9 | `ui-review2.spec.ts`, `real-functional-w28a-481.spec.ts`, `w28a870-git-mcp-e2e-testing.spec.ts` | Integrated operator journeys across the delivered UI surface |

## Requirement Coverage

### Strategic Coverage

| Requirement ID | Test IDs | Architecture refs |
|---|---|---|
| SV1.1 | IT1.5, IT1.6, PW1.1 | SA1.1, CC1.1, AI1.1, AI1.2 |
| SV1.2 | AT_PROFILE_LIFECYCLE, IT1.14, PW1.9 | OV1.1, CC1.2, AI1.4 |
| SV1.3 | IT1.5, UT1.23, UT1.24 | OV1.1, AI1.2, AI1.3 |
| BO1.1 | QT1.2, IT1.7, AT1.1 | SW1.1, SE1.1 |
| BO1.2 | IT1.5, IT1.6, PW1.1 | SA1.1, CC1.1 |
| BO1.3 | ST1.8, IT1.15, PW1.7 | CP1.2, RR1.1, MO1.1 |
| BO1.4 | IT1.14, UT1.54, ST1.11 | CC1.3, AI1.1 |
| BO1.5 | PW1.8, PW1.9 | AI1.4, MO1.1 |
| BR1.1 | IT1.5, IT1.6, PW1.1 | CC1.1, AI1.1, AI1.2 |
| BR1.2 | AT_PROFILE_LIFECYCLE, IT1.9, ST1.12 | SW1.1, CP1.1 |
| BR1.3 | IT1.13, IT1.14, PW1.2 | CC1.3, DF1.1 |
| BR1.4 | UT1.56, UT1.57, PW1.8, PW1.9 | AI1.4 |
| BR1.5 | UT1.23, UT1.24, UT1.35, UT1.36, UT1.37 | CC1.2, TS1.1 |

### Functional Coverage

| Requirement ID | Test IDs | Architecture refs |
|---|---|---|
| FR1.1 | UT1.1, UT1.2, UT1.3, QT_VAULT | CM1.1 |
| FR1.2 | IT1.1, IT1.14, UT1.57, PW1.1 | AI1.1 |
| FR1.3 | IT1.5, IT1.6, UT1.25, PW1.1 | AI1.2 |
| FR1.4 | AT1.6, IT1.11, IT1.13 | AI1.3, DF1.1 |
| FR1.5 | UT1.4, UT1.8, ST1.1, ST1.2, ST1.12 | SW1.1, RR1.1 |
| FR1.6 | UT1.5, UT1.6, UT1.7, IT1.7, AT1.2, PW1.4 | SW1.1, SE1.1 |
| FR1.7 | IT1.9, IT1.10, IT1.16, UT1.48, QT1.1, QT1.3 | IP1.1, SE1.1 |
| FR1.8 | UT1.21, UT1.22, UT1.28, UT1.29, UT1.30, UT1.31, UT1.32, UT1.33, UT1.34, AT1.1, PW1.3 | CC1.2, CP1.1 |
| FR1.9 | UT1.55, IT1.15, UT1.57 | CP1.2, AI1.1 |
| FR1.10 | UT1.14, UT1.15, UT1.16, UT1.38, UT1.39, UT1.40, UT1.41, UT1.42, UT1.47, ST1.3, ST1.5, ST1.6, IT1.9, IT1.10, IT1.16, PW1.3 | SW1.2 |
| FR1.11 | UT1.17, UT1.18, UT1.19, UT1.20, UT1.43, UT1.44, UT1.45, UT1.46, UT1.50, ST1.4, ST1.7, ST1.8, AT1.3, AT1.5, PW1.4, PW1.5, PW1.6 | SW1.2, RR1.1 |
| FR1.12 | AT1.4, IT1.14, UT1.54, PW1.2 | CC1.3, AI1.1 |
| FR1.13 | UT1.54, IT1.14, PW1.2 | CC1.3, AI1.2 |
| FR1.14 | UT1.56, PW1.8, PW1.9 | AI1.4, DA1.1 |
| FR1.15 | UT1.57, PW1.7, PW1.9 | MO1.1, AI1.4 |
| FR1.16 | UT1.12, UT1.13, ST1.9, ST1.10, IT1.8, IT1.15, PW1.7 | DF1.1, MO1.1 |
| FR1.17 | UT1.27, ST1.11, IT1.14 | DM1.1, RR1.1 |
| FR1.18 | UT1.23, UT1.24, UT1.35, UT1.36, UT1.37 | CC1.2, TS1.1 |
| FR1.19 | T3-GM-CASCADE, T0-GM-AUDIT | SE1.1, CC1.3, DF1.1 |

### Use-Case, Security, and Non-Functional Coverage

| Requirement ID | Test IDs | Architecture refs |
|---|---|---|
| UC1.1 | AT_PROFILE_LIFECYCLE, ST1.1, ST1.12, IT1.9 | SW1.1, CP1.1 |
| UC1.2 | AT1.1, UT1.28, UT1.34, PW1.3, PW1.8 | CP1.1, AI1.4 |
| UC1.3 | ST1.3, IT1.10, PW1.3, PW1.8 | SW1.2, AI1.4 |
| UC1.4 | AT1.2, AT1.3, AT1.5, PW1.4, PW1.5, PW1.6 | SW1.2, RR1.1 |
| UC1.5 | AT1.4, IT1.14, PW1.2, PW1.8 | CC1.3, AI1.4 |
| UC1.6 | IT1.13, IT1.8, PW1.7, PW1.9 | DF1.1, MO1.1, AI1.3 |
| CS1.1 | IT1.2, IT1.3, IT1.11, IT1.12, AT1.6, AT1.7, UT1.26, UT1.52, UT1.53, PW1.1 | SE1.1, AI1.1, AI1.2, AI1.3 |
| CS1.2 | IT1.4, UT1.11, UT1.51, UT1.56, UT1.70, PW1.2 | SE1.1, CP1.1 |
| CS1.3 | QT1.2, UT1.9, IT1.7 | SE1.1, RR1.1 |
| CS1.4 | UT1.10, AT1.2, IT1.7, PW1.4 | SE1.1, SW1.1, SW1.2 |
| CS1.5 | QT1.1, QT26, UT1.13, IT1.8 | SE1.1, MO1.1 |
| CS1.6 | IT1.14, UT1.54, PW1.2 | SE1.1, CC1.3 |
| NF1.1 | QT_LIB_SEPARATION, QT_MIGRATION | CC1.1, CC1.2 |
| NF1.2 | UT1.1, UT1.2, UT1.3, QT_VAULT | CM1.1 |
| NF1.3 | ST1.12, UT1.55, IT1.15 | RR1.1, CP1.2 |
| NF1.4 | UT1.21, QT1.3 | RR1.1, SW1.2 |
| NF1.5 | ST1.9, ST1.10, ST_INTEGRITY, IT1.8, PW1.7 | MO1.1, DF1.1 |
| NF1.6 | UT1.49, UT1.55, IT1.15 | SP1.1, CP1.2 |
| NF1.7 | UT1.56, UT1.57 | DA1.1, AI1.4 |
| NF1.8 | QT1.4, QT_DOCS, QT_TRACEABILITY | RD1.1, TS1.1 |

## 2. Coverage map

Mandatory 10-column schema per PS-REQ-TEST-TRACE v1.0 §4.2. One row per test entity; the `requirement`
column carries the semantic `@pytest.mark.req()` binding(s) set in lane **W28E-1804A** (zero probes;
de-mechanised from the W28C-1711-R3 bindings). `last-run-commit` is populated by the Stream-B run lane.

| Test ID | Tier | Use case | Requirement | Surface | Scenario | Variants | Env files | Known issue | Last run commit |
|---|---|---|---|---|---|---|---|---|---|
| `AT-access_control_api_contract` | AT | `UC1.1` | `FR-022` | mcp | Access control api contract | — | `tests/env-AT` | — | — |
| `AT1.1` | AT | `UC1.3` | `FR-010` | mcp | Fullworkflow branch edit push | — | `tests/env-AT` | — | — |
| `AT1.2` | AT | `UC1.4` | `FR-011` | mcp | Fullworkflow tag browse | — | `tests/env-AT` | — | — |
| `AT1.3` | AT | `UC1.4` | `FR-011` | mcp | Fullworkflow conflict resolve | — | `tests/env-AT` | — | — |
| `AT1.4` | AT | `UC1.5` | `FR-012` | mcp | Fullworkflow admin profile crud | — | `tests/env-AT` | — | — |
| `AT1.5` | AT | `UC1.4` | `FR-011` | mcp | Fullworkflow recovery restore | — | `tests/env-AT` | — | — |
| `AT1.6` | AT | `UC1.6` | `FR-004` | mcp | A2a health auth contract | — | `tests/env-AT` | — | — |
| `AT1.7` | AT | `UC1.1` | `FR-022` | mcp | At jwt auth contract | — | `tests/env-AT` | — | — |
| `AT_PROFILE_LIFECYCLE` | AT | `UC1.1` | `FR-005` | mcp | Repo profile lifecycle | — | `tests/env-AT` | — | — |
| `AT_WEBUI` | AT | `UC1.2` | `FR-014`, `NF-007` | webui | Webui playwright | — | `tests/env-AT` | — | — |
| `IT1.1` | IT | `UC1.1` | `FR-002` | mcp | Api health endpoint | — | `tests/env-IT` | — | — |
| `IT1.10` | IT | `UC1.3` | `FR-007` | mcp | Remote branch push | — | `tests/env-IT` | — | — |
| `IT1.11` | IT | `UC1.6` | `FR-004` | mcp | It a2a health auth contract | — | `tests/env-IT` | — | — |
| `IT1.12` | IT | `UC1.1` | `FR-022` | mcp | It jwt auth contract | — | `tests/env-IT` | — | — |
| `IT1.13` | IT | `UC1.6` | `FR-004` | mcp | Config change event broadcast | — | `tests/env-IT` | — | — |
| `IT1.14` | IT | `UC1.5` | `FR-012` | mcp | Admin crud parity | — | `tests/env-IT` | — | — |
| `IT1.15` | IT | `UC1.2` | `FR-009` | mcp | Managed git job | — | `tests/env-IT` | — | — |
| `IT1.16` | IT | `UC1.3` | `FR-007` | mcp | Remote fetch real remote refs | — | `tests/env-IT` | — | — |
| `IT1.2` | IT | `UC1.1` | `FR-022` | mcp | Api auth reject | — | `tests/env-IT` | — | — |
| `IT1.3` | IT | `UC1.1` | `FR-022` | mcp | Api auth accept | — | `tests/env-IT` | — | — |
| `IT1.4` | IT | `UC1.5` | `FR-023` | mcp | Api rbac enforce | — | `tests/env-IT` | — | — |
| `IT1.5` | IT | `UC1.2` | `FR-003` | mcp | Mcp tool catalogue | — | `tests/env-IT` | — | — |
| `IT1.6` | IT | `UC1.2` | `FR-003` | mcp | Mcp tool execution | — | `tests/env-IT` | — | — |
| `IT1.61` | IT | `UC1.2` | `FR-018` | mcp | Seed deep flows | — | `tests/env-IT` | — | — |
| `IT1.62` | IT | `UC1.2` | `FR-009` | mcp | Deep flow jobs | — | `tests/env-IT` | — | — |
| `IT1.7` | IT | `UC1.3` | `CS-018` | mcp | Api file ops ref readonly | — | `tests/env-IT` | — | — |
| `IT1.8` | IT | `UC1.6` | `FR-016` | mcp | Correlation id propagation | — | `tests/env-IT` | — | — |
| `IT1.9` | IT | `UC1.3` | `FR-007` | mcp | Remote clone and fetch | — | `tests/env-IT` | — | — |
| `QT1.1` | QT | `UC1.6` | `CS-019` | mcp | Secrets never logged | — | `tests/env-QT` | — | — |
| `QT1.2` | QT | `UC1.1` | `CS-017` | mcp | Symlink escape prevented | — | `tests/env-QT` | — | — |
| `QT1.3` | QT | `UC1.2` | `NF-004` | mcp | Git hooks disabled | — | `tests/env-QT` | — | — |
| `QT1.4` | QT | `UC1.6` | `NF-008` | mcp | Uk english compliance | — | `tests/env-QT` | — | — |
| `QT_COMPLIANCE` | QT | `UC1.6` | `NF-001`, `NF-002`, `NF-008`, `NF-009`, `NF-010` | mcp | Qt1 security suite | — | `tests/env-QT` | — | — |
| `QT_L` | QT | `UC1.6` | `NF-009` | mcp | Logging compliance | — | `tests/env-QT` | — | — |
| `QT_PACKAGE_COMPLIANCE` | QT | `UC1.6` | `NF-009` | mcp | Package compliance | — | `tests/env-QT` | — | — |
| `ST-access_control_matrix` | ST | `UC1.6` | `FR-016`, `FR-019` | mcp | Access control matrix | — | `tests/env-ST` | — | — |
| `ST1.1` | ST | `UC1.1` | `FR-005` | mcp | Workspace create ephemeral | — | `tests/env-ST` | — | — |
| `ST1.10` | ST | `UC1.6` | `NF-005` | mcp | Audit log persistence | — | `tests/env-ST` | — | — |
| `ST1.11` | ST | `UC1.6` | `FR-020` | mcp | Database migration | — | `tests/env-ST` | — | — |
| `ST1.12` | ST | `UC1.1` | `FR-005`, `NF-003` | mcp | Workspace persistence reopen | — | `tests/env-ST` | — | — |
| `ST1.2` | ST | `UC1.1` | `FR-005` | mcp | Workspace create persistent | — | `tests/env-ST` | — | — |
| `ST1.3` | ST | `UC1.3` | `FR-010` | mcp | Branch create commit push | — | `tests/env-ST` | — | — |
| `ST1.4` | ST | `UC1.4` | `FR-011` | mcp | Tag create and list | — | `tests/env-ST` | — | — |
| `ST1.5` | ST | `UC1.4` | `FR-011` | mcp | Merge ff only | — | `tests/env-ST` | — | — |
| `ST1.6` | ST | `UC1.4` | `FR-011` | mcp | Rebase simple | — | `tests/env-ST` | — | — |
| `ST1.7` | ST | `UC1.4` | `FR-011` | mcp | Stash save and pop | — | `tests/env-ST` | — | — |
| `ST1.8` | ST | `UC1.4` | `FR-011` | mcp | Recovery on crash | — | `tests/env-ST` | — | — |
| `ST1.9` | ST | `UC1.6` | `NF-005` | mcp | Retention enforcement | — | `tests/env-ST` | — | — |
| `ST_I` | ST | `UC1.6` | `NF-005` | mcp | Integrity running | — | `tests/env-ST` | — | — |
| `ST_L` | ST | `UC1.6` | `NF-005` | mcp | Rotation config | — | `tests/env-ST` | — | — |
| `UT1.1` | UT | `UC1.1` | `FR-001` | mcp | Config loader precedence | — | `tests/env-UT` | — | — |
| `UT1.10` | UT | `UC1.3` | `CS-018` | mcp | Protected branch policy | — | `tests/env-UT` | — | — |
| `UT1.11` | UT | `UC1.5` | `FR-023` | mcp | Rbac policy eval | — | `tests/env-UT` | — | — |
| `UT1.12` | UT | `UC1.6` | `FR-016` | mcp | Audit event shape | — | `tests/env-UT` | — | — |
| `UT1.13` | UT | `UC1.6` | `FR-016` | mcp | Audit redaction | — | `tests/env-UT` | — | — |
| `UT1.14` | UT | `UC1.3` | `FR-010` | mcp | Git status parsing | — | `tests/env-UT` | — | — |
| `UT1.15` | UT | `UC1.3` | `FR-010` | mcp | Git log filtering | — | `tests/env-UT` | — | — |
| `UT1.16` | UT | `UC1.3` | `FR-010` | mcp | Git diff generation | — | `tests/env-UT` | — | — |
| `UT1.17` | UT | `UC1.4` | `FR-011` | mcp | Tag crud | — | `tests/env-UT` | — | — |
| `UT1.18` | UT | `UC1.4` | `FR-011` | mcp | Conflict detection | — | `tests/env-UT` | — | — |
| `UT1.19` | UT | `UC1.4` | `FR-011` | mcp | Conflict resolution | — | `tests/env-UT` | — | — |
| `UT1.2` | UT | `UC1.1` | `FR-001` | mcp | Config vault integration | — | `tests/env-UT` | — | — |
| `UT1.20` | UT | `UC1.4` | `FR-011` | mcp | Recovery stash | — | `tests/env-UT` | — | — |
| `UT1.21` | UT | `UC1.2` | `FR-008`, `NF-004` | mcp | File io atomic write | — | `tests/env-UT` | — | — |
| `UT1.22` | UT | `UC1.2` | `FR-008` | mcp | File search content | — | `tests/env-UT` | — | — |
| `UT1.23` | UT | `UC1.2` | `FR-021` | mcp | Structured edit json | — | `tests/env-UT` | — | — |
| `UT1.24` | UT | `UC1.2` | `FR-021` | mcp | File validation | — | `tests/env-UT` | — | — |
| `UT1.25` | UT | `UC1.2` | `FR-003` | mcp | Tool definition schemas | — | `tests/env-UT` | — | — |
| `UT1.26` | UT | `UC1.6` | `FR-004` | mcp | A2a auth validator parity | — | `tests/env-UT` | — | — |
| `UT1.27` | UT | `UC1.6` | `FR-020` | mcp | Database abstraction | — | `tests/env-UT` | — | — |
| `UT1.28` | UT | `UC1.2` | `FR-008` | mcp | File download | — | `tests/env-UT` | — | — |
| `UT1.29` | UT | `UC1.2` | `FR-008` | mcp | File move | — | `tests/env-UT` | — | — |
| `UT1.3` | UT | `UC1.1` | `FR-001`, `NF-002` | mcp | Config validation | — | `tests/env-UT` | — | — |
| `UT1.30` | UT | `UC1.2` | `FR-008` | mcp | File copy | — | `tests/env-UT` | — | — |
| `UT1.31` | UT | `UC1.2` | `FR-008` | mcp | File delete | — | `tests/env-UT` | — | — |
| `UT1.32` | UT | `UC1.2` | `FR-008` | mcp | Dir create | — | `tests/env-UT` | — | — |
| `UT1.33` | UT | `UC1.2` | `FR-008` | mcp | Dir remove | — | `tests/env-UT` | — | — |
| `UT1.34` | UT | `UC1.2` | `FR-008` | mcp | Search files | — | `tests/env-UT` | — | — |
| `UT1.35` | UT | `UC1.2` | `FR-021` | mcp | Yaml edit | — | `tests/env-UT` | — | — |
| `UT1.36` | UT | `UC1.2` | `FR-021` | mcp | Xml html edit | — | `tests/env-UT` | — | — |
| `UT1.37` | UT | `UC1.2` | `FR-021` | mcp | Sed like edit | — | `tests/env-UT` | — | — |
| `UT1.38` | UT | `UC1.3` | `FR-010` | mcp | Branch list | — | `tests/env-UT` | — | — |
| `UT1.39` | UT | `UC1.3` | `FR-010` | mcp | Branch delete | — | `tests/env-UT` | — | — |
| `UT1.4` | UT | `UC1.5` | `FR-023` | mcp | Profile model validation | — | `tests/env-UT` | — | — |
| `UT1.40` | UT | `UC1.3` | `FR-010` | mcp | Git reset | — | `tests/env-UT` | — | — |
| `UT1.41` | UT | `UC1.3` | `FR-010` | mcp | Git pull | — | `tests/env-UT` | — | — |
| `UT1.42` | UT | `UC1.3` | `FR-010` | mcp | Force push | — | `tests/env-UT` | — | — |
| `UT1.43` | UT | `UC1.4` | `FR-011` | mcp | Merge no ff | — | `tests/env-UT` | — | — |
| `UT1.44` | UT | `UC1.4` | `FR-011` | mcp | Merge abort continue | — | `tests/env-UT` | — | — |
| `UT1.45` | UT | `UC1.4` | `FR-011` | mcp | Stash list | — | `tests/env-UT` | — | — |
| `UT1.46` | UT | `UC1.4` | `FR-011` | mcp | Tag push | — | `tests/env-UT` | — | — |
| `UT1.47` | UT | `UC1.3` | `FR-010` | mcp | Author policy | — | `tests/env-UT` | — | — |
| `UT1.48` | UT | `UC1.3` | `FR-007` | mcp | Url allowlist | — | `tests/env-UT` | — | — |
| `UT1.49` | UT | `UC1.1` | `NF-006` | mcp | Session heartbeat timeout | — | `tests/env-UT` | — | — |
| `UT1.5` | UT | `UC1.1` | `FR-006` | mcp | Ref resolver branch | — | `tests/env-UT` | — | — |
| `UT1.50` | UT | `UC1.4` | `FR-011` | mcp | Recovery list get restore | — | `tests/env-UT` | — | — |
| `UT1.51` | UT | `UC1.5` | `FR-023` | mcp | Rbac tool category | — | `tests/env-UT` | — | — |
| `UT1.52` | UT | `UC1.1` | `FR-022` | mcp | Jwt auth runtime | — | `tests/env-UT` | — | — |
| `UT1.53` | UT | `UC1.1` | `FR-022` | mcp | Enterprise auth integration | — | `tests/env-UT` | — | — |
| `UT1.54` | UT | `UC1.5` | `FR-013` | mcp | Admin crud runtime | — | `tests/env-UT` | — | — |
| `UT1.55` | UT | `UC1.2` | `FR-009` | mcp | Jobs runtime | — | `tests/env-UT` | — | — |
| `UT1.56` | UT | `UC1.5` | `CS-008`, `CS-012`, `CS-016`, `FR-014`, `FR-023` | mcp, webui | Profile scoped rbac | — | `tests/env-UT` | — | — |
| `UT1.57` | UT | `UC1.6` | `FR-015` | mcp | Ui support endpoints | — | `tests/env-UT` | — | — |
| `UT1.58` | UT | `UC1.6` | `FR-004` | mcp | A2a all tools skill parity | — | `tests/env-UT` | — | — |
| `UT1.6` | UT | `UC1.1` | `FR-006` | mcp | Ref resolver tag | — | `tests/env-UT` | — | — |
| `UT1.60` | UT | `UC1.2` | `FR-018` | mcp | Workspace enum endpoints | — | `tests/env-UT` | — | — |
| `UT1.61` | UT | `UC1.6` | `FR-017` | mcp | Settings config sources | — | `tests/env-UT` | — | — |
| `UT1.62` | UT | `UC1.5` | `CS-020` | mcp | Admin permissions unauth gate | — | `tests/env-UT` | — | — |
| `UT1.63` | UT | `UC1.2` | `FR-003` | mcp | Mcp anon auth gate | — | `tests/env-UT` | — | — |
| `UT1.64` | UT | `UC1.5` | `FR-023` | mcp | Profile persistence | — | `tests/env-UT` | — | — |
| `UT1.65` | UT | `UC1.1` | `CS-001`, `CS-002`, `CS-003`, `CS-004`, `CS-005`, `CS-006`, `CS-007`, `CS-009`, `CS-010`, `CS-011`, `CS-013`, `CS-014`, `CS-015`, `FR-002` | mcp | Vestigial git mcp routes | — | `tests/env-UT` | — | — |
| `UT1.66` | UT | `UC1.1` | `FR-022` | mcp | Auth me api key principal | — | `tests/env-UT` | — | — |
| `UT1.67` | UT | `UC1.6` | `FR-016` | mcp | Per tool call audit | — | `tests/env-UT` | — | — |
| `UT1.68` | UT | `UC1.6` | `FR-004` | mcp | A2a events gone | — | `tests/env-UT` | — | — |
| `UT1.69` | UT | `UC1.1` | `FR-005` | mcp | Workspace gc | — | `tests/env-UT` | — | — |
| `UT1.7` | UT | `UC1.1` | `FR-006` | mcp | Ref resolver commit | — | `tests/env-UT` | — | — |
| `UT1.70` | UT | `UC1.1` | `FR-022` | mcp | Flat role api authz | — | `tests/env-UT` | — | — |
| `UT1.8` | UT | `UC1.1` | `FR-005` | mcp | Workspace locking | — | `tests/env-UT` | — | — |
| `UT1.9` | UT | `UC1.1` | `CS-017` | mcp | Scope enforcement | — | `tests/env-UT` | — | — |
| `UT_A` | UT | `UC1.6` | `FR-016` | mcp | Audit log format | — | `tests/env-UT` | — | — |
| `UT_L` | UT | `UC1.6` | `NF-005` | mcp | Logging surface config | — | `tests/env-UT` | — | — |

## 3. WebUI observation catalogue (GarysWorkingNotes.md L2714-2944)

The 2026-06-11 git-mcp WebUI audit's **96 GM-NNN observations** are the Stream-B/C drive-out targets.
Each GM group below binds to the requirement it refines (see `docs/REQUIREMENTS.md` §8) and to the
Playwright spec / new AT design row that must assert its closing condition. Cross-cutting shared-component
items are routed to **W28E-1825**; git-mcp-local items drive the rows below.

| Drive-out Test ID | Tier | Use case | Requirement | Surface | GM observations covered | Last run commit |
|---|---|---|---|---|---|---|
| `PW1.8` / `AT-WEBUI-DASH` | AT | `UC1.6` | `FR-014`, `FR-015` | webui | GM-DS-01..08 dashboard layout/metrics/quick-actions | — |
| `AT-WEBUI-PROFILES` | AT | `UC1.5` | `FR-023`, `FR-012`, `FR-014` | webui | GM-PR-01..08 branch dropdown, credential/sync, RBAC linkage, click-through | — |
| `AT-WEBUI-WORKSPACE` | AT | `UC1.1` | `FR-005`, `FR-018`, `FR-015` | webui | GM-WS-01..09 derived repo-source, session UX, payload/audit panels | — |
| `PW1.3` / `AT-WEBUI-BROWSER` | AT | `UC1.2` | `FR-014`, `FR-008`, `FR-018` | webui | GM-BR-01..10 file tree/viewer dialog, dropdowns | — |
| `AT-WEBUI-COMMITS-DIFF` | AT | `UC1.3` | `FR-010`, `FR-014`, `FR-018` | webui | GM-CM-01..07, GM-DV-01..03 date pickers, drill-through, diff render | — |
| `PW1.4` / `AT-WEBUI-BRANCH-MERGE-TAG-STASH` | AT | `UC1.4` | `FR-011`, `FR-014`, `FR-018` | webui | GM-BC/MR/TG/SH-* branch/merge/tag/stash managers | — |
| `PW1.6` / `AT-WEBUI-RECOVERY` | AT | `UC1.4` | `FR-011`, `FR-014`, `FR-018` | webui | GM-RC-01..08 recovery selection/affordances/payload | — |
| `PW1.7` / `AT-WEBUI-AUDIT` | AT | `UC1.6` | `FR-016`, `FR-015` | webui | GM-AL-01..04 audit page consistency, source filters, action labels | — |
| `AT-WEBUI-ADMIN` | AT | `UC1.5` | `FR-012`, `FR-023` | webui | GM-US/GP/AK/RB/RL-* shared idam admin pages | — |
| `AT-WEBUI-DEVCONSOLES` | AT | `UC1.6` | `FR-002`, `FR-003`, `FR-004`, `FR-014` | webui | GM-AD-01..03, GM-MC-01/02, GM-AA-01..03 API-docs/MCP/A2A consoles | — |
| `AT-WEBUI-JOBS` | AT | `UC1.6` | `FR-009`, `FR-016`, `FR-014` | webui | GM-JB-01..07 jobs detail dialog, columns, audit link, sync/async | — |
| `AT-WEBUI-SETTINGS-ABOUT` | AT | `UC1.6` | `FR-017`, `FR-014` | webui | GM-ST-01..03, GM-AB-01 settings save/import, About nav→modal | — |

## 4. Supplement E2E acceptance walkthrough — design rows (W28C-1711 SUPPLEMENT, NEW-AT)

The `gitmcpserver/E2E git-mcp-server.md` supplement (operator decision **NEW-AT**, 2026-06-23) is an a–s
end-to-end acceptance walkthrough of the delivered surface. Each section becomes an explicit AT
test-design row binding to existing requirements; these are Stream-B (functional E2E) and Stream-C (WebUI
E2E) drive-out targets. No new FR was created (capability already delivered; see `02-knowledge-ingest-manifest.tsv`).

| Test ID | Tier | Use case | Requirement | Surface | Scenario (supplement section) | Last run commit |
|---|---|---|---|---|---|---|
| `AT-E2E-a` | AT | `UC1.5` | `FR-012`, `FR-023` | api, webui | (a) Profile configuration CRUD, repo source & policy, RBAC matrix | — |
| `AT-E2E-b` | AT | `UC1.1` | `FR-005`, `FR-009` | mcp, webui | (b) Workspace lifecycle: open, use, close & diagnostics, TTL cleanup | — |
| `AT-E2E-c` | AT | `UC1.3` | `FR-010`, `FR-006` | mcp | (c) Git status, log & diff read-only operations incl. read-only ref | — |
| `AT-E2E-d` | AT | `UC1.2` | `FR-008` | mcp | (d) File operations: browse, read, write, upload/download, scope enforcement | — |
| `AT-E2E-e` | AT | `UC1.2` | `FR-008` | mcp | (e) Search — content & file name (regex, case, globs, max_results) | — |
| `AT-E2E-f` | AT | `UC1.3` | `FR-010`, `CS-018` | mcp | (f) Staging, commit & push lifecycle incl. protected-branch denial | — |
| `AT-E2E-g` | AT | `UC1.3` | `FR-010` | mcp | (g) Branching — create, switch, list, delete, from-ref, protected denial | — |
| `AT-E2E-h` | AT | `UC1.4` | `FR-011` | mcp | (h) Merge, rebase & conflict resolution (ours/manual/abort/continue/ff_only) | — |
| `AT-E2E-i` | AT | `UC1.4` | `FR-011` | mcp, webui | (i) Stash & recovery (save/list/pop; recovery artefacts inspect/restore) | — |
| `AT-E2E-j` | AT | `UC1.4` | `FR-011` | mcp | (j) Tags — create (lightweight/annotated), list, push, delete, filters | — |
| `AT-E2E-k` | AT | `UC1.5` | `FR-023`, `CS-002`, `CS-018` | mcp | (k) RBAC enforcement across read vs. mutation ops; reader→writer upgrade | — |
| `AT-E2E-l` | AT | `UC1.2` | `FR-014`, `FR-008` | webui | (l) Repository browser — file tree, viewer & inline editor, deny-glob | — |
| `AT-E2E-m` | AT | `UC1.3` | `FR-014`, `FR-010` | webui | (m) Commit log viewer — history timeline with filtering & detail | — |
| `AT-E2E-n` | AT | `UC1.3` | `FR-014`, `FR-010` | webui | (n) Diff viewer — unified & side-by-side display | — |
| `AT-E2E-o` | AT | `UC1.3` | `FR-014`, `FR-010` | webui | (o) Branch manager — list, create, switch, delete & protection indicators | — |
| `AT-E2E-p` | AT | `UC1.4` | `FR-014`, `FR-011` | webui | (p) Merge & conflict resolution UI (three-way, accept ours/theirs/manual) | — |
| `AT-E2E-q` | AT | `UC1.4` | `FR-014`, `FR-011` | webui | (q) Tag manager — browse, create, push, delete | — |
| `AT-E2E-r` | AT | `UC1.4` | `FR-014`, `FR-011` | webui | (r) Stash manager — list, save, pop, drop | — |
| `AT-E2E-s` | AT | `UC1.6` | `FR-016`, `FR-015` | webui | (s) Audit log verification — every a–r action faithfully logged & formatted | — |
