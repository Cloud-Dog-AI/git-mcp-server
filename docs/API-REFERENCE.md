---
template-id: T-API
template-version: 1.0
applies-to: docs/API-REFERENCE.md
registry: service
required: must-have
when-applicable: ""
template-last-updated: 2026-06-12
template-owner: platform-standards

project: git-mcp-server
doc-last-updated: 2026-06-12
doc-git-commit: 579922dcddd9b6faa97f58b8096e325611289620
doc-git-branch: main
doc-source-shas: []
doc-age-policy: 90d
doc-conformance-stamp: 2026-06-12T12:00:00Z
---

# git-mcp-server — API-REFERENCE

> **Template version:** T-API v1.0 — REST surface authoritative reference. `openapi.json` is build-generated; this doc explains it.

## 1. Auth model
Auth modes accepted (`api_key`, `cookie`, `vault-bootstrap`), header name, RBAC mapping.

## 2. Routes

**You MUST include:** every route registered by the service. Group by section: Auth / Admin / Data / Health.

| Method | Path | Auth | RBAC | Summary | Request | Response |
|---|---|---|---|---|---|---|
| GET | `/health` | none | n/a | liveness | — | `{status:"ok"}` |

## 3. Error model
Standard error envelope, status codes, retryability.

## 4. Examples
**You MUST include:** at least one worked curl example per route group.

```
curl -H "X-API-Key: ${API_KEY}" https://<host>/api/v1/<route>
```

## 5. Cross-references
- [openapi.json](openapi.json)
- [MCP-REFERENCE.md](MCP-REFERENCE.md)
- [A2A-REFERENCE.md](A2A-REFERENCE.md)
- [WEBUI-REFERENCE.md](WEBUI-REFERENCE.md)
- PS-20-api.md

## 6. Project-specific notes



<!-- W28C-1710a recovery: full content from archive/2026-06-12/API.md (archived sha256=75ac77532ba9, 40 lines) -->

## Recovered domain content — `archive/2026-06-12/API.md` (40 lines)

_This section carries forward the full content of the archived predecessor doc verbatim. Topic checklist + SHA256 chain in `cloud-dog-ai-platform-standards/working/evidence/W28C-1710a/per-doc/git-mcp-server/API.md.topics.tsv`. Archive contents are unchanged (sha256 stable)._

# Git MCP API

This is the canonical API reference entry point for W28A-745. Historical API,
MCP, and operational references remain available in `docs/archive/` where they
have been archived; this document names the live contract and points to the
generated OpenAPI document.

## Public Surfaces

| Surface | Public route shape | Purpose |
|---|---|---|
| Health/Web | `/health`, `/`, routed SPA pages | service health and operator UI |
| API | `/api/v1/...` | health, auth, tool execution, admin CRUD, jobs, UI support |
| MCP | `/mcp`, `/mcp/tools`, `/mcp/tools/{name}` | JSON-RPC discovery and tool execution |
| A2A | `/a2a/...`, `/.well-known/agent.json` | A2A health/card/events and skills |

The generated API schema remains at `docs/openapi.json`.

## Access Control

Every domain operation reaches `ToolRegistry` and every profile-bearing operation
uses the `profile:<name>` grant check. Both `call()` and `call_with_access()`
converge through `_call_with_audit()`, so audit redaction and typed event emission
cover all tool dispatch paths.

## MCP Tool Families

| Family | Examples |
|---|---|
| Repository lifecycle | `repo_open`, `repo_close`, `repo_set_ref` |
| Git reads | `git_status`, `git_log`, `git_diff`, `git_branch_list`, `git_tag_list`, `git_stash_list` |
| Git mutations | `git_add`, `git_commit`, `git_push`, `git_merge`, `git_rebase`, `git_tag_create` |
| Files/directories | `file_read`, `file_write`, `file_upload`, `file_download`, `dir_list` |
| Administration | `admin_profile_create`, `admin_user_*`, `admin_group_*`, `admin_rbac_*`, `admin_api_key_*` |

## Secret Handling

Managed API-key creation returns `raw_key` once. List/read operations return only
metadata. Audit parameters named `content`, `password`, `secret`, `token`, or
`body` are redacted centrally before emission.
