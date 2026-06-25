---
template-id: T-ENV
template-version: 1.0
applies-to: docs/ENV-REFERENCE.md
project: git-mcp-server
doc-last-updated: 2026-06-18
doc-git-commit: 92ef7210b67e936d847a98e97d5099a5bd73ba76
doc-git-branch: main
doc-age-policy: 90d
doc-conformance-stamp: 2026-06-18T00:00:00Z
---

# Environment Reference

This reference is generated from `defaults.yaml` and the standard Cloud-Dog environment override pattern.

## `a2a_server`

| Variable | Default | Required | Example | Description |
|----------|---------|----------|---------|-------------|
| `CLOUD_DOG__A2A_SERVER__HOST` | `0.0.0.0` | Optional | `0.0.0.0` | Host binding or upstream host for a2a server. |
| `CLOUD_DOG__A2A_SERVER__PORT` | `8085` | Optional | `8085` | Port for a2a server connections. |

## `api_server`

| Variable | Default | Required | Example | Description |
|----------|---------|----------|---------|-------------|
| `CLOUD_DOG__API_SERVER__HOST` | `0.0.0.0` | Optional | `0.0.0.0` | Host binding or upstream host for api server. |
| `CLOUD_DOG__API_SERVER__PORT` | `8078` | Optional | `8078` | Port for api server connections. |
| `CLOUD_DOG__API_SERVER__CLIENT_HOST` | `-` | Optional | `<set as needed>` | Host binding or upstream host for api server client. |
| `CLOUD_DOG__API_SERVER__REQUEST_TIMEOUT_SECONDS` | `30.0` | Optional | `30.0` | Credential or authentication setting for the related subsystem. |

## `auth`

| Variable | Default | Required | Example | Description |
|----------|---------|----------|---------|-------------|
| `CLOUD_DOG__AUTH__MODE` | `api_key` | Optional | `api_key` | Configuration value for auth mode. |
| `CLOUD_DOG__AUTH__JWT__ISSUER` | `-` | Optional | `<set as needed>` | Configuration value for auth jwt issuer. |
| `CLOUD_DOG__AUTH__JWT__AUDIENCE` | `-` | Optional | `<set as needed>` | Configuration value for auth jwt audience. |
| `CLOUD_DOG__AUTH__JWT__PUBLIC_KEYS_URL` | `-` | Deployment dependent | `<set as needed>` | Endpoint or connection URL for auth jwt public keys. |
| `CLOUD_DOG__AUTH__JWT__SECRET` | `-` | Deployment dependent | `your-secret-value` | Credential or authentication setting for the related subsystem. |
| `CLOUD_DOG__AUTH__ENTERPRISE__PROVIDER` | `keycloak` | Optional | `keycloak` | Configuration value for auth enterprise provider. |
| `CLOUD_DOG__AUTH__ENTERPRISE__KEYCLOAK_BASE_URL` | `-` | Deployment dependent | `<set as needed>` | Endpoint or connection URL for auth enterprise keycloak base. |
| `CLOUD_DOG__AUTH__ENTERPRISE__KEYCLOAK_REALM` | `-` | Optional | `<set as needed>` | Configuration value for auth enterprise keycloak realm. |
| `CLOUD_DOG__AUTH__ENTERPRISE__KEYCLOAK_CLIENT_ID` | `-` | Optional | `<set as needed>` | Configuration value for auth enterprise keycloak client id. |
| `CLOUD_DOG__AUTH__ENTERPRISE__KEYCLOAK_CLIENT_SECRET` | `-` | Deployment dependent | `your-secret-value` | Credential or authentication setting for the related subsystem. |

## `git`

| Variable | Default | Required | Example | Description |
|----------|---------|----------|---------|-------------|
| `CLOUD_DOG__GIT__API_KEY` | `-` | Deployment dependent | `your-api-key` | Credential or authentication setting for the related subsystem. |

## `jobs`

| Variable | Default | Required | Example | Description |
|----------|---------|----------|---------|-------------|
| `CLOUD_DOG__JOBS__BACKEND` | `sql` | Optional | `sql` | Configuration value for jobs backend. |
| `CLOUD_DOG__JOBS__QUEUE_NAME` | `git-mcp` | Optional | `git-mcp` | Configuration value for jobs queue name. |
| `CLOUD_DOG__JOBS__RUN_TIMEOUT_SECONDS` | `300.0` | Optional | `300.0` | Timeout or duration control for jobs run timeout. |
| `CLOUD_DOG__JOBS__PAYLOAD_MAX_BYTES` | `16384` | Optional | `16384` | Configuration value for jobs payload max bytes. |

## `log`

| Variable | Default | Required | Example | Description |
|----------|---------|----------|---------|-------------|
| `CLOUD_DOG__LOG__SERVICE_INSTANCE` | `${HOSTNAME:git-mcp-local}` | Optional | `${HOSTNAME:git-mcp-local}` | Configuration value for log service instance. |
| `CLOUD_DOG__LOG__ENVIRONMENT` | `${CLOUD_DOG_ENVIRONMENT:dev}` | Optional | `${CLOUD_DOG_ENVIRONMENT:dev}` | Configuration value for log environment. |
| `CLOUD_DOG__LOG__RETENTION__HOT_DAYS` | `14` | Optional | `14` | Configuration value for log retention hot days. |
| `CLOUD_DOG__LOG__RETENTION__COLD_DAYS` | `60` | Optional | `60` | Configuration value for log retention cold days. |
| `CLOUD_DOG__LOG__RETENTION__ARCHIVE_FORMAT` | `gz` | Optional | `gz` | Configuration value for log retention archive format. |
| `CLOUD_DOG__LOG__INTEGRITY__ENABLED` | `true` | Optional | `true` | Toggle for log integrity. |
| `CLOUD_DOG__LOG__INTEGRITY__INTERVAL_SECONDS` | `300` | Optional | `300` | Timeout or duration control for log integrity interval. |
| `CLOUD_DOG__LOG__INTEGRITY__LOG_FILE` | `logs/audit-integrity.log` | Optional | `logs/audit-integrity.log` | Configuration value for log integrity log file. |
| `CLOUD_DOG__LOG__INTEGRITY__HASH_ALGORITHM` | `sha256` | Optional | `sha256` | Configuration value for log integrity hash algorithm. |
| `CLOUD_DOG__LOG__ROTATION__MODE` | `size` | Optional | `size` | Configuration value for log rotation mode. |
| `CLOUD_DOG__LOG__ROTATION__MAX_BYTES` | `104857600` | Optional | `104857600` | Configuration value for log rotation max bytes. |
| `CLOUD_DOG__LOG__ROTATION__BACKUP_COUNT` | `10` | Optional | `10` | Configuration value for log rotation backup count. |
| `CLOUD_DOG__LOG__ROTATION__WHEN` | `midnight` | Optional | `midnight` | Configuration value for log rotation when. |
| `CLOUD_DOG__LOG__ROTATION__INTERVAL` | `1` | Optional | `1` | Configuration value for log rotation interval. |
| `CLOUD_DOG__LOG__ROTATION__COMPRESS` | `true` | Optional | `true` | Configuration value for log rotation compress. |

## `mcp_server`

| Variable | Default | Required | Example | Description |
|----------|---------|----------|---------|-------------|
| `CLOUD_DOG__MCP_SERVER__HOST` | `0.0.0.0` | Optional | `0.0.0.0` | Host binding or upstream host for mcp server. |
| `CLOUD_DOG__MCP_SERVER__PORT` | `8084` | Optional | `8084` | Port for mcp server connections. |
| `CLOUD_DOG__MCP_SERVER__TRANSPORT` | `streamable-http` | Optional | `streamable-http` | Configuration value for mcp server transport. |

## `profiles`

| Variable | Default | Required | Example | Description |
|----------|---------|----------|---------|-------------|
| `CLOUD_DOG__PROFILES__LOCAL_TEST__REPO__SOURCE` | `https://git.cloud-dog.net/playgroup/test-project.git` | Optional | `https://git.cloud-dog.net/playgroup/test-project.git` | Configuration value for profiles local test repo source. |
| `CLOUD_DOG__PROFILES__LOCAL_TEST__REPO__DEFAULT_BRANCH` | `main` | Optional | `main` | Configuration value for profiles local test repo default branch. |
| `CLOUD_DOG__PROFILES__LOCAL_TEST__WORKSPACE__MODE` | `ephemeral` | Optional | `ephemeral` | Configuration value for profiles local test workspace mode. |
| `CLOUD_DOG__PROFILES__LOCAL_TEST__WORKSPACE__TTL_SECONDS` | `3600` | Optional | `3600` | Timeout or duration control for profiles local test workspace ttl. |
| `CLOUD_DOG__PROFILES__LOCAL_TEST__POLICY__PROTECTED_BRANCHES` | `["main", "release/*"]` | Optional | `<set as needed>` | Configuration value for profiles local test policy protected branches. |
| `CLOUD_DOG__PROFILES__LOCAL_TEST__POLICY__FF_ONLY_TARGETS` | `["main"]` | Optional | `<set as needed>` | Configuration value for profiles local test policy ff only targets. |
| `CLOUD_DOG__PROFILES__LOCAL_TEST__POLICY__FORCE_PUSH` | `admin_only` | Optional | `admin_only` | Configuration value for profiles local test policy force push. |
| `CLOUD_DOG__PROFILES__LOCAL_TEST__POLICY__FILE_SCOPE__DENY_GLOBS` | `["**/.git/**"]` | Optional | `<set as needed>` | Configuration value for profiles local test policy file scope deny globs. |
| `CLOUD_DOG__PROFILES__LOCAL_TEST__POLICY__FILE_SCOPE__ALLOWED_TYPES` | `["*"]` | Optional | `<set as needed>` | Configuration value for profiles local test policy file scope allowed types. |
| `CLOUD_DOG__PROFILES__LOCAL_TEST__POLICY__VALIDATION__JSON` | `strict` | Optional | `strict` | Configuration value for profiles local test policy validation json. |
| `CLOUD_DOG__PROFILES__LOCAL_TEST__POLICY__VALIDATION__YAML` | `warn` | Optional | `warn` | Configuration value for profiles local test policy validation yaml. |
| `CLOUD_DOG__PROFILES__LOCAL_TEST__POLICY__VALIDATION__XML` | `warn` | Optional | `warn` | Configuration value for profiles local test policy validation xml. |
| `CLOUD_DOG__PROFILES__LOCAL_TEST__POLICY__VALIDATION__HTML` | `ignore` | Optional | `ignore` | Configuration value for profiles local test policy validation html. |
| `CLOUD_DOG__PROFILES__LOCAL_TEST__POLICY__VALIDATION__MARKDOWN` | `ignore` | Optional | `ignore` | Configuration value for profiles local test policy validation markdown. |
| `CLOUD_DOG__PROFILES__LOCAL_TEST__AUTH__CREDENTIAL_MODE` | `session` | Optional | `session` | Configuration value for profiles local test auth credential mode. |
| `CLOUD_DOG__PROFILES__LOCAL_TEST__RECOVERY__MODE` | `stash` | Optional | `stash` | Configuration value for profiles local test recovery mode. |
| `CLOUD_DOG__PROFILES__REMOTE_CLOUD_DOG__REPO__SOURCE` | `https://git.cloud-dog.net/playgroup/test-project.git` | Optional | `https://git.cloud-dog.net/playgroup/test-project.git` | Configuration value for profiles remote cloud dog repo source. |
| `CLOUD_DOG__PROFILES__REMOTE_CLOUD_DOG__REPO__DEFAULT_BRANCH` | `main` | Optional | `main` | Configuration value for profiles remote cloud dog repo default branch. |
| `CLOUD_DOG__PROFILES__REMOTE_CLOUD_DOG__REPO__REMOTES__ORIGIN` | `https://git.cloud-dog.net/playgroup/test-project.git` | Optional | `https://git.cloud-dog.net/playgroup/test-project.git` | Configuration value for profiles remote cloud dog repo remotes origin. |
| `CLOUD_DOG__PROFILES__REMOTE_CLOUD_DOG__WORKSPACE__MODE` | `ephemeral` | Optional | `ephemeral` | Configuration value for profiles remote cloud dog workspace mode. |
| `CLOUD_DOG__PROFILES__REMOTE_CLOUD_DOG__WORKSPACE__TTL_SECONDS` | `900` | Optional | `900` | Timeout or duration control for profiles remote cloud dog workspace ttl. |
| `CLOUD_DOG__PROFILES__REMOTE_CLOUD_DOG__POLICY__PROTECTED_BRANCHES` | `["main"]` | Optional | `<set as needed>` | Configuration value for profiles remote cloud dog policy protected branches. |
| `CLOUD_DOG__PROFILES__REMOTE_CLOUD_DOG__POLICY__FF_ONLY_TARGETS` | `["main"]` | Optional | `<set as needed>` | Configuration value for profiles remote cloud dog policy ff only targets. |
| `CLOUD_DOG__PROFILES__REMOTE_CLOUD_DOG__POLICY__FORCE_PUSH` | `never` | Optional | `never` | Configuration value for profiles remote cloud dog policy force push. |
| `CLOUD_DOG__PROFILES__REMOTE_CLOUD_DOG__POLICY__FILE_SCOPE__DENY_GLOBS` | `["**/.git/**"]` | Optional | `<set as needed>` | Configuration value for profiles remote cloud dog policy file scope deny globs. |
| `CLOUD_DOG__PROFILES__REMOTE_CLOUD_DOG__POLICY__FILE_SCOPE__ALLOWED_TYPES` | `["*"]` | Optional | `<set as needed>` | Configuration value for profiles remote cloud dog policy file scope allowed types. |
| `CLOUD_DOG__PROFILES__REMOTE_CLOUD_DOG__POLICY__VALIDATION__JSON` | `strict` | Optional | `strict` | Configuration value for profiles remote cloud dog policy validation json. |
| `CLOUD_DOG__PROFILES__REMOTE_CLOUD_DOG__POLICY__VALIDATION__YAML` | `warn` | Optional | `warn` | Configuration value for profiles remote cloud dog policy validation yaml. |
| `CLOUD_DOG__PROFILES__REMOTE_CLOUD_DOG__POLICY__VALIDATION__XML` | `warn` | Optional | `warn` | Configuration value for profiles remote cloud dog policy validation xml. |
| `CLOUD_DOG__PROFILES__REMOTE_CLOUD_DOG__POLICY__VALIDATION__HTML` | `ignore` | Optional | `ignore` | Configuration value for profiles remote cloud dog policy validation html. |
| `CLOUD_DOG__PROFILES__REMOTE_CLOUD_DOG__POLICY__VALIDATION__MARKDOWN` | `ignore` | Optional | `ignore` | Configuration value for profiles remote cloud dog policy validation markdown. |
| `CLOUD_DOG__PROFILES__REMOTE_CLOUD_DOG__AUTH__CREDENTIAL_MODE` | `session` | Optional | `session` | Configuration value for profiles remote cloud dog auth credential mode. |
| `CLOUD_DOG__PROFILES__REMOTE_CLOUD_DOG__RECOVERY__MODE` | `stash` | Optional | `stash` | Configuration value for profiles remote cloud dog recovery mode. |

## `rbac`

| Variable | Default | Required | Example | Description |
|----------|---------|----------|---------|-------------|
| `CLOUD_DOG__RBAC__ENABLED` | `true` | Optional | `true` | Toggle for rbac. |
| `CLOUD_DOG__RBAC__DEFAULT_DENY` | `true` | Optional | `true` | Configuration value for rbac default deny. |
| `CLOUD_DOG__RBAC__ROLES__ADMIN` | `["*"]` | Optional | `<set as needed>` | Configuration value for rbac roles admin. |
| `CLOUD_DOG__RBAC__ROLES__MAINTAINER` | `["repo_*", "git_*", "file_*", "dir_*", "admin_profile_read", "admin_rbac_read"]` | Optional | `<set as needed>` | Configuration value for rbac roles maintainer. |
| `CLOUD_DOG__RBAC__ROLES__WRITER` | `["repo_*", "git_*", "file_*", "dir_*"]` | Optional | `<set as needed>` | Configuration value for rbac roles writer. |
| `CLOUD_DOG__RBAC__ROLES__READER` | `["repo_open", "repo_close", "git_status", "git_log", "git_diff", "git_branch_list", "git_tag_list", "file_read", "file_d...` | Optional | `<set as needed>` | Configuration value for rbac roles reader. |

## `routes`

| Variable | Default | Required | Example | Description |
|----------|---------|----------|---------|-------------|
| `CLOUD_DOG__ROUTES__API_BASE_PATH` | `/api/v1` | Optional | `/api/v1` | Credential or authentication setting for the related subsystem. |
| `CLOUD_DOG__ROUTES__LEGACY_API_BASE_PATH` | `/app/v1` | Optional | `/app/v1` | Credential or authentication setting for the related subsystem. |
| `CLOUD_DOG__ROUTES__A2A_BASE_PATH` | `/a2a` | Optional | `/a2a` | Configuration value for routes a2a base path. |

## `runtime`

| Variable | Default | Required | Example | Description |
|----------|---------|----------|---------|-------------|
| `CLOUD_DOG__RUNTIME__MODE` | `local-server` | Optional | `local-server` | Configuration value for runtime mode. |
| `CLOUD_DOG__RUNTIME__SEED_KEY_FILE` | `-` | Optional | `<set as needed>` | Credential or authentication setting for the related subsystem. |
| `CLOUD_DOG__RUNTIME__A2A_TEST_API_KEY` | `-` | Deployment dependent | `your-api-key` | Credential or authentication setting for the related subsystem. |
| `CLOUD_DOG__RUNTIME__SERVER_ID` | `${HOSTNAME:git-mcp-local}` | Optional | `${HOSTNAME:git-mcp-local}` | Configuration value for runtime server id. |

## `storage`

| Variable | Default | Required | Example | Description |
|----------|---------|----------|---------|-------------|
| `CLOUD_DOG__STORAGE__DB__URL` | `sqlite:///data/git_mcp.db` | Deployment dependent | `https://service.example.com` | Endpoint or connection URL for storage db. |
| `CLOUD_DOG__STORAGE__AUDIT__PATH` | `./data/audit/audit.jsonl` | Optional | `./data/service.dat` | Configuration value for storage audit path. |
| `CLOUD_DOG__STORAGE__EVENTS__PATH` | `./data/events/a2a_config.jsonl` | Optional | `./data/service.dat` | Configuration value for storage events path. |

## `web`

| Variable | Default | Required | Example | Description |
|----------|---------|----------|---------|-------------|
| `CLOUD_DOG__WEB__UI_DIST_DIR` | `./ui/dist` | Optional | `./ui/dist` | Configuration value for web ui dist dir. |
| `CLOUD_DOG__WEB__MCP_PROXY_BASE_PATH` | `/git-mcp` | Optional | `/git-mcp` | Configuration value for web mcp proxy base path. |
| `CLOUD_DOG__WEB__DEFAULT_PROFILE` | `remote_cloud_dog` | Optional | `remote_cloud_dog` | Configuration value for web default profile. |
| `CLOUD_DOG__WEB__ENVIRONMENT` | `${CLOUD_DOG_ENVIRONMENT:dev}` | Optional | `${CLOUD_DOG_ENVIRONMENT:dev}` | Configuration value for web environment. |

## `web_server`

| Variable | Default | Required | Example | Description |
|----------|---------|----------|---------|-------------|
| `CLOUD_DOG__WEB_SERVER__HOST` | `0.0.0.0` | Optional | `0.0.0.0` | Host binding or upstream host for web server. |
| `CLOUD_DOG__WEB_SERVER__PORT` | `8079` | Optional | `8079` | Port for web server connections. |

## `workspace`

| Variable | Default | Required | Example | Description |
|----------|---------|----------|---------|-------------|
| `CLOUD_DOG__WORKSPACE__BASE_DIR` | `./data/workspaces` | Optional | `./data/workspaces` | Configuration value for workspace base dir. |
| `CLOUD_DOG__WORKSPACE__DEFAULT_MODE` | `ephemeral` | Optional | `ephemeral` | Configuration value for workspace default mode. |
| `CLOUD_DOG__WORKSPACE__DEFAULT_TTL_SECONDS` | `3600` | Optional | `3600` | Timeout or duration control for workspace default ttl. |
| `CLOUD_DOG__WORKSPACE__CLEANUP_INTERVAL_SECONDS` | `300` | Optional | `300` | Timeout or duration control for workspace cleanup interval. |

## Vault Support

| Variable | Purpose | Example |
|----------|---------|---------|
| `VAULT_ADDR` | Vault server URL when using secret-backed config resolution. | `https://your-vault-server` |
| `VAULT_TOKEN` | Token-based authentication for Vault when applicable. | `your-vault-token` |
| `VAULT_MOUNT_POINT` | Secret mount used by your Vault deployment. | `secret` |
| `VAULT_CONFIG_PATH` | Config path holding service settings. | `services/your-service` |
