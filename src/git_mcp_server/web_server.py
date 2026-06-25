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
from git_mcp_server.http_client import build_origin
from git_mcp_server.logging import configure_service_logging
from git_mcp_server.ui_endpoints import build_status_payload
from git_mcp_server.web_flat_roles import (
    ADMIN_ROLE,
    READ_ONLY_ROLE,
    READ_WRITE_ROLE,
    flat_role_from_tool_roles,
    normalise_flat_role,
    permissions_for_role,
    role_can_write,
)
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
    _cookie_name = "git_web_session"

    # Thread-a (PROGRAM-IDAM-RECOVERY-2) flat WebUI login accounts: the three
    # flat roles admin / read-write / read-only. The admin account keeps its
    # historical credentials (back-compat with existing demo scripts/tests);
    # read-write and read-only are seeded so all three flat roles are demoable.
    # Credentials are config-overridable (defaults.yaml web_login.* / CLOUD_DOG__WEB_LOGIN__* env);
    # read-write/read-only carry the estate-canonical in-code demo defaults
    # (BlueRiverChair / GreenRiverDesk) — mirroring chat-client (W28A-727-R5) and
    # notification-agent (W28A-730-R5) web_server.py — so all three flat roles log
    # in out-of-the-box without a deployment-config write. roles/permissions come from
    # the ONE shared idam guard (web_flat_roles).
    _admin_username = config.web_login.username.strip() or "admin"
    _admin_password = config.web_login.password
    _rw_username = config.web_login.read_write_username.strip() or "read-write"
    _rw_password = (config.web_login.read_write_password or "BlueRiverChair").strip() or "BlueRiverChair"
    _ro_username = config.web_login.read_only_username.strip() or "read-only"
    _ro_password = (config.web_login.read_only_password or "GreenRiverDesk").strip() or "GreenRiverDesk"

    # username -> (password, flat-role). Built once; the comparison in
    # /auth/login is constant-time per candidate to avoid username enumeration.
    _flat_accounts: dict[str, tuple[str, str]] = {
        _admin_username: (_admin_password, ADMIN_ROLE),
        _rw_username: (_rw_password, READ_WRITE_ROLE),
        _ro_username: (_ro_password, READ_ONLY_ROLE),
    }

    def _new_session(*, user: str, user_id: str, role: str) -> tuple[str, dict]:
        """Mint a flat-role session (role + shared-engine permissions)."""
        flat = normalise_flat_role(role)
        token = secrets.token_urlsafe(32)
        sess = {
            "user": user,
            "user_id": user_id,
            "role": flat,
            "permissions": permissions_for_role(flat),
            "_created": time.time(),
        }
        _sessions[token] = sess
        return token, sess
    # PS-92 (W28A-970c-V2): per-server `<server>.base_path`; legacy /app/v1 is hardcoded compat.
    api_base_path = config.api_server.base_path
    legacy_api_base_path = LEGACY_API_BASE_PATH
    a2a_base_path = config.a2a_server.base_path

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

    def _read_only_write_block(session: dict, request: Request, path: str) -> JSONResponse | None:
        """Thread-a flat-role write-gate (read-only).

        A logged-in read-only visitor may VIEW every data surface but is denied
        mutations: any write method on a non-health data path resolves to a
        403-inline (not a 401, not a blank UI). admin / read-write fall through.
        This is defence in depth over the API server's own shared-guard RBAC.
        """
        if (
            request.method.upper() in {"POST", "PUT", "PATCH", "DELETE"}
            and not role_can_write(session.get("role"))
            and not path.endswith("/health")
        ):
            return JSONResponse(
                {
                    "detail": "read-only role: write operations are not permitted",
                    "role": READ_ONLY_ROLE,
                },
                status_code=403,
            )
        return None

    async def _resolve_apikey_flat_role(api_key: str) -> str | None:
        """Resolve an api-key sign-in to its flat role for the web proxy.

        Mirrors /auth/me (W28A-731): the configured seed/admin key -> admin; any
        other MANAGED key is resolved via the API tier's /whoami (the ONE place that
        maps a key to roles). Returns None for an unknown key (the caller is then 401).
        """
        if not api_key:
            return None
        seed = _seed_api_key()
        if seed and secrets.compare_digest(api_key, seed):
            return ADMIN_ROLE
        try:
            result = await _build_api_proxy(api_key).request("GET", f"{api_base_path}/whoami")
        except Exception:  # noqa: BLE001
            return None
        if (
            result is not None
            and getattr(result, "status_code", 0) == 200
            and isinstance(getattr(result, "data", None), dict)
        ):
            tool_roles = (result.data.get("result") or {}).get("roles") or []
            return flat_role_from_tool_roles(tool_roles)
        return None

    async def _proxy_api_request(request: Request) -> Response:
        session = _get_session(request)
        api_key = request.headers.get("x-api-key", "").strip()
        if session is not None:
            # Cookie session: forward the seed key downstream (existing behaviour).
            proxy_role = session.get("role")
            proxy_api_key = _seed_api_key()
            forward_user = str(session["user"])
        elif api_key:
            # W28A-731: api-key sign-in on the web proxy. Resolve the caller's flat
            # role, deny read-only writes inline (403), and forward the CALLER's key
            # downstream so the API tier RBAC is the backstop on this surface too.
            flat = await _resolve_apikey_flat_role(api_key)
            if flat is None:
                raise HTTPException(status_code=401, detail="Not authenticated")
            proxy_role = flat
            proxy_api_key = api_key
            forward_user = f"apikey:{flat}"
        else:
            raise HTTPException(status_code=401, detail="Not authenticated")

        blocked = _read_only_write_block({"role": proxy_role}, request, request.url.path)
        if blocked is not None:
            return blocked

        if not proxy_api_key:
            raise HTTPException(status_code=503, detail="Proxy API key unavailable")

        forward_headers = {
            key: value
            for key, value in request.headers.items()
            if key.lower() not in {"host", "cookie", "content-length", "x-api-key"}
        }
        forward_headers["x-web-auth-user"] = forward_user

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

    def _build_passthrough_proxy(upstream_base_url: str) -> WebApiProxy:
        """Build a WebApiProxy for MCP/A2A passthrough per §1.4/§1.7."""
        proxy_config = _WebApiProxyConfig(
            raw_snapshot,
            api_base_url=upstream_base_url,
            api_key=_seed_api_key(),
        )
        return WebApiProxy.from_config(proxy_config)

    _a2a_proxy = _build_passthrough_proxy(a2a_base_url)

    async def _passthrough_proxy(request: Request, proxy: WebApiProxy, *, strip_prefix: str = "") -> Response:
        session = _get_session(request)
        if session is None:
            raise HTTPException(status_code=401, detail="Not authenticated")

        blocked = _read_only_write_block(session, request, request.url.path)
        if blocked is not None:
            return blocked

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
        forward_headers["x-web-auth-user"] = str(session["user"])

        body = await request.body()
        json_body = None
        if body:
            try:
                json_body = await request.json()
            except Exception:
                pass

        result = await proxy.request(
            request.method,
            remainder,
            json=json_body,
            params=dict(request.query_params),
            headers=forward_headers,
        )
        return _response_from_proxy_result(result)

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
        """Validate username/password and create a flat-role session."""
        body = await request.json()
        username = str(body.get("username", "")).strip()
        password = str(body.get("password", "")).strip()
        if not username or not password:
            raise HTTPException(status_code=400, detail="Username and password required")
        # Flat-role credential check. Compare against EVERY account with
        # secrets.compare_digest so a wrong username and a wrong password are
        # indistinguishable (no username enumeration). The matched account
        # decides the flat role; permissions come from the shared idam guard.
        matched_role: str | None = None
        for cand_user, (cand_pw, cand_role) in _flat_accounts.items():
            user_ok = secrets.compare_digest(username, cand_user)
            pw_ok = secrets.compare_digest(password, cand_pw)
            if user_ok and pw_ok:
                matched_role = cand_role
                break
        if matched_role is None:
            raise HTTPException(status_code=401, detail="Invalid credentials")

        user_id = {ADMIN_ROLE: "1", READ_WRITE_ROLE: "2", READ_ONLY_ROLE: "3"}[matched_role]
        token, sess = _new_session(user=username, user_id=user_id, role=matched_role)
        resp = JSONResponse({
            "user": {
                "id": user_id,
                "displayName": username,
                "email": None,
                "roles": [matched_role],
                "permissions": list(sess["permissions"]),
            }
        })
        resp.set_cookie(_cookie_name, token, httponly=True, samesite="lax", max_age=3600, path="/")
        return resp

    @app.get("/auth/me")
    async def auth_me(request: Request) -> JSONResponse:
        """Return the current principal — cookie session OR X-API-Key service account (GM7)."""
        sess = _get_session(request)
        if sess:
            role = normalise_flat_role(sess.get("role"))
            permissions = sess.get("permissions")
            if not isinstance(permissions, list):
                permissions = permissions_for_role(role)
            return JSONResponse({"user": {"id": sess["user_id"], "displayName": sess["user"], "email": None, "roles": [role], "permissions": permissions}})
        # GM7 (W28C-1705): materialise a principal for X-API-Key callers too, so UI flows that
        # pivot on /auth/me no longer see "logged out" when authenticating by key. The api-key
        # sign-in is git-mcp's login surface (auth.mode=api_key); a valid configured key
        # normalises onto the admin flat role (it forwards the service api key downstream).
        api_key = request.headers.get("x-api-key", "").strip()
        expected_key = _seed_api_key()
        if api_key and expected_key and secrets.compare_digest(api_key, expected_key):
            return JSONResponse(
                {"user": {"id": "service", "displayName": "service-account", "email": None, "roles": [ADMIN_ROLE], "permissions": permissions_for_role(ADMIN_ROLE), "type": "service"}}
            )
        # W28A-731 flat-login (api_key 3-key model): resolve a MANAGED api-key
        # sign-in to its flat role via the API tier's /whoami — the ONE place that
        # resolves an api_key principal to roles (no fork). A reader/writer/admin
        # demo key thus logs into the WebUI as read-only/read-write/admin; an
        # invalid/unknown key -> whoami 401 -> user:None (logged out).
        if api_key:
            try:
                result = await _build_api_proxy(api_key).request("GET", f"{api_base_path}/whoami")
            except Exception:  # noqa: BLE001 - resolution failure must not 500 the login probe
                result = None
            if (
                result is not None
                and getattr(result, "status_code", 0) == 200
                and isinstance(getattr(result, "data", None), dict)
            ):
                tool_roles = (result.data.get("result") or {}).get("roles") or []
                flat = flat_role_from_tool_roles(tool_roles)
                return JSONResponse(
                    {"user": {"id": f"apikey:{flat}", "displayName": flat, "email": None, "roles": [flat], "permissions": permissions_for_role(flat), "type": "api_key"}}
                )
        return JSONResponse({"user": None})

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

    # W28A-876: serve the canonical SHARED cloud_dog_idam idam_v1_router (resource-registry +
    # rbac-bindings) directly on the web tier at {api_base_path}, BEFORE the catch-all proxy
    # below, so /api/v1/idam/v1/* resolves locally. ONE estate-wide implementation.
    try:
        from cloud_dog_idam.api.fastapi.router import idam_v1_router as _idam_v1_router
        # The shared WebUI sets apiBaseUrl="/api" for git, so the RBAC page calls
        # /api/v1/idam/v1/* (matching git's /api/v1/admin mirror). Mount at the api base,
        # /api/v1, and /v1 so it resolves regardless of how the request arrives.
        for _ipfx in {api_base_path, "/api/v1", "/v1"}:
            if _ipfx:
                app.include_router(_idam_v1_router, prefix=_ipfx, include_in_schema=False)
    except Exception:
        pass

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

    # GM6 (W28C-1705): the web MCP passthrough at mcp_server.base_path (=/git-mcp in the standard deployment)
    # was vestigial — Traefik routes /mcp directly to the MCP tier, and /git-mcp (exact) fell to
    # this proxy which forwarded to the now-gated MCP and ALWAYS-401'd (even with a valid key).
    # Removed entirely so /git-mcp falls through to the SPA; the MCP tier accepts api-key AND
    # cookie sessions directly (mcp_server install_auth_middleware web_session_url).
    @app.api_route(a2a_base_path + "/{path:path}", methods=["GET", "POST", "PUT", "PATCH", "DELETE"])
    async def proxy_a2a(path: str, request: Request):
        """Proxy cookie-authenticated UI A2A HTTP calls to the backend A2A server."""
        preserve_paths = {
            f"{a2a_base_path}/health",
            f"{a2a_base_path}/.well-known/agent.json",
        }
        strip_prefix = "" if request.url.path in preserve_paths else a2a_base_path
        return await _passthrough_proxy(request, _a2a_proxy, strip_prefix=strip_prefix)

    @app.api_route(a2a_base_path, methods=["GET", "POST", "PUT", "PATCH", "DELETE"])
    async def proxy_a2a_root(request: Request):
        """Proxy cookie-authenticated UI A2A root calls to the backend A2A server."""
        return await _passthrough_proxy(request, _a2a_proxy, strip_prefix=a2a_base_path)

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
