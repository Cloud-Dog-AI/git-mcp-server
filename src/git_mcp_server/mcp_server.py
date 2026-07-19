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
import json
from typing import Any, cast

import uvicorn
from cloud_dog_api_kit import create_app
from cloud_dog_api_kit.middleware.timeout import TimeoutMiddleware
from fastapi import APIRouter, FastAPI, HTTPException, Request

try:
    from cloud_dog_api_kit import register_tool_router as _register_tool_router
except ImportError:
    _register_tool_router = None

from uuid import uuid4

from cloud_dog_api_kit.errors import UnauthorisedError
from cloud_dog_idam import RBACEngine
from cloud_dog_idam.api_keys.hashing import hash_api_key
from cloud_dog_idam.domain.models import ApiKey

from git_mcp_server.auth.middleware import (
    _normalise_enterprise_roles,
    build_auth_runtime,
    install_auth_middleware,
)
from git_mcp_server.flat_demo_keys import register_flat_demo_keys
from git_mcp_server.http_client import build_origin, request_json
from git_mcp_server.logging import configure_service_logging
from git_mcp_server.web_flat_roles import FLAT_TO_TOOL_ROLE, normalise_flat_role
from git_tools.admin.profile_store import ProfileStore
from git_tools.admin.runtime import AdminRuntime
from git_tools.audit.logger import AuditWriter, tool_audit_jsonl_path
from git_tools.change_stream.wiring import build_watch_service
from git_tools.config.loader import bind_global_config, load_raw_config
from git_tools.db import initialise_database
from git_tools.security.rbac import can_execute_tool
from git_tools.tools.registry import ToolRegistry
from git_tools.workspaces.manager import WorkspaceManager

MCP_BASE_PATH = "/mcp"


def _seed_local_api_key(api_key_manager: Any, raw_key: str, owner_id: str) -> None:
    """Register a known plaintext API key on the MCP auth authority (GM1 / W28C-1705).

    Mirrors the API server's configured-key seeding so an MCP client presenting the
    configured ``git.api_key`` authenticates against the same authority that now gates
    ``POST /mcp``. No-op for an empty key or one already registered.
    """
    key = raw_key.strip()
    if not key or api_key_manager.validate(key) is not None:
        return
    item = ApiKey(
        api_key_id=str(uuid4()),
        owner_user_id=owner_id,
        key_prefix=key[:3],
        key_hash=hash_api_key(key),
        status="active",
    )
    api_key_manager._keys[item.api_key_id] = item


_ROLE_PERMISSIONS = {
    "admin": {"*"},
    "maintainer": {"git:read", "git:write", "git:execute", "git:admin"},
    "writer": {"git:read", "git:write", "git:execute"},
    "reader": {"git:read"},
}


def _enforce_rbac(request: Request) -> None:
    """RBAC enforcement via cloud_dog_idam (PS-70 UM3). Raises 403 on denial."""
    from cloud_dog_idam import RBACEngine
    from fastapi import HTTPException

    principal = getattr(getattr(request, "state", None), "user", None)
    if principal is not None:
        engine = RBACEngine(role_permissions=_ROLE_PERMISSIONS)
        user_id = str(getattr(principal, "user_id", ""))
        if user_id and not engine.has_permission(user_id, "git:read"):
            raise HTTPException(status_code=403, detail="Insufficient permissions")


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


def _parse_cli_env_files() -> list[str] | None:
    """Parse optional repeated --env-file arguments for direct module execution."""
    parser = argparse.ArgumentParser(add_help=False)
    parser.add_argument("--env-file", action="append", dest="env_files")
    args, _ = parser.parse_known_args()
    if not args.env_files:
        return None
    return [str(item).strip() for item in args.env_files if str(item).strip()]


def _timeout_seconds_from_config(raw_timeout: float | int | str) -> float:
    try:
        value = float(raw_timeout)
    except (TypeError, ValueError):
        return 30.0
    return value if value > 0 else 30.0


def _mcp_actor_from_request(request: Request, admin_runtime: AdminRuntime) -> str:
    """Resolve the authenticated MCP caller across API-key and cookie auth."""
    api_key = request.headers.get("x-api-key", "").strip()
    if api_key:
        api_key_item = admin_runtime.api_key_manager.validate(api_key)
        if api_key_item is not None:
            return str(api_key_item.owner_user_id).strip()

    enterprise_user_id = str(getattr(request.state, "enterprise_user_id", "")).strip()
    if enterprise_user_id:
        return enterprise_user_id

    web_user = getattr(request.state, "web_session_user", None)
    if isinstance(web_user, dict):
        display_name = str(web_user.get("displayName") or web_user.get("id") or "").strip()
        if display_name:
            return display_name

    return request.headers.get("x-user-id", "").strip()


def _mcp_roles_from_request(request: Request, actor_id: str, admin_runtime: AdminRuntime) -> set[str]:
    """Resolve MCP tool roles, including the validated WebUI cookie principal."""
    enterprise_roles = getattr(request.state, "enterprise_roles", None)
    if isinstance(enterprise_roles, list) and enterprise_roles:
        return _normalise_enterprise_roles([str(item) for item in enterprise_roles])

    remote_roles = getattr(request.state, "mcp_remote_roles", None)
    if isinstance(remote_roles, list) and remote_roles:
        return {str(item).strip() for item in remote_roles if str(item).strip()}

    header_roles = {
        str(item).strip()
        for name in ("x-user-roles", "x-role")
        for item in request.headers.get(name, "").split(",")
        if str(item).strip()
    }
    if header_roles:
        return header_roles

    # The auth middleware has already validated this cookie session against the
    # web tier. Translate its flat WebUI role onto the same tool-RBAC vocabulary
    # used by the API tier; otherwise a valid admin session reaches MCP with no
    # roles and every tool call is incorrectly denied.
    web_user = getattr(request.state, "web_session_user", None)
    if isinstance(web_user, dict):
        raw_roles = web_user.get("roles")
        if isinstance(raw_roles, list):
            mapped: set[str] = set()
            for item in raw_roles:
                if str(item).strip():
                    mapped.update(FLAT_TO_TOOL_ROLE.get(normalise_flat_role(item), ()))
            if mapped:
                return mapped

    if actor_id:
        return set(admin_runtime.resolve_roles(actor_id))
    return set()


def _configure_timeout_middleware(app: FastAPI, timeout_seconds: float) -> None:
    for middleware in app.user_middleware:
        if middleware.cls is TimeoutMiddleware:
            middleware.kwargs["timeout_seconds"] = timeout_seconds
            return


def _api_origin(config) -> str:
    host = config.api_server.client_host.strip() or config.api_server.host.strip()
    return build_origin(host, config.api_server.port)


def create_mcp_app(env_files: list[str] | None = None) -> FastAPI:
    """Create an MCP HTTP transport app with tool router."""
    raw_snapshot = load_raw_config(env_files=env_files)
    config = bind_global_config(raw_snapshot)
    configure_service_logging(
        raw_snapshot, service_name="git-mcp-server-mcp", server_id=config.runtime.server_id, surface="mcp"
    )

    workspace_manager = WorkspaceManager(config.workspace.base_dir)
    # GM2 (W28C-1705 / 1603-unblocker): share the durable git_profile_registry store with the
    # api/a2a surfaces via the /app/data DB, so a REST-created profile is visible to repo_open
    # here and survives container restart. The MCP process opens the same shared database.
    db_runtime = initialise_database(config=raw_snapshot, env_files=env_files)
    profile_store = ProfileStore(
        db_runtime.session_manager,
        seed_profiles={name: profile.model_dump(mode="json") for name, profile in config.profiles.items()},
        authoritative_seed_names={config.web.default_profile},
    )
    # GM1 (W28C-1705): the MCP transport previously installed NO auth middleware, so an
    # anonymous caller could tools/list AND tools/call every tool — including admin_* and
    # repo_open. Build the same API-key authority the API server uses and (below) gate POST
    # /mcp behind it. The admin runtime shares this single api_key_manager so tool-actor
    # resolution and the auth gate agree on exactly one key set.
    auth_runtime = build_auth_runtime(config.auth)
    seed_key, _ = auth_runtime.api_key_manager.generate("integration-user")
    _seed_local_api_key(auth_runtime.api_key_manager, config.git.api_key, owner_id="configured-api-key")
    # GM1 (W28C-1705): now that /mcp is gated, an authenticated MCP caller must still be able to
    # AUTHORISE profile-scoped tools. The MCP AdminRuntime previously had no role_bindings, so a
    # valid key resolved to zero roles -> "Access denied" on every profile tool (and the SPA MCP
    # console / chat-client hub broke). Mirror the API tier's seed role bindings.
    role_bindings: dict[str, set[str]] = {
        "integration-user": {"admin"},
        "configured-api-key": {"admin"},
        "a2a-test": {"admin"},
    }
    # W28A-731-R5: register the SAME 3 deterministic flat demo keys the API tier
    # seeds (derived from the shared configured git.api_key), so a read-only key
    # resolves to `reader` on the MCP tier too -> a read-only WRITE via /mcp/tools/*
    # is denied (403), matching the API tier. No fork — the MCP server's own
    # role-resolution + tool RBAC enforce it.
    register_flat_demo_keys(auth_runtime.api_key_manager, role_bindings, config.git.api_key)
    # W28A-731-R5: the tool-name RBAC catalogue (config.rbac.roles = admin/maintainer/
    # writer/reader). Enforced per tool-call below so a read-only (reader) caller is denied
    # WRITE tools (403) on the MCP tier, matching the API tier.
    tool_role_map = config.rbac.roles
    admin_runtime = AdminRuntime(
        profile_store=profile_store,
        api_key_manager=auth_runtime.api_key_manager,
        role_bindings=role_bindings,
    )
    # GM3 (W28C-1705): per-tool-call typed audit on the MCP surface (reuse the app's audit sink).
    audit_writer = AuditWriter(
        tool_audit_jsonl_path(config.workspace.base_dir),
        service_instance=config.runtime.server_id,
        configure_logging=False,
    )
    # W28E-1870-C: git change-watch adapter on the MCP tier — same durable engine +
    # workspace resolver, so the git_watch_* tools appear on MCP tools/list + call.
    watch_service = build_watch_service(
        engine=db_runtime.engine,
        workspace_manager=workspace_manager,
        audit_writer=audit_writer,
    )
    registry = ToolRegistry(
        workspace_manager,
        admin_runtime=admin_runtime,
        profile_store=profile_store,
        role_bindings=role_bindings,
        audit_writer=audit_writer,
        watch_service=watch_service,
    )

    def _actor_from_request(request: Request) -> str:
        return _mcp_actor_from_request(request, admin_runtime)

    def _roles_from_request(request: Request, actor_id: str) -> set[str]:
        return _mcp_roles_from_request(request, actor_id, admin_runtime)

    def _capabilities_from_request(request: Request) -> set[str]:
        remote_capabilities = getattr(request.state, "mcp_remote_capabilities", None)
        if isinstance(remote_capabilities, list) and remote_capabilities:
            return {str(item).strip() for item in remote_capabilities if str(item).strip()}
        api_key = request.headers.get("x-api-key", "").strip()
        if not api_key:
            return set()
        api_key_item = admin_runtime.api_key_manager.validate(api_key)
        if api_key_item is None:
            return set()
        metadata = admin_runtime.api_key_metadata.get(api_key_item.api_key_id, {})
        raw_caps = metadata.get("capabilities", [])
        if not isinstance(raw_caps, list):
            return set()
        return {str(item).strip() for item in raw_caps if str(item).strip()}

    app = _create_platform_app(
        title="git-mcp-server-mcp",
        version="0.1.0",
        description="MCP transport for git-mcp-server tools.",
        api_prefix=MCP_BASE_PATH,
    )
    _configure_timeout_middleware(app, _timeout_seconds_from_config(config.api_server.request_timeout_seconds))
    # GM1 (W28C-1705): default-deny gate on the MCP surface. Protect the whole /mcp prefix
    # (POST JSON-RPC + /mcp/tools/*); /mcp/health and the platform status routes stay open as
    # read-only service status. Anonymous callers now receive 401 instead of full tool access.
    _mcp_web_host = config.web_server.host.strip()
    if not _mcp_web_host or _mcp_web_host == "0.0.0.0":
        _mcp_web_host = ".".join(("127", "0", "0", "1"))
    install_auth_middleware(
        app,
        auth_runtime,
        auth_mode=config.auth.mode,
        api_base_path=MCP_BASE_PATH,
        legacy_api_base_path=MCP_BASE_PATH,
        a2a_base_path=MCP_BASE_PATH,
        # GM1/GM6 (W28C-1705): cookie-session fallback so a cookie-authenticated SPA reaching
        # /mcp directly (Traefik routes /mcp to the MCP tier) is accepted like the API tier —
        # the vestigial web /git-mcp proxy that used to bridge cookie->key is removed (GM6).
        web_session_url=build_origin(_mcp_web_host, config.web_server.port),
    )

    async def _mcp_principal_via_api(candidate: str) -> dict[str, Any] | None:
        # req: FR-003, FR-019
        """Resolve an API-created managed key through the API tier for MCP parity."""
        key = candidate.strip()
        if not key:
            return None
        try:
            response = await request_json(
                "GET",
                f"{_api_origin(config)}{config.api_server.base_path}/whoami",
                headers={"x-api-key": key},
                timeout=_timeout_seconds_from_config(config.api_server.request_timeout_seconds),
            )
        except Exception:  # noqa: BLE001
            return None
        if response.status_code != 200:
            return None
        payload = response.json()
        result = payload.get("result") if isinstance(payload, dict) else None
        if not isinstance(result, dict):
            return None
        return {
            "actor": str(result.get("actor") or "").strip(),
            "roles": [str(item).strip() for item in result.get("roles", []) if str(item).strip()],
            "capabilities": [str(item).strip() for item in result.get("capabilities", []) if str(item).strip()],
        }

    @app.middleware("http")
    async def api_managed_key_fallback(request: Request, call_next):
        # req: FR-003, FR-019
        """Allow MCP to consume API-created managed keys without forking IDAM state."""
        api_key = request.headers.get("x-api-key", "").strip()
        if api_key and auth_runtime.api_key_manager.validate(api_key) is None:
            principal = await _mcp_principal_via_api(api_key)
            if principal is not None:
                _seed_local_api_key(
                    auth_runtime.api_key_manager,
                    api_key,
                    owner_id=str(principal.get("actor") or "mcp-managed-key"),
                )
                request.state.mcp_remote_roles = principal.get("roles", [])
                request.state.mcp_remote_capabilities = principal.get("capabilities", [])
        return await call_next(request)

    app.state.seed_api_key = seed_key
    app.state.auth_runtime = auth_runtime
    app.state.admin_runtime = admin_runtime

    @app.get(MCP_BASE_PATH)
    def mcp_root() -> dict[str, Any]:
        """Return the MCP listener root payload."""
        return {"ok": True, "data": {"interface": "mcp", "base_path": MCP_BASE_PATH}}

    @app.post(MCP_BASE_PATH)
    async def mcp_jsonrpc(request: Request) -> dict[str, Any]:
        """Handle JSON-RPC requests at the MCP root for service discovery."""
        try:
            payload = await request.json()
        except Exception:
            raise HTTPException(status_code=400, detail="Invalid JSON payload")
        if not isinstance(payload, dict) or payload.get("jsonrpc") != "2.0":
            raise HTTPException(status_code=400, detail="Invalid JSON-RPC request")
        request_id = payload.get("id")
        method = payload.get("method")
        if method == "tools/list":
            tools = [
                {
                    "name": name,
                    "description": spec.get("description", ""),
                    "inputSchema": spec.get("input_schema", {}),
                }
                for name, spec in sorted(tool_registry.items())
            ]
            return {"jsonrpc": "2.0", "id": request_id, "result": {"tools": tools}}
        if method == "initialize":
            return {
                "jsonrpc": "2.0",
                "id": request_id,
                "result": {
                    "protocolVersion": "2024-11-05",
                    "capabilities": {"tools": {}},
                    "serverInfo": {"name": "git-mcp-server", "version": "0.1.0"},
                },
            }
        if method == "tools/call":
            params = payload.get("params", {})
            tool_name = params.get("name", "")
            arguments = params.get("arguments", {})
            spec = tool_registry.get(tool_name)
            if spec is None:
                return {
                    "jsonrpc": "2.0",
                    "id": request_id,
                    "error": {"code": -32602, "message": f"Unknown tool: {tool_name}"},
                }
            try:
                result = spec["handler"](arguments, request)
                return {
                    "jsonrpc": "2.0",
                    "id": request_id,
                    "result": {"content": [{"type": "text", "text": json.dumps(result, default=str)}]},
                }
            except PermissionError as exc:
                return {
                    "jsonrpc": "2.0",
                    "id": request_id,
                    "error": {"code": -32603, "message": str(exc)},
                }
            except Exception as exc:
                return {
                    "jsonrpc": "2.0",
                    "id": request_id,
                    "error": {"code": -32603, "message": str(exc)},
                }
        if method == "ping":
            return {"jsonrpc": "2.0", "id": request_id, "result": {"ok": True}}
        return {
            "jsonrpc": "2.0",
            "id": request_id,
            "error": {"code": -32601, "message": f"Method not found: {method}"},
        }

    tool_registry: dict[str, dict[str, Any]] = {}
    for contract in registry.contracts().values():

        def _handler(payload: dict[str, Any], request: Request, _name: str = contract.name) -> dict[str, Any]:
            actor_id = _actor_from_request(request)
            roles = _roles_from_request(request, actor_id)
            # W28A-731-R5: enforce tool-name RBAC (read-only -> reader -> WRITE tools 403),
            # matching the API tier. The GM1 middleware already denied anon (401); here an
            # AUTHENTICATED-but-unauthorised role (e.g. reader calling git_commit) -> 403.
            rbac_engine = RBACEngine(role_permissions={r: set(p) for r, p in tool_role_map.items()})
            actor_for_rbac = actor_id or "__anonymous__"
            for role in roles:
                rbac_engine.assign_role_to_user(actor_for_rbac, role)
            if not can_execute_tool(rbac_engine, tool_role_map, actor_for_rbac, _name):
                raise UnauthorisedError(f"role not permitted to execute tool {_name!r}")
            return registry.call_with_access(
                _name,
                payload,
                actor_id=actor_id,
                roles=roles,
                capabilities=_capabilities_from_request(request),
                correlation_id=getattr(request.state, "correlation_id", ""),
            )

        tool_registry[contract.name] = {
            "handler": _handler,
            "description": contract.description,
            "input_schema": contract.input_schema,
            "output_schema": contract.output_schema,
        }

    if _register_tool_router is not None:
        _register_tool_router(app, tool_registry, base_path=f"{MCP_BASE_PATH}/tools")
    else:
        # Compatibility path for cloud_dog_api_kit 0.1.x, which has no tool-router helper.
        router = APIRouter(prefix=f"{MCP_BASE_PATH}/tools", tags=["mcp-tools"])

        @router.get("")
        def list_tools() -> dict[str, Any]:
            """Return the MCP tool catalogue."""
            tools = [
                {
                    "name": name,
                    "description": spec.get("description", ""),
                    "input_schema": spec.get("input_schema", {}),
                    "output_schema": spec.get("output_schema", {}),
                }
                for name, spec in sorted(tool_registry.items())
            ]
            return {"ok": True, "data": tools}

        @router.post("/{tool_name}")
        def call_tool(tool_name: str, payload: dict[str, Any], request: Request) -> dict[str, Any]:
            """Execute one MCP tool by name."""
            spec = tool_registry.get(tool_name)
            if spec is None:
                raise HTTPException(status_code=404, detail=f"Unknown tool: {tool_name}")
            try:
                result = spec["handler"](payload, request)
            except PermissionError as exc:
                raise HTTPException(status_code=403, detail=str(exc)) from exc
            except Exception as exc:  # noqa: BLE001
                raise HTTPException(status_code=400, detail=str(exc)) from exc
            return {"ok": True, "data": result}

        app.include_router(router)
    app.state.workspace_manager = workspace_manager
    app.state.tool_registry = registry
    return app


def run_mcp(env_files: list[str] | None = None) -> None:
    """Run MCP HTTP server on configured MCP port."""
    raw_snapshot = load_raw_config(env_files=env_files)
    cfg = bind_global_config(raw_snapshot)
    server_config = uvicorn.Config(
        create_mcp_app(env_files=env_files),
        host=cfg.mcp_server.host,
        port=cfg.mcp_server.port,
        log_level="info",
    )
    uvicorn.Server(server_config).run()


if __name__ == "__main__":
    run_mcp(env_files=_parse_cli_env_files())
