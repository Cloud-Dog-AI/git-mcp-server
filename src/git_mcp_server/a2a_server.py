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

import json
from typing import Any

import uvicorn
from cloud_dog_api_kit import create_health_router
from cloud_dog_api_kit.a2a.card import create_a2a_card_router, A2ASkill
from cloud_dog_storage import path_utils
from fastapi import FastAPI, HTTPException, Request, WebSocket, WebSocketDisconnect

from git_mcp_server.api_server import (
    _create_platform_app,
    _parse_cli_env_files,
    _timeout_seconds_from_config,
    envelope,
)
from git_mcp_server.http_client import build_origin, request_json
from git_mcp_server.logging import configure_service_logging
from git_tools.admin.runtime import ConfigEventHub
from git_tools.config.loader import bind_global_config, load_raw_config
from git_tools.tools.registry import ToolRegistry
from git_tools.workspaces.manager import WorkspaceManager


def _api_origin(config) -> str:
    host = config.api_server.client_host.strip() or config.api_server.host.strip()
    return build_origin(host, config.api_server.port)


async def _api_key_valid_via_api(config, candidate: str) -> bool:
    key = candidate.strip()
    if not key:
        return False
    try:
        response = await request_json(
            "GET",
            f"{_api_origin(config)}{config.api_server.base_path}/tools",
            headers={"x-api-key": key},
            timeout=_timeout_seconds_from_config(config.api_server.request_timeout_seconds),
        )
    except Exception:  # noqa: BLE001
        return False
    return response.status_code == 200


async def _a2a_request_authorised(request: Request, config) -> bool:
    header = request.headers.get("authorization", "").strip()
    parts = header.split(" ", 1)
    if len(parts) == 2 and parts[0].lower() == "bearer":
        return await _api_key_valid_via_api(config, parts[1])
    return False


async def _a2a_websocket_authorised(websocket: WebSocket, config) -> bool:
    auth_header = websocket.headers.get("authorization", "").strip()
    parts = auth_header.split(" ", 1)
    if len(parts) == 2 and parts[0].lower() == "bearer":
        if await _api_key_valid_via_api(config, parts[1]):
            return True
    query_token = websocket.query_params.get("token", "").strip()
    return await _api_key_valid_via_api(config, query_token)


def create_a2a_app(env_files: list[str] | None = None) -> FastAPI:
    """Create the standalone A2A server."""
    raw_snapshot = load_raw_config(env_files=env_files)
    config = bind_global_config(raw_snapshot)
    configure_service_logging(raw_snapshot, service_name="git-mcp-server-a2a", server_id=config.runtime.server_id, surface="a2a")

    app = _create_platform_app(
        title="git-mcp-server-a2a",
        version="0.1.0",
        description="Standalone A2A interface for git-mcp-server.",
    )
    event_hub = ConfigEventHub(journal_path=config.storage.events.path)

    @app.get(config.a2a_server.base_path, tags=["a2a"])
    async def a2a_root(request: Request) -> dict:
        """Return a minimal A2A root payload."""
        return envelope(
            result={"status": "ok", "service": "git-mcp-server", "interface": "a2a"},
            request=request,
        )

    @app.get(f"{config.a2a_server.base_path}/health", tags=["a2a"])
    async def a2a_health(request: Request) -> dict:
        """Return the authenticated A2A health contract on the routed base path."""
        if not await _a2a_request_authorised(request, config):
            raise HTTPException(status_code=401, detail="Unauthorised")
        return envelope(
            result={"status": "ok", "service": "git-mcp-server", "interface": "a2a"},
            request=request,
        )

    # Platform health via create_health_router().
    _health_paths = {"/health", "/ready", "/live", "/status"}
    app.router.routes = [
        r for r in app.router.routes if getattr(r, "path", None) not in _health_paths
    ]
    app.include_router(create_health_router(
        application_name="git-mcp-server",
        version="0.1.0",
    ))

    @app.websocket(f"{config.a2a_server.base_path}/events/config")
    async def a2a_config_events(websocket: WebSocket) -> None:
        """Requirements: CFG-06, CFG-11."""
        if not await _a2a_websocket_authorised(websocket, config):
            await websocket.close(code=4401)
            return
        await websocket.accept()
        subscription = event_hub.subscribe()
        try:
            while True:
                event = await subscription.get()
                await websocket.send_json(event)
        except WebSocketDisconnect:
            return
        finally:
            event_hub.unsubscribe(subscription)

    # Build a ToolRegistry so A2A skill handlers can call real git tool logic.
    workspace_root = path_utils.as_path(config.workspace.base_dir).resolve()
    workspace_root.mkdir(parents=True, exist_ok=True)
    workspace_manager = WorkspaceManager(workspace_root)
    tool_registry = ToolRegistry(workspace_manager)

    def _parse_a2a_input(text: str) -> dict[str, Any]:
        """Parse JSON input text or return a minimal dict from plain text."""
        text = text.strip()
        if text.startswith("{"):
            try:
                return json.loads(text)
            except json.JSONDecodeError:
                pass
        return {"path": text} if text else {}

    def _handle_repo_access(text: str) -> Any:
        """Open a git repository via the tool registry."""
        payload = _parse_a2a_input(text)
        if not payload.get("path") and text.strip() and not text.strip().startswith("{"):
            payload["path"] = text.strip()
        return tool_registry.call("repo_open", payload)

    def _handle_git_status(text: str) -> Any:
        """Get git status via the tool registry.

        When no workspace_id is supplied, automatically selects the first
        available persistent workspace restored by WorkspaceManager so that
        callers do not need to know workspace IDs upfront.
        """
        payload = _parse_a2a_input(text)
        # Auto-resolve workspace_id when the caller omits it.
        if not payload.get("workspace_id"):
            available = list(workspace_manager._workspaces.keys())
            if not available:
                return {
                    "error": "No workspaces available",
                    "detail": "No persistent workspaces found. Use repo_open to create one.",
                    "workspaces": [],
                }
            payload["workspace_id"] = available[0]
        try:
            return tool_registry.call("git_status", payload)
        except (KeyError, ValueError, RuntimeError) as exc:
            msg = str(exc).lower()
            if "workspace" in msg or "repo" in msg or "not open" in msg:
                return {"error": "No active workspace. Use repo_open first.", "detail": str(exc)}
            raise

    def _handle_file_write(text: str) -> Any:
        """Write a file via the tool registry."""
        payload = _parse_a2a_input(text)
        return tool_registry.call("file_write", payload)

    def _handle_git_commit(text: str) -> Any:
        """Commit staged changes via the tool registry."""
        payload = _parse_a2a_input(text)
        return tool_registry.call("git_commit", payload)

    # A2A agent card and task submission router
    _a2a_skills = [
        A2ASkill(id="repo_open", name="Repo Open", description="Open a git repository for operations", handler=_handle_repo_access),
        A2ASkill(id="git_status", name="Git Status", description="Get the current status of a git repository", handler=_handle_git_status),
        A2ASkill(id="file_write", name="File Write", description="Write content to a file in the repository", handler=_handle_file_write),
        A2ASkill(id="git_commit", name="Git Commit", description="Commit staged changes in the repository", handler=_handle_git_commit),
    ]
    _a2a_card_router = create_a2a_card_router(
        name="git-mcp",
        description="Git MCP A2A server for repository operations and config events",
        skills=_a2a_skills,
    )
    app.include_router(_a2a_card_router)

    return app


def run_a2a(env_files: list[str] | None = None) -> None:
    """Start the standalone A2A server via uvicorn."""
    raw_snapshot = load_raw_config(env_files=env_files)
    cfg = bind_global_config(raw_snapshot)
    server_config = uvicorn.Config(
        create_a2a_app(env_files=env_files),
        host=cfg.a2a_server.host,
        port=cfg.a2a_server.port,
        log_level="info",
    )
    uvicorn.Server(server_config).run()


if __name__ == "__main__":
    run_a2a(env_files=_parse_cli_env_files())
# W28A-565 fix 1775032263
