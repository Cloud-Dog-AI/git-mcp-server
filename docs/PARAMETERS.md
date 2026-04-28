# Parameters

This reference is generated from `defaults.yaml`. Each key can be overridden by the corresponding environment variable.

## `a2a_server`

| Key | Default | Environment Override | Description |
|-----|---------|----------------------|-------------|
| `a2a_server.host` | `0.0.0.0` | `CLOUD_DOG__A2A_SERVER__HOST` | Host binding or upstream host for a2a server. |
| `a2a_server.port` | `8085` | `CLOUD_DOG__A2A_SERVER__PORT` | Port for a2a server connections. |
| `a2a_server.base_path` | `/a2a` | `CLOUD_DOG__A2A_SERVER__BASE_PATH` | PS-92 canonical A2A base path. |

## `api_server`

| Key | Default | Environment Override | Description |
|-----|---------|----------------------|-------------|
| `api_server.host` | `0.0.0.0` | `CLOUD_DOG__API_SERVER__HOST` | Host binding or upstream host for api server. |
| `api_server.port` | `8078` | `CLOUD_DOG__API_SERVER__PORT` | Port for api server connections. |
| `api_server.client_host` | `-` | `CLOUD_DOG__API_SERVER__CLIENT_HOST` | Host binding or upstream host for api server client. |
| `api_server.request_timeout_seconds` | `30.0` | `CLOUD_DOG__API_SERVER__REQUEST_TIMEOUT_SECONDS` | Credential or authentication setting for the related subsystem. |
| `api_server.base_path` | `/api/v1` | `CLOUD_DOG__API_SERVER__BASE_PATH` | PS-92 canonical API base path. Legacy `/app/v1` is hardcoded compat (NOT configurable). |

## `auth`

| Key | Default | Environment Override | Description |
|-----|---------|----------------------|-------------|
| `auth.mode` | `api_key` | `CLOUD_DOG__AUTH__MODE` | Configuration value for auth mode. |
| `auth.jwt.issuer` | `-` | `CLOUD_DOG__AUTH__JWT__ISSUER` | Configuration value for auth jwt issuer. |
| `auth.jwt.audience` | `-` | `CLOUD_DOG__AUTH__JWT__AUDIENCE` | Configuration value for auth jwt audience. |
| `auth.jwt.public_keys_url` | `-` | `CLOUD_DOG__AUTH__JWT__PUBLIC_KEYS_URL` | Endpoint or connection URL for auth jwt public keys. |
| `auth.jwt.secret` | `-` | `CLOUD_DOG__AUTH__JWT__SECRET` | Credential or authentication setting for the related subsystem. |
| `auth.enterprise.provider` | `keycloak` | `CLOUD_DOG__AUTH__ENTERPRISE__PROVIDER` | Configuration value for auth enterprise provider. |
| `auth.enterprise.keycloak_base_url` | `-` | `CLOUD_DOG__AUTH__ENTERPRISE__KEYCLOAK_BASE_URL` | Endpoint or connection URL for auth enterprise keycloak base. |
| `auth.enterprise.keycloak_realm` | `-` | `CLOUD_DOG__AUTH__ENTERPRISE__KEYCLOAK_REALM` | Configuration value for auth enterprise keycloak realm. |
| `auth.enterprise.keycloak_client_id` | `-` | `CLOUD_DOG__AUTH__ENTERPRISE__KEYCLOAK_CLIENT_ID` | Configuration value for auth enterprise keycloak client id. |
| `auth.enterprise.keycloak_client_secret` | `-` | `CLOUD_DOG__AUTH__ENTERPRISE__KEYCLOAK_CLIENT_SECRET` | Credential or authentication setting for the related subsystem. |

## `git`

| Key | Default | Environment Override | Description |
|-----|---------|----------------------|-------------|
| `git.api_key` | `-` | `CLOUD_DOG__GIT__API_KEY` | Credential or authentication setting for the related subsystem. |

## `jobs`

| Key | Default | Environment Override | Description |
|-----|---------|----------------------|-------------|
| `jobs.backend` | `sql` | `CLOUD_DOG__JOBS__BACKEND` | Configuration value for jobs backend. |
| `jobs.queue_name` | `git-mcp` | `CLOUD_DOG__JOBS__QUEUE_NAME` | Configuration value for jobs queue name. |
| `jobs.run_timeout_seconds` | `300.0` | `CLOUD_DOG__JOBS__RUN_TIMEOUT_SECONDS` | Timeout or duration control for jobs run timeout. |
| `jobs.payload_max_bytes` | `16384` | `CLOUD_DOG__JOBS__PAYLOAD_MAX_BYTES` | Configuration value for jobs payload max bytes. |

## `log`

| Key | Default | Environment Override | Description |
|-----|---------|----------------------|-------------|
| `log.service_instance` | `${HOSTNAME:git-mcp-local}` | `CLOUD_DOG__LOG__SERVICE_INSTANCE` | Configuration value for log service instance. |
| `log.environment` | `${CLOUD_DOG_ENVIRONMENT:dev}` | `CLOUD_DOG__LOG__ENVIRONMENT` | Configuration value for log environment. |
| `log.retention.hot_days` | `14` | `CLOUD_DOG__LOG__RETENTION__HOT_DAYS` | Configuration value for log retention hot days. |
| `log.retention.cold_days` | `60` | `CLOUD_DOG__LOG__RETENTION__COLD_DAYS` | Configuration value for log retention cold days. |
| `log.retention.archive_format` | `gz` | `CLOUD_DOG__LOG__RETENTION__ARCHIVE_FORMAT` | Configuration value for log retention archive format. |
| `log.integrity.enabled` | `true` | `CLOUD_DOG__LOG__INTEGRITY__ENABLED` | Toggle for log integrity. |
| `log.integrity.interval_seconds` | `300` | `CLOUD_DOG__LOG__INTEGRITY__INTERVAL_SECONDS` | Timeout or duration control for log integrity interval. |
| `log.integrity.log_file` | `logs/audit-integrity.log` | `CLOUD_DOG__LOG__INTEGRITY__LOG_FILE` | Configuration value for log integrity log file. |
| `log.integrity.hash_algorithm` | `sha256` | `CLOUD_DOG__LOG__INTEGRITY__HASH_ALGORITHM` | Configuration value for log integrity hash algorithm. |
| `log.rotation.mode` | `size` | `CLOUD_DOG__LOG__ROTATION__MODE` | Configuration value for log rotation mode. |
| `log.rotation.max_bytes` | `104857600` | `CLOUD_DOG__LOG__ROTATION__MAX_BYTES` | Configuration value for log rotation max bytes. |
| `log.rotation.backup_count` | `10` | `CLOUD_DOG__LOG__ROTATION__BACKUP_COUNT` | Configuration value for log rotation backup count. |
| `log.rotation.when` | `midnight` | `CLOUD_DOG__LOG__ROTATION__WHEN` | Configuration value for log rotation when. |
| `log.rotation.interval` | `1` | `CLOUD_DOG__LOG__ROTATION__INTERVAL` | Configuration value for log rotation interval. |
| `log.rotation.compress` | `true` | `CLOUD_DOG__LOG__ROTATION__COMPRESS` | Configuration value for log rotation compress. |

## `mcp_server`

| Key | Default | Environment Override | Description |
|-----|---------|----------------------|-------------|
| `mcp_server.host` | `0.0.0.0` | `CLOUD_DOG__MCP_SERVER__HOST` | Host binding or upstream host for mcp server. |
| `mcp_server.port` | `8084` | `CLOUD_DOG__MCP_SERVER__PORT` | Port for mcp server connections. |
| `mcp_server.transport` | `streamable-http` | `CLOUD_DOG__MCP_SERVER__TRANSPORT` | Configuration value for mcp server transport. |
| `mcp_server.base_path` | `/git-mcp` | `CLOUD_DOG__MCP_SERVER__BASE_PATH` | PS-92 canonical MCP proxy base path. |

## `profiles`

| Key | Default | Environment Override | Description |
|-----|---------|----------------------|-------------|
| `profiles.local_test.repo.source` | `<set per environment>` | `CLOUD_DOG__PROFILES__LOCAL_TEST__REPO__SOURCE` | Configuration value for profiles local test repo source. |
| `profiles.local_test.repo.default_branch` | `main` | `CLOUD_DOG__PROFILES__LOCAL_TEST__REPO__DEFAULT_BRANCH` | Configuration value for profiles local test repo default branch. |
| `profiles.local_test.workspace.mode` | `ephemeral` | `CLOUD_DOG__PROFILES__LOCAL_TEST__WORKSPACE__MODE` | Configuration value for profiles local test workspace mode. |
| `profiles.local_test.workspace.ttl_seconds` | `3600` | `CLOUD_DOG__PROFILES__LOCAL_TEST__WORKSPACE__TTL_SECONDS` | Timeout or duration control for profiles local test workspace ttl. |
| `profiles.local_test.policy.protected_branches` | `["main", "release/*"]` | `CLOUD_DOG__PROFILES__LOCAL_TEST__POLICY__PROTECTED_BRANCHES` | Configuration value for profiles local test policy protected branches. |
| `profiles.local_test.policy.ff_only_targets` | `["main"]` | `CLOUD_DOG__PROFILES__LOCAL_TEST__POLICY__FF_ONLY_TARGETS` | Configuration value for profiles local test policy ff only targets. |
| `profiles.local_test.policy.force_push` | `admin_only` | `CLOUD_DOG__PROFILES__LOCAL_TEST__POLICY__FORCE_PUSH` | Configuration value for profiles local test policy force push. |
| `profiles.local_test.policy.file_scope.deny_globs` | `["**/.git/**"]` | `CLOUD_DOG__PROFILES__LOCAL_TEST__POLICY__FILE_SCOPE__DENY_GLOBS` | Configuration value for profiles local test policy file scope deny globs. |
| `profiles.local_test.policy.file_scope.allowed_types` | `["*"]` | `CLOUD_DOG__PROFILES__LOCAL_TEST__POLICY__FILE_SCOPE__ALLOWED_TYPES` | Configuration value for profiles local test policy file scope allowed types. |
| `profiles.local_test.policy.validation.json` | `strict` | `CLOUD_DOG__PROFILES__LOCAL_TEST__POLICY__VALIDATION__JSON` | Configuration value for profiles local test policy validation json. |
| `profiles.local_test.policy.validation.yaml` | `warn` | `CLOUD_DOG__PROFILES__LOCAL_TEST__POLICY__VALIDATION__YAML` | Configuration value for profiles local test policy validation yaml. |
| `profiles.local_test.policy.validation.xml` | `warn` | `CLOUD_DOG__PROFILES__LOCAL_TEST__POLICY__VALIDATION__XML` | Configuration value for profiles local test policy validation xml. |
| `profiles.local_test.policy.validation.html` | `ignore` | `CLOUD_DOG__PROFILES__LOCAL_TEST__POLICY__VALIDATION__HTML` | Configuration value for profiles local test policy validation html. |
| `profiles.local_test.policy.validation.markdown` | `ignore` | `CLOUD_DOG__PROFILES__LOCAL_TEST__POLICY__VALIDATION__MARKDOWN` | Configuration value for profiles local test policy validation markdown. |
| `profiles.local_test.auth.credential_mode` | `session` | `CLOUD_DOG__PROFILES__LOCAL_TEST__AUTH__CREDENTIAL_MODE` | Configuration value for profiles local test auth credential mode. |
| `profiles.local_test.recovery.mode` | `stash` | `CLOUD_DOG__PROFILES__LOCAL_TEST__RECOVERY__MODE` | Configuration value for profiles local test recovery mode. |
| `profiles.remote_cloud_dog.repo.source` | `https://example.invalid/authorised-remote-required.git` | `CLOUD_DOG__PROFILES__REMOTE_CLOUD_DOG__REPO__SOURCE` | Configuration value for profiles remote cloud dog repo source. |
| `profiles.remote_cloud_dog.repo.default_branch` | `main` | `CLOUD_DOG__PROFILES__REMOTE_CLOUD_DOG__REPO__DEFAULT_BRANCH` | Configuration value for profiles remote cloud dog repo default branch. |
| `profiles.remote_cloud_dog.repo.remotes.origin` | `https://example.invalid/authorised-remote-required.git` | `CLOUD_DOG__PROFILES__REMOTE_CLOUD_DOG__REPO__REMOTES__ORIGIN` | Configuration value for profiles remote cloud dog repo remotes origin. |
| `profiles.remote_cloud_dog.workspace.mode` | `ephemeral` | `CLOUD_DOG__PROFILES__REMOTE_CLOUD_DOG__WORKSPACE__MODE` | Configuration value for profiles remote cloud dog workspace mode. |
| `profiles.remote_cloud_dog.workspace.ttl_seconds` | `900` | `CLOUD_DOG__PROFILES__REMOTE_CLOUD_DOG__WORKSPACE__TTL_SECONDS` | Timeout or duration control for profiles remote cloud dog workspace ttl. |
| `profiles.remote_cloud_dog.policy.protected_branches` | `["main"]` | `CLOUD_DOG__PROFILES__REMOTE_CLOUD_DOG__POLICY__PROTECTED_BRANCHES` | Configuration value for profiles remote cloud dog policy protected branches. |
| `profiles.remote_cloud_dog.policy.ff_only_targets` | `["main"]` | `CLOUD_DOG__PROFILES__REMOTE_CLOUD_DOG__POLICY__FF_ONLY_TARGETS` | Configuration value for profiles remote cloud dog policy ff only targets. |
| `profiles.remote_cloud_dog.policy.force_push` | `never` | `CLOUD_DOG__PROFILES__REMOTE_CLOUD_DOG__POLICY__FORCE_PUSH` | Configuration value for profiles remote cloud dog policy force push. |
| `profiles.remote_cloud_dog.policy.file_scope.deny_globs` | `["**/.git/**"]` | `CLOUD_DOG__PROFILES__REMOTE_CLOUD_DOG__POLICY__FILE_SCOPE__DENY_GLOBS` | Configuration value for profiles remote cloud dog policy file scope deny globs. |
| `profiles.remote_cloud_dog.policy.file_scope.allowed_types` | `["*"]` | `CLOUD_DOG__PROFILES__REMOTE_CLOUD_DOG__POLICY__FILE_SCOPE__ALLOWED_TYPES` | Configuration value for profiles remote cloud dog policy file scope allowed types. |
| `profiles.remote_cloud_dog.policy.validation.json` | `strict` | `CLOUD_DOG__PROFILES__REMOTE_CLOUD_DOG__POLICY__VALIDATION__JSON` | Configuration value for profiles remote cloud dog policy validation json. |
| `profiles.remote_cloud_dog.policy.validation.yaml` | `warn` | `CLOUD_DOG__PROFILES__REMOTE_CLOUD_DOG__POLICY__VALIDATION__YAML` | Configuration value for profiles remote cloud dog policy validation yaml. |
| `profiles.remote_cloud_dog.policy.validation.xml` | `warn` | `CLOUD_DOG__PROFILES__REMOTE_CLOUD_DOG__POLICY__VALIDATION__XML` | Configuration value for profiles remote cloud dog policy validation xml. |
| `profiles.remote_cloud_dog.policy.validation.html` | `ignore` | `CLOUD_DOG__PROFILES__REMOTE_CLOUD_DOG__POLICY__VALIDATION__HTML` | Configuration value for profiles remote cloud dog policy validation html. |
| `profiles.remote_cloud_dog.policy.validation.markdown` | `ignore` | `CLOUD_DOG__PROFILES__REMOTE_CLOUD_DOG__POLICY__VALIDATION__MARKDOWN` | Configuration value for profiles remote cloud dog policy validation markdown. |
| `profiles.remote_cloud_dog.auth.credential_mode` | `session` | `CLOUD_DOG__PROFILES__REMOTE_CLOUD_DOG__AUTH__CREDENTIAL_MODE` | Configuration value for profiles remote cloud dog auth credential mode. |
| `profiles.remote_cloud_dog.recovery.mode` | `stash` | `CLOUD_DOG__PROFILES__REMOTE_CLOUD_DOG__RECOVERY__MODE` | Configuration value for profiles remote cloud dog recovery mode. |

## `rbac`

| Key | Default | Environment Override | Description |
|-----|---------|----------------------|-------------|
| `rbac.enabled` | `true` | `CLOUD_DOG__RBAC__ENABLED` | Toggle for rbac. |
| `rbac.default_deny` | `true` | `CLOUD_DOG__RBAC__DEFAULT_DENY` | Configuration value for rbac default deny. |
| `rbac.roles.admin` | `["*"]` | `CLOUD_DOG__RBAC__ROLES__ADMIN` | Configuration value for rbac roles admin. |
| `rbac.roles.maintainer` | `["repo_*", "git_*", "file_*", "dir_*", "admin_profile_read", "admin_rbac_read"]` | `CLOUD_DOG__RBAC__ROLES__MAINTAINER` | Configuration value for rbac roles maintainer. |
| `rbac.roles.writer` | `["repo_*", "git_*", "file_*", "dir_*"]` | `CLOUD_DOG__RBAC__ROLES__WRITER` | Configuration value for rbac roles writer. |
| `rbac.roles.reader` | `["repo_open", "repo_close", "git_status", "git_log", "git_diff", "git_branch_list", "git_tag_list", "file_read", "file_d...` | `CLOUD_DOG__RBAC__ROLES__READER` | Configuration value for rbac roles reader. |

## `runtime`

| Key | Default | Environment Override | Description |
|-----|---------|----------------------|-------------|
| `runtime.mode` | `local-server` | `CLOUD_DOG__RUNTIME__MODE` | Configuration value for runtime mode. |
| `runtime.seed_key_file` | `-` | `CLOUD_DOG__RUNTIME__SEED_KEY_FILE` | Credential or authentication setting for the related subsystem. |
| `runtime.a2a_test_api_key` | `-` | `CLOUD_DOG__RUNTIME__A2A_TEST_API_KEY` | Credential or authentication setting for the related subsystem. |
| `runtime.server_id` | `${HOSTNAME:git-mcp-local}` | `CLOUD_DOG__RUNTIME__SERVER_ID` | Configuration value for runtime server id. |

## `storage`

| Key | Default | Environment Override | Description |
|-----|---------|----------------------|-------------|
| `storage.db.url` | `sqlite:///data/git_mcp.db` | `CLOUD_DOG__STORAGE__DB__URL` | Endpoint or connection URL for storage db. |
| `storage.audit.path` | `./data/audit/audit.jsonl` | `CLOUD_DOG__STORAGE__AUDIT__PATH` | Configuration value for storage audit path. |
| `storage.events.path` | `./data/events/a2a_config.jsonl` | `CLOUD_DOG__STORAGE__EVENTS__PATH` | Configuration value for storage events path. |

## `web`

| Key | Default | Environment Override | Description |
|-----|---------|----------------------|-------------|
| `web.ui_dist_dir` | `./ui/dist` | `CLOUD_DOG__WEB__UI_DIST_DIR` | Configuration value for web ui dist dir. |
| `web.default_profile` | `remote_cloud_dog` | `CLOUD_DOG__WEB__DEFAULT_PROFILE` | Configuration value for web default profile. |
| `web.environment` | `${CLOUD_DOG_ENVIRONMENT:dev}` | `CLOUD_DOG__WEB__ENVIRONMENT` | Configuration value for web environment. |

## `web_server`

| Key | Default | Environment Override | Description |
|-----|---------|----------------------|-------------|
| `web_server.host` | `0.0.0.0` | `CLOUD_DOG__WEB_SERVER__HOST` | Host binding or upstream host for web server. |
| `web_server.port` | `8079` | `CLOUD_DOG__WEB_SERVER__PORT` | Port for web server connections. |

## `workspace`

| Key | Default | Environment Override | Description |
|-----|---------|----------------------|-------------|
| `workspace.base_dir` | `./data/workspaces` | `CLOUD_DOG__WORKSPACE__BASE_DIR` | Configuration value for workspace base dir. |
| `workspace.default_mode` | `ephemeral` | `CLOUD_DOG__WORKSPACE__DEFAULT_MODE` | Configuration value for workspace default mode. |
| `workspace.default_ttl_seconds` | `3600` | `CLOUD_DOG__WORKSPACE__DEFAULT_TTL_SECONDS` | Timeout or duration control for workspace default ttl. |
| `workspace.cleanup_interval_seconds` | `300` | `CLOUD_DOG__WORKSPACE__CLEANUP_INTERVAL_SECONDS` | Timeout or duration control for workspace cleanup interval. |
