# API Documentation

## Base URLs
- Local development: `http://localhost:8083`
- Deployed: `https://git-mcp.your-domain.com`

## Authentication
Use `Authorisation: Bearer <your-api-key>` or `X-API-Key: <your-api-key>` for REST, MCP, and A2A access.

## Verification Basis
- Source files reviewed: `src/git_mcp_server/a2a_server.py`, `src/git_mcp_server/api_server.py`, `src/git_mcp_server/mcp_server.py`, `src/git_mcp_server/web_server.py`
- Route inventory size: 37

## Route Inventory
| Method | Path | Notes |
|--------|------|-------|
| GET | `<dynamic>` | Handler `mcp_root` in `src/git_mcp_server/mcp_server.py`. |
| POST | `<dynamic>` | Handler `mcp_jsonrpc` in `src/git_mcp_server/mcp_server.py`. |
| GET | `` | Handler `list_tools` in `src/git_mcp_server/mcp_server.py`. |
| POST | `/{tool_name}` | Handler `call_tool` in `src/git_mcp_server/mcp_server.py`. |
| GET | `<dynamic>` | Handler `a2a_root` in `src/git_mcp_server/a2a_server.py`. |
| GET | `/runtime-config.js` | Handler `runtime_config` in `src/git_mcp_server/web_ui.py`. |
| GET | `/` | Handler `spa_root` in `src/git_mcp_server/web_ui.py`. |
| GET | `/{path:path}` | Handler `spa_fallback` in `src/git_mcp_server/web_ui.py`. |
| POST | `/auth/login` | Handler `auth_login` in `src/git_mcp_server/web_server.py`. |
| GET | `/auth/me` | Handler `auth_me` in `src/git_mcp_server/web_server.py`. |
| POST | `/auth/logout` | Handler `auth_logout` in `src/git_mcp_server/web_server.py`. |
| GET | `/queue/status` | Handler `queue_status` in `src/git_mcp_server/jobs/endpoints.py`. |
| GET | `` | Handler `list_jobs` in `src/git_mcp_server/jobs/endpoints.py`. |
| GET | `/{job_id}` | Handler `job_status` in `src/git_mcp_server/jobs/endpoints.py`. |
| POST | `/repo-open` | Handler `submit_repo_open` in `src/git_mcp_server/jobs/endpoints.py`. |
| POST | `/git-diff` | Handler `submit_git_diff` in `src/git_mcp_server/jobs/endpoints.py`. |
| POST | `/file-batch` | Handler `submit_file_batch` in `src/git_mcp_server/jobs/endpoints.py`. |
| GET | `/profiles` | Handler `list_profiles` in `src/git_mcp_server/admin/endpoints.py`. |
| GET | `/profiles/{name}` | Handler `read_profile` in `src/git_mcp_server/admin/endpoints.py`. |
| POST | `/profiles/{name}` | Handler `create_profile` in `src/git_mcp_server/admin/endpoints.py`. |
| PUT | `/profiles/{name}` | Handler `update_profile` in `src/git_mcp_server/admin/endpoints.py`. |
| DELETE | `/profiles/{name}` | Handler `delete_profile` in `src/git_mcp_server/admin/endpoints.py`. |
| GET | `/users` | Handler `list_users` in `src/git_mcp_server/admin/endpoints.py`. |
| GET | `/users/{user_id}` | Handler `read_user` in `src/git_mcp_server/admin/endpoints.py`. |
| POST | `/users/{user_id}` | Handler `create_user` in `src/git_mcp_server/admin/endpoints.py`. |
| PUT | `/users/{user_id}` | Handler `update_user` in `src/git_mcp_server/admin/endpoints.py`. |
| DELETE | `/users/{user_id}` | Handler `delete_user` in `src/git_mcp_server/admin/endpoints.py`. |
| GET | `/groups` | Handler `list_groups` in `src/git_mcp_server/admin/endpoints.py`. |
| GET | `/groups/{group_id}` | Handler `read_group` in `src/git_mcp_server/admin/endpoints.py`. |
| POST | `/groups/{group_id}` | Handler `create_group` in `src/git_mcp_server/admin/endpoints.py`. |
| PUT | `/groups/{group_id}` | Handler `update_group` in `src/git_mcp_server/admin/endpoints.py`. |
| DELETE | `/groups/{group_id}` | Handler `delete_group` in `src/git_mcp_server/admin/endpoints.py`. |
| GET | `/api-keys` | Handler `list_api_keys` in `src/git_mcp_server/admin/endpoints.py`. |
| GET | `/api-keys/{key_id}` | Handler `read_api_key` in `src/git_mcp_server/admin/endpoints.py`. |
| POST | `/api-keys` | Handler `create_api_key` in `src/git_mcp_server/admin/endpoints.py`. |
| PUT | `/api-keys/{key_id}` | Handler `update_api_key` in `src/git_mcp_server/admin/endpoints.py`. |
| DELETE | `/api-keys/{key_id}` | Handler `revoke_api_key` in `src/git_mcp_server/admin/endpoints.py`. |

## Example Request
```bash
curl -H "Authorisation: Bearer your-api-key" http://localhost:8083/health
```

## Example Response
```json
{
  "ok": true,
  "result": {
    "status": "healthy"
  }
}
```
