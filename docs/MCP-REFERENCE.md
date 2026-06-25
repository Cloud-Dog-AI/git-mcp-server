---
template-id: T-MCP
template-version: 1.0
applies-to: docs/MCP-REFERENCE.md
registry: service
required: must-have
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

# git-mcp-server — MCP-REFERENCE

> **Template version:** T-MCP v1.0 — MCP tool surface (JSON-RPC 2.0 at `/mcp`).

## 1. Auth model

The MCP surface uses `api_key` auth by default. Callers supply the key in the
`X-API-Key` HTTP header. The resolved key is matched against `cloud_dog_idam`
managed API keys; the key's `capabilities` list is forwarded as RBAC roles to
the tool registry.

Role hierarchy (from `_ROLE_PERMISSIONS` in the server):

| Role | Permissions |
|---|---|
| `admin` | `*` (all) |
| `maintainer` | `git:read`, `git:write`, `git:execute`, `git:admin` |
| `writer` | `git:read`, `git:write`, `git:execute` |
| `reader` | `git:read` |

Admin tools (`admin_*`) require the resolved principal to be the service admin
or to carry admin-level capabilities. Repository tools enforce per-profile
access: the caller must hold the `profile:<name>` permission (or `admin`/`*`)
to open or mutate a workspace on that profile. Mutation tools are additionally
blocked on read-only profiles or `ref_readonly` workspaces.

## 2. Tools

63 tools are registered. They are grouped below for readability; all share the
JSON-RPC 2.0 envelope `{"jsonrpc":"2.0","method":"tools/call","params":{"name":"<tool>","arguments":{...}},"id":1}`.

---

### 2.1 `repo_open`

- **Description:** Create a workspace and open a repository context against a named profile.
- **RBAC:** Any authenticated caller with access to the target profile (`profile:<name>` or `admin`/`*`). Disk usage above 95 % causes refusal.
- **Input schema:**
  ```json
  {
    "type": "object",
    "properties": {
      "profile":        { "type": "string",  "description": "Profile name to open." },
      "session_id":     { "type": "string",  "description": "Request-correlation session identifier." },
      "repo_source":    { "type": ["string","null"], "description": "Override profile repo.source URL." },
      "workspace_mode": { "type": "string",  "enum": ["ephemeral","persistent"], "default": "ephemeral" },
      "ref":            { "type": ["object","null"], "description": "Optional RefSpec {type,name} to check out on open." },
      "workspace_id":   { "type": ["string","null"], "description": "Reopen an existing workspace by ID." }
    },
    "required": ["profile","session_id"]
  }
  ```
- **Returns:** `{workspace_id, path, mode, resolved_ref}`
- **Errors:** `PermissionError` if profile access denied; `RuntimeError` if disk pressure ≥ 95 %.

---

### 2.2 `repo_close`

- **Description:** Close and optionally clean a workspace.
- **RBAC:** Any authenticated caller.
- **Input schema:**
  ```json
  { "type": "object", "properties": { "workspace_id": { "type": "string" } }, "required": ["workspace_id"] }
  ```
- **Returns:** `{workspace_id, closed: true}`

---

### 2.3 `repo_set_ref`

- **Description:** Switch the workspace ref context (branch / tag / commit).
- **RBAC:** Any authenticated caller with profile access.
- **Input schema:**
  ```json
  {
    "type": "object",
    "properties": {
      "workspace_id": { "type": "string" },
      "ref": { "type": "object", "properties": { "type": { "type": "string", "enum": ["branch","tag","commit"] }, "name": { "type": "string" } }, "required": ["type","name"] }
    },
    "required": ["workspace_id","ref"]
  }
  ```
- **Returns:** `{workspace_id, resolved_ref: {type, name, resolved_commit, mode}}`
- **Errors:** `PermissionError` if branch not in profile `allowed_branches`.

---

### 2.4 `git_status`

- **Description:** Read git status (index + worktree state) for the workspace.
- **RBAC:** `reader` and above.
- **Input schema:**
  ```json
  { "type": "object", "properties": { "workspace_id": { "type": "string" } }, "required": ["workspace_id"] }
  ```
- **Returns:** `{entries: [{index_status, worktree_status, path}]}`

---

### 2.5 `git_log`

- **Description:** Read filtered git commit log.
- **RBAC:** `reader` and above.
- **Input schema:**
  ```json
  {
    "type": "object",
    "properties": {
      "workspace_id": { "type": "string" },
      "author":    { "type": ["string","null"] },
      "since":     { "type": ["string","null"] },
      "until":     { "type": ["string","null"] },
      "path":      { "type": ["string","null"] },
      "max_count": { "type": ["integer","null"] }
    },
    "required": ["workspace_id"]
  }
  ```
- **Returns:** `{log: <string>}`

---

### 2.6 `git_diff`

- **Description:** Read a git diff between two refs.
- **RBAC:** `reader` and above.
- **Input schema:**
  ```json
  {
    "type": "object",
    "properties": {
      "workspace_id": { "type": "string" },
      "left":  { "type": "string", "default": "HEAD~1" },
      "right": { "type": "string", "default": "HEAD" }
    },
    "required": ["workspace_id"]
  }
  ```
- **Returns:** `{diff: <string>}`

---

### 2.7 `git_add`

- **Description:** Stage files (git add).
- **RBAC:** `writer` and above. Blocked on read-only profiles.
- **Input schema:**
  ```json
  {
    "type": "object",
    "properties": {
      "workspace_id": { "type": "string" },
      "paths": { "type": "array", "items": { "type": "string" } }
    },
    "required": ["workspace_id","paths"]
  }
  ```
- **Returns:** `{staged: [...]}`

---

### 2.8 `git_reset`

- **Description:** Reset staged changes (git reset, optionally --hard).
- **RBAC:** `writer` and above. Blocked on read-only profiles.
- **Input schema:**
  ```json
  {
    "type": "object",
    "properties": {
      "workspace_id": { "type": "string" },
      "paths": { "type": "array", "items": { "type": "string" }, "default": [] },
      "hard": { "type": "boolean", "default": false }
    },
    "required": ["workspace_id"]
  }
  ```
- **Returns:** `{result: <string>}`

---

### 2.9 `git_commit`

- **Description:** Create a commit. Supports optional author/committer identity override (W28M-1602).
- **RBAC:** `writer` and above. Blocked on read-only profiles.
- **Input schema:**
  ```json
  {
    "type": "object",
    "properties": {
      "workspace_id":    { "type": "string" },
      "message":         { "type": "string" },
      "author_name":     { "type": ["string","null"] },
      "author_email":    { "type": ["string","null"] },
      "committer_name":  { "type": ["string","null"] },
      "committer_email": { "type": ["string","null"] }
    },
    "required": ["workspace_id","message"]
  }
  ```
- **Returns:** `{commit: <sha>}`

---

### 2.10 `git_fetch`

- **Description:** Fetch remote refs.
- **RBAC:** `reader` and above.
- **Input schema:**
  ```json
  {
    "type": "object",
    "properties": {
      "workspace_id": { "type": "string" },
      "remote": { "type": "string", "default": "origin" }
    },
    "required": ["workspace_id"]
  }
  ```
- **Returns:** `{result: <string>}`

---

### 2.11 `git_pull`

- **Description:** Pull from remote (fetch + merge).
- **RBAC:** `writer` and above. Blocked on read-only profiles.
- **Input schema:**
  ```json
  {
    "type": "object",
    "properties": {
      "workspace_id": { "type": "string" },
      "remote": { "type": "string", "default": "origin" },
      "branch": { "type": ["string","null"] }
    },
    "required": ["workspace_id"]
  }
  ```
- **Returns:** `{result: <string>}`

---

### 2.12 `git_push`

- **Description:** Push to remote.
- **RBAC:** `writer` and above. Blocked on read-only profiles.
- **Input schema:**
  ```json
  {
    "type": "object",
    "properties": {
      "workspace_id":    { "type": "string" },
      "remote":          { "type": "string", "default": "origin" },
      "branch":          { "type": ["string","null"] },
      "force_with_lease": { "type": "boolean", "default": false }
    },
    "required": ["workspace_id"]
  }
  ```
- **Returns:** `{result: <string>}`

---

### 2.13 `git_checkout`

- **Description:** Check out a branch, tag, or commit.
- **RBAC:** `writer` and above. Blocked on read-only profiles or branch not in allowlist.
- **Input schema:**
  ```json
  {
    "type": "object",
    "properties": {
      "workspace_id": { "type": "string" },
      "ref": { "type": "string" }
    },
    "required": ["workspace_id","ref"]
  }
  ```
- **Returns:** `{checked_out: <ref>}`

---

### 2.14 `git_branch_list`

- **Description:** List branches in the workspace repository.
- **RBAC:** `reader` and above.
- **Input schema:**
  ```json
  { "type": "object", "properties": { "workspace_id": { "type": "string" } }, "required": ["workspace_id"] }
  ```
- **Returns:** `{branches: [...]}`

---

### 2.15 `git_branch_create`

- **Description:** Create a new branch from a ref.
- **RBAC:** `writer` and above. Blocked on read-only profiles.
- **Input schema:**
  ```json
  {
    "type": "object",
    "properties": {
      "workspace_id": { "type": "string" },
      "name":     { "type": "string" },
      "from_ref": { "type": "string", "default": "HEAD" }
    },
    "required": ["workspace_id","name"]
  }
  ```
- **Returns:** `{branch, from_ref}`

---

### 2.16 `git_branch_delete`

- **Description:** Delete a branch.
- **RBAC:** `writer` and above. Blocked on read-only profiles.
- **Input schema:**
  ```json
  {
    "type": "object",
    "properties": {
      "workspace_id": { "type": "string" },
      "name":  { "type": "string" },
      "force": { "type": "boolean", "default": false }
    },
    "required": ["workspace_id","name"]
  }
  ```
- **Returns:** `{deleted: <name>}`

---

### 2.17 `git_branch_from_ref`

- **Description:** Create a branch from a specific ref (alias for branch_create with explicit from_ref).
- **RBAC:** `writer` and above. Blocked on read-only profiles.
- **Input schema:**
  ```json
  {
    "type": "object",
    "properties": {
      "workspace_id": { "type": "string" },
      "from_ref":    { "type": "string" },
      "new_branch":  { "type": "string" }
    },
    "required": ["workspace_id","from_ref","new_branch"]
  }
  ```
- **Returns:** `{branch, from_ref}`

---

### 2.18 `git_merge`

- **Description:** Merge a branch or ref into HEAD.
- **RBAC:** `maintainer` and above. Blocked on read-only profiles.
- **Input schema:**
  ```json
  {
    "type": "object",
    "properties": {
      "workspace_id": { "type": "string" },
      "ref":     { "type": "string" },
      "ff_only": { "type": "boolean", "default": false }
    },
    "required": ["workspace_id","ref"]
  }
  ```
- **Returns:** `{result: <string>}`

---

### 2.19 `git_merge_abort`

- **Description:** Abort an in-progress merge.
- **RBAC:** `maintainer` and above. Blocked on read-only profiles.
- **Input schema:**
  ```json
  { "type": "object", "properties": { "workspace_id": { "type": "string" } }, "required": ["workspace_id"] }
  ```
- **Returns:** `{result: <string>}`

---

### 2.20 `git_merge_continue`

- **Description:** Continue a merge after manual conflict resolution.
- **RBAC:** `maintainer` and above. Blocked on read-only profiles.
- **Input schema:**
  ```json
  { "type": "object", "properties": { "workspace_id": { "type": "string" } }, "required": ["workspace_id"] }
  ```
- **Returns:** `{result: <string>}`

---

### 2.21 `git_rebase`

- **Description:** Rebase the current branch onto a target ref.
- **RBAC:** `maintainer` and above. Blocked on read-only profiles.
- **Input schema:**
  ```json
  {
    "type": "object",
    "properties": {
      "workspace_id": { "type": "string" },
      "onto": { "type": "string" }
    },
    "required": ["workspace_id","onto"]
  }
  ```
- **Returns:** `{result: <string>}`

---

### 2.22 `git_rebase_abort`

- **Description:** Abort an in-progress rebase.
- **RBAC:** `maintainer` and above. Blocked on read-only profiles.
- **Input schema:**
  ```json
  { "type": "object", "properties": { "workspace_id": { "type": "string" } }, "required": ["workspace_id"] }
  ```
- **Returns:** `{result: <string>}`

---

### 2.23 `git_rebase_continue`

- **Description:** Continue a rebase after manual conflict resolution.
- **RBAC:** `maintainer` and above. Blocked on read-only profiles.
- **Input schema:**
  ```json
  { "type": "object", "properties": { "workspace_id": { "type": "string" } }, "required": ["workspace_id"] }
  ```
- **Returns:** `{result: <string>}`

---

### 2.24 `git_stash_save`

- **Description:** Stash uncommitted changes with a message label.
- **RBAC:** `writer` and above. Blocked on read-only profiles.
- **Input schema:**
  ```json
  {
    "type": "object",
    "properties": {
      "workspace_id": { "type": "string" },
      "message": { "type": "string" }
    },
    "required": ["workspace_id","message"]
  }
  ```
- **Returns:** `{result: <string>}`

---

### 2.25 `git_stash_list`

- **Description:** List all stashes in the workspace repository.
- **RBAC:** `reader` and above.
- **Input schema:**
  ```json
  { "type": "object", "properties": { "workspace_id": { "type": "string" } }, "required": ["workspace_id"] }
  ```
- **Returns:** `{result: [...]}`

---

### 2.26 `git_stash_pop`

- **Description:** Pop the latest stash entry.
- **RBAC:** `writer` and above. Blocked on read-only profiles.
- **Input schema:**
  ```json
  { "type": "object", "properties": { "workspace_id": { "type": "string" } }, "required": ["workspace_id"] }
  ```
- **Returns:** `{result: <string>}`

---

### 2.27 `git_tag_create`

- **Description:** Create a lightweight or annotated tag.
- **RBAC:** `writer` and above. Blocked on read-only profiles.
- **Input schema:**
  ```json
  {
    "type": "object",
    "properties": {
      "workspace_id": { "type": "string" },
      "tag":      { "type": "string" },
      "commit":   { "type": ["string","null"] },
      "annotated":{ "type": "boolean", "default": false },
      "message":  { "type": ["string","null"] }
    },
    "required": ["workspace_id","tag"]
  }
  ```
- **Returns:** `{tag: <name>}`

---

### 2.28 `git_tag_delete`

- **Description:** Delete a local tag.
- **RBAC:** `writer` and above. Blocked on read-only profiles.
- **Input schema:**
  ```json
  {
    "type": "object",
    "properties": {
      "workspace_id": { "type": "string" },
      "tag": { "type": "string" }
    },
    "required": ["workspace_id","tag"]
  }
  ```
- **Returns:** `{deleted: <name>}`

---

### 2.29 `git_tag_list`

- **Description:** List tags, with optional glob pattern and `--contains` filter.
- **RBAC:** `reader` and above.
- **Input schema:**
  ```json
  {
    "type": "object",
    "properties": {
      "workspace_id": { "type": "string" },
      "pattern":  { "type": ["string","null"] },
      "contains": { "type": ["string","null"] }
    },
    "required": ["workspace_id"]
  }
  ```
- **Returns:** `{tags: [...]}`

---

### 2.30 `git_tag_push`

- **Description:** Push one tag or all tags to remote.
- **RBAC:** `writer` and above. Blocked on read-only profiles.
- **Input schema:**
  ```json
  {
    "type": "object",
    "properties": {
      "workspace_id": { "type": "string" },
      "remote":   { "type": "string", "default": "origin" },
      "tag":      { "type": ["string","null"] },
      "all_tags": { "type": "boolean", "default": false }
    },
    "required": ["workspace_id"]
  }
  ```
- **Returns:** `{result: <string>}`
- **Errors:** `ValueError` if neither `tag` nor `all_tags=true` is supplied.

---

### 2.31 `git_conflicts_list`

- **Description:** List unresolved conflict paths in the workspace.
- **RBAC:** `reader` and above.
- **Input schema:**
  ```json
  { "type": "object", "properties": { "workspace_id": { "type": "string" } }, "required": ["workspace_id"] }
  ```
- **Returns:** `{conflicts: [...]}`

---

### 2.32 `git_conflict_resolve`

- **Description:** Resolve conflicts using `ours`, `theirs`, or `manual` content for a set of paths.
- **RBAC:** `writer` and above. Blocked on read-only profiles.
- **Input schema:**
  ```json
  {
    "type": "object",
    "properties": {
      "workspace_id":   { "type": "string" },
      "mode":           { "type": "string", "enum": ["ours","theirs","manual"] },
      "paths":          { "type": "array", "items": { "type": "string" } },
      "manual_content": { "type": ["string","null"] }
    },
    "required": ["workspace_id","mode","paths"]
  }
  ```
- **Returns:** `{resolved: [...], mode}`

---

### 2.33 `git_conflict_resolve_manual`

- **Description:** Resolve a single conflict path with caller-supplied file content.
- **RBAC:** `writer` and above. Blocked on read-only profiles.
- **Input schema:**
  ```json
  {
    "type": "object",
    "properties": {
      "workspace_id": { "type": "string" },
      "path":    { "type": "string" },
      "content": { "type": "string" }
    },
    "required": ["workspace_id","path","content"]
  }
  ```
- **Returns:** `{resolved: [...], mode: "manual"}`

---

### 2.34 `file_read`

- **Description:** Read file content from the workspace.
- **RBAC:** `reader` and above.
- **Input schema:**
  ```json
  {
    "type": "object",
    "properties": {
      "workspace_id": { "type": "string" },
      "path": { "type": "string" }
    },
    "required": ["workspace_id","path"]
  }
  ```
- **Returns:** `{content: <string>}`

---

### 2.35 `file_write`

- **Description:** Write (create or overwrite) a file in the workspace.
- **RBAC:** `writer` and above. Blocked on read-only profiles.
- **Input schema:**
  ```json
  {
    "type": "object",
    "properties": {
      "workspace_id": { "type": "string" },
      "path":      { "type": "string" },
      "content":   { "type": "string" },
      "overwrite": { "type": "boolean", "default": true }
    },
    "required": ["workspace_id","path","content"]
  }
  ```
- **Returns:** `{path: <relative-path>}`
- **Errors:** `FileExistsError` if file exists and `overwrite=false`.

---

### 2.36 `file_upload`

- **Description:** Upload a base64-encoded payload as a binary file.
- **RBAC:** `writer` and above. Blocked on read-only profiles.
- **Input schema:**
  ```json
  {
    "type": "object",
    "properties": {
      "workspace_id":   { "type": "string" },
      "path":           { "type": "string" },
      "base64_content": { "type": "string" },
      "overwrite":      { "type": "boolean", "default": true }
    },
    "required": ["workspace_id","path","base64_content"]
  }
  ```
- **Returns:** `{path, size_bytes}`

---

### 2.37 `file_download`

- **Description:** Download a file as a base64-encoded payload.
- **RBAC:** `reader` and above.
- **Input schema:**
  ```json
  {
    "type": "object",
    "properties": {
      "workspace_id": { "type": "string" },
      "path": { "type": "string" }
    },
    "required": ["workspace_id","path"]
  }
  ```
- **Returns:** `{base64_content, path}`

---

### 2.38 `file_move`

- **Description:** Move (rename) a file or directory within the workspace.
- **RBAC:** `writer` and above. Blocked on read-only profiles.
- **Input schema:**
  ```json
  {
    "type": "object",
    "properties": {
      "workspace_id": { "type": "string" },
      "src":      { "type": "string" },
      "dst":      { "type": "string" },
      "overwrite":{ "type": "boolean", "default": false }
    },
    "required": ["workspace_id","src","dst"]
  }
  ```
- **Returns:** `{path: <new-relative-path>}`

---

### 2.39 `file_copy`

- **Description:** Copy a file or directory within the workspace.
- **RBAC:** `writer` and above. Blocked on read-only profiles.
- **Input schema:**
  ```json
  {
    "type": "object",
    "properties": {
      "workspace_id": { "type": "string" },
      "src":      { "type": "string" },
      "dst":      { "type": "string" },
      "overwrite":{ "type": "boolean", "default": false }
    },
    "required": ["workspace_id","src","dst"]
  }
  ```
- **Returns:** `{path: <new-relative-path>}`

---

### 2.40 `file_delete`

- **Description:** Delete a file path from the workspace.
- **RBAC:** `writer` and above. Blocked on read-only profiles.
- **Input schema:**
  ```json
  {
    "type": "object",
    "properties": {
      "workspace_id": { "type": "string" },
      "path": { "type": "string" }
    },
    "required": ["workspace_id","path"]
  }
  ```
- **Returns:** `{deleted: <path>}`

---

### 2.41 `dir_list`

- **Description:** List directory entries in the workspace.
- **RBAC:** `reader` and above.
- **Input schema:**
  ```json
  {
    "type": "object",
    "properties": {
      "workspace_id":    { "type": "string" },
      "path":            { "type": "string", "default": "." },
      "recursive":       { "type": "boolean", "default": false },
      "include_hidden":  { "type": "boolean", "default": false }
    },
    "required": ["workspace_id"]
  }
  ```
- **Returns:** `{entries: [...]}`

---

### 2.42 `dir_mkdir`

- **Description:** Create a directory (with parents by default).
- **RBAC:** `writer` and above. Blocked on read-only profiles.
- **Input schema:**
  ```json
  {
    "type": "object",
    "properties": {
      "workspace_id": { "type": "string" },
      "path":    { "type": "string" },
      "parents": { "type": "boolean", "default": true }
    },
    "required": ["workspace_id","path"]
  }
  ```
- **Returns:** `{path: <relative-path>}`

---

### 2.43 `dir_rmdir`

- **Description:** Remove a directory from the workspace.
- **RBAC:** `writer` and above. Blocked on read-only profiles.
- **Input schema:**
  ```json
  {
    "type": "object",
    "properties": {
      "workspace_id": { "type": "string" },
      "path":      { "type": "string" },
      "recursive": { "type": "boolean", "default": false }
    },
    "required": ["workspace_id","path"]
  }
  ```
- **Returns:** `{removed: <path>}`

---

### 2.44 `search_content`

- **Description:** Search file content in the workspace (literal or regex, case-insensitive by default).
- **RBAC:** `reader` and above.
- **Input schema:**
  ```json
  {
    "type": "object",
    "properties": {
      "workspace_id":   { "type": "string" },
      "query":          { "type": "string" },
      "globs":          { "type": ["array","null"], "items": { "type": "string" } },
      "regex":          { "type": "boolean", "default": false },
      "case_sensitive": { "type": "boolean", "default": false },
      "max_results":    { "type": "integer", "default": 200 }
    },
    "required": ["workspace_id","query"]
  }
  ```
- **Returns:** `{results: [...]}`

---

### 2.45 `search_files`

- **Description:** Search file paths in the workspace by name query and optional glob filter.
- **RBAC:** `reader` and above.
- **Input schema:**
  ```json
  {
    "type": "object",
    "properties": {
      "workspace_id": { "type": "string" },
      "query": { "type": "string" },
      "globs": { "type": ["array","null"], "items": { "type": "string" } }
    },
    "required": ["workspace_id","query"]
  }
  ```
- **Returns:** `{results: [...]}`

---

### 2.46 `admin_profile_create`

- **Description:** Create or replace a repository profile configuration.
- **RBAC:** `admin` only.
- **Input schema:**
  ```json
  {
    "type": "object",
    "properties": {
      "name":    { "type": "string" },
      "profile": { "type": "object" }
    },
    "required": ["name","profile"]
  }
  ```
- **Returns:** `{name, created: true}` or AdminRuntime profile result.

---

### 2.47 `admin_user_create`

- **Description:** Create an IDAM user record.
- **RBAC:** `admin` only.
- **Input schema:**
  ```json
  {
    "type": "object",
    "properties": {
      "user_id":   { "type": "string" },
      "username":  { "type": "string" },
      "email":     { "type": "string", "default": "" },
      "group_ids": { "type": "array", "items": { "type": "string" }, "default": [] }
    },
    "required": ["user_id","username"]
  }
  ```
- **Returns:** `{user_id, created: true}` or full user record.

---

### 2.48 `admin_user_read`

- **Description:** Read an IDAM user record by user ID.
- **RBAC:** `admin` only.
- **Input schema:**
  ```json
  { "type": "object", "properties": { "user_id": { "type": "string" } }, "required": ["user_id"] }
  ```
- **Returns:** User record object.

---

### 2.49 `admin_user_list`

- **Description:** List all IDAM user records.
- **RBAC:** `admin` only.
- **Input schema:**
  ```json
  { "type": "object", "properties": {} }
  ```
- **Returns:** `{items: {...}}`

---

### 2.50 `admin_user_update`

- **Description:** Update an IDAM user record.
- **RBAC:** `admin` only.
- **Input schema:**
  ```json
  {
    "type": "object",
    "properties": {
      "user_id":   { "type": "string" },
      "username":  { "type": "string" },
      "email":     { "type": "string", "default": "" },
      "group_ids": { "type": "array", "items": { "type": "string" }, "default": [] },
      "status":    { "type": "string", "default": "active" }
    },
    "required": ["user_id","username"]
  }
  ```
- **Returns:** Updated user record object.

---

### 2.51 `admin_user_delete`

- **Description:** Delete an IDAM user record.
- **RBAC:** `admin` only.
- **Input schema:**
  ```json
  { "type": "object", "properties": { "user_id": { "type": "string" } }, "required": ["user_id"] }
  ```
- **Returns:** `{user_id, deleted: true}`

---

### 2.52 `admin_group_create`

- **Description:** Create an IDAM group record with roles and initial members.
- **RBAC:** `admin` only.
- **Input schema:**
  ```json
  {
    "type": "object",
    "properties": {
      "group_id":    { "type": "string" },
      "description": { "type": "string", "default": "" },
      "roles":       { "type": "array", "items": { "type": "string" }, "default": [] },
      "members":     { "type": "array", "items": { "type": "string" }, "default": [] }
    },
    "required": ["group_id"]
  }
  ```
- **Returns:** `{group_id, created: true}` or full group record.

---

### 2.53 `admin_group_read`

- **Description:** Read an IDAM group record by group ID.
- **RBAC:** `admin` only.
- **Input schema:**
  ```json
  { "type": "object", "properties": { "group_id": { "type": "string" } }, "required": ["group_id"] }
  ```
- **Returns:** Group record object.

---

### 2.54 `admin_group_list`

- **Description:** List all IDAM group records.
- **RBAC:** `admin` only.
- **Input schema:**
  ```json
  { "type": "object", "properties": {} }
  ```
- **Returns:** `{items: {...}}`

---

### 2.55 `admin_group_update`

- **Description:** Update an IDAM group record.
- **RBAC:** `admin` only.
- **Input schema:**
  ```json
  {
    "type": "object",
    "properties": {
      "group_id":    { "type": "string" },
      "description": { "type": "string", "default": "" },
      "roles":       { "type": "array", "items": { "type": "string" }, "default": [] },
      "members":     { "type": "array", "items": { "type": "string" }, "default": [] }
    },
    "required": ["group_id"]
  }
  ```
- **Returns:** Updated group record object.

---

### 2.56 `admin_group_delete`

- **Description:** Delete an IDAM group record.
- **RBAC:** `admin` only.
- **Input schema:**
  ```json
  { "type": "object", "properties": { "group_id": { "type": "string" } }, "required": ["group_id"] }
  ```
- **Returns:** `{group_id, deleted: true}`

---

### 2.57 `admin_rbac_bind`

- **Description:** Bind a role label to a user (direct role assignment).
- **RBAC:** `admin` only.
- **Input schema:**
  ```json
  {
    "type": "object",
    "properties": {
      "user_id": { "type": "string" },
      "role":    { "type": "string" }
    },
    "required": ["user_id","role"]
  }
  ```
- **Returns:** `{user_id, roles: [...]}`

---

### 2.58 `admin_rbac_unbind`

- **Description:** Remove a direct role binding from a user.
- **RBAC:** `admin` only.
- **Input schema:**
  ```json
  {
    "type": "object",
    "properties": {
      "user_id": { "type": "string" },
      "role":    { "type": "string" }
    },
    "required": ["user_id","role"]
  }
  ```
- **Returns:** `{user_id, roles: [...]}`

---

### 2.59 `admin_credentials_set`

- **Description:** Store a named credential reference (e.g. SSH key passphrase) in the credential store.
- **RBAC:** `admin` only.
- **Input schema:**
  ```json
  {
    "type": "object",
    "properties": {
      "name":   { "type": "string" },
      "secret": { "type": "string" }
    },
    "required": ["name","secret"]
  }
  ```
- **Returns:** `{name, stored: true}`

---

### 2.60 `admin_api_key_create`

- **Description:** Create a managed API key with capability scope metadata. Returns the one-time raw key.
- **RBAC:** `admin` only. Requires AdminRuntime.
- **Input schema:**
  ```json
  {
    "type": "object",
    "properties": {
      "name":           { "type": "string" },
      "owner_user_id":  { "type": "string" },
      "capabilities":   { "type": "array", "items": { "type": "string" }, "default": [] },
      "ttl_days":       { "type": ["integer","null"] }
    },
    "required": ["name","owner_user_id"]
  }
  ```
- **Returns:** `{key_id, raw_key, ...}` (raw_key shown once only).

---

### 2.61 `admin_api_key_list`

- **Description:** List managed API keys, optionally filtered by owner user ID.
- **RBAC:** `admin` only. Requires AdminRuntime.
- **Input schema:**
  ```json
  {
    "type": "object",
    "properties": {
      "owner_user_id": { "type": ["string","null"] }
    }
  }
  ```
- **Returns:** `{items: [...]}`

---

### 2.62 `admin_api_key_read`

- **Description:** Read metadata for a managed API key by key ID.
- **RBAC:** `admin` only. Requires AdminRuntime.
- **Input schema:**
  ```json
  { "type": "object", "properties": { "key_id": { "type": "string" } }, "required": ["key_id"] }
  ```
- **Returns:** Key metadata object (no raw key).

---

### 2.63 `admin_api_key_revoke`

- **Description:** Revoke a managed API key by key ID.
- **RBAC:** `admin` only. Requires AdminRuntime.
- **Input schema:**
  ```json
  { "type": "object", "properties": { "key_id": { "type": "string" } }, "required": ["key_id"] }
  ```
- **Returns:** Revocation result object.

---

## 3. Cross-references
- [API-REFERENCE.md](API-REFERENCE.md)
- [A2A-REFERENCE.md](A2A-REFERENCE.md)
- PS-72-mcp-a2a-webui.md

## 4. Project-specific notes

All tool calls are emitted to the structured audit log (PS-40 / PS-73 v2 audit chokepoint).
`content`, `secret`, `password`, `token`, and `body` parameters are redacted in audit records.
Mutation tools are gated by two checks: (1) the profile `read_only` policy flag and (2) the
workspace `ref_readonly` mode (set when a tag or commit ref is checked out). The workspace
disk pressure guard (W28C-1705) refuses `repo_open` at 95 % disk usage and warns at 80 %.
