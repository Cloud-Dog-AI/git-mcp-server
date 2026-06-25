---
template-id: T-REQ
template-version: 1.1
applies-to: docs/REQUIREMENTS.md
project: git-mcp-server
doc-last-updated: 2026-06-23
doc-git-commit: c12b180e687b0a9dfac728161b44a963a12359ac
doc-git-branch: main
doc-age-policy: indefinite
doc-conformance-stamp: 2026-06-23T00:00:00Z
req-trace-version: 1.0
req-id-prefixes-used: [SV, BO, BR, FR, UC, CS, NF]
surface-coverage: [api, mcp, a2a, webui]
---

# Requirements — git-mcp-server

**Version:** 2.2  
**Date:** 2026-06-08  
**Standards:** PS-00, PS-10, PS-71, PS-73 v2, PS-76 v2, PS-77, RULES §6.2, RULES §6.4  
**Platform packages:** `cloud_dog_config`, `cloud_dog_logging`, `cloud_dog_api_kit`, `cloud_dog_idam`, `cloud_dog_db`, `cloud_dog_jobs`

**v2.2 (W28J forensic UI uplift, 2026-06-08):** adds FR1.17 (settings read-only + source-attributed
provenance), FR1.18 (unified selection criteria, audit deep-linking, and the workspace-first
conceptual model — session is a request-correlation parameter, not a first-class UI entity). The WebUI
adopts the shared `@cloud-dog/ui` patterns (SelectionCriteriaPanel, AdminRbacPage, QuickActionBar,
JsonExplorer, Ps72 consoles, JobsPage) in place of bespoke per-page surfaces.

## Verified Current Surface

The current requirement set was verified against source and test inventory on 2026-04-21.

- Runtime surfaces: API, MCP, Web, A2A
- MCP tool catalogue: 63 tools from `src/git_tools/tools/registry.py`
- Managed job submissions: `repo-open`, `git-diff`, `file-batch`
- A2A skills: `repo_open`, `git_status`, `file_write`, `git_commit`
- Routed WebUI pages: `/`, `/profiles`, `/workspace`, `/repository`, `/history`, `/diff`, `/branches`, `/merge`, `/tags`, `/stashes`, `/recovery`, `/audit`, `/admin/users`, `/admin/groups`, `/admin/api-keys`, `/admin/rbac`, `/api-docs`, `/mcp-console`, `/a2a-console`, `/jobs`, `/settings`

This document follows the required prefix scheme from RULES §6.2: `SV`, `BO`, `BR`, `FR`, `UC`, `CS`, `NF`, each restarting at `1.1`.

## 1. Scope/Vision (SV)

### SV1.1: Controlled Git Operations Boundary
`git-mcp-server` shall provide a controlled repository-operations boundary for human and agent clients across API, MCP, Web, and A2A surfaces, with shared domain logic for workspaces, refs, git actions, file actions, RBAC, and audit.

**Alignment:** `ARCH:OV1.1, SA1.1, CC1.1` | `TASK:T001` | `TEST:IT1.5, IT1.6, PW1.1`

### SV1.2: Delivered Capability Envelope
The delivered capability envelope shall include profile administration, workspace lifecycle control, branch/tag/commit ref handling, scoped file and search operations, git workflows, recovery workflows, managed jobs, audit/log review, settings support, and routed operator pages for repository and admin workflows.

**Alignment:** `ARCH:OV1.1, CC1.2, AI1.4` | `TASK:T003, T004, T005, T006, T008, T009, T010, T011` | `TEST:AT_PROFILE_LIFECYCLE, IT1.14, PW1.9`

### SV1.3: Bounded Runtime Surface
The runtime surface shall remain bounded to the verified API routes, 63-tool MCP catalogue, three managed-job submission types, four A2A skills, and the routed WebUI pages listed in this release; reusable structured-edit and validation helpers remain code-level capabilities rather than standalone MCP or API contracts.

**Alignment:** `ARCH:OV1.1, AI1.1, AI1.2, AI1.3, AI1.4` | `TASK:T001, T005, T013` | `TEST:IT1.5, UT1.23, UT1.24`

## 2. Business Objectives (BO)

### BO1.1: Safe Repository Automation
The service shall let operators and automations work on repositories inside profile-defined workspaces without escaping scope, mutating read-only refs, or bypassing protected-branch policy.

**Alignment:** `ARCH:SW1.1, SE1.1` | `TASK:T003, T004, T005, T007` | `TEST:QT1.2, IT1.7, AT1.1`

### BO1.2: Multi-Surface Access With Shared Behaviour
The service shall offer consistent repository behaviour across API, MCP, Web, and A2A entry points by dispatching through shared runtime and registry components instead of duplicating business logic per transport.

**Alignment:** `ARCH:SA1.1, CC1.1, OV1.1` | `TASK:T001, T011, T013` | `TEST:IT1.5, IT1.6, PW1.1`

### BO1.3: Auditable and Recoverable Change Work
The service shall make repository changes observable, recoverable, and reviewable through audit logging, recovery artefacts, managed jobs, and operator audit/log views.

**Alignment:** `ARCH:CP1.2, RR1.1, MO1.1` | `TASK:T006, T009, T010` | `TEST:ST1.8, IT1.15, PW1.7`

### BO1.4: Governed Administration
The service shall provide governed administration for repository profiles, users, groups, API keys, and capability metadata so teams can operate repository automation under explicit access control.

**Alignment:** `ARCH:CC1.3, SE1.1, AI1.1` | `TASK:T008, T012` | `TEST:IT1.14, UT1.54, ST1.11`

### BO1.5: First-Class Operator UI
The service shall provide a routed operator UI for repository workflows, diagnostics, developer consoles, and administration rather than restricting users to raw tool calls.

**Alignment:** `ARCH:AI1.4, MO1.1` | `TASK:T011, T014` | `TEST:PW1.8, PW1.9`

## 3. Business Requirements (BR)

### BR1.1: Authenticated Tool Execution
The system shall expose authenticated repository tooling over API and MCP using stable request and response envelopes backed by the shared `ToolRegistry`.

**Alignment:** `ARCH:CC1.1, AI1.1, AI1.2` | `TASK:T001, T007` | `TEST:IT1.5, IT1.6, PW1.1`

### BR1.2: Profile-Driven Repository Sessions
The system shall let callers open repository sessions by profile, session, workspace mode, and ref so repository work is explicit, repeatable, and policy-aware.

**Alignment:** `ARCH:SW1.1, CP1.1` | `TASK:T003, T004, T009` | `TEST:AT_PROFILE_LIFECYCLE, IT1.9, ST1.12`

### BR1.3: Administrative Control Plane
The system shall provide an administrative control plane for profile CRUD, identity CRUD, API-key metadata, capability-scoped access, and config-change broadcasting.

**Alignment:** `ARCH:CC1.3, DF1.1, AI1.1, AI1.3` | `TASK:T008, T010, T013` | `TEST:IT1.13, IT1.14, PW1.2`

### BR1.4: Browser-Based Operations
The system shall provide browser-delivered workflows for repository browsing, history, diff, branching, merge/conflict handling, tags, stashes, recovery, audit review, jobs, settings, and administration.

**Alignment:** `ARCH:AI1.4, MO1.1` | `TASK:T011` | `TEST:UT1.56, UT1.57, PW1.8, PW1.9`

### BR1.5: Reusable Library Helpers
The codebase shall retain reusable file-edit and validation helpers for JSON, YAML, XML, HTML, Markdown, and text as internal or library capabilities that can be tested independently of transport surfaces.

**Alignment:** `ARCH:CC1.2, TS1.1` | `TASK:T005, T014` | `TEST:UT1.23, UT1.24, UT1.35, UT1.36, UT1.37`

## 4. Functional Requirements (FR)

### FR1.1: Configuration Loading and Typed Runtime Model
The service shall load raw configuration with deterministic precedence, bind it into the typed global model, and use that model to drive listeners, profiles, storage, auth, jobs, and workspace settings.

**Alignment:** `ARCH:CM1.1, CC1.2` | `TASK:T002` | `TEST:UT1.1, UT1.2, UT1.3, QT_VAULT`

### FR1.2: API Runtime Surface
The API runtime shall provide health endpoints, authenticated tool catalogue and execution routes, admin routes, managed-job routes, and UI support routes using standard service envelopes.

**Alignment:** `ARCH:CC1.1, AI1.1` | `TASK:T001` | `TEST:IT1.1, IT1.14, UT1.57, PW1.1`

### FR1.3: MCP Runtime Surface
The MCP runtime shall provide MCP root discovery, JSON-RPC initialisation and `tools/list` handling, and authenticated HTTP tool execution at `/mcp/tools` over the shared tool contracts.

**Alignment:** `ARCH:CC1.1, AI1.2` | `TASK:T001` | `TEST:IT1.5, IT1.6, UT1.25, PW1.1`

### FR1.4: A2A Runtime Surface
The A2A runtime shall provide authenticated root and health routes, config-event streaming on `/a2a/events/config`, and an A2A card exposing the delivered skills `repo_open`, `git_status`, `file_write`, and `git_commit`.

**Alignment:** `ARCH:CC1.1, DF1.1, AI1.3` | `TASK:T013` | `TEST:AT1.6, IT1.11, IT1.13`

### FR1.5: Workspace Lifecycle
The workspace runtime shall create ephemeral and persistent workspaces, generate deterministic persistent workspace identifiers, restore persisted workspaces on startup, and support close and TTL cleanup behaviour.

**Alignment:** `ARCH:SW1.1, RR1.1` | `TASK:T003` | `TEST:UT1.4, UT1.8, ST1.1, ST1.2, ST1.12`

### FR1.6: Ref Resolution and Read-Only Semantics
The ref runtime shall resolve branch, tag, and commit refs and enforce read-only semantics for tag and commit contexts while preserving working-tree semantics for branch contexts.

**Alignment:** `ARCH:SW1.1, SE1.1` | `TASK:T003, T007` | `TEST:UT1.5, UT1.6, UT1.7, IT1.7, AT1.2, PW1.4`

### FR1.7: Remote Git Access and Transport Safety
The git runtime shall support clone, fetch, pull, and push against permitted remotes with credential priming, URL-policy checks, and disabled repository hook execution.

**Alignment:** `ARCH:IP1.1, SE1.1` | `TASK:T004, T007` | `TEST:IT1.9, IT1.10, IT1.16, UT1.48, QT1.1, QT1.3`

### FR1.8: File, Directory, and Search Operations
The tool catalogue shall provide scoped file read, write, upload, download, move, copy, delete, directory list/create/remove, content search, and file-path search operations inside the active workspace.

**Alignment:** `ARCH:CC1.2, CP1.1` | `TASK:T005` | `TEST:UT1.21, UT1.22, UT1.28, UT1.29, UT1.30, UT1.31, UT1.32, UT1.33, UT1.34, AT1.1, PW1.3`

### FR1.9: Managed Jobs
The jobs runtime shall expose queue status, job list and detail views, cancel, retry, and delete operations, plus managed submissions for `repo-open`, `git-diff`, and batch file mutations.

**Alignment:** `ARCH:CP1.2, AI1.1` | `TASK:T009` | `TEST:UT1.55, IT1.15, UT1.57`

### FR1.10: Core Git Workflow Tools
The tool catalogue shall provide git status, log, diff, add, reset, commit, checkout, branch list, branch create, branch delete, branch-from-ref, fetch, pull, and push operations.

**Alignment:** `ARCH:CC1.2, SW1.2` | `TASK:T004` | `TEST:UT1.14, UT1.15, UT1.16, UT1.38, UT1.39, UT1.40, UT1.41, UT1.42, UT1.47, ST1.3, ST1.5, ST1.6, IT1.9, IT1.10, IT1.16, PW1.3`

### FR1.11: Advanced Git, Conflict, and Recovery Tools
The tool catalogue shall provide merge, merge abort, merge continue, rebase, rebase abort, rebase continue, stash save, stash list, stash pop, tag create, tag delete, tag list, tag push, conflict listing, conflict resolution, and recovery restore workflows.

**Alignment:** `ARCH:SW1.2, RR1.1` | `TASK:T006` | `TEST:UT1.17, UT1.18, UT1.19, UT1.20, UT1.44, UT1.45, UT1.46, UT1.50, ST1.4, ST1.7, ST1.8, AT1.3, AT1.5, PW1.4, PW1.5, PW1.6`

### FR1.12: Administrative HTTP CRUD
The API admin surface shall provide CRUD for profiles, users, groups, and managed API keys with role and capability checks for `admin.profile` and `admin.identity`.

**Alignment:** `ARCH:CC1.3, AI1.1, SE1.1` | `TASK:T008` | `TEST:AT1.4, IT1.14, UT1.54, PW1.2`

### FR1.13: Administrative Tool Operations
The tool catalogue shall provide profile write, user and group CRUD, RBAC bind and unbind, credential-reference storage, and managed API-key create, list, read, and revoke operations.

**Alignment:** `ARCH:CC1.3, AI1.2, SE1.1` | `TASK:T008` | `TEST:UT1.54, IT1.14, PW1.2`

### FR1.14: Web UI Delivery and Routed Pages
The web runtime shall serve the built SPA, runtime configuration, and routed operator pages for dashboard, profiles, workspace, repository browser, commit history, diff viewer, branch manager, merge, tags, stashes, recovery, audit, admin, developer consoles, jobs, and settings.

**Alignment:** `ARCH:AI1.4, DA1.1` | `TASK:T011` | `TEST:UT1.56, PW1.8, PW1.9`

### FR1.15: UI Support Endpoints
The API surface shall provide UI support endpoints for version, service status, runtime settings, audit-log projection, and operational log projection so the SPA can render operator diagnostics without direct filesystem access.

**Alignment:** `ARCH:MO1.1, AI1.1, AI1.4` | `TASK:T010, T011` | `TEST:UT1.57, PW1.7, PW1.9`

### FR1.16: Audit Logging and Correlation
Tool calls, managed jobs, and operational actions shall emit redact-safe audit or log records with correlation metadata, outcome metadata, and persisted audit storage.

**Alignment:** `ARCH:DF1.1, MO1.1, SE1.1` | `TASK:T010` | `TEST:UT1.12, UT1.13, ST1.9, ST1.10, IT1.8, IT1.15, PW1.7`

### FR1.17: Settings — Read-Only Effective Configuration with Source Provenance
The settings page shall present the effective configuration as a read-only, source-attributed view: it
shall not offer a save action (configuration is owned by environment, config file, default YAML, and
Vault), it shall expose a masked effective-config export and an audited admin secret-reveal, and it shall
surface each setting's origin both inline (per leaf) and as an at-a-glance source summary. (W28J GMC-SE-01,
GMC-SE-02.)

**Alignment:** `ARCH:AI1.4` | `STANDARD:PS-73 v2` | `TASK:T011` | `TEST:UT1.57, PW1.9`

### FR1.18: Unified Selection Criteria, Audit Deep-Linking, and Conceptual Model
Repository-scoped pages (browser, history, diff, branches, merge, tags, stashes, recovery) shall share one
selection-criteria surface keyed on profile and workspace, with enumerated (not free-typed) refs, paths,
authors, and stashes sourced from the backend; the session identifier shall be a client-generated
request-correlation parameter rather than a user-selected entity. Every entity row and job shall deep-link
to the shared Audit page pre-filtered to that entity (AND-combinable dimensions). Workspaces shall be a
first-class, owner-scoped page. (W28J GMC root-causes CC-A/CC-B/CC-C/CC-D.)

**Alignment:** `ARCH:AI1.4, DA1.1` | `STANDARD:PS-71, PS-77` | `TASK:T011` | `TEST:UT1.60, PW1.8, PW1.9`

### FR1.19: Thread-B Resource-Aware IDAM Cascade
The service shall support resource-aware access for repository profiles by composing user membership,
group roles, profile-scoped grants, and the shared tool dispatch guard. A user added to a group with a
`profile:<name>` grant shall gain access to that repository profile, shall not gain access to unbound
profiles, and shall lose that access when removed from the group. Tool execution shall remain routed
through `ToolRegistry._call_with_audit()` so the cascade, denial, and audit records share one dispatch
path.

**Alignment:** `ARCH:SE1.1, CC1.3, DF1.1` | `STANDARD:PS-82, IDAM-B2` | `TASK:T008, T010` | `TEST:T3-GM-CASCADE, T1-GM-AUDIT`

### FR1.17: Database Runtime and Migration
The service shall initialise platform database state, report database health, and support the configured migration path for supported backends.

**Alignment:** `ARCH:DM1.1, RR1.1, DA1.1` | `TASK:T012` | `TEST:UT1.27, ST1.11, IT1.14`

### FR1.18: Structured Edit and Validation Helpers
The codebase shall provide reusable structured-edit and validation helpers for JSON, YAML, XML, HTML, Markdown, and plain-text workflows, with test coverage independent of the runtime transport layer.

**Alignment:** `ARCH:CC1.2, TS1.1` | `TASK:T005` | `TEST:UT1.23, UT1.24, UT1.35, UT1.36, UT1.37`

## 5. Use Cases (UC)

### UC1.1: Open and Reopen a Repository Workspace
An operator or automation client shall be able to open a repository from a profile, reopen a persistent workspace, switch ref context, and close the workspace when work is complete.

**Alignment:** `ARCH:SW1.1, CP1.1` | `TASK:T003, T004` | `TEST:AT_PROFILE_LIFECYCLE, ST1.1, ST1.12, IT1.9`

### UC1.2: Browse, Search, and Edit Repository Content
An authenticated user shall be able to browse repository content, search paths or content, download and upload files, and perform branch-scoped edits directly or through batch jobs.

**Alignment:** `ARCH:CP1.1, AI1.4` | `TASK:T005, T009, T011` | `TEST:AT1.1, UT1.28, UT1.34, PW1.3, PW1.8`

### UC1.3: Review and Advance Repository History
An authenticated user shall be able to inspect status, review history and diffs, stage changes, commit, push, and manage branches through tool and WebUI flows.

**Alignment:** `ARCH:SW1.2, AI1.4` | `TASK:T004, T011` | `TEST:ST1.3, IT1.10, PW1.3, PW1.8`

### UC1.4: Manage Tags, Stashes, Merges, and Recovery
An authenticated user shall be able to work with tag refs, stash entries, merge and rebase conflicts, and recovery artefacts from both the tool and browser surfaces.

**Alignment:** `ARCH:SW1.2, RR1.1, AI1.4` | `TASK:T006, T011` | `TEST:AT1.2, AT1.3, AT1.5, PW1.4, PW1.5, PW1.6`

### UC1.5: Administer Profiles and Access
An administrator shall be able to manage profiles, users, groups, API keys, RBAC bindings, and settings from the admin APIs and routed admin pages.

**Alignment:** `ARCH:CC1.3, AI1.1, AI1.4` | `TASK:T008, T011` | `TEST:AT1.4, IT1.14, PW1.2, PW1.8`

### UC1.6: Observe Activity and Configuration Changes
An operator shall be able to review audit and operational logs, inspect service status, and consume config-change events through WebUI and A2A-compatible flows.

**Alignment:** `ARCH:DF1.1, MO1.1, AI1.3, AI1.4` | `TASK:T010, T011, T013` | `TEST:IT1.13, IT1.8, PW1.7, PW1.9`

### UC1.7: Group-Scoped Repository Profile Access
A group administrator shall be able to add a user to a group that carries a repository-profile grant;
the user shall be able to use only that profile, shall be denied other profiles, and shall lose the
grant immediately when removed from the group.

**Alignment:** `ARCH:SE1.1, CC1.3` | `TASK:T008` | `TEST:T3-GM-CASCADE`

## 6. Cyber Security (CS)

### CS1.1: Authenticated Surface Access
API, MCP, admin, jobs, and A2A entry points shall require the delivered authentication modes for their surface, including API-key, JWT, bearer-token, cookie-session, and enterprise-role handling where configured.

**Alignment:** `ARCH:SE1.1, AI1.1, AI1.2, AI1.3, AI1.4` | `TASK:T007, T013` | `TEST:IT1.2, IT1.3, IT1.11, IT1.12, AT1.6, AT1.7, PW1.1`

### CS1.2: RBAC and Capability Enforcement
The service shall enforce admin-role, tool-category, profile-scoped, and managed-capability access rules before executing repository or admin operations.

**Alignment:** `ARCH:SE1.1, CP1.1` | `TASK:T007, T008` | `TEST:IT1.4, UT1.11, UT1.51, UT1.56, PW1.2`

### CS1.3: Workspace and Path Scope Enforcement
Workspace and file operations shall reject path traversal, symlink escape, and deny-pattern violations outside the configured workspace scope.

**Alignment:** `ARCH:SE1.1, RR1.1` | `TASK:T003, T005, T007` | `TEST:QT1.2, UT1.9, IT1.7`

### CS1.4: Read-Only Ref and Protected-Branch Enforcement
Mutating operations shall be blocked when the active ref is read-only or when branch-protection policy denies the current actor the required write action.

**Alignment:** `ARCH:SE1.1, SW1.1, SW1.2` | `TASK:T003, T004, T007` | `TEST:UT1.10, AT1.2, IT1.7, PW1.4`

### CS1.5: Secret Hygiene and Redaction
Repository credentials, API keys, tokens, and sensitive payload fields shall not be written to audit or operational logs in raw form.

**Alignment:** `ARCH:SE1.1, MO1.1` | `TASK:T004, T007, T010` | `TEST:QT1.1, QT26, UT1.13, IT1.8`

### CS1.6: Admin Capability Segmentation
Administrative functions shall support segmented capabilities such as `admin.profile` and `admin.identity` so managed API keys can be limited to the intended administrative scope.

**Alignment:** `ARCH:SE1.1, CC1.3` | `TASK:T007, T008, T013` | `TEST:IT1.14, UT1.54, PW1.2`

## 7. Non-Functional Requirements (NF)

### NF1.1: Shared Core and Transport Separation
Transport layers shall remain thin adapters over shared domain and registry components so repository logic stays reusable and testable outside server entry points.

**Alignment:** `ARCH:CC1.1, CC1.2` | `TASK:T001` | `TEST:QT_LIB_SEPARATION, QT_MIGRATION`

### NF1.2: Deterministic Configuration Behaviour
Runtime configuration shall behave deterministically across environment variables, env files, config files, defaults, and Vault-backed values.

**Alignment:** `ARCH:CM1.1` | `TASK:T002` | `TEST:UT1.1, UT1.2, UT1.3, QT_VAULT`

### NF1.3: Stable Workspace and Job State
Persistent workspace restore, job progress, and job status polling shall provide stable state that survives normal process and workflow boundaries.

**Alignment:** `ARCH:RR1.1, CP1.2` | `TASK:T003, T009` | `TEST:ST1.12, UT1.55, IT1.15`

### NF1.4: Safe Mutation Mechanics
File mutation paths shall use atomic write patterns where applicable, and git execution shall disable repository hooks during managed operations.

**Alignment:** `ARCH:RR1.1, SW1.2` | `TASK:T004, T005` | `TEST:UT1.21, QT1.3`

### NF1.5: Durable Audit and Log Reviewability
Audit and operational logging shall remain durable, correlated, and reviewable through the persisted audit stream and UI log-projection endpoints.

**Alignment:** `ARCH:MO1.1, DF1.1` | `TASK:T010, T012` | `TEST:ST1.9, ST1.10, ST_INTEGRITY, IT1.8, PW1.7`

### NF1.6: Bounded Execution
HTTP requests, queue work, and session support shall operate with explicit timeout and bounded-execution settings suitable for operator workflows.

**Alignment:** `ARCH:SP1.1, CP1.2` | `TASK:T001, T009` | `TEST:UT1.49, UT1.55, IT1.15`

### NF1.7: Browser Delivery Discipline
The SPA runtime configuration and fallback delivery shall behave predictably behind local and reverse-proxy deployment topologies without exposing reserved API paths as SPA routes.

**Alignment:** `ARCH:DA1.1, AI1.4` | `TASK:T011` | `TEST:UT1.56, UT1.57`

### NF1.8: Documentation and Traceability Integrity
The project documentation set shall maintain requirement, architecture, task, and test cross-references for the delivered surface described in this release.

**Alignment:** `ARCH:RD1.1, TS1.1` | `TASK:T014` | `TEST:QT_DOCS, QT_TRACEABILITY`

## PS-40 / W28A-619 Logging and Audit Requirements

The service MUST use `cloud_dog_logging` as the only application and audit logging implementation. Raw stdlib logging setup, direct `logging.getLogger()` calls, bespoke audit emitters, and print-based operational logging are not compliant except inside the platform logging package itself.

Every auditable event MUST emit a PS-40/NIST AU-3 audit record with: `event_type`, `action`, `timestamp`, `service`, `component`, `service_instance`, `environment`, `source_host`, `source_process`, `source_application`, `source_address` where available, `destination_address` where available, `outcome`, actor identity including user/service/system plus account/process/device identifiers where available, `target`, `process_id`, `affected_files` where relevant, `correlation_id`, `trace_id`, and `request_id`.

Auditable events MUST include authentication and authorisation decisions, user/group/API-key/RBAC changes, repository/branch/commit/file/diff operations, MCP/A2A/API calls, job lifecycle changes, configuration changes, data access and mutation, denials, failures, and privileged operations. Secrets MUST be redacted before persistence. Tests MUST cover schema fields, event coverage, redaction, append-only audit persistence, retention/integrity, and WebUI observability rendering/filtering.

## Canonical Requirement Traceability Tables (PS-REQ-TEST-TRACE v1.0)

These tables are the **binding traceability surface** for `git-mcp-server`. Every `@pytest.mark.req("...")`
in `tests/` references a row here, and every row is referenced by at least one test (enforced by
`scripts/check-req-test-traceability.sh`). They supersede and de-mechanise the W28C-1711-R3 stub rows
(immutable IDs retained; descriptions and bindings made semantic per capability in lane **W28E-1804A**).
The narrative `§1`–`§7` requirements above remain the human-readable source; the rows below are the
machine-traceable projection. `since:` is the git short-sha (or lane) where the canonical ID was first
introduced; `source-evidence:` cites the driving `src/` module and/or knowledge source.

### 4A. Functional Requirements — canonical FR-NNN

| ID | Requirement | Surface | Priority | Since | Source-evidence | UCs | Tests |
|---|---|---|---|---|---|---|---|
| `FR-001` | Configuration loading & typed runtime model with deterministic precedence (env, env-file, config, defaults, Vault) bound into the global typed model. | `api`, `mcp`, `internal` | `must` | `b42adef` | `src/git_tools/config/models.py`; KNOWLEDGE FR1.1 | `UC1.1` | `UT1.1`, `UT1.2`, `UT1.3` |
| `FR-002` | API runtime surface: health, authenticated tool catalogue/execution, admin, managed-job and UI-support routes over standard service envelopes. | `api` | `must` | `b42adef` | `src/git_mcp_server/api_server.py`; KNOWLEDGE FR1.2 | `UC1.1`, `UC1.6` | `IT1.1`, `UT1.65` |
| `FR-003` | MCP runtime surface: root discovery, JSON-RPC initialise & `tools/list`, authenticated `/mcp/tools` execution over shared tool contracts. | `mcp` | `must` | `b42adef` | `src/git_mcp_server/mcp_server.py`; KNOWLEDGE FR1.3 | `UC1.2`, `UC1.3` | `IT1.5`, `IT1.6`, `UT1.25`, `UT1.63` |
| `FR-004` | A2A runtime surface: authenticated root/health, config-event streaming on `/a2a/events/config`, agent card exposing `repo_open`/`git_status`/`file_write`/`git_commit`. | `a2a` | `must` | `b42adef` | `src/git_mcp_server/a2a_server.py`; KNOWLEDGE FR1.4 | `UC1.6` | `AT1.6`, `IT1.11`, `IT1.13`, `UT1.26`, `UT1.58`, `UT1.68` |
| `FR-005` | Workspace lifecycle: ephemeral & persistent workspaces, deterministic persistent ids, startup restore, close, TTL/GC cleanup. | `mcp`, `api` | `must` | `b42adef` | `src/git_tools/workspaces/manager.py`; KNOWLEDGE FR1.5 | `UC1.1` | `ST1.1`, `ST1.2`, `ST1.12`, `UT1.8`, `UT1.69`, `AT_PROFILE_LIFECYCLE` |
| `FR-006` | Ref resolution & read-only semantics: resolve branch/tag/commit refs; tag & commit contexts are read-only, branch contexts keep working-tree semantics. | `mcp`, `api` | `must` | `b42adef` | `src/git_tools/git/repo.py` (`RefSpec`); KNOWLEDGE FR1.6 | `UC1.1`, `UC1.4` | `UT1.5`, `UT1.6`, `UT1.7` |
| `FR-007` | Remote git access & transport safety: clone/fetch/pull/push against permitted remotes with credential priming, URL-policy checks, disabled repo hooks. | `mcp`, `api` | `must` | `b42adef` | `src/git_tools/git/operations.py`; KNOWLEDGE FR1.7 | `UC1.3` | `IT1.9`, `IT1.10`, `IT1.16`, `UT1.48` |
| `FR-008` | File, directory & search operations: scoped read/write/upload/download/move/copy/delete, dir list/mkdir/rmdir, content & file-path search inside the active workspace. | `mcp`, `api` | `must` | `b42adef` | `src/git_tools/files/io.py`, `search.py`; KNOWLEDGE FR1.8 | `UC1.2` | `UT1.21`, `UT1.22`, `UT1.28`–`UT1.34` |
| `FR-009` | Managed jobs: queue status, job list/detail, cancel/retry/delete, and `repo-open`/`git-diff`/file-batch submissions. | `mcp`, `api`, `webui` | `must` | `b42adef` | `src/git_tools/jobs/`, `src/git_mcp_server/jobs/`; KNOWLEDGE FR1.9 | `UC1.2`, `UC1.6` | `UT1.55`, `IT1.15`, `IT1.62` |
| `FR-010` | Core git workflow tools: status/log/diff/add/reset/commit/checkout, branch list/create/delete/from-ref, fetch/pull/push. | `mcp`, `api` | `must` | `b42adef` | `src/git_tools/git/operations.py`; KNOWLEDGE FR1.10 | `UC1.3` | `UT1.14`–`UT1.16`, `UT1.38`–`UT1.42`, `UT1.47`, `ST1.3`, `AT1.1` |
| `FR-011` | Advanced git, conflict & recovery tools: merge/rebase (+abort/continue), stash save/list/pop, tag create/delete/list/push, conflict list/resolve/manual, recovery restore. | `mcp`, `api` | `must` | `b42adef` | `src/git_tools/git/conflicts.py`, `tags.py`; KNOWLEDGE FR1.11 | `UC1.4` | `UT1.17`–`UT1.20`, `UT1.43`–`UT1.46`, `UT1.50`, `ST1.4`–`ST1.8`, `AT1.2`, `AT1.3`, `AT1.5` |
| `FR-012` | Administrative HTTP CRUD for profiles/users/groups/managed API-keys with `admin.profile` & `admin.identity` capability checks. | `api` | `must` | `b42adef` | `src/git_tools/admin/runtime.py`; KNOWLEDGE FR1.12 | `UC1.5` | `AT1.4`, `IT1.14` |
| `FR-013` | Administrative tool operations: profile write, user/group CRUD, RBAC bind/unbind, credential-reference store, API-key create/list/read/revoke. | `mcp` | `must` | `b42adef` | `src/git_tools/admin/runtime.py`, `roles_service.py`; KNOWLEDGE FR1.13 | `UC1.5` | `UT1.54` |
| `FR-014` | Web UI delivery & routed operator pages: built SPA, runtime config, and the 21 routed pages (dashboard…settings). | `webui` | `must` | `W28E-1804A (c12b180)` | `src/git_mcp_server/web_server.py`; KNOWLEDGE FR1.14; GWN GM-DS/BR/CM/DV/BC/MR/TG/SH/RC | `UC1.2`, `UC1.3`, `UC1.5`, `UC1.6` | `AT_WEBUI`, `UT1.56` |
| `FR-015` | UI support endpoints: version, service status, runtime settings, audit-log & operational-log projections for the SPA. | `api`, `webui` | `must` | `W28E-1804A (c12b180)` | `src/git_mcp_server/ui_endpoints.py`; KNOWLEDGE FR1.15 | `UC1.6` | `UT1.57` |
| `FR-016` | Audit logging & correlation: every tool call/job/op converges through `ToolRegistry._call_with_audit()` emitting redact-safe records with correlation metadata. | `mcp`, `api`, `a2a`, `webui` | `must` | `W28E-1804A (c12b180)` | `src/git_tools/audit/logger.py`, `events.py`; PS-AUDIT-LOG; GWN GM-AL/JB | `UC1.6` | `UT1.12`, `UT1.13`, `UT1.67`, `IT1.8`, `T0-GM-AUDIT` |
| `FR-017` | Settings — read-only effective configuration with per-leaf source provenance, masked export, audited admin secret-reveal, no save action. | `webui`, `api` | `should` | `W28E-1804A (c12b180)` | `src/git_mcp_server/ui_endpoints.py` (settings); GWN GM-ST | `UC1.6` | `UT1.61` |
| `FR-018` | Unified selection criteria, audit deep-linking & workspace-first conceptual model: one profile+workspace selection surface with enumerated refs/paths/authors; session is a request-correlation parameter. | `webui`, `api` | `should` | `W28E-1804A (c12b180)` | `src/git_mcp_server/workspace_enum_endpoints.py`; GWN GM-CC-03/06, GM-WS | `UC1.2` | `UT1.60`, `IT1.61` |
| `FR-019` | Thread-B resource-aware IDAM cascade: a group `profile:<name>` grant gives access to that profile, denies unbound profiles, and is revoked on group removal. | `mcp`, `api`, `a2a`, `webui` | `must` | `b42adef` | `src/git_tools/admin/runtime.py` (`role_bindings`); KNOWLEDGE FR1.19 | `UC1.7` | `T3-GM-CASCADE` |
| `FR-020` | Database runtime & migration: platform DB initialisation, health, and configured migration path across supported backends. | `internal`, `api` | `should` | `W28E-1804A (c12b180)` | `src/git_tools/db/`; KNOWLEDGE FR1.17(db) | `UC1.6` | `UT1.27`, `ST1.11` |
| `FR-021` | Structured-edit & validation helpers for JSON/YAML/XML/HTML/Markdown/text, testable independently of transport surfaces. | `internal` | `should` | `W28E-1804A (c12b180)` | `src/git_tools/files/` (helpers); KNOWLEDGE BR1.5/FR1.18(helpers) | `UC1.2` | `UT1.23`, `UT1.24`, `UT1.35`, `UT1.36`, `UT1.37` |
| `FR-022` | Authentication modes: API-key, JWT/bearer, cookie-session, enterprise-role and flat username/password login across all surfaces. | `api`, `mcp`, `a2a`, `webui` | `must` | `W28E-1804A (c12b180)` | `src/git_mcp_server/auth/`; KNOWLEDGE CS1.1; W28A-731-R5 flat-login | `UC1.1`, `UC1.5` | `IT1.2`, `IT1.3`, `IT1.12`, `UT1.52`, `UT1.53`, `UT1.66`, `UT1.70`, `AT1.7` |
| `FR-023` | Profile administration & RBAC capability enforcement: profile model validation plus admin-role, tool-category and profile-scoped access checks before repository/admin operations. | `api`, `mcp`, `webui` | `must` | `W28E-1804A (c12b180)` | `src/git_tools/admin/roles_service.py`; KNOWLEDGE FR1.12/CS1.2; GWN GM-PR/RB/RL | `UC1.5`, `UC1.7` | `IT1.4`, `UT1.4`, `UT1.11`, `UT1.51`, `UT1.56`, `UT1.64` |

### 5. Cyber Security & Negative Flows — canonical CS-NNN

Mandatory schema per PS-REQ-TEST-TRACE v1.0 §3.4. Every project covers **anon-denied**,
**wrong-role-denied**, and **missing-param-error** per declared surface (`api`, `mcp`, `a2a`, `webui`).
`CS-001`–`CS-016` are the platform baseline; `CS-017`–`CS-020` are git-mcp-specific negatives. Each row
binds to at least one `@pytest.mark.req()` negative test with an explicit expected denial code.

| ID | Threat / negative scenario | Surface | Role(s) attempted | Expected | Since | Tests |
|---|---|---|---|---|---|---|
| `CS-001` | Anon attempts data read | `api`, `mcp`, `a2a`, `webui` | `anon` | `401` | `a1fbf7c` | `UT1.65` |
| `CS-002` | read-only attempts write | `api`, `mcp` | `read-only` | `403` | `a1fbf7c` | `UT1.65` |
| `CS-003` | Missing required param | `api` | `admin` | `422` | `a1fbf7c` | `UT1.65` |
| `CS-004` | Wrong-role privileged op | `mcp` | `read-write` | `403` | `a1fbf7c` | `UT1.65` |
| `CS-005` | anon-denied | `api` | `anon` | `401` | `a1fbf7c` | `UT1.65` |
| `CS-006` | anon-denied | `mcp` | `anon` | `401` | `a1fbf7c` | `UT1.65` |
| `CS-007` | anon-denied | `a2a` | `anon` | `401` | `a1fbf7c` | `UT1.65` |
| `CS-008` | anon-denied | `webui` | `anon` | `401` | `a1fbf7c` | `UT1.56` |
| `CS-009` | wrong-role-denied | `api` | `read-only` | `403` | `a1fbf7c` | `UT1.65` |
| `CS-010` | wrong-role-denied | `mcp` | `read-only` | `403` | `a1fbf7c` | `UT1.65` |
| `CS-011` | wrong-role-denied | `a2a` | `read-only` | `403` | `a1fbf7c` | `UT1.65` |
| `CS-012` | wrong-role-denied | `webui` | `read-only` | `403` | `a1fbf7c` | `UT1.56` |
| `CS-013` | missing-param-error | `api` | `*` | `422` | `a1fbf7c` | `UT1.65` |
| `CS-014` | missing-param-error | `mcp` | `*` | `422` | `a1fbf7c` | `UT1.65` |
| `CS-015` | missing-param-error | `a2a` | `*` | `422` | `a1fbf7c` | `UT1.65` |
| `CS-016` | missing-param-error | `webui` | `*` | `422` | `a1fbf7c` | `UT1.56` |
| `CS-017` | Path traversal / symlink escape outside workspace scope | `api`, `mcp` | any authenticated | `denied` | `W28E-1804A (c12b180)` | `UT1.9`, `QT1.2` |
| `CS-018` | Mutation attempted on read-only ref or protected branch | `api`, `mcp` | `read-write`, non-admin | `403` / `denied` | `W28E-1804A (c12b180)` | `UT1.10`, `IT1.7` |
| `CS-019` | Secret / credential value reaches audit or operational logs | `mcp`, `api` | any | `no-raw-secret` | `W28E-1804A (c12b180)` | `QT1.1` |
| `CS-020` | Admin capability segmentation bypass / unauth admin gate | `api`, `mcp` | wrong-scope, `anon` | `403` / `401` | `W28E-1804A (c12b180)` | `UT1.62` |

### 6A. Non-Functional Requirements — canonical NF-NNN

| ID | Requirement | Surface | Priority | Since | Source-evidence | Tests |
|---|---|---|---|---|---|---|
| `NF-001` | Shared core & transport separation: transports are thin adapters over shared domain/registry components. | `internal` | `should` | `W28E-1804A (c12b180)` | `src/git_tools/`; KNOWLEDGE NF1.1 | `QT_LIB_SEPARATION` |
| `NF-002` | Deterministic configuration behaviour across env, env-file, config, defaults and Vault-backed values. | `internal` | `should` | `W28E-1804A (c12b180)` | `src/git_tools/config/`; KNOWLEDGE NF1.2 | `UT1.3`, `QT_VAULT` |
| `NF-003` | Stable workspace & job state: persistent restore, job progress and status polling survive process/workflow boundaries. | `internal` | `should` | `W28E-1804A (c12b180)` | `src/git_tools/workspaces/`, `jobs/`; KNOWLEDGE NF1.3 | `ST1.12` |
| `NF-004` | Safe mutation mechanics: atomic file-write patterns; repository hooks disabled during managed operations. | `internal` | `must` | `W28E-1804A (c12b180)` | `src/git_tools/files/io.py`; KNOWLEDGE NF1.4 | `QT1.3`, `UT1.21` |
| `NF-005` | Durable audit & log reviewability: persisted audit stream, rotation, retention and integrity verification. | `internal` | `must` | `W28E-1804A (c12b180)` | `src/git_tools/audit/`; PS-AUDIT-LOG; KNOWLEDGE NF1.5 | `ST1.9`, `ST1.10`, `ST_INTEGRITY`, `ST_LOG_ROTATION`, `UT_LOGGING_CONFIG` |
| `NF-006` | Bounded execution: HTTP, queue and session work operate with explicit timeout and bounded-execution settings. | `internal` | `should` | `W28E-1804A (c12b180)` | `src/git_mcp_server/`; KNOWLEDGE NF1.6 | `UT1.49` |
| `NF-007` | Browser delivery discipline: SPA runtime config and fallback delivery behave predictably behind reverse-proxy topologies without exposing reserved API paths as SPA routes. | `webui` | `should` | `W28E-1804A (c12b180)` | `src/git_mcp_server/web_server.py`; KNOWLEDGE NF1.7 | `AT_WEBUI` |
| `NF-008` | Documentation & traceability integrity: requirement↔test↔code trace, docs-set conformance, UK-English, rules compliance. | `internal` | `should` | `W28E-1804A (c12b180)` | `docs/`, `tests/quality/`; KNOWLEDGE NF1.8; PS-REQ-TEST-TRACE | `QT_DOCS`, `QT_TRACEABILITY`, `QT_RULES`, `QT1.4` |
| `NF-009` | Platform package adoption, security hardening & no-bespoke-code: reuse `cloud_dog_*` packages; no bespoke config/logging/auth/db/llm/vdb; security suite passes. | `internal` | `must` | `W28E-1804A (c12b180)` | `tests/quality/`; PS-COMMON-SVC-REQ CSR-001; CSR-028 | `QT_PACKAGE`, `QT_BESPOKE_SCAN`, `QT_MIGRATION`, `QT_SECURITY_SUITE`, `QT_LOGGING_COMPLIANCE` |
| `NF-010` | Secret separation & Vault config contract: no plaintext secrets in source/defaults/config; env files use Vault expressions or scoped test files. | `internal` | `must` | `W28E-1804A (c12b180)` | `tests/quality/`; PS-COMMON-SVC-REQ CSR-010; CSR-034 | `QT26`, `QT_VAULT` |

## 8. WebUI Observation Trace (W28E-1804A — GarysWorkingNotes.md L2714-2944)

The 2026-06-11 git-mcp WebUI audit recorded **96 atomic GM-NNN observations** (rollup: 18 FIXED, 53 OPEN,
9 PARTIAL, 16 UNKNOWN). Every atomic item maps to an existing requirement row and an explicit Stream-B/C
drive-out test row (see `docs/TESTS.md` §3 WebUI observation catalogue). Cross-cutting `@cloud-dog/ui`
shared-component items are routed to **W28E-1825 PS-WEBUI-STYLE-COMPONENTS**; git-mcp-view-local items fold
to the requirements below.

| GM group | Page / concern | Maps to REQ | Routing |
|---|---|---|---|
| `GM-CC-01/02/05` | About dialog, single copyright footer, shared Button | `FR-014` | local (FIXED — regression-guarded) |
| `GM-CC-03/04/07` | WorkspaceSessionCard dropdowns, title-case, RepoContextBar iconography | `FR-018` + `FR-014` | shared component → **W28E-1825** |
| `GM-CC-06` | Cross-page click-through (Profile→Workspace→…→Audit) | `FR-018` | local |
| `GM-DS-01..08` | Dashboard layout, metrics validation, quick-actions | `FR-014`, `FR-015` | local |
| `GM-PR-01..08` | Profiles: branch dropdown, credential/sync info, RBAC linkage, click-through | `FR-023`, `FR-012`, `FR-014` | local |
| `GM-WS-01..09` | Workspace diagnostics: derived repo-source, session UX, payload/audit panels | `FR-005`, `FR-018`, `FR-015` | local |
| `GM-BR/CM/DV/BC/MR/TG/SH-*` | Browser, commits, diff, branches, merge, tags, stashes pages | `FR-014`, `FR-010`, `FR-011`, `FR-018` | local + shared FileTree → **W28E-1825** |
| `GM-RC-01..08` | Recovery page selection/affordances/payload | `FR-011`, `FR-014`, `FR-018` | local |
| `GM-AL-01..04` | Audit & Log page consistency, source filters, action labels | `FR-016`, `FR-015` | local + cross-svc audit alignment |
| `GM-US/GP/AK/RB/RL-*` | Users/Groups/API-Keys/RBAC/Roles admin pages vs shared idam components | `FR-012`, `FR-023` | shared idam → **W28E-1825** |
| `GM-AD-01..03` | API Docs consolidation & load | `FR-014`, `FR-002` | local |
| `GM-MC-01/02`, `GM-AA-01..03` | MCP/A2A console sizing & per-skill docs | `FR-003`, `FR-004`, `FR-014` | shared Ps72 → **W28E-1825** |
| `GM-JB-01..07` | Jobs page detail dialog, columns, audit link, sync/async test | `FR-009`, `FR-016`, `FR-014` | local |
| `GM-ST-01..03`, `GM-AB-01` | Settings save/import, About nav→modal | `FR-017`, `FR-014` | local |

## 9. Common Service Requirements (PS-COMMON-SVC-REQ pin)

Per **PS-COMMON-SVC-REQ v1.0**, git-mcp-server consumes the common platform baseline (identity, RBAC,
config, request context, API/MCP/A2A/WebUI, jobs, audit, logging, security, deployment identity) **by
reference, not by restatement**. The applicable-CSR consumption matrix is in the lane evidence pack
(`ps_common_svc_req_consumption.tsv`); key bindings: CSR-005/006 → `FR-022`/`FR-023`+`CS-001..020`;
CSR-014 → `FR-003`; CSR-015 → `FR-004`; CSR-017 → `FR-009`; CSR-023 → `FR-016`; CSR-010/034 → `NF-010`;
CSR-001/028 → `NF-009`; CSR-031 → `docs/REQ-COVERAGE.md` + `tests/SCOPE-MAP.md`. Surfaces git-mcp does not
expose are marked `N/A` with evidence in that file; no baseline rule is forked or weakened here.

## 10. Docs-Manifest

This project's approved doc set is declared in `.docs-manifest.yml`. Any additional documentation requires
a template registered in `cloud-dog-ai-platform-standards/templates/REGISTRY.md`.

## 11. Traceability

- Use cases: `docs/ROLES-AND-USECASES.md` (UC1.1–UC1.7 + cross-surface FR mapping).
- Tests: `docs/TESTS.md` (10-column coverage map + WebUI observation catalogue + supplement E2E AT rows).
- Coverage: `docs/REQ-COVERAGE.md` (script-generated; 0 NO-TEST).
- Architecture / data model: `docs/ARCHITECTURE.md`, `docs/DATA-MODEL.md`.
- Warranty: `docs/WARRANTY-1.0RC01.md` Section A (every FR/CS/NF/UC row `verdict=PASS`).
