---
template-id: T-SCM
template-version: 1.0
applies-to: tests/SCOPE-MAP.md
project: git-mcp-server
doc-last-updated: 2026-06-23
doc-git-commit: c12b180e687b0a9dfac728161b44a963a12359ac
doc-git-branch: main
doc-age-policy: 30d
doc-conformance-stamp: 2026-06-23T00:00:00Z
---

# git-mcp-server — Test scope map

> **Template version:** T-SCM v1.0 — required by PS-REQ-TEST-TRACE §5. Maps source-module globs to the
> test IDs that must run when those paths change (RULES §5.8 scoped runs). Refreshed in W28E-1804A with the
> de-mechanised semantic `req()` bindings.

## Mapping

| Source glob | Requirement(s) | Test IDs |
|---|---|---|
| `src/git_tools/config/**` | `FR-001`, `NF-002` | `UT1.1`, `UT1.2`, `UT1.3`, `QT_VAULT` |
| `src/git_mcp_server/api_server.py`, `src/git_mcp_server/ui_endpoints.py` | `FR-002`, `FR-015` | `IT1.1`, `UT1.57`, `UT1.65` |
| `src/git_mcp_server/mcp_server.py`, `src/git_tools/tools/**` | `FR-003` | `IT1.5`, `IT1.6`, `UT1.25`, `UT1.63` |
| `src/git_mcp_server/a2a_server.py` | `FR-004` | `AT1.6`, `IT1.11`, `IT1.13`, `UT1.26`, `UT1.58`, `UT1.68` |
| `src/git_tools/workspaces/**` | `FR-005`, `NF-003` | `ST1.1`, `ST1.2`, `ST1.12`, `UT1.8`, `UT1.69` |
| `src/git_tools/git/repo.py` (RefSpec) | `FR-006`, `CS-018` | `UT1.5`, `UT1.6`, `UT1.7`, `IT1.7`, `UT1.10` |
| `src/git_tools/git/operations.py` (remote) | `FR-007` | `IT1.9`, `IT1.10`, `IT1.16`, `UT1.48` |
| `src/git_tools/files/**` | `FR-008`, `FR-021`, `NF-004`, `CS-017` | `UT1.21`–`UT1.37`, `UT1.9`, `QT1.2` |
| `src/git_tools/jobs/**`, `src/git_mcp_server/jobs/**` | `FR-009`, `NF-006` | `UT1.55`, `IT1.15`, `IT1.62`, `UT1.49` |
| `src/git_tools/git/operations.py` (workflow) | `FR-010` | `UT1.14`–`UT1.16`, `UT1.38`–`UT1.42`, `UT1.47`, `ST1.3`, `AT1.1` |
| `src/git_tools/git/conflicts.py`, `src/git_tools/git/tags.py` | `FR-011` | `UT1.17`–`UT1.20`, `UT1.43`–`UT1.46`, `UT1.50`, `ST1.4`–`ST1.8` |
| `src/git_tools/admin/**`, `src/git_mcp_server/admin/**` | `FR-012`, `FR-013`, `FR-023` | `AT1.4`, `IT1.4`, `IT1.14`, `UT1.4`, `UT1.11`, `UT1.51`, `UT1.54`, `UT1.56`, `UT1.64` |
| `src/git_mcp_server/web_server.py` | `FR-014`, `NF-007` | `AT_WEBUI`, `UT1.56` |
| `src/git_tools/audit/**` | `FR-016`, `NF-005` | `UT1.12`, `UT1.13`, `UT1.67`, `IT1.8`, `ST1.9`, `ST1.10`, `UT_AUDIT_FORMAT` |
| `src/git_mcp_server/ui_endpoints.py` (settings), `src/git_mcp_server/workspace_enum_endpoints.py` | `FR-017`, `FR-018` | `UT1.60`, `UT1.61`, `IT1.61` |
| `src/git_tools/admin/runtime.py` (role_bindings) | `FR-019` | `T3-GM-CASCADE` (smoke) |
| `src/git_tools/db/**` | `FR-020` | `UT1.27`, `ST1.11` |
| `src/git_mcp_server/auth/**` | `FR-022`, `CS-001`–`CS-016`, `CS-020` | `IT1.2`, `IT1.3`, `IT1.12`, `UT1.52`, `UT1.53`, `UT1.62`, `UT1.65`, `UT1.66`, `UT1.70`, `AT1.7` |
| `src/git_tools/security/**` | `CS-019`, `NF-009`, `NF-010` | `QT1.1`, `QT26`, `QT_VAULT`, `QT_SECURITY_SUITE`, `QT_PACKAGE` |
| `src/**/*.py` (cross-cutting quality) | `NF-001`, `NF-008` | `QT_LIB_SEPARATION`, `QT_DOCS`, `QT_TRACEABILITY`, `QT_RULES`, `QT1.4` |

## Cross-references

- Platform standard: PS-REQ-TEST-TRACE v1.0 §5
- Tier policy: standards/TEST-POLICY-SCOPED.md
- Requirements: `docs/REQUIREMENTS.md` §4A / §5 / §6A canonical tables
