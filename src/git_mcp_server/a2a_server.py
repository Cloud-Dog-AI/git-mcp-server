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
from uuid import uuid4

import uvicorn
from cloud_dog_api_kit import create_health_router
from cloud_dog_api_kit.a2a.card import create_a2a_card_router, A2ASkill
from cloud_dog_storage import path_utils
from fastapi import FastAPI, HTTPException, Request, WebSocket, WebSocketDisconnect
from fastapi.responses import JSONResponse

from git_mcp_server.api_server import (
    _create_platform_app,
    _parse_cli_env_files,
    _timeout_seconds_from_config,
    envelope,
)
from git_mcp_server.http_client import build_origin, request_json
from git_mcp_server.logging import configure_service_logging
from git_tools.admin.runtime import ConfigEventHub
from git_tools.change_stream.wiring import build_watch_service
from git_tools.config.loader import bind_global_config, load_raw_config
from git_tools.admin.profile_store import ProfileStore
from git_tools.audit.logger import AuditWriter, tool_audit_jsonl_path
from git_tools.db import initialise_database
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


async def _a2a_principal_via_api(config, candidate: str) -> dict[str, Any] | None:
    # req: FR-004, FR-019
    """Resolve an A2A bearer API key through the API tier's IDAM authority."""
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
        "capabilities": [
            str(item).strip() for item in result.get("capabilities", []) if str(item).strip()
        ],
    }


async def _a2a_principal_from_request(request: Request, config) -> dict[str, Any] | None:
    # req: FR-004, FR-019
    """Resolve the authenticated A2A task principal from a bearer API key."""
    header = request.headers.get("authorization", "").strip()
    parts = header.split(" ", 1)
    if len(parts) != 2 or parts[0].lower() != "bearer":
        return None
    return await _a2a_principal_via_api(config, parts[1])


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

    # W28E-1870-C: platform change-stream broadcaster (PS-102 §5.2). The common
    # make_broadcast_hook maps each emitted ChangeEvent onto a ConfigChangeEvent
    # and publishes it here for live SSE fan-out — no bespoke broadcaster.
    _change_stream_broadcaster: Any = None
    with __import__("contextlib").suppress(Exception):
        from cloud_dog_api_kit.a2a.events import InMemoryEventBroadcaster

        _change_stream_broadcaster = InMemoryEventBroadcaster()

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

    # GM5 (W28C-1705, OPT-B): /a2a/events + /a2a/events/stream were advertised by an older
    # topology but never implemented (always-404). The agent-card already declares streaming:
    # false and no longer lists them; return an explicit 410 Gone (not an ambiguous 404) so any
    # client still polling gets a clear signal. Per-operation observability is the GM3 audit log
    # (cloud_dog_logging.audit_schema); config-change events remain on /a2a/events/config (WS).
    async def _a2a_events_gone() -> None:
        raise HTTPException(
            status_code=410,
            detail=(
                "The /a2a/events SSE stream is not implemented on git-mcp. Per-operation "
                "observability is the audit log (cloud_dog_logging.audit_schema); config-change "
                "events are on the /a2a/events/config websocket."
            ),
        )

    # Register at BOTH the configured base_path and the reverse-proxy strip-prefixed path
    # strips /a2a so the a2a tier actually receives /events; tests/local hit /a2a/events directly.
    _events_paths = [
        f"{config.a2a_server.base_path}/events",
        f"{config.a2a_server.base_path}/events/stream",
        "/events",
        "/events/stream",
    ]
    for _i, _events_path in enumerate(dict.fromkeys(_events_paths)):
        app.add_api_route(
            _events_path,
            _a2a_events_gone,
            methods=["GET"],
            include_in_schema=False,
            name=f"a2a_events_gone_{_i}",
        )

    # Build a ToolRegistry so A2A skill handlers can call real git tool logic.
    workspace_root = path_utils.as_path(config.workspace.base_dir).resolve()
    workspace_root.mkdir(parents=True, exist_ok=True)
    workspace_manager = WorkspaceManager(workspace_root)
    # GM2 (W28C-1705 / 1603-unblocker): resolve profiles from the same durable
    # git_profile_registry store the api/mcp surfaces use (shared /app/data DB), so A2A skill
    # handlers see REST-/MCP-created profiles and they survive container restart.
    db_runtime = initialise_database(config=raw_snapshot, env_files=env_files)
    profile_store = ProfileStore(
        db_runtime.session_manager,
        seed_profiles={
            name: profile.model_dump(mode="json") for name, profile in config.profiles.items()
        },
    )
    # GM3 (W28C-1705): per-tool-call typed audit on the A2A surface (reuse the app's audit sink).
    audit_writer = AuditWriter(tool_audit_jsonl_path(config.workspace.base_dir), service_instance=config.runtime.server_id, configure_logging=False)
    # W28E-1870-C: git change-watch adapter on the A2A surface, with the platform
    # a2a.events broadcaster wired for live change fan-out (PS-102 §5.2). The
    # git_watch_* tools surface as A2A agent-card skills + task dispatch.
    watch_service = build_watch_service(
        engine=db_runtime.engine,
        workspace_manager=workspace_manager,
        broadcaster=_change_stream_broadcaster,
        audit_writer=audit_writer,
    )
    tool_registry = ToolRegistry(
        workspace_manager,
        profile_store=profile_store,
        audit_writer=audit_writer,
        watch_service=watch_service,
    )

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

    # A2A agent card and task submission router — expose ALL tools as skills.
    # Build a generic handler for each tool that parses JSON text and
    # delegates to tool_registry.call().
    def _make_tool_handler(tool_name: str):  # noqa: ANN202
        def _handler(text: str) -> Any:
            payload = _parse_a2a_input(text)
            return tool_registry.call(tool_name, payload)
        return _handler

    def _make_authenticated_tool_handler(tool_name: str):  # noqa: ANN202
        # req: FR-004, FR-019
        def _handler(text: str, principal: dict[str, Any]) -> Any:
            payload = _parse_a2a_input(text)
            return tool_registry.call_with_access(
                tool_name,
                payload,
                actor_id=str(principal.get("actor") or "a2a-bearer"),
                roles=set(principal.get("roles", [])),
                capabilities=set(principal.get("capabilities", [])),
            )

        return _handler

    _authenticated_skill_handlers = {
        _tool_name: _make_authenticated_tool_handler(_tool_name)
        for _tool_name in tool_registry.contracts()
    }

    async def _submit_authenticated_task(request: Request) -> JSONResponse:
        # req: FR-004, FR-019
        """Accept an authenticated A2A task and dispatch through the guarded registry."""
        principal = await _a2a_principal_from_request(request, config)
        if principal is None:
            raise HTTPException(status_code=401, detail="Unauthorised")
        body = await request.json()
        task_id = body.get("id", str(uuid4()))
        skill_id = str(body.get("skill_id", "")).strip()
        input_data = body.get("input", {})
        input_text = input_data.get("text", "") if isinstance(input_data, dict) else str(input_data)
        if skill_id == "health":
            return JSONResponse(
                {
                    "id": task_id,
                    "status": "completed",
                    "output": {"type": "text", "text": "git-mcp is healthy"},
                }
            )
        handler = _authenticated_skill_handlers.get(skill_id)
        if handler is None:
            return JSONResponse(
                {
                    "id": task_id,
                    "status": "failed",
                    "error": f"Unknown skill: {skill_id}. Available: {list(_authenticated_skill_handlers)}",
                },
                status_code=404,
            )
        try:
            result = handler(input_text, principal)
        except PermissionError as exc:
            return JSONResponse({"id": task_id, "status": "failed", "error": str(exc)}, status_code=403)
        except Exception as exc:  # noqa: BLE001
            return JSONResponse({"id": task_id, "status": "failed", "error": str(exc)}, status_code=400)
        return JSONResponse(
            {
                "id": task_id,
                "status": "completed",
                "output": {"type": "text", "text": str(result)},
            }
        )

    app.add_api_route(
        f"{config.a2a_server.base_path}/tasks",
        _submit_authenticated_task,
        methods=["POST"],
        tags=["a2a"],
        name="authenticated_a2a_tasks",
    )
    app.add_api_route(
        "/tasks",
        _submit_authenticated_task,
        methods=["POST"],
        tags=["a2a"],
        name="authenticated_a2a_tasks_stripped",
    )

    def _blocked_card_handler(_text: str) -> Any:
        raise PermissionError("A2A task execution requires the authenticated dispatcher")

    _a2a_skills: list[A2ASkill] = []
    for _tool_name, _contract in tool_registry.contracts().items():
        _a2a_skills.append(
            A2ASkill(
                id=_tool_name,
                name=_tool_name.replace("_", " ").title(),
                description=_contract.description or _tool_name,
                handler=_blocked_card_handler,
            )
        )
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
