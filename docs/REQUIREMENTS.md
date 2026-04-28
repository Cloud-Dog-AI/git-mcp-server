# Requirements — git-mcp-server

**Version:** 2.1  
**Date:** 2026-04-22  
**Standards:** PS-00, PS-10, RULES §6.2, RULES §6.4  
**Platform packages:** `cloud_dog_config`, `cloud_dog_logging`, `cloud_dog_api_kit`, `cloud_dog_idam`, `cloud_dog_db`, `cloud_dog_jobs`

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
The MCP runtime shall provide MCP root discovery, JSON-RPC `initialize` and `tools/list` handling, and authenticated HTTP tool execution at `/mcp/tools` over the shared tool contracts.

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
