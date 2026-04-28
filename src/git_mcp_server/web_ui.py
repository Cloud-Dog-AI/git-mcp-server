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

from cloud_dog_storage import path_utils
from fastapi import FastAPI, Request, Response
from fastapi.responses import FileResponse, HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles

from git_tools.config.models import GlobalConfigModel


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


def _ui_root(config: GlobalConfigModel):
    """Resolve the built SPA asset directory from configuration."""
    return path_utils.as_path(config.web.ui_dist_dir).resolve()


def _index_response(ui_root: Path) -> Response:
    """Return index.html or a deterministic 503 when the UI has not been built."""
    index_path = ui_root / "index.html"
    if not index_path.exists():
        return HTMLResponse("<h1>UI not built</h1>", status_code=503)
    return FileResponse(index_path)


def _request_origin(request: Request) -> str:
    """Resolve the external origin, honouring reverse-proxy forwarded headers."""
    forwarded_proto = request.headers.get("x-forwarded-proto", "").split(",", 1)[0].strip()
    forwarded_host = request.headers.get("x-forwarded-host", "").split(",", 1)[0].strip()
    host = forwarded_host or request.headers.get("host", "").strip()
    scheme = forwarded_proto or request.url.scheme
    if host:
        return f"{scheme}://{host}"
    return str(request.base_url).rstrip("/")


def _runtime_config_payload(config: GlobalConfigModel, request: Request) -> dict[str, Any]:
    """Build the browser runtime config from the resolved service config."""
    origin = _request_origin(request)
    default_profile = config.web.default_profile.strip() or next(iter(config.profiles.keys()), "")
    remote_repo_url = ""
    if default_profile:
        profile = config.profiles.get(default_profile)
        if profile is not None:
            remote_repo_url = profile.repo.source
    a2a_base_url = f"{origin}{config.a2a_server.base_path}"
    return {
        "ENV": config.web.environment,
        "API_BASE_URL": origin,
        "MCP_BASE_URL": f"{origin}{config.mcp_server.base_path}",
        "A2A_BASE_URL": a2a_base_url,
        "AUTH_MODE": "cookie",
        "DEFAULT_PROFILE": default_profile,
        "REMOTE_REPO_URL": remote_repo_url,
        "SESSION_TIMEOUT_MINUTES": config.web.session_timeout_minutes,
    }


def _is_reserved_spa_path(path: str, config: GlobalConfigModel) -> bool:
    """Return whether the path belongs to a non-SPA route family."""
    trimmed = path.strip("/")
    if not trimmed:
        return False
    protected_roots = {
        "api",
        "app",
        "admin",
        "mcp",
        "a2a",
        "assets",
        "docs",
        "openapi.json",
        "redoc",
        config.mcp_server.base_path.strip("/"),
        "health",
        "live",
        "ready",
        "status",
        "runtime-config.js",
    }
    first = trimmed.split("/", 1)[0]
    return first in protected_roots


def register_web_ui(app: FastAPI, config: GlobalConfigModel) -> None:
    """Register PS-30 SPA delivery and runtime config endpoints.

    Requirements: FR-16, FR-17.
    """
    ui_root = _ui_root(config)
    assets_root = ui_root / "assets"

    if assets_root.exists():
        app.mount("/assets", StaticFiles(directory=str(assets_root)), name="ui-assets")

    @app.get("/runtime-config.js", response_class=Response)
    async def runtime_config(request: Request) -> Response:
        """Requirements: FR-16, FR-17.

        Uses JavaScript expressions for URL values so the browser resolves
        the correct protocol behind a reverse proxy (Traefik / HTTPS).
        """
        cfg = _runtime_config_payload(config, request)
        mcp_path = str(config.mcp_server.base_path or "/mcp")
        env = cfg.get("ENV", "dev")
        default_profile = cfg.get("DEFAULT_PROFILE", "")
        remote_repo = cfg.get("REMOTE_REPO_URL", "")
        a2a_base_url = cfg.get("A2A_BASE_URL", f"{mcp_path}/../a2a")
        session_timeout_minutes = cfg.get("SESSION_TIMEOUT_MINUTES", 30)
        body = (
            "const __origin = window.location.origin;\n"
            "window.__RUNTIME_CONFIG__ = {\n"
            f'  "ENV": "{env}",\n'
            '  "API_BASE_URL": __origin,\n'
            f'  "MCP_BASE_URL": __origin + "{mcp_path}",\n'
            f'  "A2A_BASE_URL": "{a2a_base_url}",\n'
            '  "AUTH_MODE": "cookie",\n'
            f'  "DEFAULT_PROFILE": "{default_profile}",\n'
            f'  "REMOTE_REPO_URL": "{remote_repo}",\n'
            f'  "SESSION_TIMEOUT_MINUTES": {int(session_timeout_minutes)}\n'
            "};\n"
        )
        return Response(
            content=body,
            media_type="application/javascript",
            headers={"Cache-Control": "no-store"},
        )

    @app.get("/", response_class=Response)
    async def spa_root() -> Response:
        """Requirements: FR-16, FR-17."""
        return _index_response(ui_root)

    @app.get("/{path:path}", response_class=Response)
    async def spa_fallback(path: str) -> Response:
        """Requirements: FR-16, FR-17."""
        if _is_reserved_spa_path(path, config):
            return JSONResponse({"detail": "Not Found"}, status_code=404)
        return _index_response(ui_root)
