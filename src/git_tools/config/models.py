# Copyright 2026 Cloud-Dog, Viewdeck Engineering Limited
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

from __future__ import annotations

from typing import Any, Literal

from pydantic import BaseModel, Field, field_validator


def _route_path(*segments: str) -> str:
    """Build an absolute path from slash-free segments."""
    return "/" + "/".join(part.strip("/") for part in segments if part.strip("/"))


class ListenerConfig(BaseModel):
    """Common host/port listener settings."""

    host: str = "0.0.0.0"
    port: int


# PS-92 (W28A-970c-V2): HTTP base paths live on the per-server listener configs
# instead of a dedicated RouteConfig. Legacy `/app/v1` is hardcoded in the API
# routing layer as include_in_schema=False compatibility and is NOT configurable.
LEGACY_API_BASE_PATH = "/app/v1"


class ApiServerConfig(ListenerConfig):
    """API server runtime settings."""

    port: int
    client_host: str = ""
    request_timeout_seconds: float = 30.0
    base_path: str = Field(default_factory=lambda: _route_path("api", "v1"))


class WebServerConfig(ListenerConfig):
    """Web server runtime settings."""

    port: int


class MCPServerConfig(ListenerConfig):
    """MCP server runtime settings."""

    port: int
    transport: Literal["streamable-http", "http_sse", "stdio"] = "streamable-http"
    base_path: str = Field(default_factory=lambda: _route_path("git-mcp"))


class A2AServerConfig(ListenerConfig):
    """A2A server runtime settings."""

    port: int
    base_path: str = Field(default_factory=lambda: _route_path("a2a"))


class RuntimeConfig(BaseModel):
    """Runtime-only settings used by local orchestration flows."""

    mode: str = "local-server"
    seed_key_file: str = ""
    a2a_test_api_key: str = ""
    server_id: str = "git-mcp-local"

    @field_validator("a2a_test_api_key", mode="before")
    @classmethod
    def _coerce_a2a_test_api_key(cls, value: Any) -> str:
        """Accept numeric env-derived values while allowing an unset test-only key."""
        return str(value).strip() if value is not None else ""

    @field_validator("server_id", mode="before")
    @classmethod
    def _coerce_server_id(cls, value: Any) -> str:
        """Accept env-derived values while enforcing a non-empty server ID."""
        candidate = str(value).strip() if value is not None else ""
        if not candidate:
            raise ValueError("runtime.server_id must be a non-empty string")
        return candidate


class GitConfig(BaseModel):
    """Git service runtime settings."""

    api_key: str = ""


class JobsConfig(BaseModel):
    """Managed-jobs settings used for long-running git operations."""

    backend: Literal["sql"] = "sql"
    queue_name: str = "git-mcp"
    run_timeout_seconds: float = 300.0
    payload_max_bytes: int = 16384
    claim_timeout_seconds: int = 120
    max_retries: int = 3
    dead_letter_queue: str = "git_mcp_dead_letter"

    @field_validator("queue_name", mode="before")
    @classmethod
    def _coerce_queue_name(cls, value: Any) -> str:
        """Accept env-derived values while enforcing a non-empty queue name."""
        candidate = str(value).strip() if value is not None else ""
        if not candidate:
            raise ValueError("jobs.queue_name must be a non-empty string")
        return candidate


class WebConfig(BaseModel):
    """Web UI delivery settings for the PS-30 split architecture."""

    ui_dist_dir: str = "./ui/dist"
    default_profile: str = "remote_cloud_dog"
    environment: Literal["dev", "staging", "production"] = "dev"
    session_timeout_minutes: int = 30


class WebLoginConfig(BaseModel):
    """Cookie-login credentials for the standalone Web UI."""

    username: str = "admin"
    password: str = ""


class JWTConfig(BaseModel):
    """JWT settings used by IDAM token verification."""

    issuer: str = ""
    audience: str = ""
    public_keys_url: str = ""
    secret: str = ""


class EnterpriseAuthConfig(BaseModel):
    """Enterprise provider settings for auth.mode=enterprise."""

    provider: Literal["keycloak", "ldap", "saml"] = "keycloak"
    keycloak_base_url: str = ""
    keycloak_realm: str = ""
    keycloak_client_id: str = ""
    keycloak_client_secret: str = ""


class AuthConfig(BaseModel):
    """Authentication mode settings."""

    mode: Literal["api_key", "jwt", "api_key+jwt", "enterprise"] = "api_key"
    jwt: JWTConfig = Field(default_factory=JWTConfig)
    enterprise: EnterpriseAuthConfig = Field(default_factory=EnterpriseAuthConfig)


class DatabaseConfig(BaseModel):
    """Database settings."""

    url: str


class AuditStorageConfig(BaseModel):
    """Audit storage settings."""

    path: str


class EventStorageConfig(BaseModel):
    """Config-event journal storage settings."""

    path: str = "./data/events/a2a_config.jsonl"


class StorageConfig(BaseModel):
    """Storage settings."""

    db: DatabaseConfig
    audit: AuditStorageConfig
    events: EventStorageConfig = Field(default_factory=EventStorageConfig)


class WorkspaceConfig(BaseModel):
    """Workspace defaults and cleanup cadence."""

    base_dir: str = "./data/workspaces"
    default_mode: Literal["ephemeral", "persistent"] = "ephemeral"
    default_ttl_seconds: int = 3600
    cleanup_interval_seconds: int = 300


class FileScopeConfig(BaseModel):
    """File scope policy settings."""

    deny_globs: list[str] = Field(default_factory=lambda: ["**/.git/**"])
    allowed_types: list[str] = Field(default_factory=lambda: ["*"])


class ValidationConfig(BaseModel):
    """Validation policy per file type."""

    json_mode: Literal["strict", "warn", "ignore"] = Field(default="strict", alias="json")
    yaml_mode: Literal["strict", "warn", "ignore"] = Field(default="warn", alias="yaml")
    xml_mode: Literal["strict", "warn", "ignore"] = Field(default="warn", alias="xml")
    html_mode: Literal["strict", "warn", "ignore"] = Field(default="ignore", alias="html")
    markdown_mode: Literal["strict", "warn", "ignore"] = Field(default="ignore", alias="markdown")


class PolicyConfig(BaseModel):
    """Git and file policy settings for a profile."""

    allowed_branches: list[str] = Field(default_factory=list)
    read_only: bool = False
    protected_branches: list[str] = Field(default_factory=list)
    ff_only_targets: list[str] = Field(default_factory=list)
    force_push: Literal["admin_only", "never", "maintainer+"] = "admin_only"
    file_scope: FileScopeConfig = Field(default_factory=FileScopeConfig)
    validation: ValidationConfig = Field(default_factory=ValidationConfig)


class RepoConfig(BaseModel):
    """Git repository source and remote settings."""

    source: str
    default_branch: str = "main"
    remotes: dict[str, str] = Field(default_factory=dict)


class ProfileWorkspaceConfig(BaseModel):
    """Per-profile workspace configuration."""

    mode: Literal["ephemeral", "persistent"] = "ephemeral"
    ttl_seconds: int = 3600


class ProfileAuthConfig(BaseModel):
    """Profile auth/credential settings."""

    credential_mode: Literal["session", "stored"] = "session"


class RecoveryConfig(BaseModel):
    """Recovery policy configuration."""

    mode: Literal["stash", "recovery_branch", "patch_bundle"] = "stash"


class ProfileConfig(BaseModel):
    """Repository profile configuration."""

    repo: RepoConfig
    workspace: ProfileWorkspaceConfig = Field(default_factory=ProfileWorkspaceConfig)
    policy: PolicyConfig = Field(default_factory=PolicyConfig)
    auth: ProfileAuthConfig = Field(default_factory=ProfileAuthConfig)
    recovery: RecoveryConfig = Field(default_factory=RecoveryConfig)


class RBACConfig(BaseModel):
    """RBAC roles and default posture."""

    enabled: bool = True
    default_deny: bool = True
    roles: dict[str, list[str]] = Field(default_factory=dict)


class GlobalConfigModel(BaseModel):
    """Top-level configuration model."""

    api_server: ApiServerConfig = Field(default_factory=ApiServerConfig)
    web_server: WebServerConfig = Field(default_factory=WebServerConfig)
    mcp_server: MCPServerConfig = Field(default_factory=MCPServerConfig)
    a2a_server: A2AServerConfig = Field(default_factory=A2AServerConfig)
    runtime: RuntimeConfig = Field(default_factory=RuntimeConfig)
    git: GitConfig = Field(default_factory=GitConfig)
    jobs: JobsConfig = Field(default_factory=JobsConfig)
    web: WebConfig = Field(default_factory=WebConfig)
    web_login: WebLoginConfig = Field(default_factory=WebLoginConfig)
    auth: AuthConfig
    storage: StorageConfig
    workspace: WorkspaceConfig
    profiles: dict[str, ProfileConfig] = Field(default_factory=dict)
    rbac: RBACConfig = Field(default_factory=RBACConfig)
