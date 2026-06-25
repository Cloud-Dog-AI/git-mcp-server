---
template-id: T-WUI
template-version: 1.0
applies-to: docs/WEBUI-REFERENCE.md
registry: service
required: conditional
when-applicable: ""
template-last-updated: 2026-06-12
template-owner: platform-standards

project: git-mcp-server
doc-last-updated: 2026-06-18
doc-git-commit: 92ef7210b67e936d847a98e97d5099a5bd73ba76
doc-git-branch: main
doc-source-shas: []
doc-age-policy: 90d
doc-conformance-stamp: 2026-06-18T00:00:00Z
---

# git-mcp-server — WEBUI-REFERENCE

> **Template version:** T-WUI v1.0 — conditional: service has a WebUI panel.

## 1. Panel structure

The git-mcp-server ships a React SPA (built from `apps/git-mcp` in the
ui-monorepo). Static assets are served from `ui/dist/` via FastAPI's
`StaticFiles` mount. A `runtime-config.js` endpoint delivers browser-side
configuration at runtime.

Navigation is organised into four top-level groups. Role-gated panels show a
`RestrictedPage` placeholder for callers without the required access.

| Route | Panel | Roles | Backend route |
|---|---|---|---|
| `/` | Dashboard — workspace metrics, service health status bar | all | `GET /api/v1/ui/status`, `GET /api/v1/ui/version` |
| `/profiles` | Profiles — repository profile management | `admin`, `maintainer` | `GET/POST/PUT /api/v1/admin/profiles` |
| `/workspaces` | Workspaces — active workspace listing and lifecycle | all | `GET /api/v1/workspaces` |
| `/workspace` | Workspace Diagnostics — ref context, disk, diagnostics | all | `GET /api/v1/workspaces/{id}` |
| `/repository` | Repository Browser — directory tree, file read/write | all (write: `writer`+) | `tools/call: dir_list`, `file_read`, `file_write` |
| `/history` | Commit Log — filtered git log with author/since/until | all | `tools/call: git_log` |
| `/diff` | Diff Viewer — diff between two refs | all | `tools/call: git_diff` |
| `/branches` | Branch Manager — list, create, delete, checkout | all (write: `writer`+) | `tools/call: git_branch_*`, `git_checkout` |
| `/merge` | Merge — merge and conflict resolution workflow | `maintainer`+ | `tools/call: git_merge`, `git_merge_abort`, `git_merge_continue`, `git_conflict_*` |
| `/tags` | Tag Manager — list, create, delete, push tags | all (write: `writer`+) | `tools/call: git_tag_*` |
| `/stashes` | Stash Manager — list, save, pop stashes | all (write: `writer`+) | `tools/call: git_stash_*` |
| `/recovery` | Recovery — rebase/stash recovery and conflict resolution | `maintainer`+ | `tools/call: git_rebase_*`, `git_conflict_*` |
| `/audit` | Audit & Log — normalised audit log viewer with filters | `admin` | `GET /api/v1/audit`, `GET /api/v1/logs` |
| `/idam/users` | Users — IDAM user management | `admin` | `GET/POST/PUT/DELETE /api/v1/admin/users` |
| `/idam/groups` | Groups — IDAM group management | `admin` | `GET/POST/PUT/DELETE /api/v1/admin/groups` |
| `/idam/api-keys` | API Keys — managed API key lifecycle | `admin` | `GET/POST/DELETE /api/v1/admin/api-keys` |
| `/idam/roles` | Roles — role label management | `admin` | `GET /api/v1/admin/roles` |
| `/idam/rbac` | RBAC — role binding management | `admin` | `GET/POST/DELETE /api/v1/admin/rbac` |
| `/api-docs` | API Docs — embedded OpenAPI (Redoc/Swagger) | all | `GET /openapi.json` |
| `/mcp-console` | MCP Console — interactive `tools/list` + `tools/call` | all | `POST /mcp` (JSON-RPC 2.0) |
| `/a2a-console` | A2A Console — Agent-to-Agent event stream console | all | `GET /a2a/...` |
| `/jobs` | Jobs — background job queue listing | all | `GET /api/v1/jobs` |
| `/settings` | Settings — runtime config viewer, secret reveal, log paths | `admin` | `GET/PUT /api/v1/settings`, `GET /api/v1/settings/config` |

**Alias routes** (redirect to canonical):

| Alias | Canonical |
|---|---|
| `/dashboard` | `/` |
| `/browser`, `/files` | `/repository` |
| `/log`, `/commits` | `/history` |
| `/audit-recovery` | `/recovery` |
| `/admin/*` | `/idam/*` (PS-71 lock) |

## 2. Login

Login mode is `cookie` (username/password). The SPA reads `AUTH_MODE` from
`/runtime-config.js`; git-mcp always advertises `"cookie"` regardless of the
service-to-service API `auth.mode` setting.

**Flow:**
1. Unauthenticated SPA renders the shared `@cloud-dog/auth` `LoginPage`
   component with `mode="cookie"`.
2. User submits username + password; the SPA `POST`s to `/auth/login`.
3. On success the server mints a `git_web_session` cookie (HttpOnly, SameSite).
4. The SPA redirects to `/`.
5. Logout: `POST /auth/logout` clears the cookie and redirects to `/login`.
6. Session timeout: configured via `SESSION_TIMEOUT_MINUTES` (default 30 min);
   a warning dialog appears 5 minutes before expiry.

Three flat-role accounts are seeded at startup:

| Account | Default role |
|---|---|
| `admin` | admin |
| `read-write` | writer |
| `read-only` | reader |

Credentials are configured via `web_login.*` in the service config and are
distinct from the API/MCP X-API-Key service-to-service path.

## 3. RBAC visibility matrix

Role hierarchy: `admin` > `maintainer` > `writer` > `reader`.

| Panel | admin | maintainer | writer | reader |
|---|---|---|---|---|
| Dashboard | full | full | full | full |
| Profiles | manage | manage | hidden (RestrictedPage) | hidden |
| Workspaces | full | full | full | full |
| Workspace Diagnostics | full | full | full | full |
| Repository Browser | read + write | read + write | read + write | read only |
| Commit Log | full | full | full | full |
| Diff Viewer | full | full | full | full |
| Branch Manager | read + write + delete | read + write + delete | read + write | read only |
| Merge | full (merge + conflict resolve) | full | hidden / read-only view | hidden |
| Tag Manager | read + write + push | read + write + push | read + write | read only |
| Stash Manager | full | full | full (save/pop) | read only (list) |
| Recovery | full | full | hidden | hidden |
| Audit & Log | full | hidden (RestrictedPage) | hidden | hidden |
| IDAM pages (Users/Groups/API Keys/Roles/RBAC) | full | hidden | hidden | hidden |
| API Docs | full | full | full | full |
| MCP Console | full | full | full | full |
| A2A Console | full | full | full | full |
| Jobs | full | full | full | full |
| Settings | full | hidden (RestrictedPage) | hidden | hidden |

## 4. Static routes

SPA-served routes (served via SPA fallback handler, `index.html` returned for
non-API paths). The following path roots are **reserved** and return 404 from
the SPA fallback (they route to API/MCP/A2A backends):

```
api, app, mcp, a2a, assets, docs, openapi.json, redoc, health, live, ready,
status, runtime-config.js
```

Three known SPA deep-link routes receive explicit `@app.get` registrations to
prevent the SPA fallback from routing them as API paths:

| Route | SPA page |
|---|---|
| `/api-docs` | API Docs |
| `/mcp-console` | MCP Console |
| `/a2a-console` | A2A Console |

All other `/{path:path}` requests that do not match a reserved root are served
as SPA entry points (returning `index.html`).

## 5. Cross-references
- [API-REFERENCE.md](API-REFERENCE.md)
- [ROLES-AND-USECASES.md](ROLES-AND-USECASES.md)
- PS-77-webui-comprehensive.md
- PS-30-ui.md

## 6. Project-specific notes

The `runtime-config.js` endpoint (served at `/runtime-config.js`) delivers
browser-side runtime configuration as a JavaScript assignment to
`window.__RUNTIME_CONFIG__`. It is always `Cache-Control: no-store`. Key
fields injected: `ENV`, `API_BASE_URL`, `MCP_BASE_URL`, `A2A_BASE_URL`,
`AUTH_MODE` (always `"cookie"`), `DEFAULT_PROFILE`, `REMOTE_REPO_URL`,
`SESSION_TIMEOUT_MINUTES`.

The Settings page (`/settings`) exposes a `GET /api/v1/settings/config/sources`
endpoint (W28J-1328 GMC-SE-02) that returns per-leaf source provenance
(defaults.yaml vs config.yaml layer attribution) for each config key. Secret
values are masked (`"****"`) in both `/settings/config` and the source
provenance response. An admin-only `POST /api/v1/settings/config/audit-reveal`
emits an audit event when secrets are revealed client-side.
