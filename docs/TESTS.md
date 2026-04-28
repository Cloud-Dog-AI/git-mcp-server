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

## Supporting Test Entries

| Test ID | Suite | Test module(s) |
|---|---|---|
| AT_PROFILE_LIFECYCLE | Application | `test_repo_profile_lifecycle.py` |
| QT26 | Quality | `test_qt26_secrets_separation.py` |
| QT_DOCS | Quality | `test_qt3_documentation_suite.py` |
| QT_LIB_SEPARATION | Quality | `test_qt_library_server_separation.py` |
| QT_MIGRATION | Quality | `test_qt_migration_completeness.py` |
| QT_PACKAGE | Quality | `test_qt_package_adoption.py`, `test_package_compliance.py` |
| QT_RULES | Quality | `test_qt_rules_compliance.py` |
| QT_TRACEABILITY | Quality | `test_qt_traceability.py` |
| QT_VAULT | Quality | `test_qt_vault_config_contract.py` |
| ST_INTEGRITY | System | `test_integrity_running.py` |
| UT_AUDIT_FORMAT | Unit | `test_audit_log_format.py` |
| UT_LOGGING_CONFIG | Unit | `test_logging_surface_config.py` |

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
| FR1.11 | UT1.17, UT1.18, UT1.19, UT1.20, UT1.44, UT1.45, UT1.46, UT1.50, ST1.4, ST1.7, ST1.8, AT1.3, AT1.5, PW1.4, PW1.5, PW1.6 | SW1.2, RR1.1 |
| FR1.12 | AT1.4, IT1.14, UT1.54, PW1.2 | CC1.3, AI1.1 |
| FR1.13 | UT1.54, IT1.14, PW1.2 | CC1.3, AI1.2 |
| FR1.14 | UT1.56, PW1.8, PW1.9 | AI1.4, DA1.1 |
| FR1.15 | UT1.57, PW1.7, PW1.9 | MO1.1, AI1.4 |
| FR1.16 | UT1.12, UT1.13, ST1.9, ST1.10, IT1.8, IT1.15, PW1.7 | DF1.1, MO1.1 |
| FR1.17 | UT1.27, ST1.11, IT1.14 | DM1.1, RR1.1 |
| FR1.18 | UT1.23, UT1.24, UT1.35, UT1.36, UT1.37 | CC1.2, TS1.1 |

### Use-Case, Security, and Non-Functional Coverage

| Requirement ID | Test IDs | Architecture refs |
|---|---|---|
| UC1.1 | AT_PROFILE_LIFECYCLE, ST1.1, ST1.12, IT1.9 | SW1.1, CP1.1 |
| UC1.2 | AT1.1, UT1.28, UT1.34, PW1.3, PW1.8 | CP1.1, AI1.4 |
| UC1.3 | ST1.3, IT1.10, PW1.3, PW1.8 | SW1.2, AI1.4 |
| UC1.4 | AT1.2, AT1.3, AT1.5, PW1.4, PW1.5, PW1.6 | SW1.2, RR1.1 |
| UC1.5 | AT1.4, IT1.14, PW1.2, PW1.8 | CC1.3, AI1.4 |
| UC1.6 | IT1.13, IT1.8, PW1.7, PW1.9 | DF1.1, MO1.1, AI1.3 |
| CS1.1 | IT1.2, IT1.3, IT1.11, IT1.12, AT1.6, AT1.7, PW1.1 | SE1.1, AI1.1, AI1.2, AI1.3 |
| CS1.2 | IT1.4, UT1.11, UT1.51, UT1.56, PW1.2 | SE1.1, CP1.1 |
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
| NF1.8 | QT_DOCS, QT_TRACEABILITY | RD1.1, TS1.1 |
