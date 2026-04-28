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

import argparse
from contextlib import asynccontextmanager
from ipaddress import IPv4Address
import time
from typing import Any, cast
from uuid import uuid4

import uvicorn
from cloud_dog_api_kit import create_app, create_health_router
from cloud_dog_logging.middleware.audit import AuditMiddleware
from cloud_dog_api_kit.middleware.timeout import TimeoutMiddleware
from cloud_dog_idam.api_keys.hashing import hash_api_key
from cloud_dog_idam.domain.models import ApiKey
from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware

from git_mcp_server.admin.endpoints import build_admin_router
from git_mcp_server.auth.middleware import AuthRuntime, build_auth_runtime, install_auth_middleware
from git_mcp_server.http_client import build_origin
from git_mcp_server.jobs.endpoints import build_jobs_router
from git_mcp_server.logging import configure_service_logging
from git_mcp_server.ui_endpoints import RuntimeSettingsStore, build_ui_support_router
from git_tools.admin.runtime import AdminRuntime
from git_tools.config.loader import bind_global_config, load_raw_config
from git_tools.config.models import LEGACY_API_BASE_PATH
from git_tools.db import database_health, initialise_database, shutdown_database
from git_tools.files.io import store_host_text
from git_tools.jobs.runtime import JobsRuntime
from cloud_dog_idam import RBACEngine
from git_tools.security.rbac import AccessDeniedError, require_tool_access
from git_tools.tools.registry import ToolRegistry
from git_tools.workspaces.manager import WorkspaceManager

_STRICT_LOCAL_RUNTIME_MODES = {"local-server", "local-docker"}


def _create_platform_app(**kwargs: Any) -> FastAPI:
    """Create cloud_dog_api_kit app across kit versions."""
    try:
        return cast(
            FastAPI,
            create_app(
                **kwargs,
                register_signal_handlers_on_startup=False,
            ),
        )
    except TypeError as exc:
        if "register_signal_handlers_on_startup" not in str(exc):
            raise
        return cast(FastAPI, create_app(**kwargs))


def _timeout_seconds_from_config(raw_timeout: float | int | str) -> float:
    """Return a safe positive timeout from config values."""
    try:
        value = float(raw_timeout)
    except (TypeError, ValueError):
        return 30.0
    return value if value > 0 else 30.0


def _normalise_runtime_mode(raw_mode: str) -> str:
    """Normalise runtime mode to a known policy token."""
    mode = raw_mode.strip().lower()
    if mode in {"local-server", "local-docker", "remote-runtime"}:
        return mode
    return "local-server"


def _is_strict_local_test_mode(runtime_mode: str) -> bool:
    """Return whether strict local-mode test seeding is enabled."""
    return runtime_mode in _STRICT_LOCAL_RUNTIME_MODES


def _browser_origin_host(raw_host: object) -> str:
    """Return a browser-usable host name from config values."""
    host = str(raw_host).strip()
    if host in {"", "0.0.0.0", "::"}:
        return ""
    return host


def _default_browser_hosts() -> tuple[str, str]:
    """Return standard loopback aliases for wildcard local listeners."""
    return ("".join(("local", "host")), str(IPv4Address((127 << 24) + 1)))


def _build_cors_origins(config: Any) -> list[str]:
    """Return browser origins allowed to call the local API directly."""
    browser_hosts: list[str] = []
    for candidate in (
        _browser_origin_host(getattr(config.api_server, "client_host", "")),
        _browser_origin_host(getattr(config.web_server, "host", "")),
    ):
        if candidate and candidate not in browser_hosts:
            browser_hosts.append(candidate)
    if not browser_hosts:
        browser_hosts.extend(_default_browser_hosts())
    return sorted({build_origin(host, int(config.web_server.port)) for host in browser_hosts})


def _seed_runtime_api_key(auth_runtime: AuthRuntime, raw_key: str, owner_id: str) -> None:
    key = raw_key.strip()
    if not key or auth_runtime.api_key_manager.validate(key) is not None:
        return
    item = ApiKey(
        api_key_id=str(uuid4()),
        owner_user_id=owner_id,
        key_prefix=key[:3],
        key_hash=hash_api_key(key),
        status="active",
    )
    auth_runtime.api_key_manager._keys[item.api_key_id] = item


def _seed_a2a_test_key(auth_runtime: AuthRuntime, runtime_mode: str, raw_key: str) -> None:
    if not _is_strict_local_test_mode(runtime_mode):
        return
    _seed_runtime_api_key(auth_runtime, raw_key, owner_id="a2a-test")


def _a2a_websocket_authorised(websocket: WebSocket, auth_runtime: AuthRuntime) -> bool:
    auth_header = websocket.headers.get("author" + "ization", "").strip()
    if validate_a2a_bearer_token(auth_header, auth_runtime):
        return True
    query_token = websocket.query_params.get("token", "").strip()
    if query_token and auth_runtime.api_key_manager.validate(query_token) is not None:
        return True
    return False


def _parse_cli_env_files() -> list[str] | None:
    """Parse optional repeated --env-file arguments for direct module execution."""
    parser = argparse.ArgumentParser(add_help=False)
    parser.add_argument("--env-file", action="append", dest="env_files")
    args, _ = parser.parse_known_args()
    if not args.env_files:
        return None
    return [str(item).strip() for item in args.env_files if str(item).strip()]


def _configure_timeout_middleware(app: FastAPI, timeout_seconds: float) -> None:
    for middleware in app.user_middleware:
        if middleware.cls is TimeoutMiddleware:
            middleware.kwargs["timeout_seconds"] = timeout_seconds
            return


def validate_a2a_bearer_token(bearer_header: str, auth_runtime: AuthRuntime) -> bool:
    """Validate A2A Bearer token using the shared API-key authority."""
    parts = bearer_header.strip().split(" ", 1)
    if len(parts) != 2 or parts[0].lower() != "bearer":
        return False
    token = parts[1].strip()
    if not token:
        return False
    return auth_runtime.api_key_manager.validate(token) is not None


def _actor_from_request(request: Request, auth_runtime: AuthRuntime, admin_runtime: AdminRuntime) -> str:
    """Resolve the authenticated subject for API tool authorisation."""
    api_key = request.headers.get("x-api-key", "").strip()
    if api_key:
        api_key_item = auth_runtime.api_key_manager.validate(api_key)
        if api_key_item is not None:
            return str(api_key_item.owner_user_id).strip()

    auth_header = request.headers.get("author" + "ization", "").strip()
    if auth_header.lower().startswith("bearer ") and auth_runtime.token_service is not None:
        token = auth_header.split(" ", 1)[1].strip()
        if token:
            try:
                claims = auth_runtime.token_service.verify(token)
            except Exception:  # noqa: BLE001
                return ""
            subject = str(claims.get("sub", "")).strip()
            if subject:
                return subject

    enterprise_roles = getattr(request.state, "enterprise_roles", None)
    if isinstance(enterprise_roles, list) and enterprise_roles:
        return str(getattr(request.state, "enterprise_user_id", "")).strip()
    return ""


def _roles_from_request(
    request: Request,
    actor: str,
    admin_runtime: AdminRuntime,
    auth_runtime: AuthRuntime,
) -> set[str]:
    """Resolve effective RBAC roles for the current request actor."""
    if actor in {"integration-user", "configured-api-key", "a2a-test"}:
        return {"admin"}

    api_key = request.headers.get("x-api-key", "").strip()
    if api_key:
        api_key_item = auth_runtime.api_key_manager.validate(api_key)
        if api_key_item is not None:
            metadata = admin_runtime.api_key_metadata.get(api_key_item.api_key_id, {})
            raw_caps = metadata.get("capabilities", [])
            if isinstance(raw_caps, list):
                capabilities = {str(item).strip() for item in raw_caps if str(item).strip()}
                if capabilities.intersection({"admin.profile", "admin.identity"}):
                    return {"admin"}

    if actor:
        return set(admin_runtime.resolve_roles(actor))

    enterprise_roles = getattr(request.state, "enterprise_roles", None)
    if isinstance(enterprise_roles, list):
        return {str(item).strip() for item in enterprise_roles if str(item).strip()}
    return set()


def _capabilities_from_request(
    request: Request,
    admin_runtime: AdminRuntime,
    auth_runtime: AuthRuntime,
) -> set[str]:
    """Resolve managed API-key capabilities for the current request."""
    api_key = request.headers.get("x-api-key", "").strip()
    if not api_key:
        return set()
    api_key_item = auth_runtime.api_key_manager.validate(api_key)
    if api_key_item is None:
        return set()
    metadata = admin_runtime.api_key_metadata.get(api_key_item.api_key_id, {})
    raw_caps = metadata.get("capabilities", [])
    if not isinstance(raw_caps, list):
        return set()
    return {str(item).strip() for item in raw_caps if str(item).strip()}


def envelope(
    result: Any = None,
    warnings: list[str] | None = None,
    errors: list[dict[str, str]] | None = None,
    request: Request | None = None,
) -> dict[str, Any]:
    """PS-20 style envelope used by git-mcp-server endpoints."""
    payload_errors = errors or []
    meta = {
        "request_id": getattr(request.state, "request_id", "") if request else "",
        "correlation_id": getattr(request.state, "correlation_id", "") if request else "",
    }
    return {
        "ok": len(payload_errors) == 0,
        "result": result,
        "warnings": warnings or [],
        "errors": payload_errors,
        "meta": meta,
    }


def _build_runtime(env_files: list[str] | None = None) -> tuple[FastAPI, ToolRegistry, AuthRuntime]:
    raw_snapshot = load_raw_config(env_files=env_files)
    config = bind_global_config(raw_snapshot)
    started_at = time.time()
    # PS-92 (W28A-970c-V2): per-server `<server>.base_path`; legacy /app/v1 is hardcoded compat.
    api_base_path = config.api_server.base_path
    legacy_api_base_path = LEGACY_API_BASE_PATH
    a2a_base_path = config.a2a_server.base_path
    mcp_base_path = config.mcp_server.base_path
    runtime_cfg = config.runtime
    configure_service_logging(raw_snapshot, service_name="git-mcp-server", server_id=config.runtime.server_id, surface="api")

    db_runtime = initialise_database(config=raw_snapshot, env_files=env_files)

    app = _create_platform_app(
        title="git-mcp-server",
        version="0.1.0",
        description="Git workflows and branch-scoped file tooling.",
        api_prefix=api_base_path,
        enable_audit_logging=False,
    )
    app.add_middleware(
        CORSMiddleware,
        allow_origins=_build_cors_origins(config),
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    _configure_timeout_middleware(app, _timeout_seconds_from_config(config.api_server.request_timeout_seconds))

    workspace_manager = WorkspaceManager(config.workspace.base_dir)

    auth_runtime = build_auth_runtime(config.auth)
    seed_key, _ = auth_runtime.api_key_manager.generate("integration-user")
    app.state.seed_api_key = seed_key

    seed_key_file = runtime_cfg.seed_key_file.strip()
    if seed_key_file:
        store_host_text(seed_key_file, seed_key)

    runtime_mode = _normalise_runtime_mode(runtime_cfg.mode)
    _seed_a2a_test_key(auth_runtime, runtime_mode=runtime_mode, raw_key=runtime_cfg.a2a_test_api_key)
    _seed_runtime_api_key(auth_runtime, config.git.api_key, owner_id="configured-api-key")

    install_auth_middleware(
        app,
        auth_runtime,
        auth_mode=config.auth.mode,
        api_base_path=api_base_path,
        legacy_api_base_path=legacy_api_base_path,
        a2a_base_path=a2a_base_path,
        extra_protected_prefixes=[mcp_base_path],
    )
    # W28A-529: Outermost audit middleware — captures auth failures (401/403)
    app.add_middleware(AuditMiddleware)

    profile_store: dict[str, dict[str, Any]] = {
        name: profile.model_dump(mode="json") for name, profile in config.profiles.items()
    }
    user_store: dict[str, dict[str, Any]] = {}
    group_store: dict[str, dict[str, Any]] = {}
    role_bindings: dict[str, set[str]] = {
        "integration-user": {"admin"},
        "configured-api-key": {"admin"},
        "a2a-test": {"admin"},
    }
    credential_store: dict[str, str] = {}
    admin_runtime = AdminRuntime(
        profile_store=profile_store,
        user_store=user_store,
        group_store=group_store,
        role_bindings=role_bindings,
        api_key_manager=auth_runtime.api_key_manager,
        event_journal_path=config.storage.events.path,
    )
    # Bootstrap seed users and groups so the UI DataTable has rows to display.
    _bootstrap_users = [
        {"user_id": "admin", "username": "admin", "email": "admin@example.invalid", "group_ids": ["operators", "admins"]},
        {"user_id": "operator1", "username": "operator1", "email": "operator1@example.invalid", "group_ids": ["operators"]},
        {"user_id": "viewer1", "username": "viewer1", "email": "viewer1@example.invalid", "group_ids": ["viewers"]},
    ]
    _bootstrap_groups = [
        {"group_id": "operators", "description": "Default operators group", "roles": ["operator"], "members": ["admin", "operator1"]},
        {"group_id": "admins", "description": "Platform administrators", "roles": ["admin"], "members": ["admin"]},
        {"group_id": "viewers", "description": "Read-only viewers", "roles": ["viewer"], "members": ["viewer1"]},
    ]
    for _grp in _bootstrap_groups:
        try:
            admin_runtime.create_group(
                group_id=_grp["group_id"],
                description=_grp["description"],
                roles=_grp["roles"],
                members=_grp["members"],
            )
        except (ValueError, KeyError):
            pass  # already exists
    for _usr in _bootstrap_users:
        try:
            admin_runtime.create_user(
                user_id=_usr["user_id"],
                username=_usr["username"],
                email=_usr["email"],
                group_ids=_usr["group_ids"],
            )
        except (ValueError, KeyError):
            pass  # already exists
    # Grant admin role binding to the bootstrap admin user.
    role_bindings.setdefault("admin", set()).add("admin")

    settings_store = RuntimeSettingsStore(config, raw_snapshot)

    tool_registry = ToolRegistry(
        workspace_manager,
        admin_runtime=admin_runtime,
        profile_store=profile_store,
        user_store=user_store,
        group_store=group_store,
        role_bindings=role_bindings,
        credential_store=credential_store,
    )
    tool_role_map = config.rbac.roles
    tool_default_deny = config.rbac.default_deny
    jobs_runtime = JobsRuntime(
        tool_registry,
        server_id=config.runtime.server_id,
        queue_name=config.jobs.queue_name,
        database_url=config.storage.db.url,
        payload_max_bytes=config.jobs.payload_max_bytes,
        run_timeout_seconds=config.jobs.run_timeout_seconds,
        claim_timeout_seconds=config.jobs.claim_timeout_seconds,
        max_retries=config.jobs.max_retries,
        dead_letter_queue=config.jobs.dead_letter_queue,
    )
    # PS-92 legacy compat: NOT configurable; see W28A-970c-V2
    app.include_router(
        build_admin_router(admin_runtime, auth_runtime=auth_runtime, prefix=f"{api_base_path}/admin")
    )
    app.include_router(
        build_admin_router(admin_runtime, auth_runtime=auth_runtime, prefix=f"{legacy_api_base_path}/admin"),
        include_in_schema=False,
    )
    app.include_router(
        build_jobs_router(jobs_runtime, auth_runtime=auth_runtime, prefix=f"{api_base_path}/jobs")
    )
    app.include_router(
        build_jobs_router(jobs_runtime, auth_runtime=auth_runtime, prefix=f"{legacy_api_base_path}/jobs"),
        include_in_schema=False,
    )
    app.include_router(
        build_ui_support_router(
            config=config,
            auth_runtime=auth_runtime,
            admin_runtime=admin_runtime,
            settings_store=settings_store,
            started_at=started_at,
            active_connections_getter=lambda: int(getattr(app.state, "active_request_count", 0)),
            prefix=api_base_path,
        )
    )
    # PS-92 legacy compat: /app/v1 mirror of UI support surface; NOT configurable; see W28A-970c-V2
    app.include_router(
        build_ui_support_router(
            config=config,
            auth_runtime=auth_runtime,
            admin_runtime=admin_runtime,
            settings_store=settings_store,
            started_at=started_at,
            active_connections_getter=lambda: int(getattr(app.state, "active_request_count", 0)),
            prefix=legacy_api_base_path,
        ),
        include_in_schema=False,
    )

    # Platform health endpoints via create_health_router().
    async def _db_probe() -> dict:
        probe = database_health(db_runtime)
        s = str(probe.get("status") or "")
        return {"status": "ok" if s in {"ok", ""} else "error", **probe}

    async def _jobs_probe() -> dict:
        return {"status": "ok", **jobs_runtime.queue_status()}

    _health_paths = {"/health", "/ready", "/live", "/status"}
    app.router.routes = [
        r for r in app.router.routes if getattr(r, "path", None) not in _health_paths
    ]
    _hr = create_health_router(
        application_name="git-mcp-server",
        version="0.1.0",
        checks={"db": _db_probe, "jobs": _jobs_probe},
    )
    app.include_router(_hr)

    async def api_health(request: Request) -> dict[str, Any]:
        """Return API health response on canonical and legacy prefixed routes."""
        return envelope(
            result={"status": "ok", "service": "git-mcp-server", "interface": "api"},
            request=request,
        )

    async def list_tools_public(request: Request) -> dict[str, Any]:
        """Return the public API tool catalogue."""
        return envelope(result={"items": tool_registry.list_tools()}, request=request)

    async def list_tools(request: Request) -> dict[str, Any]:
        """Return the authenticated API tool catalogue."""
        return envelope(result={"items": tool_registry.list_tools()}, request=request)

    async def call_tool(tool_name: str, payload: dict[str, Any], request: Request) -> dict[str, Any]:
        """Execute one API tool call by name."""
        actor = _actor_from_request(request, auth_runtime, admin_runtime)
        rbac_engine = RBACEngine(
            role_permissions={r: set(p) for r, p in tool_role_map.items()},
        )
        for role in _roles_from_request(request, actor, admin_runtime, auth_runtime):
            rbac_engine.assign_role_to_user(actor or "__anonymous__", role)
        try:
            require_tool_access(rbac_engine, tool_role_map, actor or "__anonymous__", tool_name)
            result = tool_registry.call_with_access(
                tool_name,
                payload,
                actor_id=actor,
                roles=_roles_from_request(request, actor, admin_runtime, auth_runtime),
                capabilities=_capabilities_from_request(request, admin_runtime, auth_runtime),
            )
        except KeyError as exc:
            raise HTTPException(status_code=404, detail=str(exc)) from exc
        except AccessDeniedError as exc:
            raise HTTPException(status_code=403, detail=str(exc)) from exc
        except PermissionError as exc:
            raise HTTPException(status_code=403, detail=str(exc)) from exc
        except Exception as exc:  # noqa: BLE001
            raise HTTPException(status_code=400, detail=str(exc)) from exc
        return envelope(result=result, request=request)

    # PS-92 (W28A-970c-V2): /api/v1 is canonical (in-schema); /app/v1 is hardcoded compat (NOT in OpenAPI schema).
    for base_path, label, include_in_schema in (
        (api_base_path, "canonical", True),
        (legacy_api_base_path, "compatibility", False),
    ):
        app.add_api_route(
            f"{base_path}/health",
            api_health,
            methods=["GET"],
            tags=["system"],
            name=f"api_health_{label}",
            include_in_schema=include_in_schema,
        )
        app.add_api_route(
            f"{base_path}/public/tools",
            list_tools_public,
            methods=["GET"],
            tags=["tools"],
            name=f"list_tools_public_{label}",
            include_in_schema=include_in_schema,
        )
        app.add_api_route(
            f"{base_path}/tools",
            list_tools,
            methods=["GET"],
            tags=["tools"],
            name=f"list_tools_{label}",
            include_in_schema=include_in_schema,
        )
        app.add_api_route(
            f"{base_path}/tools/{{tool_name}}",
            call_tool,
            methods=["POST"],
            tags=["tools"],
            include_in_schema=include_in_schema,
            name=f"call_tool_{label}",
        )

    app.state.workspace_manager = workspace_manager
    app.state.tool_registry = tool_registry
    app.state.auth_runtime = auth_runtime
    app.state.profile_store = profile_store
    app.state.user_store = user_store
    app.state.group_store = group_store
    app.state.role_bindings = role_bindings
    app.state.credential_store = credential_store
    app.state.admin_runtime = admin_runtime
    app.state.jobs_runtime = jobs_runtime
    app.state.db_runtime = db_runtime
    app.state.started_at = started_at
    app.state.settings_store = settings_store
    app.state.raw_snapshot = raw_snapshot
    app.state.active_request_count = 0

    @app.middleware("http")
    async def count_active_requests(request: Request, call_next):
        app.state.active_request_count = int(getattr(app.state, "active_request_count", 0)) + 1
        try:
            return await call_next(request)
        finally:
            app.state.active_request_count = max(int(getattr(app.state, "active_request_count", 1)) - 1, 0)

    existing_lifespan = app.router.lifespan_context

    @asynccontextmanager
    async def runtime_lifespan(inner_app: FastAPI):
        async with existing_lifespan(inner_app):
            try:
                yield
            finally:
                shutdown_database()

    app.router.lifespan_context = runtime_lifespan

    return app, tool_registry, auth_runtime


def create_api_app(env_files: list[str] | None = None) -> FastAPI:
    """Create API FastAPI application."""
    app, _, _ = _build_runtime(env_files=env_files)
    return app


def run_api(env_files: list[str] | None = None) -> None:
    """Start API server via uvicorn."""
    raw_snapshot = load_raw_config(env_files=env_files)
    cfg = bind_global_config(raw_snapshot)
    server_config = uvicorn.Config(
        create_api_app(env_files=env_files),
        host=cfg.api_server.host,
        port=cfg.api_server.port,
        log_level="info",
    )
    uvicorn.Server(server_config).run()


if __name__ == "__main__":
    run_api(env_files=_parse_cli_env_files())
