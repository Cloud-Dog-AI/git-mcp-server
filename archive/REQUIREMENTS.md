# Requirements — git-mcp-server

**Version:** 1.1  
**Date:** 2026-02-28  
**Standards:** PS-00, PS-10, PS-20, PS-40, PS-70, PS-80, PS-90, PS-95  
**Platform packages:** `cloud_dog_config`, `cloud_dog_logging`, `cloud_dog_api_kit`, `cloud_dog_idam`

---

## 1. Purpose

`git-mcp-server` is an **API-first** service that exposes **Git repository workflows** and **branch-scoped file/directory tooling** over:
- an MCP-compatible **A2A tool interface** (language-neutral), and
- an **HTTP API** (used by WebUI and automation clients).

It supports:
- local repositories (working copies backed by any upstream remote), and/or
- GitHub / GitLab (cloud or self-hosted) by using standard git remotes (MVP),
  with optional future service-API adapters.

It provides the full range of file tools similar to `file-mcp-server` (read, write, search, edit, validate, diff, delete, directory ops, upload/download), **explicitly in the context of a specific branch/tag/commit ref**.

It also supports:
- branches, tags, commits
- fetch/pull/push
- merge, rebase, fast-forward, simplified conflict resolution
- session safety and auto-recovery for ungraceful endings
- multiple repository profiles
- RBAC (users/groups/roles) and enterprise auth options (LDAP/Keycloak/SAML)
- Admin CRUD of profiles via tools
- WebUI (admin-focused: user mgmt, config, logs, credentials)

**No LLMs are used or required.**

---

## 2. Core Concepts & Definitions

- **Profile**: Named repository configuration (e.g. `repoA`, `repoB`) with repo target, auth mode, policies, scope, file types.
- **Ref**: A specific Git reference: `branch`, `tag`, or `commit`.
- **Workspace**: A working directory bound to `(profile, session_id)` that has a checked-out ref.
- **Ref Context**: The `(workspace_id, ref, mode)` tuple used to scope operations.
  - `mode=working_tree`: mutable operations allowed (typically branch checkout)
  - `mode=ref_readonly`: read-only browsing (typically tag/commit/detached)
- **Protected branches**: Branch patterns restricted by RBAC/policy (e.g. `main`, `release/*`).
- **Audit log**: Append-only record of operations and outcomes (no secrets).

---

## 3. Stakeholders & Actors

- **Agent/Client**: Calls MCP tools and/or HTTP API.
- **Admin**: Manages profiles, RBAC, credentials, policies, diagnostics.
- **Operator**: Deploys and monitors system.

---

## 4. High-level Use Cases

### UC-01: Open repo on a feature branch, upload file, commit, push
1. `repo_open(profile="repoA", ref={type:"branch", name:"feature/x"}, workspace_mode="ephemeral") -> workspace_id`
2. `file_upload(workspace_id, path="docs/spec.md", bytes|base64, overwrite=true)`
3. `git_add(workspace_id, paths=["docs/spec.md"])`
4. `git_commit(workspace_id, message="Add spec")`
5. `git_push(workspace_id, remote="origin", branch="feature/x")`

### UC-02: Search and edit within the checked-out branch
1. `search_content(workspace_id, query="TODO", globs=["**/*.md"])`
2. `edit_markdown(workspace_id, path="README.md", op="replace_section", section=["Usage"], content="...")`
3. `validate_file(workspace_id, path="README.md", mode="warn")`
4. `git_status(workspace_id)` shows changed file.

### UC-03: Browse a release tag read-only
1. `repo_open(profile="repoA", ref={type:"tag", name:"v1.2.0"}, mode="ref_readonly")`
2. `dir_list(workspace_id, path=".", recursive=false)`
3. `file_read(workspace_id, path="CHANGELOG.md")`
4. Attempts to `file_write` MUST fail (read-only mode).

### UC-04: Create a branch from a tag and apply edits
1. `repo_open(profile="repoA", ref={type:"tag", name:"v1.2.0"}, mode="ref_readonly")`
2. `git_branch_from_ref(workspace_id, from_ref={type:"tag", name:"v1.2.0"}, new_branch="hotfix/v1.2.1")`
3. `repo_set_ref(workspace_id, ref={type:"branch", name:"hotfix/v1.2.1"}, mode="working_tree")`
4. Edit, commit, push.

### UC-05: Simplified rebase onto main with conflict helpers
1. `git_fetch(workspace_id, remote="origin")`
2. `git_rebase(workspace_id, onto="origin/main", strategy="auto")`
3. If conflicts:
   - `git_conflicts_list(workspace_id)`
   - `git_conflict_resolve(workspace_id, mode="ours", paths=[...])` (or theirs/manual)
   - `git_rebase_continue(workspace_id)`
4. `git_push(workspace_id, force_with_lease=true)`

### UC-06: Ungraceful session end triggers auto-recovery
1. Session times out or crashes.
2. System applies profile recovery policy:
   - `stash` OR `commit_recovery_branch` OR `patch_bundle`
3. Records recovery artefact and audit event.
4. Admin/agent can `recovery_list(profile|workspace_id)` and optionally `recovery_restore(...)` (if enabled).

### UC-07: Admin creates repo profile and assigns RBAC
1. `admin_profile_create(...)`
2. `admin_rbac_bind(group="devs", profile="repoA", role="writer")`
3. WebUI displays profile; users see it based on RBAC.

---

## 5. Functional Requirements (FR)

### FR-01 Interfaces: MCP A2A + HTTP API (API-first) (PS-00 P1, PS-20)
- SHALL expose a tool catalogue and tool execution via MCP-compatible A2A interface.
- SHALL expose HTTP API endpoints (via `cloud_dog_api_kit` FastAPI factory) providing equivalent capabilities.
- HTTP API SHALL include correlation IDs, structured error responses, and health endpoints per PS-20.
- WebUI SHALL call HTTP API only (no privileged bypass).

### FR-02 Configuration precedence and no hard-coded values (PS-80, PS-00 P2)
- SHALL use `cloud_dog_config` for all configuration loading.
- Precedence: `os.environ → .env → config.yaml → defaults.yaml → Vault`.
- SHALL support Vault integration for shared secrets (database, credentials, keys).
- SHALL support env interpolation in YAML values (e.g. `${VAR}`).
- SHALL NOT hard-code any paths, URLs, scopes, credentials, keys, or policies.
- After startup, all code MUST read from a single GlobalConfig object only.

### FR-03 Multi-profile repositories
- SHALL support multiple profiles, each describing:
  - repo source (local path or clone URL)
  - remotes configuration
  - workspace mode (`persistent` or `ephemeral`)
  - file scope + allowed types
  - Git policy (protected branches, ff-only rules, force push rules)
  - recovery policy
  - auth/credential mode

### FR-04 Authentication (AuthN) (PS-70)
- SHALL use `cloud_dog_idam` for all authentication.
- SHALL support API key and JWT bearer tokens via `cloud_dog_idam` middleware.
- SHALL support LDAP, Keycloak OIDC, and SAML SSO via `cloud_dog_idam` pluggable providers.
- SHALL expose `/a2a/health` on the API runtime port under the canonical `/a2a` namespace.
- `/a2a/*` endpoints SHALL require `Authorisation: Bearer <token>` and SHALL NOT accept `x-api-key` fallback.
- In strict local test mode, key `12345678` SHALL be accepted for A2A contract verification.
- A2A bearer validation SHALL use the same API-key authority (`cloud_dog_idam` APIKeyManager) as HTTP API auth.

### FR-05 Authorisation (RBAC) (PS-70)
- SHALL use `cloud_dog_idam` RBAC engine for all authorisation.
- SHALL implement RBAC over:
  - profiles (repo access)
  - tool categories (file ops, git ops, admin ops)
  - branch/tag constraints (e.g. protected branches)
- SHALL define users, groups, roles (reader/writer/maintainer/admin) via `cloud_dog_idam`.
- SHALL provide admin tools/APIs to manage RBAC via `cloud_dog_idam` admin services.

### FR-06 Credential handling
- SHALL support:
  - stored credentials (encrypted at rest), and/or
  - session-provided credentials for upstream pass-through
- SHALL support SSH and HTTPS token approaches.
- SHALL never log raw credentials/tokens/keys.

### FR-07 Ref Context is mandatory for file operations
- All file/directory tools SHALL require `workspace_id` and SHALL operate relative to the repo root.
- File/directory tools SHALL be executed within an explicit ref context:
  - `mode=working_tree`: branch checked out; edits allowed per RBAC/policy
  - `mode=ref_readonly`: browsing tag/commit; mutating file tools MUST fail
- The system MAY provide a profile default ref, but the resolved ref MUST be returned to the client.

### FR-08 Branch-scoped file and directory tools
The system SHALL provide (minimum) the following tools, scoped to the branch in the workspace:

**Directory**
- `dir_list(workspace_id, path=".", recursive?, glob?, include_hidden?, max_entries?)`
- `dir_mkdir(workspace_id, path, parents?)`
- `dir_rmdir(workspace_id, path, recursive?)`

**File read/download**
- `file_read(workspace_id, path, range?, encoding_hint?)`
- `file_download(workspace_id, path)` (HTTP endpoint; MCP returns bytes/base64)

**File write/upload**
- `file_write(workspace_id, path, content, create?, overwrite?, dry_run?)`
- `file_upload(workspace_id, path, bytes|base64, overwrite?)`

**Move/copy/delete**
- `file_move(workspace_id, src, dst, overwrite?, dry_run?)`
- `file_copy(workspace_id, src, dst, overwrite?, dry_run?)`
- `file_delete(workspace_id, path, dry_run?)`

**Search**
- `search_files(workspace_id, query, globs?, regex?, case_sensitive?, max_results?)`
- `search_content(workspace_id, query, globs?, regex?, context_lines?, max_results?)`

**Edit/validate/diff**
- `edit_text`, `edit_json`, `edit_yaml`, `edit_xml`, `edit_html`, `edit_markdown`
- `validate_file`
- `diff_files`, `diff_text`
- `meld` (optional)

All tools MUST enforce: RBAC + profile scope + allowed types.

### FR-09 Structured edits and validation (parity with file-mcp-server)
- SHALL support structured edits for: `.md .txt .json .yaml .yml .html .xml`.
- SHALL support:
  - sed-like edits (regex/range/line ops)
  - structured CRUD:
    - JSON/YAML: JSON Pointer and optional dot-path
    - XML: XPath
    - HTML: CSS selectors and/or XPath
    - Markdown: heading-path section operations and frontmatter update
- SHALL implement `validate_file` for:
  - JSON/YAML/XML/HTML/Markdown
- Validation policy SHALL support `strict | warn | ignore` per file type.
- After any change, post-validation SHALL run according to policy (strict can block write).

### FR-10 Git tools (minimum)
Repository state and history:
- `git_status`
- `git_log` (filters)
- `git_diff` (working tree/index/commit)

Branching and checkout:
- `git_branch_list`
- `git_branch_create`
- `git_branch_delete`
- `git_checkout`
- `git_branch_from_ref` (create branch from tag/commit)

Staging and commits:
- `git_add`
- `git_reset` (paths)
- `git_commit` (message, author policy)

Remotes:
- `git_fetch`
- `git_pull`
- `git_push` (incl `force_with_lease` subject to policy)

Merging/rebasing:
- `git_merge` (ff-only / no-ff)
- `git_rebase` (simplified)
- `git_merge_abort`, `git_merge_continue`
- `git_rebase_abort`, `git_rebase_continue`

Stash:
- `git_stash_save`, `git_stash_list`, `git_stash_pop`

### FR-11 Tags are first-class
- SHALL support:
  - `git_tag_list(profile|workspace_id, pattern?, contains?)`
  - `git_tag_create(workspace_id, tag, commit?=HEAD, annotated?, message?)`
  - `git_tag_delete(profile|workspace_id, tag, local_only?=false)`
  - `git_tag_push(profile|workspace_id, remote="origin", tag? | all_tags?)`
- Checkout of a tag SHALL default to detached/read-only unless explicitly creating a branch.

### FR-12 Conflict detection and simplified resolution
- SHALL detect conflicts during merge/rebase.
- SHALL provide:
  - `git_conflicts_list`
  - `git_conflict_resolve(mode=ours|theirs, paths=...)`
  - `git_conflict_resolve_manual(path, content)` (agent provides merged content)
- SHALL provide safe one-shot strategies (policy-controlled):
  - fast-forward only merges
  - rebaseline (rebase onto target + push with lease)

### FR-13 Session lifecycle and auto-recovery
- SHALL implement `repo_open`, `repo_set_ref`, `repo_close`, and session heartbeat/timeout.
- On ungraceful termination, SHALL apply recovery policy:
  - stash OR recovery branch commit OR patch bundle snapshot
- SHALL record recovery manifest and audit events.
- SHALL provide `recovery_list` and `recovery_get` tools; `recovery_restore` is optional but recommended.

### FR-14 Audit logging (PS-40)
- SHALL use `cloud_dog_logging` for all structured operational logs and audit trail.
- SHALL write append-only audit entries (JSONL format via `cloud_dog_logging` audit logger) for:
  - git operations
  - file operations (incl upload/download/delete)
  - admin operations
  - auth events (no secrets)
- Audit entries SHALL include:
  - timestamp UTC
  - actor identity
  - profile + workspace_id + resolved ref
  - operation + redacted params
  - before/after commit hashes when applicable
  - status + errors/warnings

### FR-15 Admin CRUD of profiles and RBAC (tools + API)
Admin-only:
- `admin_profile_create/read/update/delete(soft)`
- `admin_user_create/update/disable`
- `admin_group_create/update/delete`
- `admin_rbac_bind/unbind`
- `admin_credentials_set/revoke` (if stored creds are enabled)

### FR-16 WebUI (admin-oriented) (PS-30)
- SHALL be built using `@cloud-dog/*` frontend packages when implemented.
- SHALL implement the WebUI as a strict API client: no direct filesystem, git, database, or secret-store access from browser code.
- SHALL support:
  - user/group management
  - profile CRUD + policy validation
  - branch/tag policy administration
  - audit/log viewing with correlation ID drill-down
  - credentials management (where permitted)
  - diagnostics/debug controls
- SHALL call HTTP API endpoints only (PS-00 P1).

### FR-17 WebUI/API parity and CRUD completeness
- Every mutating admin capability available in MCP/API SHALL be available in WebUI (create/read/update/delete or explicit policy-denied variant).
- Every WebUI screen action SHALL map to a documented HTTP API endpoint and deterministic error contract.
- WebUI SHALL expose operational views for:
  - profiles and RBAC
  - repository/workspace diagnostics
  - audit + structured logs
  - recovery artefacts and restore actions
- WebUI SHALL support safe confirmation flows for destructive actions (delete/revoke/force operations).
- WebUI SHALL surface API status codes and machine error codes without masking upstream failures.

---

## 6. Non-Functional Requirements (NFR)

### NFR-01 POSIX-Friendly
- Atomic file writes and portable filesystem assumptions.

### NFR-02 Security (PS-90)
- Robust scope enforcement, protected branch rules.
- Secrets NEVER logged (enforced by `cloud_dog_logging` redaction).
- Encrypted at rest if stored.
- Default-deny RBAC posture via `cloud_dog_idam`.

### NFR-03 Determinism
- Structured edits serialise consistently; conflict helpers are predictable.

### NFR-04 Performance
- Configurable caps on repo size, file size, search results, and timeouts (via `cloud_dog_config`).

### NFR-05 Observability (PS-40)
- Structured operational logs via `cloud_dog_logging` (JSON, correlation IDs).
- Separate audit log (JSONL) via `cloud_dog_logging` audit logger.
- Health endpoint via `cloud_dog_api_kit`.

### NFR-06 Extensibility (PS-10)
- `git_tools/` library reusable without server transport.
- Library/server separation per PS-10.

### NFR-07 Testing (PS-95)
- Full test hierarchy: UT/ST/IT/AT/QT.
- All tests use `--env` for configuration.
- See TESTS.md for complete test plan.

### NFR-08 WebUI usability and accessibility (PS-30)
- WebUI SHALL meet keyboard-only operation for all controls.
- WebUI SHALL meet WCAG 2.2 AA colour contrast, focus visibility, and form labelling.
- WebUI SHALL provide responsive behaviour for desktop and standard laptop viewport widths used in Playwright suites.
- WebUI SHALL present explicit success/failure feedback for all CRUD operations.

---

## 7. Acceptance Criteria (examples)

1. File tools cannot run without a `workspace_id`; resolved `ref` is always returned.
2. In `ref_readonly` mode (tag/commit browsing), `file_write/file_delete/edit_*` fail without modifying anything.
3. Writer role can create branch/commit; reader role cannot.
4. Protected branch policy prevents direct pushes to `main` for non-maintainers.
5. `git_tag_create` creates tag; `git_tag_push(all_tags=true)` pushes to remote when permitted.
6. Merge conflict yields non-empty conflict list; `ours/theirs` resolution can complete and produce a clean index.
7. Session crash triggers recovery artefact according to policy; artefact is listed and audit logged.
8. Changing config YAML changes scope/paths/policies without code changes (no hard-coded values).
9. WebUI can complete profile CRUD and RBAC bind/unbind using API-only calls, with matching audit entries.
10. WebUI shows API error responses and correlation IDs for failed operations without fallback masking.

### Database Abstraction (cloud_dog_db adoption)

- R-DB-01: All database access MUST use `cloud_dog_db` engine/session/CRUD abstractions
- R-DB-02: Engine creation MUST use `cloud_dog_db` engine factories
- R-DB-03: Session management MUST use `cloud_dog_db.session.SyncSessionManager`/`AsyncSessionManager`
- R-DB-04: Schema migrations MUST use `cloud_dog_db` migration runner
- R-DB-05: Direct sqlite3/create_engine()/sessionmaker()/raw Session() FORBIDDEN in app code
- R-DB-06: DB health MUST use `cloud_dog_db.health.probe_database()`
- R-DB-07: DB connection config MUST come from cloud_dog_config/Vault-backed env hierarchy
- R-DB-08: Schema versioning MUST be tested across SQLite, MySQL, and PostgreSQL
- R-DB-09: Schema upgrade/downgrade MUST be validated with at least two migrations per dialect
- R-DB-10: CRUD outcomes MUST be consistent across SQLite, MySQL, and PostgreSQL
