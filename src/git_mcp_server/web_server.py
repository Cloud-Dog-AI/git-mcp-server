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

import secrets
import time
from typing import Any

import uvicorn
from cloud_dog_api_kit.web.proxy import WebApiProxy
from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import JSONResponse, Response

from git_mcp_server.api_server import _create_platform_app, _parse_cli_env_files
from git_mcp_server.http_client import build_origin, request_json
from git_mcp_server.logging import configure_service_logging
from git_mcp_server.ui_endpoints import build_status_payload
from git_mcp_server.web_ui import register_web_ui
from git_tools.config.loader import bind_global_config, load_raw_config
from git_tools.config.models import LEGACY_API_BASE_PATH
from git_tools.files.io import load_host_text
from cloud_dog_storage import path_utils


_ROLE_PERMISSIONS = {
    "admin": {"*"},
    "maintainer": {"git:read", "git:write", "git:execute", "git:admin"},
    "writer": {"git:read", "git:write", "git:execute"},
    "reader": {"git:read"},
}


class _WebApiProxyConfig:
    """Bridge runtime values into the cloud_dog_api_kit WebApiProxy config contract."""

    def __init__(self, source: Any, *, api_base_url: str, api_key: str) -> None:
        self._source = source
        self._overrides = {
            "web_server.api_base_url": api_base_url,
            "api_server.api_key": api_key,
        }

    def get(self, key: str, default: Any = None) -> Any:
        """Return override values first, then defer to the source config snapshot."""
        if key in self._overrides:
            return self._overrides[key]
        getter = getattr(self._source, "get", None)
        if callable(getter):
            return getter(key, default)
        return default


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


def create_web_app(env_files: list[str] | None = None) -> FastAPI:
    """Create the standalone SPA delivery server."""
    raw_snapshot = load_raw_config(env_files=env_files)
    config = bind_global_config(raw_snapshot)
    configure_service_logging(raw_snapshot, service_name="git-mcp-server-web", server_id=config.runtime.server_id, surface="web")

    app = _create_platform_app(
        title="git-mcp-server-web",
        version="0.1.0",
        description="Standalone SPA delivery server for git-mcp-server.",
    )
    started_at = time.time()
    app.state.active_request_count = 0
    _sessions: dict[str, dict] = {}

    @app.middleware("http")
    async def count_active_requests(request: Request, call_next):
        app.state.active_request_count = int(getattr(app.state, "active_request_count", 0)) + 1
        try:
            return await call_next(request)
        finally:
            app.state.active_request_count = max(int(getattr(app.state, "active_request_count", 1)) - 1, 0)

    # In-memory token session store (no itsdangerous dependency).
    _admin_username = config.web_login.username.strip() or "admin"
    _admin_password = config.web_login.password
    _cookie_name = "git_web_session"
    # PS-92 (W28A-970c-V2): per-server `<server>.base_path`; legacy /app/v1 is hardcoded compat.
    api_base_path = config.api_server.base_path
    legacy_api_base_path = LEGACY_API_BASE_PATH
    a2a_base_path = config.a2a_server.base_path
    mcp_base_path = config.mcp_server.base_path

    def _seed_api_key() -> str:
        configured = config.git.api_key.strip()
        if configured:
            return configured
        key_paths = [config.runtime.seed_key_file.strip()]
        for raw_path in key_paths:
            if not raw_path:
                continue
            candidate = path_utils.as_path(raw_path).expanduser().resolve()
            if candidate.exists():
                value = load_host_text(candidate).strip()
                if value:
                    return value
        return ""

    api_base_url = build_origin(config.api_server.client_host.strip() or config.api_server.host.strip(), config.api_server.port)
    mcp_base_url = build_origin(config.mcp_server.host.strip(), config.mcp_server.port)
    a2a_base_url = build_origin(config.a2a_server.host.strip(), config.a2a_server.port)

    def _build_api_proxy(api_key: str) -> WebApiProxy:
        proxy_config = _WebApiProxyConfig(
            raw_snapshot,
            api_base_url=api_base_url,
            api_key=api_key,
        )
        return WebApiProxy.from_config(proxy_config)

    def _response_from_proxy_result(result: Any) -> Response:
        response_headers = {
            key: value
            for key, value in result.headers.items()
            if key.lower() not in {"content-length", "transfer-encoding", "connection", "keep-alive"}
        }
        if isinstance(result.data, (dict, list)):
            return JSONResponse(
                status_code=result.status_code,
                content=result.data,
                headers=response_headers,
            )
        content = result.data if result.data is not None else result.error or ""
        return Response(
            status_code=result.status_code,
            content=content,
            media_type=result.headers.get("content-type"),
            headers=response_headers,
        )

    async def _proxy_api_request(request: Request) -> Response:
        session = _get_session(request)
        if session is None:
            raise HTTPException(status_code=401, detail="Not authenticated")

        proxy_api_key = _seed_api_key()
        if not proxy_api_key:
            raise HTTPException(status_code=503, detail="Proxy API key unavailable")

        forward_headers = {
            key: value
            for key, value in request.headers.items()
            if key.lower() not in {"host", "cookie", "content-length", "x-api-key"}
        }
        forward_headers["x-web-auth-user"] = str(session["user"])

        body = await request.body()
        json_body = None
        if body:
            try:
                json_body = await request.json()
            except Exception:
                json_body = None

        result = await _build_api_proxy(proxy_api_key).request(
            request.method,
            request.url.path,
            json=json_body,
            params=dict(request.query_params),
            headers=forward_headers,
            cookies=dict(request.cookies),
        )
        return _response_from_proxy_result(result)

    async def _passthrough_proxy(request: Request, upstream_base_url: str, *, strip_prefix: str = "") -> Response:
        session = _get_session(request)
        if session is None:
            raise HTTPException(status_code=401, detail="Not authenticated")

        proxy_api_key = _seed_api_key()
        if not proxy_api_key:
            raise HTTPException(status_code=503, detail="Proxy API key unavailable")

        remainder = request.url.path
        if strip_prefix and request.url.path.startswith(strip_prefix):
            remainder = request.url.path[len(strip_prefix):]
        if not remainder.startswith("/"):
            remainder = f"/{remainder}" if remainder else "/"

        forward_headers = {
            key: value
            for key, value in request.headers.items()
            if key.lower() not in {"host", "cookie", "content-length", "x-api-key"}
        }
        forward_headers["x-api-key"] = proxy_api_key
        forward_headers["x-web-auth-user"] = str(session["user"])

        body = await request.body()
        upstream = await request_json(
            request.method,
            f"{upstream_base_url}{remainder}",
            params=request.query_params,
            content=body if body else None,
            headers=forward_headers,
            timeout=30.0,
        )
        response_headers = {
            key: value
            for key, value in upstream.headers.items()
            if key.lower() not in {"content-length", "transfer-encoding", "connection", "keep-alive"}
        }
        if "application/json" in upstream.headers.get("content-type", ""):
            return JSONResponse(
                status_code=upstream.status_code,
                content=upstream.json(),
                headers=response_headers,
            )
        return Response(
            status_code=upstream.status_code,
            content=upstream.content,
            media_type=upstream.headers.get("content-type"),
            headers=response_headers,
        )

    def _get_session(request: Request) -> dict | None:
        token = request.cookies.get(_cookie_name)
        if token and token in _sessions:
            sess = _sessions[token]
            if time.time() - sess.get("_created", 0) < 3600:
                return sess
            del _sessions[token]
        return None

    @app.post("/auth/login")
    async def auth_login(request: Request) -> JSONResponse:
        """Validate username/password and create session."""
        body = await request.json()
        username = str(body.get("username", "")).strip()
        password = str(body.get("password", "")).strip()
        if not username or not password:
            raise HTTPException(status_code=400, detail="Username and password required")
        if username != _admin_username or password != _admin_password:
            raise HTTPException(status_code=401, detail="Invalid credentials")
        token = secrets.token_urlsafe(32)
        _sessions[token] = {"user": username, "user_id": "1", "role": "admin", "_created": time.time()}
        resp = JSONResponse({"user": {"id": "1", "displayName": username, "email": None, "roles": ["admin"], "permissions": ["*"]}})
        resp.set_cookie(_cookie_name, token, httponly=True, samesite="lax", max_age=3600, path="/")
        return resp

    @app.get("/auth/me")
    async def auth_me(request: Request) -> JSONResponse:
        """Return current session user."""
        sess = _get_session(request)
        if not sess:
            return JSONResponse({"user": None})
        return JSONResponse({"user": {"id": sess["user_id"], "displayName": sess["user"], "email": None, "roles": [sess["role"]], "permissions": ["*"]}})

    @app.post("/auth/logout")
    async def auth_logout(request: Request) -> JSONResponse:
        """Clear session."""
        token = request.cookies.get(_cookie_name)
        if token:
            _sessions.pop(token, None)
        resp = JSONResponse({"ok": True})
        resp.delete_cookie(_cookie_name, path="/")
        return resp

    app.router.routes = [route for route in app.router.routes if getattr(route, "path", None) != "/status"]

    @app.get("/status")
    async def ui_status() -> JSONResponse:
        """Return the unauthenticated UI status payload used by the SPA dashboard."""
        active_connections = max(
            int(getattr(app.state, "active_request_count", 0)),
            len(_sessions),
        )
        return JSONResponse(
            build_status_payload(
                config=config,
                started_at=started_at,
                active_connections=active_connections,
            )
        )

    @app.api_route(f"{api_base_path}" + "/{path:path}", methods=["GET", "POST", "PUT", "PATCH", "DELETE"])
    async def proxy_api(path: str, request: Request):
        """Proxy cookie-authenticated UI API calls to the backend API server."""
        return await _proxy_api_request(request)

    @app.api_route(f"{api_base_path}", methods=["GET", "POST", "PUT", "PATCH", "DELETE"])
    async def proxy_api_root(request: Request):
        """Proxy cookie-authenticated UI API root calls to the backend API server."""
        return await _proxy_api_request(request)

    # PS-92 legacy compat: /app/v1 route; NOT configurable; see W28A-970c-V2
    @app.api_route(f"{legacy_api_base_path}" + "/{path:path}", methods=["GET", "POST", "PUT", "PATCH", "DELETE"], include_in_schema=False)
    async def proxy_legacy_api(path: str, request: Request):
        """Proxy legacy cookie-authenticated UI API calls to the backend API server."""
        return await _proxy_api_request(request)

    @app.api_route(f"{legacy_api_base_path}", methods=["GET", "POST", "PUT", "PATCH", "DELETE"], include_in_schema=False)
    async def proxy_legacy_api_root(request: Request):
        """Proxy legacy cookie-authenticated UI API root calls to the backend API server."""
        return await _proxy_api_request(request)

    @app.api_route(mcp_base_path + "/{path:path}", methods=["GET", "POST", "PUT", "PATCH", "DELETE"])
    async def proxy_mcp(path: str, request: Request):
        """Proxy cookie-authenticated UI MCP calls to the backend MCP server."""
        return await _passthrough_proxy(request, mcp_base_url, strip_prefix=mcp_base_path)

    @app.api_route(mcp_base_path, methods=["GET", "POST", "PUT", "PATCH", "DELETE"])
    async def proxy_mcp_root(request: Request):
        """Proxy cookie-authenticated UI MCP root calls to the backend MCP server."""
        return await _passthrough_proxy(request, mcp_base_url, strip_prefix=mcp_base_path)

    @app.api_route(a2a_base_path + "/{path:path}", methods=["GET", "POST", "PUT", "PATCH", "DELETE"])
    async def proxy_a2a(path: str, request: Request):
        """Proxy cookie-authenticated UI A2A HTTP calls to the backend A2A server."""
        return await _passthrough_proxy(request, a2a_base_url, strip_prefix=a2a_base_path)

    @app.api_route(a2a_base_path, methods=["GET", "POST", "PUT", "PATCH", "DELETE"])
    async def proxy_a2a_root(request: Request):
        """Proxy cookie-authenticated UI A2A root calls to the backend A2A server."""
        return await _passthrough_proxy(request, a2a_base_url, strip_prefix=a2a_base_path)

    @app.api_route("/web/api/{path:path}", methods=["GET", "POST", "PUT", "PATCH", "DELETE"])
    async def proxy_web_api(path: str, request: Request):
        """Proxy compatibility cleanup routes under /web/api/* to JSON API surfaces."""
        if not (
            path.startswith("admin/")
            or path == "jobs"
            or path.startswith("jobs/")
            or path == "logs"
            or path.startswith("logs/")
        ):
            raise HTTPException(status_code=404, detail="Not Found")
        rewritten_path = f"{legacy_api_base_path}/{path}"
        return await _proxy_api_request(_rewrite_request_path(request, rewritten_path))

    @app.api_route("/web/api", methods=["GET", "POST", "PUT", "PATCH", "DELETE"])
    async def proxy_web_api_root(request: Request):
        """Reject unsupported bare compatibility root requests deterministically."""
        raise HTTPException(status_code=404, detail="Not Found")

    register_web_ui(app, config)
    return app


def _rewrite_request_path(request: Request, new_path: str) -> Request:
    """Clone a request with a rewritten path for compatibility proxying."""
    scope = dict(request.scope)
    query_string = scope.get("query_string", b"")
    scope["path"] = new_path
    scope["raw_path"] = new_path.encode("utf-8") + (b"?" + query_string if query_string else b"")
    return Request(scope, getattr(request, "_receive"))


def run_web(env_files: list[str] | None = None) -> None:
    """Start the standalone web server via uvicorn."""
    raw_snapshot = load_raw_config(env_files=env_files)
    cfg = bind_global_config(raw_snapshot)
    server_config = uvicorn.Config(
        create_web_app(env_files=env_files),
        host=cfg.web_server.host,
        port=cfg.web_server.port,
        log_level="info",
    )
    uvicorn.Server(server_config).run()


if __name__ == "__main__":
    run_web(env_files=_parse_cli_env_files())
