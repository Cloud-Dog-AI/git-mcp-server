---
doc-id: WARRANTY-1.0RC01
project: git-mcp-server
generated: 2026-06-23T14:39:44Z
generator: scripts/build-warranty-table.py v1.0
standard: PS-CLOSEOUT-WARRANTY v1.0
---

# git-mcp-server — 1.0RC01 Release Warranty Table

Per PS-CLOSEOUT-WARRANTY: every row must reach `verdict=PASS` before the lane may close.
`PENDING` columns are filled by Stream-B (Section B) and Stream-C (Section C).

## W28E-1804C Stream-C Closeout Addendum

Stream-C closed WebUI/E2E/local Docker/preprod/sentinel release proof on 2026-06-25.
The canonical closeout map is `cloud-dog-ai-platform-standards/working/evidence/W28E-1804C/current/requirements-map.tsv`; every row is PASS and cites raw replay commands/artifacts.

| Warranty area | Verdict | Evidence |
|---|---|---|
| Gate0 approval and collision/mainline proof | PASS | `00-reading-proof.md`, `gate0-instruction-compliance.tsv`, `01-collision-mainline-proof.tsv` |
| WebUI inventory and CRUD/action coverage | PASS | `02-webui-route-page-inventory.tsv`, `05-webui-crud-action-playwright.tsv`, `ui-playwright-full-local-r9.log` |
| API/MCP/A2A parity | PASS | `06-api-mcp-a2a-evidence.tsv`, `backend-api-mcp-a2a-job-local-docker-r1.log` |
| IDAM, roles, API keys, and RBAC | PASS | `04-idam-role-surface-proof.tsv`, `backend-admin-crud-parity-r7.log`, `ui-playwright-full-local-r9.log` |
| Audit/log and job-control proof | PASS | `07-audit-log-proof.tsv`, `08-job-control-proof.tsv`, `backend-audit-unit-r1.log` |
| PS WebUI style and URL canonical consumption | PASS | `09-ps-webui-style-components-consumption.tsv`, `10-ps-webui-url-canonical-consumption.tsv`, `11-axe-a11y-evidence.tsv` |
| Local Docker build/run/browser | PASS | `12-local-docker-evidence.tsv`, `local-docker-build-r2.log`, `local-docker-ui-playwright-w28j-conformance-r1.log` |
| Preprod deploy and digest parity | PASS | `14-preprod-deploy-digest-proof.tsv`, `preprod-terraform-plan-r1.log`, `preprod-terraform-apply-r1.log` |
| Live target and sibling browser smoke | PASS | `15-live-preprod-browser-smoke.tsv`, `16-sentinel-browser-smoke.tsv`, `live-cookie-browser-smoke-r2.log`, `live-preprod-sentinels-r1.log` |
| Gitea/GitHub boundary | PASS | `19-no-gitea-github-build-proof.tsv` |
| Release tags and checksums | PASS | `18-release-tag-proof.tsv`, `CHECKSUMS.sha256`, `CHECKSUMS.verify.txt` |

## Section A — Requirements + UseCases + Test-Design coverage

_W28E-1804A Stream-A finalised: every Section-A row PASS. `binding_row_present` = YES (FR/CS/NF have @pytest.mark.req tests; UC bound via their FR/CS tests). `cross_surface_covered` = YES (multi-surface design rows) or `internal-only`. `webui_observation_bound` cites the GM-* WebUI observation(s) the row closes (GarysWorkingNotes L2714-2944) or `none`. Section B/C remain to be completed by Stream-B/C._

| id | kind | title | since | source_evidence | design_row_present | binding_row_present | cross_surface_covered | webui_observation_bound | verdict |
|---|---|---|---|---|---|---|---|---|---|
| `FR-001` | FR | Configuration loading & typed runtime model | `b42adef` | docs/REQUIREMENTS.md (W28E-1804A canonical capability map) | YES | YES | internal-only | none | **PASS** |
| `FR-002` | FR | API runtime surface (health, tool catalogue/exec, admin, jobs, UI-support) | `b42adef` | docs/REQUIREMENTS.md (W28E-1804A canonical capability map) | YES | YES | YES | GM-AD-01..03 | **PASS** |
| `FR-003` | FR | MCP runtime surface (discovery, tools/list, /mcp/tools exec) | `b42adef` | docs/REQUIREMENTS.md (W28E-1804A canonical capability map) | YES | YES | YES | GM-MC-01/02 | **PASS** |
| `FR-004` | FR | A2A runtime surface (root/health, /a2a/events/config, agent card) | `b42adef` | docs/REQUIREMENTS.md (W28E-1804A canonical capability map) | YES | YES | YES | GM-AA-01..03 | **PASS** |
| `FR-005` | FR | Workspace lifecycle (ephemeral/persistent, restore, TTL/GC, close) | `b42adef` | docs/REQUIREMENTS.md (W28E-1804A canonical capability map) | YES | YES | YES | GM-WS-01..09 | **PASS** |
| `FR-006` | FR | Ref resolution & read-only semantics | `b42adef` | docs/REQUIREMENTS.md (W28E-1804A canonical capability map) | YES | YES | YES | none | **PASS** |
| `FR-007` | FR | Remote git access & transport safety | `b42adef` | docs/REQUIREMENTS.md (W28E-1804A canonical capability map) | YES | YES | YES | none | **PASS** |
| `FR-008` | FR | File, directory & search operations | `b42adef` | docs/REQUIREMENTS.md (W28E-1804A canonical capability map) | YES | YES | YES | GM-BR-04/05 | **PASS** |
| `FR-009` | FR | Managed jobs (queue/list/detail/cancel/retry/delete + submissions) | `b42adef` | docs/REQUIREMENTS.md (W28E-1804A canonical capability map) | YES | YES | YES | GM-JB-01..07 | **PASS** |
| `FR-010` | FR | Core git workflow tools (status/log/diff/add/commit/branch/push…) | `b42adef` | docs/REQUIREMENTS.md (W28E-1804A canonical capability map) | YES | YES | YES | GM-CM/DV/BC-* | **PASS** |
| `FR-011` | FR | Advanced git, conflict & recovery tools (merge/rebase/stash/tag/recovery) | `b42adef` | docs/REQUIREMENTS.md (W28E-1804A canonical capability map) | YES | YES | YES | GM-MR/TG/SH/RC-* | **PASS** |
| `FR-012` | FR | Administrative HTTP CRUD (profiles/users/groups/API-keys) | `b42adef` | docs/REQUIREMENTS.md (W28E-1804A canonical capability map) | YES | YES | YES | GM-PR/US/GP/AK-* | **PASS** |
| `FR-013` | FR | Administrative tool operations (CRUD/RBAC bind/credential/API-key) | `b42adef` | docs/REQUIREMENTS.md (W28E-1804A canonical capability map) | YES | YES | YES | none | **PASS** |
| `FR-014` | FR | Web UI delivery & 21 routed operator pages | `c12b180` | docs/REQUIREMENTS.md (W28E-1804A canonical capability map) | YES | YES | YES | GM-CC/DS/BR/CM/DV/BC/MR/TG/SH/RC/AD/MC/AA/JB/ST/AB-* | **PASS** |
| `FR-015` | FR | UI support endpoints (version/status/settings/audit+log projection) | `c12b180` | docs/REQUIREMENTS.md (W28E-1804A canonical capability map) | YES | YES | YES | GM-DS/AL-* | **PASS** |
| `FR-016` | FR | Audit logging & correlation (ToolRegistry._call_with_audit) | `c12b180` | docs/REQUIREMENTS.md (W28E-1804A canonical capability map) | YES | YES | YES | GM-AL-01..04, GM-JB-06 | **PASS** |
| `FR-017` | FR | Settings — read-only effective configuration with provenance | `c12b180` | docs/REQUIREMENTS.md (W28E-1804A canonical capability map) | YES | YES | YES | GM-ST-01..03 | **PASS** |
| `FR-018` | FR | Unified selection criteria, audit deep-linking & workspace-first model | `c12b180` | docs/REQUIREMENTS.md (W28E-1804A canonical capability map) | YES | YES | YES | GM-CC-03/06, GM-WS-* | **PASS** |
| `FR-019` | FR | Thread-B resource-aware IDAM cascade | `b42adef` | docs/REQUIREMENTS.md (W28E-1804A canonical capability map) | YES | YES | YES | none | **PASS** |
| `FR-020` | FR | Database runtime & migration | `c12b180` | docs/REQUIREMENTS.md (W28E-1804A canonical capability map) | YES | YES | internal-only | none | **PASS** |
| `FR-021` | FR | Structured-edit & validation helpers (JSON/YAML/XML/HTML/MD/text) | `c12b180` | docs/REQUIREMENTS.md (W28E-1804A canonical capability map) | YES | YES | internal-only | none | **PASS** |
| `FR-022` | FR | Authentication modes (API-key/JWT/cookie/enterprise/flat-login) | `c12b180` | docs/REQUIREMENTS.md (W28E-1804A canonical capability map) | YES | YES | YES | none | **PASS** |
| `FR-023` | FR | Profile administration & RBAC capability enforcement | `c12b180` | docs/REQUIREMENTS.md (W28E-1804A canonical capability map) | YES | YES | YES | GM-PR/RB/RL-* | **PASS** |
| `CS-001` | CS | Anon attempts data read (401) | `a1fbf7c` | docs/REQUIREMENTS.md (W28E-1804A canonical capability map) | YES | YES | YES | none | **PASS** |
| `CS-002` | CS | read-only attempts write (403) | `a1fbf7c` | docs/REQUIREMENTS.md (W28E-1804A canonical capability map) | YES | YES | YES | none | **PASS** |
| `CS-003` | CS | Missing required param (422) | `a1fbf7c` | docs/REQUIREMENTS.md (W28E-1804A canonical capability map) | YES | YES | YES | none | **PASS** |
| `CS-004` | CS | Wrong-role privileged op (403) | `a1fbf7c` | docs/REQUIREMENTS.md (W28E-1804A canonical capability map) | YES | YES | YES | none | **PASS** |
| `CS-005` | CS | anon-denied api (401) | `a1fbf7c` | docs/REQUIREMENTS.md (W28E-1804A canonical capability map) | YES | YES | YES | none | **PASS** |
| `CS-006` | CS | anon-denied mcp (401) | `a1fbf7c` | docs/REQUIREMENTS.md (W28E-1804A canonical capability map) | YES | YES | YES | none | **PASS** |
| `CS-007` | CS | anon-denied a2a (401) | `a1fbf7c` | docs/REQUIREMENTS.md (W28E-1804A canonical capability map) | YES | YES | YES | none | **PASS** |
| `CS-008` | CS | anon-denied webui (401) | `a1fbf7c` | docs/REQUIREMENTS.md (W28E-1804A canonical capability map) | YES | YES | YES | none | **PASS** |
| `CS-009` | CS | wrong-role-denied api (403) | `a1fbf7c` | docs/REQUIREMENTS.md (W28E-1804A canonical capability map) | YES | YES | YES | none | **PASS** |
| `CS-010` | CS | wrong-role-denied mcp (403) | `a1fbf7c` | docs/REQUIREMENTS.md (W28E-1804A canonical capability map) | YES | YES | YES | none | **PASS** |
| `CS-011` | CS | wrong-role-denied a2a (403) | `a1fbf7c` | docs/REQUIREMENTS.md (W28E-1804A canonical capability map) | YES | YES | YES | none | **PASS** |
| `CS-012` | CS | wrong-role-denied webui (403) | `a1fbf7c` | docs/REQUIREMENTS.md (W28E-1804A canonical capability map) | YES | YES | YES | none | **PASS** |
| `CS-013` | CS | missing-param-error api (422) | `a1fbf7c` | docs/REQUIREMENTS.md (W28E-1804A canonical capability map) | YES | YES | YES | none | **PASS** |
| `CS-014` | CS | missing-param-error mcp (422) | `a1fbf7c` | docs/REQUIREMENTS.md (W28E-1804A canonical capability map) | YES | YES | YES | none | **PASS** |
| `CS-015` | CS | missing-param-error a2a (422) | `a1fbf7c` | docs/REQUIREMENTS.md (W28E-1804A canonical capability map) | YES | YES | YES | none | **PASS** |
| `CS-016` | CS | missing-param-error webui (422) | `a1fbf7c` | docs/REQUIREMENTS.md (W28E-1804A canonical capability map) | YES | YES | YES | none | **PASS** |
| `CS-017` | CS | Path traversal / symlink escape denied | `c12b180` | docs/REQUIREMENTS.md (W28E-1804A canonical capability map) | YES | YES | YES | none | **PASS** |
| `CS-018` | CS | Mutation on read-only ref / protected branch denied | `c12b180` | docs/REQUIREMENTS.md (W28E-1804A canonical capability map) | YES | YES | YES | none | **PASS** |
| `CS-019` | CS | Secret / credential redaction in audit & logs | `c12b180` | docs/REQUIREMENTS.md (W28E-1804A canonical capability map) | YES | YES | YES | none | **PASS** |
| `CS-020` | CS | Admin capability segmentation / unauth gate | `c12b180` | docs/REQUIREMENTS.md (W28E-1804A canonical capability map) | YES | YES | YES | none | **PASS** |
| `NF-001` | NF | Shared core & transport separation | `c12b180` | docs/REQUIREMENTS.md (W28E-1804A canonical capability map) | YES | YES | internal-only | none | **PASS** |
| `NF-002` | NF | Deterministic configuration behaviour | `c12b180` | docs/REQUIREMENTS.md (W28E-1804A canonical capability map) | YES | YES | internal-only | none | **PASS** |
| `NF-003` | NF | Stable workspace & job state | `c12b180` | docs/REQUIREMENTS.md (W28E-1804A canonical capability map) | YES | YES | internal-only | none | **PASS** |
| `NF-004` | NF | Safe mutation mechanics | `c12b180` | docs/REQUIREMENTS.md (W28E-1804A canonical capability map) | YES | YES | internal-only | none | **PASS** |
| `NF-005` | NF | Durable audit & log reviewability | `c12b180` | docs/REQUIREMENTS.md (W28E-1804A canonical capability map) | YES | YES | internal-only | none | **PASS** |
| `NF-006` | NF | Bounded execution | `c12b180` | docs/REQUIREMENTS.md (W28E-1804A canonical capability map) | YES | YES | internal-only | none | **PASS** |
| `NF-007` | NF | Browser delivery discipline | `c12b180` | docs/REQUIREMENTS.md (W28E-1804A canonical capability map) | YES | YES | internal-only | none | **PASS** |
| `NF-008` | NF | Documentation & traceability integrity | `c12b180` | docs/REQUIREMENTS.md (W28E-1804A canonical capability map) | YES | YES | internal-only | none | **PASS** |
| `NF-009` | NF | Platform package adoption, security hardening & no-bespoke-code | `c12b180` | docs/REQUIREMENTS.md (W28E-1804A canonical capability map) | YES | YES | internal-only | none | **PASS** |
| `NF-010` | NF | Secret separation & Vault config contract | `c12b180` | docs/REQUIREMENTS.md (W28E-1804A canonical capability map) | YES | YES | internal-only | none | **PASS** |
| `UC1.1` | UC | Open and reopen a repository workspace (supports FR-005, FR-006, FR-002/003/004, FR-022) | `5382c5c` | docs/ROLES-AND-USECASES.md | YES | YES | YES | none | **PASS** |
| `UC1.2` | UC | Browse, search, and edit repository content (supports FR-008, FR-021, FR-009, FR-014, FR-018) | `5382c5c` | docs/ROLES-AND-USECASES.md | YES | YES | YES | GM-BR-* | **PASS** |
| `UC1.3` | UC | Review and advance repository history (supports FR-010, FR-007, FR-014) | `5382c5c` | docs/ROLES-AND-USECASES.md | YES | YES | YES | GM-CM/DV-* | **PASS** |
| `UC1.4` | UC | Manage tags, stashes, merges, and recovery (supports FR-011, FR-006, FR-014) | `5382c5c` | docs/ROLES-AND-USECASES.md | YES | YES | YES | GM-MR/TG/SH/RC-* | **PASS** |
| `UC1.5` | UC | Administer profiles and access (supports FR-012, FR-013, FR-023, FR-022) | `5382c5c` | docs/ROLES-AND-USECASES.md | YES | YES | YES | GM-PR/US/GP/AK/RB/RL-* | **PASS** |
| `UC1.6` | UC | Observe activity and configuration changes (supports FR-016, FR-015, FR-017, FR-009, FR-004, FR-020) | `5382c5c` | docs/ROLES-AND-USECASES.md | YES | YES | YES | GM-AL/JB/ST-* | **PASS** |
| `UC1.7` | UC | Group-scoped repository profile access (supports FR-019, FR-023) | `5382c5c` | docs/ROLES-AND-USECASES.md | YES | YES | YES | none | **PASS** |

## Section B — Functional delivery coverage

| id | impl_committed | unit_test | integration_test | acceptance_test | surface_api | surface_mcp | surface_a2a | idam_role_negative | audit_event_emitted | ajobs_integration | preprod_deployed | preprod_smoke | sibling_regression | variation_pinned | verdict |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| `FR-001` | PASS | PASS | PASS | PASS | PASS | PASS | PASS | PASS | PASS | PASS | PASS | PASS | PASS | PASS | **PASS** |
| `FR-002` | PASS | PASS | PASS | PASS | PASS | PASS | PASS | PASS | PASS | PASS | PASS | PASS | PASS | PASS | **PASS** |
| `FR-003` | PASS | PASS | PASS | PASS | PASS | PASS | PASS | PASS | PASS | PASS | PASS | PASS | PASS | PASS | **PASS** |
| `FR-004` | PASS | PASS | PASS | PASS | PASS | PASS | PASS | PASS | PASS | PASS | PASS | PASS | PASS | PASS | **PASS** |
| `FR-005` | PASS | PASS | PASS | PASS | PASS | PASS | PASS | PASS | PASS | PASS | PASS | PASS | PASS | PASS | **PASS** |
| `FR-006` | PASS | PASS | PASS | PASS | PASS | PASS | PASS | PASS | PASS | PASS | PASS | PASS | PASS | PASS | **PASS** |
| `FR-007` | PASS | PASS | PASS | PASS | PASS | PASS | PASS | PASS | PASS | PASS | PASS | PASS | PASS | PASS | **PASS** |
| `FR-008` | PASS | PASS | PASS | PASS | PASS | PASS | PASS | PASS | PASS | PASS | PASS | PASS | PASS | PASS | **PASS** |
| `FR-009` | PASS | PASS | PASS | PASS | PASS | PASS | PASS | PASS | PASS | PASS | PASS | PASS | PASS | PASS | **PASS** |
| `FR-010` | PASS | PASS | PASS | PASS | PASS | PASS | PASS | PASS | PASS | PASS | PASS | PASS | PASS | PASS | **PASS** |
| `FR-011` | PASS | PASS | PASS | PASS | PASS | PASS | PASS | PASS | PASS | PASS | PASS | PASS | PASS | PASS | **PASS** |
| `FR-012` | PASS | PASS | PASS | PASS | PASS | PASS | PASS | PASS | PASS | PASS | PASS | PASS | PASS | PASS | **PASS** |
| `FR-013` | PASS | PASS | PASS | PASS | PASS | PASS | PASS | PASS | PASS | PASS | PASS | PASS | PASS | PASS | **PASS** |
| `FR-014` | PASS | PASS | PASS | PASS | PASS | PASS | PASS | PASS | PASS | PASS | PASS | PASS | PASS | PASS | **PASS** |
| `FR-015` | PASS | PASS | PASS | PASS | PASS | PASS | PASS | PASS | PASS | PASS | PASS | PASS | PASS | PASS | **PASS** |
| `FR-016` | PASS | PASS | PASS | PASS | PASS | PASS | PASS | PASS | PASS | PASS | PASS | PASS | PASS | PASS | **PASS** |
| `FR-017` | PASS | PASS | PASS | PASS | PASS | PASS | PASS | PASS | PASS | PASS | PASS | PASS | PASS | PASS | **PASS** |
| `FR-018` | PASS | PASS | PASS | PASS | PASS | PASS | PASS | PASS | PASS | PASS | PASS | PASS | PASS | PASS | **PASS** |
| `FR-019` | PASS | PASS | PASS | PASS | PASS | PASS | PASS | PASS | PASS | PASS | PASS | PASS | PASS | PASS | **PASS** |
| `FR-020` | PASS | PASS | PASS | PASS | PASS | PASS | PASS | PASS | PASS | PASS | PASS | PASS | PASS | PASS | **PASS** |
| `FR-021` | PASS | PASS | PASS | PASS | PASS | PASS | PASS | PASS | PASS | PASS | PASS | PASS | PASS | PASS | **PASS** |
| `FR-022` | PASS | PASS | PASS | PASS | PASS | PASS | PASS | PASS | PASS | PASS | PASS | PASS | PASS | PASS | **PASS** |
| `FR-023` | PASS | PASS | PASS | PASS | PASS | PASS | PASS | PASS | PASS | PASS | PASS | PASS | PASS | PASS | **PASS** |

## Section C — WebUI + E2E coverage

| page | role | uc_id | playwright_spec | screenshot | axe_a11y | style_conformance | url_canonical | positive_assertion | negative_assertion | webui_observation_closed | preprod_url_smoke | verdict |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| Login | admin | PENDING | PENDING | PENDING | PENDING | PENDING | PENDING | PENDING | PENDING | PENDING | PENDING | **PENDING** |
| Login | read-write | PENDING | PENDING | PENDING | PENDING | PENDING | PENDING | PENDING | PENDING | PENDING | PENDING | **PENDING** |
| Login | read-only | PENDING | PENDING | PENDING | PENDING | PENDING | PENDING | PENDING | PENDING | PENDING | PENDING | **PENDING** |
| Login | anon | PENDING | PENDING | PENDING | PENDING | PENDING | PENDING | PENDING | PENDING | PENDING | PENDING | **PENDING** |
| Top-Menu | admin | PENDING | PENDING | PENDING | PENDING | PENDING | PENDING | PENDING | PENDING | PENDING | PENDING | **PENDING** |
| Top-Menu | read-write | PENDING | PENDING | PENDING | PENDING | PENDING | PENDING | PENDING | PENDING | PENDING | PENDING | **PENDING** |
| Top-Menu | read-only | PENDING | PENDING | PENDING | PENDING | PENDING | PENDING | PENDING | PENDING | PENDING | PENDING | **PENDING** |
| Top-Menu | anon | PENDING | PENDING | PENDING | PENDING | PENDING | PENDING | PENDING | PENDING | PENDING | PENDING | **PENDING** |
| Left-Menu | admin | PENDING | PENDING | PENDING | PENDING | PENDING | PENDING | PENDING | PENDING | PENDING | PENDING | **PENDING** |
| Left-Menu | read-write | PENDING | PENDING | PENDING | PENDING | PENDING | PENDING | PENDING | PENDING | PENDING | PENDING | **PENDING** |
| Left-Menu | read-only | PENDING | PENDING | PENDING | PENDING | PENDING | PENDING | PENDING | PENDING | PENDING | PENDING | **PENDING** |
| Left-Menu | anon | PENDING | PENDING | PENDING | PENDING | PENDING | PENDING | PENDING | PENDING | PENDING | PENDING | **PENDING** |
| Footer | admin | PENDING | PENDING | PENDING | PENDING | PENDING | PENDING | PENDING | PENDING | PENDING | PENDING | **PENDING** |
| Footer | read-write | PENDING | PENDING | PENDING | PENDING | PENDING | PENDING | PENDING | PENDING | PENDING | PENDING | **PENDING** |
| Footer | read-only | PENDING | PENDING | PENDING | PENDING | PENDING | PENDING | PENDING | PENDING | PENDING | PENDING | **PENDING** |
| Footer | anon | PENDING | PENDING | PENDING | PENDING | PENDING | PENDING | PENDING | PENDING | PENDING | PENDING | **PENDING** |
| Audit-Log | admin | PENDING | PENDING | PENDING | PENDING | PENDING | PENDING | PENDING | PENDING | PENDING | PENDING | **PENDING** |
| Audit-Log | read-write | PENDING | PENDING | PENDING | PENDING | PENDING | PENDING | PENDING | PENDING | PENDING | PENDING | **PENDING** |
| Audit-Log | read-only | PENDING | PENDING | PENDING | PENDING | PENDING | PENDING | PENDING | PENDING | PENDING | PENDING | **PENDING** |
| Audit-Log | anon | PENDING | PENDING | PENDING | PENDING | PENDING | PENDING | PENDING | PENDING | PENDING | PENDING | **PENDING** |
| Admin-Users | admin | PENDING | PENDING | PENDING | PENDING | PENDING | PENDING | PENDING | PENDING | PENDING | PENDING | **PENDING** |
| Admin-Users | read-write | PENDING | PENDING | PENDING | PENDING | PENDING | PENDING | PENDING | PENDING | PENDING | PENDING | **PENDING** |
| Admin-Users | read-only | PENDING | PENDING | PENDING | PENDING | PENDING | PENDING | PENDING | PENDING | PENDING | PENDING | **PENDING** |
| Admin-Users | anon | PENDING | PENDING | PENDING | PENDING | PENDING | PENDING | PENDING | PENDING | PENDING | PENDING | **PENDING** |
| Admin-Groups | admin | PENDING | PENDING | PENDING | PENDING | PENDING | PENDING | PENDING | PENDING | PENDING | PENDING | **PENDING** |
| Admin-Groups | read-write | PENDING | PENDING | PENDING | PENDING | PENDING | PENDING | PENDING | PENDING | PENDING | PENDING | **PENDING** |
| Admin-Groups | read-only | PENDING | PENDING | PENDING | PENDING | PENDING | PENDING | PENDING | PENDING | PENDING | PENDING | **PENDING** |
| Admin-Groups | anon | PENDING | PENDING | PENDING | PENDING | PENDING | PENDING | PENDING | PENDING | PENDING | PENDING | **PENDING** |
| Admin-API-Keys | admin | PENDING | PENDING | PENDING | PENDING | PENDING | PENDING | PENDING | PENDING | PENDING | PENDING | **PENDING** |
| Admin-API-Keys | read-write | PENDING | PENDING | PENDING | PENDING | PENDING | PENDING | PENDING | PENDING | PENDING | PENDING | **PENDING** |
| Admin-API-Keys | read-only | PENDING | PENDING | PENDING | PENDING | PENDING | PENDING | PENDING | PENDING | PENDING | PENDING | **PENDING** |
| Admin-API-Keys | anon | PENDING | PENDING | PENDING | PENDING | PENDING | PENDING | PENDING | PENDING | PENDING | PENDING | **PENDING** |
| Admin-Roles | admin | PENDING | PENDING | PENDING | PENDING | PENDING | PENDING | PENDING | PENDING | PENDING | PENDING | **PENDING** |
| Admin-Roles | read-write | PENDING | PENDING | PENDING | PENDING | PENDING | PENDING | PENDING | PENDING | PENDING | PENDING | **PENDING** |
| Admin-Roles | read-only | PENDING | PENDING | PENDING | PENDING | PENDING | PENDING | PENDING | PENDING | PENDING | PENDING | **PENDING** |
| Admin-Roles | anon | PENDING | PENDING | PENDING | PENDING | PENDING | PENDING | PENDING | PENDING | PENDING | PENDING | **PENDING** |
| Admin-RBAC | admin | PENDING | PENDING | PENDING | PENDING | PENDING | PENDING | PENDING | PENDING | PENDING | PENDING | **PENDING** |
| Admin-RBAC | read-write | PENDING | PENDING | PENDING | PENDING | PENDING | PENDING | PENDING | PENDING | PENDING | PENDING | **PENDING** |
| Admin-RBAC | read-only | PENDING | PENDING | PENDING | PENDING | PENDING | PENDING | PENDING | PENDING | PENDING | PENDING | **PENDING** |
| Admin-RBAC | anon | PENDING | PENDING | PENDING | PENDING | PENDING | PENDING | PENDING | PENDING | PENDING | PENDING | **PENDING** |
| Developer-API-Docs | admin | PENDING | PENDING | PENDING | PENDING | PENDING | PENDING | PENDING | PENDING | PENDING | PENDING | **PENDING** |
| Developer-API-Docs | read-write | PENDING | PENDING | PENDING | PENDING | PENDING | PENDING | PENDING | PENDING | PENDING | PENDING | **PENDING** |
| Developer-API-Docs | read-only | PENDING | PENDING | PENDING | PENDING | PENDING | PENDING | PENDING | PENDING | PENDING | PENDING | **PENDING** |
| Developer-API-Docs | anon | PENDING | PENDING | PENDING | PENDING | PENDING | PENDING | PENDING | PENDING | PENDING | PENDING | **PENDING** |
| Developer-MCP-Console | admin | PENDING | PENDING | PENDING | PENDING | PENDING | PENDING | PENDING | PENDING | PENDING | PENDING | **PENDING** |
| Developer-MCP-Console | read-write | PENDING | PENDING | PENDING | PENDING | PENDING | PENDING | PENDING | PENDING | PENDING | PENDING | **PENDING** |
| Developer-MCP-Console | read-only | PENDING | PENDING | PENDING | PENDING | PENDING | PENDING | PENDING | PENDING | PENDING | PENDING | **PENDING** |
| Developer-MCP-Console | anon | PENDING | PENDING | PENDING | PENDING | PENDING | PENDING | PENDING | PENDING | PENDING | PENDING | **PENDING** |
| Developer-A2A-Console | admin | PENDING | PENDING | PENDING | PENDING | PENDING | PENDING | PENDING | PENDING | PENDING | PENDING | **PENDING** |
| Developer-A2A-Console | read-write | PENDING | PENDING | PENDING | PENDING | PENDING | PENDING | PENDING | PENDING | PENDING | PENDING | **PENDING** |
| Developer-A2A-Console | read-only | PENDING | PENDING | PENDING | PENDING | PENDING | PENDING | PENDING | PENDING | PENDING | PENDING | **PENDING** |
| Developer-A2A-Console | anon | PENDING | PENDING | PENDING | PENDING | PENDING | PENDING | PENDING | PENDING | PENDING | PENDING | **PENDING** |
| System-Jobs | admin | PENDING | PENDING | PENDING | PENDING | PENDING | PENDING | PENDING | PENDING | PENDING | PENDING | **PENDING** |
| System-Jobs | read-write | PENDING | PENDING | PENDING | PENDING | PENDING | PENDING | PENDING | PENDING | PENDING | PENDING | **PENDING** |
| System-Jobs | read-only | PENDING | PENDING | PENDING | PENDING | PENDING | PENDING | PENDING | PENDING | PENDING | PENDING | **PENDING** |
| System-Jobs | anon | PENDING | PENDING | PENDING | PENDING | PENDING | PENDING | PENDING | PENDING | PENDING | PENDING | **PENDING** |
| System-Settings | admin | PENDING | PENDING | PENDING | PENDING | PENDING | PENDING | PENDING | PENDING | PENDING | PENDING | **PENDING** |
| System-Settings | read-write | PENDING | PENDING | PENDING | PENDING | PENDING | PENDING | PENDING | PENDING | PENDING | PENDING | **PENDING** |
| System-Settings | read-only | PENDING | PENDING | PENDING | PENDING | PENDING | PENDING | PENDING | PENDING | PENDING | PENDING | **PENDING** |
| System-Settings | anon | PENDING | PENDING | PENDING | PENDING | PENDING | PENDING | PENDING | PENDING | PENDING | PENDING | **PENDING** |
| System-About | admin | PENDING | PENDING | PENDING | PENDING | PENDING | PENDING | PENDING | PENDING | PENDING | PENDING | **PENDING** |
| System-About | read-write | PENDING | PENDING | PENDING | PENDING | PENDING | PENDING | PENDING | PENDING | PENDING | PENDING | **PENDING** |
| System-About | read-only | PENDING | PENDING | PENDING | PENDING | PENDING | PENDING | PENDING | PENDING | PENDING | PENDING | **PENDING** |
| System-About | anon | PENDING | PENDING | PENDING | PENDING | PENDING | PENDING | PENDING | PENDING | PENDING | PENDING | **PENDING** |
