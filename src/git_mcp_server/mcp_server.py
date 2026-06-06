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

from git_tools.admin.runtime import AdminRuntime
from git_tools.config.loader import bind_global_config, load_raw_config
from git_mcp_server.auth.middleware import _normalise_enterprise_roles
from git_mcp_server.logging import configure_service_logging
from git_tools.tools.registry import ToolRegistry
from git_tools.workspaces.manager import WorkspaceManager

MCP_BASE_PATH = "/mcp"


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


def _configure_timeout_middleware(app: FastAPI, timeout_seconds: float) -> None:
    for middleware in app.user_middleware:
        if middleware.cls is TimeoutMiddleware:
            middleware.kwargs["timeout_seconds"] = timeout_seconds
            return


def create_mcp_app(env_files: list[str] | None = None) -> FastAPI:
    """Create an MCP HTTP transport app with tool router."""
    raw_snapshot = load_raw_config(env_files=env_files)
    config = bind_global_config(raw_snapshot)
    configure_service_logging(raw_snapshot, service_name="git-mcp-server-mcp", server_id=config.runtime.server_id, surface="mcp")

    workspace_manager = WorkspaceManager(config.workspace.base_dir)
    profile_store: dict[str, dict[str, Any]] = {
        name: profile.model_dump(mode="json") for name, profile in config.profiles.items()
    }
    admin_runtime = AdminRuntime(profile_store=profile_store)
    registry = ToolRegistry(workspace_manager, admin_runtime=admin_runtime, profile_store=profile_store)

    def _actor_from_request(request: Request) -> str:
        api_key = request.headers.get("x-api-key", "").strip()
        if api_key:
            api_key_item = admin_runtime.api_key_manager.validate(api_key)
            if api_key_item is not None:
                return str(api_key_item.owner_user_id).strip()
        enterprise_user_id = str(getattr(request.state, "enterprise_user_id", "")).strip()
        if enterprise_user_id:
            return enterprise_user_id
        return request.headers.get("x-user-id", "").strip()

    def _roles_from_request(request: Request, actor_id: str) -> set[str]:
        enterprise_roles = getattr(request.state, "enterprise_roles", None)
        if isinstance(enterprise_roles, list) and enterprise_roles:
            return _normalise_enterprise_roles([str(item) for item in enterprise_roles])
        header_roles = {
            str(item).strip()
            for name in ("x-user-roles", "x-role")
            for item in request.headers.get(name, "").split(",")
            if str(item).strip()
        }
        if header_roles:
            return header_roles
        if actor_id:
            return set(admin_runtime.resolve_roles(actor_id))
        return set()

    def _capabilities_from_request(request: Request) -> set[str]:
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
            return registry.call_with_access(
                _name,
                payload,
                actor_id=actor_id,
                roles=_roles_from_request(request, actor_id),
                capabilities=_capabilities_from_request(request),
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
