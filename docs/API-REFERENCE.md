# API Reference — git-mcp-server

This document describes all public HTTP interfaces and MCP tools exposed by git-mcp-server.

## 1. REST API

| Method | Path | Description | Auth | Request Body | Success | Errors |
|---|---|---|---|---|---|---|
| GET | `/a2a/health` | A2A Health | Bearer token (A2A contract) | - | 200 | - |
| GET | `/api/v1/admin/profiles` | List Profiles | x-api-key or Bearer token | - | 200 | - |
| DELETE | `/api/v1/admin/profiles/{name}` | Delete Profile | x-api-key or Bearer token | - | 200 | 422 |
| GET | `/api/v1/admin/profiles/{name}` | Read Profile | x-api-key or Bearer token | - | 200 | 422 |
| POST | `/api/v1/admin/profiles/{name}` | Create Profile | x-api-key or Bearer token | JSON object | 200 | 422 |
| PUT | `/api/v1/admin/profiles/{name}` | Update Profile | x-api-key or Bearer token | JSON object | 200 | 422 |
| GET | `/api/v1/health` | Api Health Compatibility | None (health/version/public) | - | 200 | - |
| GET | `/api/v1/public/tools` | List Tools Public Compatibility | None (health/version/public) | - | 200 | - |
| GET | `/api/v1/tools` | List Tools Compatibility | x-api-key or Bearer token | - | 200 | - |
| POST | `/api/v1/tools/{tool_name}` | Call Tool Compatibility | x-api-key or Bearer token | JSON object | 200 | 422 |
| GET | `/api/v1/admin/profiles` | List Profiles | x-api-key or Bearer token | - | 200 | - |
| DELETE | `/api/v1/admin/profiles/{name}` | Delete Profile | x-api-key or Bearer token | - | 200 | 422 |
| GET | `/api/v1/admin/profiles/{name}` | Read Profile | x-api-key or Bearer token | - | 200 | 422 |
| POST | `/api/v1/admin/profiles/{name}` | Create Profile | x-api-key or Bearer token | JSON object | 200 | 422 |
| PUT | `/api/v1/admin/profiles/{name}` | Update Profile | x-api-key or Bearer token | JSON object | 200 | 422 |
| GET | `/api/v1/health` | Api Health Canonical | None (health/version/public) | - | 200 | - |
| GET | `/api/v1/public/tools` | List Tools Public Canonical | None (health/version/public) | - | 200 | - |
| GET | `/api/v1/tools` | List Tools Canonical | x-api-key or Bearer token | - | 200 | - |
| POST | `/api/v1/tools/{tool_name}` | Call Tool Canonical | x-api-key or Bearer token | JSON object | 200 | 422 |
| GET | `/api/v1/version` | Api Version | None (health/version/public) | - | 200 | - |
| GET | `/health` | Health | None (health/version/public) | - | 200 | - |
| GET | `/live` | Live | None (health/version/public) | - | 200 | - |
| GET | `/ready` | Ready | None (health/version/public) | - | 200 | - |
| GET | `/status` | Status No Auth | None (health/version/public) | - | 200 | - |

## 2. MCP Tools

Total tools: **51**

| Tool | Description |
|---|---|
| `admin_credentials_set` | Store named credential reference. |
| `admin_group_create` | Create admin group record. |
| `admin_profile_create` | Create or replace profile configuration. |
| `admin_rbac_bind` | Bind role to user. |
| `admin_rbac_unbind` | Unbind role from user. |
| `admin_user_create` | Create admin user record. |
| `dir_list` | List directory entries. |
| `dir_mkdir` | Create directory. |
| `dir_rmdir` | Remove directory. |
| `file_copy` | Copy file/directory path. |
| `file_delete` | Delete file path. |
| `file_download` | Download file as base64 payload. |
| `file_move` | Move file/directory path. |
| `file_read` | Read file content. |
| `file_upload` | Upload base64 payload as file. |
| `file_write` | Write file content. |
| `git_add` | Stage files. |
| `git_branch_create` | Create branch. |
| `git_branch_delete` | Delete branch. |
| `git_branch_from_ref` | Create branch from a specific ref. |
| `git_branch_list` | List branches. |
| `git_checkout` | Checkout branch/tag/commit. |
| `git_commit` | Create commit. |
| `git_conflict_resolve` | Resolve conflicts using ours/theirs/manual content. |
| `git_conflict_resolve_manual` | Resolve a single conflict with provided content. |
| `git_conflicts_list` | List unresolved conflicts. |
| `git_diff` | Read git diff between refs. |
| `git_fetch` | Fetch remote refs. |
| `git_log` | Read filtered git log. |
| `git_merge` | Merge branch/ref. |
| `git_merge_abort` | Abort merge. |
| `git_merge_continue` | Continue merge after conflict resolution. |
| `git_pull` | Pull from remote. |
| `git_push` | Push to remote. |
| `git_rebase` | Rebase branch. |
| `git_rebase_abort` | Abort rebase. |
| `git_rebase_continue` | Continue rebase after conflict resolution. |
| `git_reset` | Reset staged changes. |
| `git_stash_list` | List stashes. |
| `git_stash_pop` | Pop latest stash. |
| `git_stash_save` | Stash changes. |
| `git_status` | Read git status. |
| `git_tag_create` | Create tag. |
| `git_tag_delete` | Delete tag. |
| `git_tag_list` | List tags. |
| `git_tag_push` | Push tag(s). |
| `repo_close` | Close and optionally clean workspace. |
| `repo_open` | Create workspace and open repository context. |
| `repo_set_ref` | Switch workspace ref context. |
| `search_content` | Search file content. |
| `search_files` | Search file paths. |

### `admin_credentials_set`

Store named credential reference.

Parameters:

| Name | Type | Required | Default | Description |
|---|---|---|---|---|
| `name` | `string` | Yes | `-` | - |
| `secret` | `string` | Yes | `-` | - |

Return schema:

```json
{
  "type": "object"
}
```

Example request:

```http
POST /api/v1/tools/admin_credentials_set
Content-Type: application/json
x-api-key: <api-key>
```

```json
{
  "name": "feature/example",
  "secret": "example"
}
```

### `admin_group_create`

Create admin group record.

Parameters:

| Name | Type | Required | Default | Description |
|---|---|---|---|---|
| `description` | `string` | No | `` | - |
| `group_id` | `string` | Yes | `-` | - |

Return schema:

```json
{
  "type": "object"
}
```

Example request:

```http
POST /api/v1/tools/admin_group_create
Content-Type: application/json
x-api-key: <api-key>
```

```json
{
  "description": "",
  "group_id": "example"
}
```

### `admin_profile_create`

Create or replace profile configuration.

Parameters:

| Name | Type | Required | Default | Description |
|---|---|---|---|---|
| `name` | `string` | Yes | `-` | - |
| `profile` | `object` | Yes | `-` | - |

Return schema:

```json
{
  "type": "object"
}
```

Example request:

```http
POST /api/v1/tools/admin_profile_create
Content-Type: application/json
x-api-key: <api-key>
```

```json
{
  "name": "feature/example",
  "profile": "local_test"
}
```

### `admin_rbac_bind`

Bind role to user.

Parameters:

| Name | Type | Required | Default | Description |
|---|---|---|---|---|
| `role` | `string` | Yes | `-` | - |
| `user_id` | `string` | Yes | `-` | - |

Return schema:

```json
{
  "type": "object"
}
```

Example request:

```http
POST /api/v1/tools/admin_rbac_bind
Content-Type: application/json
x-api-key: <api-key>
```

```json
{
  "role": "example",
  "user_id": "example"
}
```

### `admin_rbac_unbind`

Unbind role from user.

Parameters:

| Name | Type | Required | Default | Description |
|---|---|---|---|---|
| `role` | `string` | Yes | `-` | - |
| `user_id` | `string` | Yes | `-` | - |

Return schema:

```json
{
  "type": "object"
}
```

Example request:

```http
POST /api/v1/tools/admin_rbac_unbind
Content-Type: application/json
x-api-key: <api-key>
```

```json
{
  "role": "example",
  "user_id": "example"
}
```

### `admin_user_create`

Create admin user record.

Parameters:

| Name | Type | Required | Default | Description |
|---|---|---|---|---|
| `email` | `string` | No | `` | - |
| `user_id` | `string` | Yes | `-` | - |
| `username` | `string` | Yes | `-` | - |

Return schema:

```json
{
  "type": "object"
}
```

Example request:

```http
POST /api/v1/tools/admin_user_create
Content-Type: application/json
x-api-key: <api-key>
```

```json
{
  "email": "",
  "user_id": "example",
  "username": "example"
}
```

### `dir_list`

List directory entries.

Parameters:

| Name | Type | Required | Default | Description |
|---|---|---|---|---|
| `include_hidden` | `boolean` | No | `False` | - |
| `path` | `string` | No | `.` | - |
| `recursive` | `boolean` | No | `False` | - |
| `workspace_id` | `string` | Yes | `-` | - |

Return schema:

```json
{
  "type": "object"
}
```

Example request:

```http
POST /api/v1/tools/dir_list
Content-Type: application/json
x-api-key: <api-key>
```

```json
{
  "include_hidden": false,
  "path": ".",
  "recursive": false,
  "workspace_id": "<workspace_id>"
}
```

### `dir_mkdir`

Create directory.

Parameters:

| Name | Type | Required | Default | Description |
|---|---|---|---|---|
| `parents` | `boolean` | No | `True` | - |
| `path` | `string` | Yes | `-` | - |
| `workspace_id` | `string` | Yes | `-` | - |

Return schema:

```json
{
  "type": "object"
}
```

Example request:

```http
POST /api/v1/tools/dir_mkdir
Content-Type: application/json
x-api-key: <api-key>
```

```json
{
  "parents": true,
  "path": "README.md",
  "workspace_id": "<workspace_id>"
}
```

### `dir_rmdir`

Remove directory.

Parameters:

| Name | Type | Required | Default | Description |
|---|---|---|---|---|
| `path` | `string` | Yes | `-` | - |
| `recursive` | `boolean` | No | `False` | - |
| `workspace_id` | `string` | Yes | `-` | - |

Return schema:

```json
{
  "type": "object"
}
```

Example request:

```http
POST /api/v1/tools/dir_rmdir
Content-Type: application/json
x-api-key: <api-key>
```

```json
{
  "path": "README.md",
  "recursive": false,
  "workspace_id": "<workspace_id>"
}
```

### `file_copy`

Copy file/directory path.

Parameters:

| Name | Type | Required | Default | Description |
|---|---|---|---|---|
| `dst` | `string` | Yes | `-` | - |
| `overwrite` | `boolean` | No | `False` | - |
| `src` | `string` | Yes | `-` | - |
| `workspace_id` | `string` | Yes | `-` | - |

Return schema:

```json
{
  "type": "object"
}
```

Example request:

```http
POST /api/v1/tools/file_copy
Content-Type: application/json
x-api-key: <api-key>
```

```json
{
  "dst": "docs/README.md",
  "overwrite": false,
  "src": "README.md",
  "workspace_id": "<workspace_id>"
}
```

### `file_delete`

Delete file path.

Parameters:

| Name | Type | Required | Default | Description |
|---|---|---|---|---|
| `path` | `string` | Yes | `-` | - |
| `workspace_id` | `string` | Yes | `-` | - |

Return schema:

```json
{
  "type": "object"
}
```

Example request:

```http
POST /api/v1/tools/file_delete
Content-Type: application/json
x-api-key: <api-key>
```

```json
{
  "path": "README.md",
  "workspace_id": "<workspace_id>"
}
```

### `file_download`

Download file as base64 payload.

Parameters:

| Name | Type | Required | Default | Description |
|---|---|---|---|---|
| `path` | `string` | Yes | `-` | - |
| `workspace_id` | `string` | Yes | `-` | - |

Return schema:

```json
{
  "type": "object"
}
```

Example request:

```http
POST /api/v1/tools/file_download
Content-Type: application/json
x-api-key: <api-key>
```

```json
{
  "path": "README.md",
  "workspace_id": "<workspace_id>"
}
```

### `file_move`

Move file/directory path.

Parameters:

| Name | Type | Required | Default | Description |
|---|---|---|---|---|
| `dst` | `string` | Yes | `-` | - |
| `overwrite` | `boolean` | No | `False` | - |
| `src` | `string` | Yes | `-` | - |
| `workspace_id` | `string` | Yes | `-` | - |

Return schema:

```json
{
  "type": "object"
}
```

Example request:

```http
POST /api/v1/tools/file_move
Content-Type: application/json
x-api-key: <api-key>
```

```json
{
  "dst": "docs/README.md",
  "overwrite": false,
  "src": "README.md",
  "workspace_id": "<workspace_id>"
}
```

### `file_read`

Read file content.

Parameters:

| Name | Type | Required | Default | Description |
|---|---|---|---|---|
| `path` | `string` | Yes | `-` | - |
| `workspace_id` | `string` | Yes | `-` | - |

Return schema:

```json
{
  "type": "object"
}
```

Example request:

```http
POST /api/v1/tools/file_read
Content-Type: application/json
x-api-key: <api-key>
```

```json
{
  "path": "README.md",
  "workspace_id": "<workspace_id>"
}
```

### `file_upload`

Upload base64 payload as file.

Parameters:

| Name | Type | Required | Default | Description |
|---|---|---|---|---|
| `base64_content` | `string` | Yes | `-` | - |
| `overwrite` | `boolean` | No | `True` | - |
| `path` | `string` | Yes | `-` | - |
| `workspace_id` | `string` | Yes | `-` | - |

Return schema:

```json
{
  "type": "object"
}
```

Example request:

```http
POST /api/v1/tools/file_upload
Content-Type: application/json
x-api-key: <api-key>
```

```json
{
  "base64_content": "example",
  "overwrite": true,
  "path": "README.md",
  "workspace_id": "<workspace_id>"
}
```

### `file_write`

Write file content.

Parameters:

| Name | Type | Required | Default | Description |
|---|---|---|---|---|
| `content` | `string` | Yes | `-` | - |
| `overwrite` | `boolean` | No | `True` | - |
| `path` | `string` | Yes | `-` | - |
| `workspace_id` | `string` | Yes | `-` | - |

Return schema:

```json
{
  "type": "object"
}
```

Example request:

```http
POST /api/v1/tools/file_write
Content-Type: application/json
x-api-key: <api-key>
```

```json
{
  "content": "example",
  "overwrite": true,
  "path": "README.md",
  "workspace_id": "<workspace_id>"
}
```

### `git_add`

Stage files.

Parameters:

| Name | Type | Required | Default | Description |
|---|---|---|---|---|
| `paths` | `array` | Yes | `-` | - |
| `workspace_id` | `string` | Yes | `-` | - |

Return schema:

```json
{
  "type": "object"
}
```

Example request:

```http
POST /api/v1/tools/git_add
Content-Type: application/json
x-api-key: <api-key>
```

```json
{
  "paths": [],
  "workspace_id": "<workspace_id>"
}
```

### `git_branch_create`

Create branch.

Parameters:

| Name | Type | Required | Default | Description |
|---|---|---|---|---|
| `from_ref` | `string` | No | `HEAD` | - |
| `name` | `string` | Yes | `-` | - |
| `workspace_id` | `string` | Yes | `-` | - |

Return schema:

```json
{
  "type": "object"
}
```

Example request:

```http
POST /api/v1/tools/git_branch_create
Content-Type: application/json
x-api-key: <api-key>
```

```json
{
  "from_ref": "HEAD",
  "name": "feature/example",
  "workspace_id": "<workspace_id>"
}
```

### `git_branch_delete`

Delete branch.

Parameters:

| Name | Type | Required | Default | Description |
|---|---|---|---|---|
| `force` | `boolean` | No | `False` | - |
| `name` | `string` | Yes | `-` | - |
| `workspace_id` | `string` | Yes | `-` | - |

Return schema:

```json
{
  "type": "object"
}
```

Example request:

```http
POST /api/v1/tools/git_branch_delete
Content-Type: application/json
x-api-key: <api-key>
```

```json
{
  "force": false,
  "name": "feature/example",
  "workspace_id": "<workspace_id>"
}
```

### `git_branch_from_ref`

Create branch from a specific ref.

Parameters:

| Name | Type | Required | Default | Description |
|---|---|---|---|---|
| `from_ref` | `string` | Yes | `-` | - |
| `new_branch` | `string` | Yes | `-` | - |
| `workspace_id` | `string` | Yes | `-` | - |

Return schema:

```json
{
  "type": "object"
}
```

Example request:

```http
POST /api/v1/tools/git_branch_from_ref
Content-Type: application/json
x-api-key: <api-key>
```

```json
{
  "from_ref": "main",
  "new_branch": "feature/example",
  "workspace_id": "<workspace_id>"
}
```

### `git_branch_list`

List branches.

Parameters:

| Name | Type | Required | Default | Description |
|---|---|---|---|---|
| `workspace_id` | `string` | Yes | `-` | - |

Return schema:

```json
{
  "type": "object"
}
```

Example request:

```http
POST /api/v1/tools/git_branch_list
Content-Type: application/json
x-api-key: <api-key>
```

```json
{
  "workspace_id": "<workspace_id>"
}
```

### `git_checkout`

Checkout branch/tag/commit.

Parameters:

| Name | Type | Required | Default | Description |
|---|---|---|---|---|
| `ref` | `string` | Yes | `-` | - |
| `workspace_id` | `string` | Yes | `-` | - |

Return schema:

```json
{
  "type": "object"
}
```

Example request:

```http
POST /api/v1/tools/git_checkout
Content-Type: application/json
x-api-key: <api-key>
```

```json
{
  "ref": {
    "name": "main",
    "type": "branch"
  },
  "workspace_id": "<workspace_id>"
}
```

### `git_commit`

Create commit.

Parameters:

| Name | Type | Required | Default | Description |
|---|---|---|---|---|
| `message` | `string` | Yes | `-` | - |
| `workspace_id` | `string` | Yes | `-` | - |

Return schema:

```json
{
  "type": "object"
}
```

Example request:

```http
POST /api/v1/tools/git_commit
Content-Type: application/json
x-api-key: <api-key>
```

```json
{
  "message": "example update",
  "workspace_id": "<workspace_id>"
}
```

### `git_conflict_resolve`

Resolve conflicts using ours/theirs/manual content.

Parameters:

| Name | Type | Required | Default | Description |
|---|---|---|---|---|
| `manual_content` | `string | null` | No | `None` | - |
| `mode` | `string` | Yes | `-` | - |
| `paths` | `array` | Yes | `-` | - |
| `workspace_id` | `string` | Yes | `-` | - |

Return schema:

```json
{
  "type": "object"
}
```

Example request:

```http
POST /api/v1/tools/git_conflict_resolve
Content-Type: application/json
x-api-key: <api-key>
```

```json
{
  "manual_content": null,
  "mode": "ours",
  "paths": [],
  "workspace_id": "<workspace_id>"
}
```

### `git_conflict_resolve_manual`

Resolve a single conflict with provided content.

Parameters:

| Name | Type | Required | Default | Description |
|---|---|---|---|---|
| `content` | `string` | Yes | `-` | - |
| `path` | `string` | Yes | `-` | - |
| `workspace_id` | `string` | Yes | `-` | - |

Return schema:

```json
{
  "type": "object"
}
```

Example request:

```http
POST /api/v1/tools/git_conflict_resolve_manual
Content-Type: application/json
x-api-key: <api-key>
```

```json
{
  "content": "example",
  "path": "README.md",
  "workspace_id": "<workspace_id>"
}
```

### `git_conflicts_list`

List unresolved conflicts.

Parameters:

| Name | Type | Required | Default | Description |
|---|---|---|---|---|
| `workspace_id` | `string` | Yes | `-` | - |

Return schema:

```json
{
  "type": "object"
}
```

Example request:

```http
POST /api/v1/tools/git_conflicts_list
Content-Type: application/json
x-api-key: <api-key>
```

```json
{
  "workspace_id": "<workspace_id>"
}
```

### `git_diff`

Read git diff between refs.

Parameters:

| Name | Type | Required | Default | Description |
|---|---|---|---|---|
| `left` | `string` | No | `HEAD~1` | - |
| `right` | `string` | No | `HEAD` | - |
| `workspace_id` | `string` | Yes | `-` | - |

Return schema:

```json
{
  "type": "object"
}
```

Example request:

```http
POST /api/v1/tools/git_diff
Content-Type: application/json
x-api-key: <api-key>
```

```json
{
  "left": "HEAD~1",
  "right": "HEAD",
  "workspace_id": "<workspace_id>"
}
```

### `git_fetch`

Fetch remote refs.

Parameters:

| Name | Type | Required | Default | Description |
|---|---|---|---|---|
| `remote` | `string` | No | `origin` | - |
| `workspace_id` | `string` | Yes | `-` | - |

Return schema:

```json
{
  "type": "object"
}
```

Example request:

```http
POST /api/v1/tools/git_fetch
Content-Type: application/json
x-api-key: <api-key>
```

```json
{
  "remote": "origin",
  "workspace_id": "<workspace_id>"
}
```

### `git_log`

Read filtered git log.

Parameters:

| Name | Type | Required | Default | Description |
|---|---|---|---|---|
| `author` | `string | null` | No | `None` | - |
| `max_count` | `integer | null` | No | `None` | - |
| `path` | `string | null` | No | `None` | - |
| `since` | `string | null` | No | `None` | - |
| `until` | `string | null` | No | `None` | - |
| `workspace_id` | `string` | Yes | `-` | - |

Return schema:

```json
{
  "type": "object"
}
```

Example request:

```http
POST /api/v1/tools/git_log
Content-Type: application/json
x-api-key: <api-key>
```

```json
{
  "author": null,
  "max_count": null,
  "path": null,
  "since": null,
  "until": null,
  "workspace_id": "<workspace_id>"
}
```

### `git_merge`

Merge branch/ref.

Parameters:

| Name | Type | Required | Default | Description |
|---|---|---|---|---|
| `ff_only` | `boolean` | No | `False` | - |
| `ref` | `string` | Yes | `-` | - |
| `workspace_id` | `string` | Yes | `-` | - |

Return schema:

```json
{
  "type": "object"
}
```

Example request:

```http
POST /api/v1/tools/git_merge
Content-Type: application/json
x-api-key: <api-key>
```

```json
{
  "ff_only": false,
  "ref": {
    "name": "main",
    "type": "branch"
  },
  "workspace_id": "<workspace_id>"
}
```

### `git_merge_abort`

Abort merge.

Parameters:

| Name | Type | Required | Default | Description |
|---|---|---|---|---|
| `workspace_id` | `string` | Yes | `-` | - |

Return schema:

```json
{
  "type": "object"
}
```

Example request:

```http
POST /api/v1/tools/git_merge_abort
Content-Type: application/json
x-api-key: <api-key>
```

```json
{
  "workspace_id": "<workspace_id>"
}
```

### `git_merge_continue`

Continue merge after conflict resolution.

Parameters:

| Name | Type | Required | Default | Description |
|---|---|---|---|---|
| `workspace_id` | `string` | Yes | `-` | - |

Return schema:

```json
{
  "type": "object"
}
```

Example request:

```http
POST /api/v1/tools/git_merge_continue
Content-Type: application/json
x-api-key: <api-key>
```

```json
{
  "workspace_id": "<workspace_id>"
}
```

### `git_pull`

Pull from remote.

Parameters:

| Name | Type | Required | Default | Description |
|---|---|---|---|---|
| `branch` | `string | null` | No | `None` | - |
| `remote` | `string` | No | `origin` | - |
| `workspace_id` | `string` | Yes | `-` | - |

Return schema:

```json
{
  "type": "object"
}
```

Example request:

```http
POST /api/v1/tools/git_pull
Content-Type: application/json
x-api-key: <api-key>
```

```json
{
  "branch": null,
  "remote": "origin",
  "workspace_id": "<workspace_id>"
}
```

### `git_push`

Push to remote.

Parameters:

| Name | Type | Required | Default | Description |
|---|---|---|---|---|
| `branch` | `string | null` | No | `None` | - |
| `force_with_lease` | `boolean` | No | `False` | - |
| `remote` | `string` | No | `origin` | - |
| `workspace_id` | `string` | Yes | `-` | - |

Return schema:

```json
{
  "type": "object"
}
```

Example request:

```http
POST /api/v1/tools/git_push
Content-Type: application/json
x-api-key: <api-key>
```

```json
{
  "branch": null,
  "force_with_lease": false,
  "remote": "origin",
  "workspace_id": "<workspace_id>"
}
```

### `git_rebase`

Rebase branch.

Parameters:

| Name | Type | Required | Default | Description |
|---|---|---|---|---|
| `onto` | `string` | Yes | `-` | - |
| `workspace_id` | `string` | Yes | `-` | - |

Return schema:

```json
{
  "type": "object"
}
```

Example request:

```http
POST /api/v1/tools/git_rebase
Content-Type: application/json
x-api-key: <api-key>
```

```json
{
  "onto": "example",
  "workspace_id": "<workspace_id>"
}
```

### `git_rebase_abort`

Abort rebase.

Parameters:

| Name | Type | Required | Default | Description |
|---|---|---|---|---|
| `workspace_id` | `string` | Yes | `-` | - |

Return schema:

```json
{
  "type": "object"
}
```

Example request:

```http
POST /api/v1/tools/git_rebase_abort
Content-Type: application/json
x-api-key: <api-key>
```

```json
{
  "workspace_id": "<workspace_id>"
}
```

### `git_rebase_continue`

Continue rebase after conflict resolution.

Parameters:

| Name | Type | Required | Default | Description |
|---|---|---|---|---|
| `workspace_id` | `string` | Yes | `-` | - |

Return schema:

```json
{
  "type": "object"
}
```

Example request:

```http
POST /api/v1/tools/git_rebase_continue
Content-Type: application/json
x-api-key: <api-key>
```

```json
{
  "workspace_id": "<workspace_id>"
}
```

### `git_reset`

Reset staged changes.

Parameters:

| Name | Type | Required | Default | Description |
|---|---|---|---|---|
| `hard` | `boolean` | No | `False` | - |
| `paths` | `array` | No | `-` | - |
| `workspace_id` | `string` | Yes | `-` | - |

Return schema:

```json
{
  "type": "object"
}
```

Example request:

```http
POST /api/v1/tools/git_reset
Content-Type: application/json
x-api-key: <api-key>
```

```json
{
  "hard": false,
  "workspace_id": "<workspace_id>"
}
```

### `git_stash_list`

List stashes.

Parameters:

| Name | Type | Required | Default | Description |
|---|---|---|---|---|
| `workspace_id` | `string` | Yes | `-` | - |

Return schema:

```json
{
  "type": "object"
}
```

Example request:

```http
POST /api/v1/tools/git_stash_list
Content-Type: application/json
x-api-key: <api-key>
```

```json
{
  "workspace_id": "<workspace_id>"
}
```

### `git_stash_pop`

Pop latest stash.

Parameters:

| Name | Type | Required | Default | Description |
|---|---|---|---|---|
| `workspace_id` | `string` | Yes | `-` | - |

Return schema:

```json
{
  "type": "object"
}
```

Example request:

```http
POST /api/v1/tools/git_stash_pop
Content-Type: application/json
x-api-key: <api-key>
```

```json
{
  "workspace_id": "<workspace_id>"
}
```

### `git_stash_save`

Stash changes.

Parameters:

| Name | Type | Required | Default | Description |
|---|---|---|---|---|
| `message` | `string` | Yes | `-` | - |
| `workspace_id` | `string` | Yes | `-` | - |

Return schema:

```json
{
  "type": "object"
}
```

Example request:

```http
POST /api/v1/tools/git_stash_save
Content-Type: application/json
x-api-key: <api-key>
```

```json
{
  "message": "example update",
  "workspace_id": "<workspace_id>"
}
```

### `git_status`

Read git status.

Parameters:

| Name | Type | Required | Default | Description |
|---|---|---|---|---|
| `workspace_id` | `string` | Yes | `-` | - |

Return schema:

```json
{
  "type": "object"
}
```

Example request:

```http
POST /api/v1/tools/git_status
Content-Type: application/json
x-api-key: <api-key>
```

```json
{
  "workspace_id": "<workspace_id>"
}
```

### `git_tag_create`

Create tag.

Parameters:

| Name | Type | Required | Default | Description |
|---|---|---|---|---|
| `annotated` | `boolean` | No | `False` | - |
| `commit` | `string | null` | No | `None` | - |
| `message` | `string | null` | No | `None` | - |
| `tag` | `string` | Yes | `-` | - |
| `workspace_id` | `string` | Yes | `-` | - |

Return schema:

```json
{
  "type": "object"
}
```

Example request:

```http
POST /api/v1/tools/git_tag_create
Content-Type: application/json
x-api-key: <api-key>
```

```json
{
  "annotated": false,
  "commit": null,
  "message": null,
  "tag": "v1.0.0",
  "workspace_id": "<workspace_id>"
}
```

### `git_tag_delete`

Delete tag.

Parameters:

| Name | Type | Required | Default | Description |
|---|---|---|---|---|
| `tag` | `string` | Yes | `-` | - |
| `workspace_id` | `string` | Yes | `-` | - |

Return schema:

```json
{
  "type": "object"
}
```

Example request:

```http
POST /api/v1/tools/git_tag_delete
Content-Type: application/json
x-api-key: <api-key>
```

```json
{
  "tag": "v1.0.0",
  "workspace_id": "<workspace_id>"
}
```

### `git_tag_list`

List tags.

Parameters:

| Name | Type | Required | Default | Description |
|---|---|---|---|---|
| `contains` | `string | null` | No | `None` | - |
| `pattern` | `string | null` | No | `None` | - |
| `workspace_id` | `string` | Yes | `-` | - |

Return schema:

```json
{
  "type": "object"
}
```

Example request:

```http
POST /api/v1/tools/git_tag_list
Content-Type: application/json
x-api-key: <api-key>
```

```json
{
  "contains": null,
  "pattern": null,
  "workspace_id": "<workspace_id>"
}
```

### `git_tag_push`

Push tag(s).

Parameters:

| Name | Type | Required | Default | Description |
|---|---|---|---|---|
| `all_tags` | `boolean` | No | `False` | - |
| `remote` | `string` | No | `origin` | - |
| `tag` | `string | null` | No | `None` | - |
| `workspace_id` | `string` | Yes | `-` | - |

Return schema:

```json
{
  "type": "object"
}
```

Example request:

```http
POST /api/v1/tools/git_tag_push
Content-Type: application/json
x-api-key: <api-key>
```

```json
{
  "all_tags": false,
  "remote": "origin",
  "tag": null,
  "workspace_id": "<workspace_id>"
}
```

### `repo_close`

Close and optionally clean workspace.

Parameters:

| Name | Type | Required | Default | Description |
|---|---|---|---|---|
| `workspace_id` | `string` | Yes | `-` | - |

Return schema:

```json
{
  "type": "object"
}
```

Example request:

```http
POST /api/v1/tools/repo_close
Content-Type: application/json
x-api-key: <api-key>
```

```json
{
  "workspace_id": "<workspace_id>"
}
```

### `repo_open`

Create workspace and open repository context.

Parameters:

| Name | Type | Required | Default | Description |
|---|---|---|---|---|
| `profile` | `string` | Yes | `-` | - |
| `ref` | `object | null` | No | `None` | - |
| `repo_source` | `string | null` | No | `None` | - |
| `session_id` | `string` | Yes | `-` | - |
| `workspace_mode` | `string` | No | `ephemeral` | - |

Return schema:

```json
{
  "type": "object"
}
```

Example request:

```http
POST /api/v1/tools/repo_open
Content-Type: application/json
x-api-key: <api-key>
```

```json
{
  "profile": "local_test",
  "ref": null,
  "repo_source": null,
  "session_id": "session-001",
  "workspace_mode": "ephemeral"
}
```

### `repo_set_ref`

Switch workspace ref context.

Parameters:

| Name | Type | Required | Default | Description |
|---|---|---|---|---|
| `ref` | `RefSpec` | Yes | `-` | - |
| `workspace_id` | `string` | Yes | `-` | - |

Return schema:

```json
{
  "type": "object"
}
```

Example request:

```http
POST /api/v1/tools/repo_set_ref
Content-Type: application/json
x-api-key: <api-key>
```

```json
{
  "ref": {
    "name": "main",
    "type": "branch"
  },
  "workspace_id": "<workspace_id>"
}
```

### `search_content`

Search file content.

Parameters:

| Name | Type | Required | Default | Description |
|---|---|---|---|---|
| `case_sensitive` | `boolean` | No | `False` | - |
| `globs` | `array | null` | No | `None` | - |
| `max_results` | `integer` | No | `200` | - |
| `query` | `string` | Yes | `-` | - |
| `regex` | `boolean` | No | `False` | - |
| `workspace_id` | `string` | Yes | `-` | - |

Return schema:

```json
{
  "type": "object"
}
```

Example request:

```http
POST /api/v1/tools/search_content
Content-Type: application/json
x-api-key: <api-key>
```

```json
{
  "case_sensitive": false,
  "globs": null,
  "max_results": 200,
  "query": "example",
  "regex": false,
  "workspace_id": "<workspace_id>"
}
```

### `search_files`

Search file paths.

Parameters:

| Name | Type | Required | Default | Description |
|---|---|---|---|---|
| `globs` | `array | null` | No | `None` | - |
| `query` | `string` | Yes | `-` | - |
| `workspace_id` | `string` | Yes | `-` | - |

Return schema:

```json
{
  "type": "object"
}
```

Example request:

```http
POST /api/v1/tools/search_files
Content-Type: application/json
x-api-key: <api-key>
```

```json
{
  "globs": null,
  "query": "example",
  "workspace_id": "<workspace_id>"
}
```

## 3. A2A Endpoints

| Method | Path | Description | Auth | Success | Error |
|---|---|---|---|---|---|
| GET | `/a2a/health` | A2A health contract endpoint | `Authorisation: Bearer <token>` | 200 | 401 |

## 4. OpenAPI

- Runtime endpoint: `/openapi.json`
- Static snapshot in repository: `docs/openapi.json`
