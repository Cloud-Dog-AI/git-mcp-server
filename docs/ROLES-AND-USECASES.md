---
template-id: T-RUC
template-version: 1.1
applies-to: docs/ROLES-AND-USECASES.md
project: git-mcp-server
doc-last-updated: 2026-06-18
doc-git-commit: 92ef7210b67e936d847a98e97d5099a5bd73ba76
doc-git-branch: main
doc-age-policy: 90d
doc-conformance-stamp: 2026-06-18T00:00:00Z
---

# Git MCP Roles And Use Cases

This document is the W28A-745 Thread-B b-method traceability surface for `git-mcp-server`.
It follows the accepted W28A-742 template: identity and domain entities are separated,
role vocabularies are reconciled, requirements use cases are mapped verbatim, and the
group-to-resource cascade is explicit instead of inferred.

## Entities

### Identity Family

| Entity | Source | Key fields | Relationships |
|---|---|---|---|
| User | `AdminRuntime.user_store` | `user_id`, `username`, `email`, `group_ids`, `status` | belongs to zero or more groups; direct roles may be bound through `role_bindings` |
| Group | `AdminRuntime.group_store` | `group_id`, `description`, `roles`, `members` | owns role labels; synchronises inverse user memberships |
| RoleBinding | `AdminRuntime.role_bindings` | `user_id`, role string | direct user role attachment used with group-derived roles |
| ApiKey | `cloud_dog_idam.APIKeyManager` plus `api_key_metadata` | `key_id`, `owner_user_id`, `status`, `capabilities`, one-time `raw_key` | authenticates API/MCP/A2A callers; capabilities map to admin/profile grants |

### Domain Family

| Entity | Source | Key fields | Relationships |
|---|---|---|---|
| RepositoryProfile | `ProfileStore` / `GitProfileRegistry` | `name`, `repo.source`, `policy`, `owner_user_id`, `owner_group_id`, `rbac_role_required` | selects repository source, workspace policy, and access metadata |
| Workspace | `WorkspaceManager` | `workspace_id`, `profile`, `session_id`, `mode`, `owner`, `ref_context` | opened from a profile; drives all repository and file operations |
| GitRef | `RefSpec` / workspace ref context | `type`, `name`, `resolved_commit`, `mode` | branch refs may be mutable; tag/commit refs are read-only |
| RepositoryFile | workspace filesystem | path within active workspace | read/write/upload/download/move/copy/delete/search |
| GitOperation | `ToolRegistry` handlers | tool name and payload | dispatches through one registry and audit chokepoint |
| Job | `JobsRuntime` | job id, type, lifecycle status, payload | managed submissions for long-running repository work |
| AuditEvent | `AuditWriter` | operation, actor, params, result hash, status | records every tool call and redacts sensitive inputs |

## Role Catalogue

### Central Roles And Grants

| Role id | Scope | Permissions / behaviour | Source |
|---|---|---|---|
| `admin` | central | wildcard administration, profile CRUD, user/group/API-key/RBAC administration, all repository operations | PS-82 baseline; `ToolRegistry._require_profile_access` wildcard/admin branch |
| `group-admin` | central | manages group membership and group-bound access records | Thread-B cascade role; represented in git-mcp by group membership plus group roles |
| `user` | central | authenticated baseline access to WebUI/API/MCP/A2A and read-only in-scope repository operations | PS-82 baseline; git-mcp maps flat roles to tool roles |
| `restricted` | central | no default access; explicit profile or capability grants only | PS-82 baseline |
| `job-control` | central grant | `jobs.read` and `jobs.control` surfaces | Jobs runtime and WebUI jobs page |
| `audit-log` | central grant | read audit/log surfaces; secret values remain masked | audit page/API support endpoints |

### Git MCP Business Roles

| Role id | Domain meaning | Permissions / behaviour | Reconciliation |
|---|---|---|---|
| `git-admin` | full repository automation operator | all profile, git, file, job, audit, admin, and settings read surfaces | maps to `admin` |
| `git-maintainer` | write-capable profile user | branch-scoped edit, commit, push, merge, rebase, tag, stash, recovery according to profile policy | maps to `user` plus write profile grants |
| `git-reader` | read-only profile user | browse repository, history, diff, tags, stashes, audit references; mutating tools 403 | maps to `user` plus read-only profile grants |
| `profile-scoped` | group/resource cascade role | a role string of `profile:<name>` grants access to that one RepositoryProfile | maps to `GROUPUSER` resource binding |
| `service` | machine/API-key caller | capability list on the managed API key | maps to `SERVICE` principal |

## Traceability Matrix

| Req | Entity | Action | Use-case text | Role | Surfaces | Test IDs |
|---|---|---|---|---|---|---|
| UC1.1 | RepositoryProfile, Workspace | create/read/close | "An operator or automation client shall be able to open a repository from a profile, reopen a persistent workspace, switch ref context, and close the workspace when work is complete." | git-reader, git-maintainer | API, MCP, A2A, WebUI | T0-GM-WORKSPACE, T3-GM-WORKSPACE |
| UC1.2 | RepositoryFile | read/search/write | "An authenticated user shall be able to browse repository content, search paths or content, download and upload files, and perform branch-scoped edits directly or through batch jobs." | git-reader for read; git-maintainer for write | API, MCP, A2A, WebUI | T0-GM-READ, T2-GM-READONLY, T3-GM-FILE |
| UC1.3 | GitOperation | status/log/diff/commit/push | "An authenticated user shall be able to inspect status, review history and diffs, stage changes, commit, push, and manage branches through tool and WebUI flows." | git-maintainer | API, MCP, A2A, WebUI | T3-GM-GIT-WORKFLOW |
| UC1.4 | GitRef, Recovery | tags/stashes/merge/rebase/recovery | "An authenticated user shall be able to work with tag refs, stash entries, merge and rebase conflicts, and recovery artefacts from both the tool and browser surfaces." | git-reader for tag browse; git-maintainer for mutation | API, MCP, A2A, WebUI | T2-GM-REF-READONLY, T3-GM-CONFLICT |
| UC1.5 | User, Group, ApiKey, RepositoryProfile | admin CRUD | "An administrator shall be able to manage profiles, users, groups, API keys, RBAC bindings, and settings from the admin APIs and routed admin pages." | admin, group-admin | API, MCP, WebUI | T1-GM-IDAM, T2-GM-RBAC |
| UC1.6 | AuditEvent, config events | observe | "An operator shall be able to review audit and operational logs, inspect service status, and consume config-change events through WebUI and A2A-compatible flows." | audit-log, admin | API, A2A, WebUI | T1-GM-AUDIT, T2-GM-SECRET-MASK |
| UC1.7 / FR1.19 | Group, User, RepositoryProfile | membership cascade | "An administrator shall be able to manage profiles, users, groups, API keys, RBAC bindings, and settings from the admin APIs and routed admin pages." plus group membership granting a profile-scoped repository resource | group-admin adds member; member becomes profile-scoped | API, MCP, A2A, WebUI | T3-GM-CASCADE |

## WebUI Justification

| Page | Use case / role justification |
|---|---|
| `/` dashboard | operator overview for authenticated `user`, `admin`, and service health diagnostics |
| `/profiles` | `UC1.5` profile CRUD for `admin`; profile read for scoped `user` |
| `/workspace` | `UC1.1` workspace lifecycle for any profile-scoped user |
| `/repository`, `/history`, `/diff` | `UC1.2` and `UC1.3` repository inspection for `git-reader` and `git-maintainer` |
| `/branches`, `/merge`, `/tags`, `/stashes`, `/recovery` | `UC1.3` and `UC1.4` git workflow pages; write controls require maintainer/admin grants |
| `/audit` | `UC1.6` audit/log review for `audit-log` and `admin`; secrets are masked |
| `/admin/users`, `/admin/groups`, `/admin/api-keys`, `/admin/rbac` | `UC1.5` IDAM administration for `admin` and scoped `group-admin` |
| `/api-docs`, `/mcp-console`, `/a2a-console` | developer/operator surfaces for authenticated users; backend guard enforces the same permissions as API/MCP/A2A |
| `/jobs` | `job-control` grant views and controls managed jobs |
| `/settings` | read-only effective configuration and masked values for authenticated operators |

## Reconciliation Gaps

| Gap | Status |
|---|---|
| The service uses `profile:<name>` role labels as the concrete group-to-resource edge. Thread-B central `RBACBinding` enforcement is consumed as the future estate-wide source once W28A-741 is live everywhere. | flagged, not papered over |
| Group membership and role propagation exist in `AdminRuntime`, but there is not yet a separate git-mcp domain table FK from profile to group. | acceptable by Thread-B design: no per-service FK |
| Existing WebUI browser specs live in the UI monorepo. This lane documents parity and proves backend contracts without touching the monorepo dirty-state. | scoped to avoid W28A-871 conflict |


<!-- W28E-1804A cross-surface UC->FR mapping (de-mechanised; supersedes W28C-1710b deferral) -->

## Cross-surface UC mappings (W28E-1804A)

Per T-RUC v1.1 + PS-REQ-TEST-TRACE §3.5, every `UC-NNN` maps to one or more canonical `FR-NNN`
(see `docs/REQUIREMENTS.md` §4A) across this service's surface set **api, mcp, a2a, webui**. The same
`UC` can be satisfied by different `FR` rows per surface; negative `CS-NNN` rows guard each surface.

| UC | Goal | API mapping | MCP mapping | A2A mapping | WebUI mapping | Negatives |
|---|---|---|---|---|---|---|
| `UC1.1` | Open / reopen / switch-ref / close a repository workspace | `FR-002`, `FR-022` | `FR-003`, `FR-005`, `FR-006` | `FR-004` | `FR-014`, `FR-018` | `CS-001`, `CS-005`–`CS-008`, `CS-017` |
| `UC1.2` | Browse, search, download/upload, and edit repository content | `FR-002`, `FR-008` | `FR-008`, `FR-021` | `FR-004` (`file_write`) | `FR-014`, `FR-009`, `FR-018` | `CS-002`, `CS-009`–`CS-012`, `CS-018` |
| `UC1.3` | Inspect status, review history/diffs, stage/commit/push, manage branches | `FR-002`, `FR-007` | `FR-010` | `FR-004` (`git_status`/`git_commit`) | `FR-014` | `CS-018`, `CS-013`–`CS-016` |
| `UC1.4` | Work with tags, stashes, merge/rebase conflicts, recovery artefacts | `FR-002` | `FR-011`, `FR-006` | — | `FR-014`, `FR-018` | `CS-004`, `CS-018` |
| `UC1.5` | Administer profiles, users, groups, API keys, RBAC, settings | `FR-012`, `FR-022` | `FR-013`, `FR-023` | — | `FR-014`, `FR-017` | `CS-002`–`CS-004`, `CS-020` |
| `UC1.6` | Review audit/operational logs, service status, config-change events | `FR-015`, `FR-002` | `FR-016` | `FR-004` (`/a2a/events/config`) | `FR-014`, `FR-016`, `FR-009`, `FR-020` | `CS-019` |
| `UC1.7` | Group-scoped repository-profile access (membership cascade) | `FR-023` | `FR-019`, `FR-023` | `FR-019` | `FR-014` | `CS-002`, `CS-018` |

Non-functional coverage (`NF-001`–`NF-010`) underpins every UC: shared-core separation, deterministic
config, stable workspace/job state, safe mutation, durable audit, bounded execution, browser-delivery
discipline, documentation/traceability integrity, platform-package adoption, and secret separation.
