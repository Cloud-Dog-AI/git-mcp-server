# Git MCP Data Model

This document is the canonical data-model reference for the W28A-745 Thread-B lane.
It separates identity, access, repository-domain, jobs, and audit records so the
group-to-resource cascade can be verified explicitly.

## Identity And Access

| Model | Storage | Purpose |
|---|---|---|
| User | `AdminRuntime.user_store` / admin API materialisation | Human principal with username, email, status, and group memberships |
| Group | `AdminRuntime.group_store` | Role-bearing group with member list |
| RoleBinding | `AdminRuntime.role_bindings` | Direct user role labels |
| ApiKey | `cloud_dog_idam.APIKeyManager` plus `AdminRuntime.api_key_metadata` | API-key identity, owner, status, and capability metadata |
| Profile Grant | role/capability label `profile:<profile_name>` | git-mcp resource grant used by `ToolRegistry._require_profile_access` |

Membership resolution is implemented in `AdminRuntime.resolve_roles(user_id)`: direct
roles and group roles are combined, then `ToolRegistry._require_profile_access(...)`
checks for wildcard/admin or the concrete `profile:<name>` grant. Removing the user
from the group removes the group role from the next resolution and revokes access.

## Repository Domain

| Model | Storage | Purpose |
|---|---|---|
| RepositoryProfile | `ProfileStore` backed by `git_profile_registry` when DB is enabled; dict store in tests | Repository source, policy, owner, and access metadata |
| Workspace | `WorkspaceManager` metadata under configured workspace root | Active or persistent checkout tied to a profile/session/ref |
| RefContext | workspace metadata | Resolved branch, tag, or commit with mutability mode |
| RepositoryFile | workspace filesystem | File or directory path within the active checkout |
| GitOperation | `ToolRegistry` handler table | Shared business operation invoked by API, MCP, A2A, or WebUI |

## Jobs And Events

| Model | Storage | Purpose |
|---|---|---|
| Managed Job | `cloud_dog_jobs` runtime through `JobsRuntime` | Long-running repository/file operations with lifecycle controls |
| Config Event | `ConfigEventHub` journal | A2A config-change stream for profile mutations |
| AuditEvent | `AuditWriter` JSONL/event sink | Typed, redacted record for every tool dispatch path |

## Cascade

The service does not add a per-service foreign key from profile to group. The cascade
is the composition required by Thread-B:

1. Group `G` has role `profile:P`.
2. User `U` is added to `G`.
3. `AdminRuntime.resolve_roles(U)` returns `profile:P`.
4. `ToolRegistry._require_profile_access(... profile=P ...)` allows access.
5. Removing `U` from `G` removes `profile:P` from the resolved role set and the
   same profile access check raises `PermissionError`.

This preserves the W28A-741 design rule: the group-to-resource edge is a central
binding concept, not a bespoke FK in git-mcp domain rows.
