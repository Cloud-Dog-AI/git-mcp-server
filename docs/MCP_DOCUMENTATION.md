# MCP Server Documentation

## Transport
Primary transport: Streamable HTTP at `/mcp` unless the service documents an alternative mode in its runtime configuration.

## Authentication
Use `Authorisation: Bearer <your-api-key>` or `X-API-Key: <your-api-key>` for REST, MCP, and A2A access.

## Verification Basis
- Source files reviewed: `src/git_mcp_server/a2a_server.py`, `src/git_mcp_server/api_server.py`, `src/git_mcp_server/mcp_server.py`, `src/git_mcp_server/web_server.py`
- Tool inventory size: 63

## Tools
| Tool | Notes |
|------|-------|
| `repo_open` | Source-verified MCP tool name. Input and output schemas are enforced in the server runtime. |
| `repo_close` | Source-verified MCP tool name. Input and output schemas are enforced in the server runtime. |
| `repo_set_ref` | Source-verified MCP tool name. Input and output schemas are enforced in the server runtime. |
| `git_status` | Source-verified MCP tool name. Input and output schemas are enforced in the server runtime. |
| `git_log` | Source-verified MCP tool name. Input and output schemas are enforced in the server runtime. |
| `git_diff` | Source-verified MCP tool name. Input and output schemas are enforced in the server runtime. |
| `git_add` | Source-verified MCP tool name. Input and output schemas are enforced in the server runtime. |
| `git_reset` | Source-verified MCP tool name. Input and output schemas are enforced in the server runtime. |
| `git_commit` | Source-verified MCP tool name. Input and output schemas are enforced in the server runtime. |
| `git_fetch` | Source-verified MCP tool name. Input and output schemas are enforced in the server runtime. |
| `git_pull` | Source-verified MCP tool name. Input and output schemas are enforced in the server runtime. |
| `git_push` | Source-verified MCP tool name. Input and output schemas are enforced in the server runtime. |
| `git_checkout` | Source-verified MCP tool name. Input and output schemas are enforced in the server runtime. |
| `git_branch_list` | Source-verified MCP tool name. Input and output schemas are enforced in the server runtime. |
| `git_branch_create` | Source-verified MCP tool name. Input and output schemas are enforced in the server runtime. |
| `git_branch_delete` | Source-verified MCP tool name. Input and output schemas are enforced in the server runtime. |
| `git_branch_from_ref` | Source-verified MCP tool name. Input and output schemas are enforced in the server runtime. |
| `git_merge` | Source-verified MCP tool name. Input and output schemas are enforced in the server runtime. |
| `git_merge_abort` | Source-verified MCP tool name. Input and output schemas are enforced in the server runtime. |
| `git_merge_continue` | Source-verified MCP tool name. Input and output schemas are enforced in the server runtime. |
| `git_rebase` | Source-verified MCP tool name. Input and output schemas are enforced in the server runtime. |
| `git_rebase_abort` | Source-verified MCP tool name. Input and output schemas are enforced in the server runtime. |
| `git_rebase_continue` | Source-verified MCP tool name. Input and output schemas are enforced in the server runtime. |
| `git_stash_save` | Source-verified MCP tool name. Input and output schemas are enforced in the server runtime. |
| `git_stash_list` | Source-verified MCP tool name. Input and output schemas are enforced in the server runtime. |
| `git_stash_pop` | Source-verified MCP tool name. Input and output schemas are enforced in the server runtime. |
| `git_tag_create` | Source-verified MCP tool name. Input and output schemas are enforced in the server runtime. |
| `git_tag_delete` | Source-verified MCP tool name. Input and output schemas are enforced in the server runtime. |
| `git_tag_list` | Source-verified MCP tool name. Input and output schemas are enforced in the server runtime. |
| `git_tag_push` | Source-verified MCP tool name. Input and output schemas are enforced in the server runtime. |
| `git_conflicts_list` | Source-verified MCP tool name. Input and output schemas are enforced in the server runtime. |
| `git_conflict_resolve` | Source-verified MCP tool name. Input and output schemas are enforced in the server runtime. |
| `git_conflict_resolve_manual` | Source-verified MCP tool name. Input and output schemas are enforced in the server runtime. |
| `file_read` | Source-verified MCP tool name. Input and output schemas are enforced in the server runtime. |
| `file_write` | Source-verified MCP tool name. Input and output schemas are enforced in the server runtime. |
| `file_upload` | Source-verified MCP tool name. Input and output schemas are enforced in the server runtime. |
| `file_download` | Source-verified MCP tool name. Input and output schemas are enforced in the server runtime. |
| `file_move` | Source-verified MCP tool name. Input and output schemas are enforced in the server runtime. |
| `file_copy` | Source-verified MCP tool name. Input and output schemas are enforced in the server runtime. |
| `file_delete` | Source-verified MCP tool name. Input and output schemas are enforced in the server runtime. |
| `dir_list` | Source-verified MCP tool name. Input and output schemas are enforced in the server runtime. |
| `dir_mkdir` | Source-verified MCP tool name. Input and output schemas are enforced in the server runtime. |
| `dir_rmdir` | Source-verified MCP tool name. Input and output schemas are enforced in the server runtime. |
| `search_content` | Source-verified MCP tool name. Input and output schemas are enforced in the server runtime. |
| `search_files` | Source-verified MCP tool name. Input and output schemas are enforced in the server runtime. |
| `admin_profile_create` | Source-verified MCP tool name. Input and output schemas are enforced in the server runtime. |
| `admin_user_create` | Source-verified MCP tool name. Input and output schemas are enforced in the server runtime. |
| `admin_user_read` | Source-verified MCP tool name. Input and output schemas are enforced in the server runtime. |
| `admin_user_list` | Source-verified MCP tool name. Input and output schemas are enforced in the server runtime. |
| `admin_user_update` | Source-verified MCP tool name. Input and output schemas are enforced in the server runtime. |
| `admin_user_delete` | Source-verified MCP tool name. Input and output schemas are enforced in the server runtime. |
| `admin_group_create` | Source-verified MCP tool name. Input and output schemas are enforced in the server runtime. |
| `admin_group_read` | Source-verified MCP tool name. Input and output schemas are enforced in the server runtime. |
| `admin_group_list` | Source-verified MCP tool name. Input and output schemas are enforced in the server runtime. |
| `admin_group_update` | Source-verified MCP tool name. Input and output schemas are enforced in the server runtime. |
| `admin_group_delete` | Source-verified MCP tool name. Input and output schemas are enforced in the server runtime. |
| `admin_rbac_bind` | Source-verified MCP tool name. Input and output schemas are enforced in the server runtime. |
| `admin_rbac_unbind` | Source-verified MCP tool name. Input and output schemas are enforced in the server runtime. |
| `admin_credentials_set` | Source-verified MCP tool name. Input and output schemas are enforced in the server runtime. |
| `admin_api_key_create` | Source-verified MCP tool name. Input and output schemas are enforced in the server runtime. |
| `admin_api_key_list` | Source-verified MCP tool name. Input and output schemas are enforced in the server runtime. |
| `admin_api_key_read` | Source-verified MCP tool name. Input and output schemas are enforced in the server runtime. |
| `admin_api_key_revoke` | Source-verified MCP tool name. Input and output schemas are enforced in the server runtime. |

## Example Call
```json
{
  "jsonrpc": "2.0",
  "id": "1",
  "method": "tools/list",
  "params": {}
}
```

## Example Response
```json
{
  "jsonrpc": "2.0",
  "id": "1",
  "result": {
    "tools": [
      {
        "name": "tool_name",
        "description": "What the tool does",
        "inputSchema": {"type": "object"}
      }
    ]
  }
}
```
