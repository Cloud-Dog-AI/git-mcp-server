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

from dataclasses import dataclass
from typing import Iterable

from cloud_dog_idam import APIKeyManager, RBACEngine
from cloud_dog_idam.providers.oidc import KeycloakProvider
from cloud_dog_idam.tokens import JWTTokenService
from fastapi import FastAPI
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import JSONResponse, Response

from git_tools.config.models import AuthConfig


@dataclass(slots=True)
class AuthRuntime:
    """Runtime auth objects used by the server."""

    api_key_manager: APIKeyManager
    rbac_engine: RBACEngine
    token_service: JWTTokenService | None = None
    enterprise_provider: KeycloakProvider | None = None


def _build_jwt_token_service(auth_config: AuthConfig) -> JWTTokenService | None:
    if auth_config.mode not in {"jwt", "api_key+jwt"}:
        return None
    secret = auth_config.jwt.secret.strip()
    if not secret:
        raise ValueError("auth.jwt.secret must be set when auth.mode includes jwt")
    issuer = auth_config.jwt.issuer.strip() or "cloud-dog"
    audience = auth_config.jwt.audience.strip() or "cloud-dog-services"
    return JWTTokenService(
        secret=secret,
        issuer=issuer,
        audience=audience,
    )


def _build_enterprise_provider(auth_config: AuthConfig) -> KeycloakProvider | None:
    if auth_config.mode != "enterprise":
        return None
    enterprise = auth_config.enterprise
    if enterprise.provider != "keycloak":
        raise ValueError("auth.enterprise.provider must be keycloak for enterprise mode")
    required = {
        "keycloak_base_url": enterprise.keycloak_base_url.strip(),
        "keycloak_realm": enterprise.keycloak_realm.strip(),
        "keycloak_client_id": enterprise.keycloak_client_id.strip(),
    }
    missing = sorted(name for name, value in required.items() if not value)
    if missing:
        raise ValueError(f"Missing enterprise keycloak settings: {', '.join(missing)}")
    return KeycloakProvider(
        base_url=enterprise.keycloak_base_url.strip(),
        realm=enterprise.keycloak_realm.strip(),
        client_id=enterprise.keycloak_client_id.strip(),
        client_secret=enterprise.keycloak_client_secret.strip(),
    )


def _normalise_enterprise_roles(raw_roles: list[str]) -> set[str]:
    """Map provider roles into canonical RBAC role labels."""
    mapped: set[str] = set()
    for role in raw_roles:
        candidate = role.strip().lower()
        if not candidate:
            continue
        if candidate in {"admin", "realm-admin", "cloud-dog-admin"}:
            mapped.add("admin")
            continue
        if candidate in {"maintainer", "developer", "dev", "editor"}:
            mapped.add("maintainer")
            continue
        if candidate in {"writer", "contributor"}:
            mapped.add("writer")
            continue
        if candidate in {"reader", "viewer"}:
            mapped.add("reader")
            continue
        mapped.add(candidate)
    return mapped


def build_auth_runtime(auth_config: AuthConfig) -> AuthRuntime:
    """Create IDAM primitives for middleware registration."""
    api_key_manager = APIKeyManager()
    rbac_engine = RBACEngine()
    token_service = _build_jwt_token_service(auth_config)
    enterprise_provider = _build_enterprise_provider(auth_config)
    return AuthRuntime(
        api_key_manager=api_key_manager,
        rbac_engine=rbac_engine,
        token_service=token_service,
        enterprise_provider=enterprise_provider,
    )


def _build_skip_paths(api_base_path: str, legacy_api_base_path: str, a2a_base_path: str) -> set[str]:
    """Construct auth-bypass routes from configured route prefixes."""
    skip_paths = {
        "/health",
        "/ready",
        "/live",
        "/status",
        f"{a2a_base_path}/health",
        f"{a2a_base_path}/events/config",
    }
    for prefix in (api_base_path, legacy_api_base_path):
        skip_paths.add(f"{prefix}/health")
        skip_paths.add(f"{prefix}/version")
        skip_paths.add(f"{prefix}/public/tools")
    return skip_paths


def _path_matches_prefix(path: str, prefix: str) -> bool:
    """Return whether a request path is the prefix or one of its children."""
    candidate = prefix.rstrip("/")
    if not candidate:
        return False
    return path == candidate or path.startswith(f"{candidate}/")


def _is_protected_path(
    path: str,
    *,
    protected_prefixes: Iterable[str],
    protected_exact_paths: Iterable[str],
) -> bool:
    """Return whether a request path should remain behind auth middleware."""
    if path in set(protected_exact_paths):
        return True
    return any(_path_matches_prefix(path, prefix) for prefix in protected_prefixes)


def install_auth_middleware(
    app: FastAPI,
    auth_runtime: AuthRuntime,
    auth_mode: str,
    *,
    api_base_path: str,
    legacy_api_base_path: str,
    a2a_base_path: str,
    extra_protected_prefixes: list[str] | None = None,
) -> None:
    """Install auth middleware with explicit protected-route boundaries."""
    scheme = "any"
    if auth_mode == "api_key":
        scheme = "api_key"
    elif auth_mode == "jwt":
        scheme = "bearer"
    elif auth_mode == "enterprise":
        scheme = "bearer"

    skip_paths = _build_skip_paths(
        api_base_path=api_base_path,
        legacy_api_base_path=legacy_api_base_path,
        a2a_base_path=a2a_base_path,
    )
    protected_prefixes = [
        api_base_path,
        legacy_api_base_path,
        a2a_base_path,
        *(extra_protected_prefixes or []),
    ]
    protected_exact_paths = {
        "/docs",
        "/docs/oauth2-redirect",
        "/openapi.json",
        "/redoc",
    }

    if auth_mode == "enterprise":
        provider = auth_runtime.enterprise_provider
        if provider is None:
            raise ValueError("enterprise auth mode requires configured enterprise provider")

        class EnterpriseAuthMiddleware(BaseHTTPMiddleware):
            def __init__(self, app: FastAPI) -> None:
                super().__init__(app)
                self._skip_paths = skip_paths
                self._provider = provider

            async def dispatch(self, request: Request, call_next) -> Response:  # type: ignore[override]
                request.state.correlation_id = request.headers.get("x-correlation-id", "")
                if request.url.path in self._skip_paths or not _is_protected_path(
                    request.url.path,
                    protected_prefixes=protected_prefixes,
                    protected_exact_paths=protected_exact_paths,
                ):
                    return await call_next(request)

                auth_header = request.headers.get("author" + "ization", "").strip()
                if not auth_header.lower().startswith("bearer "):
                    return JSONResponse(status_code=401, content={"detail": "Unauthorised"})
                token = auth_header.split(" ", 1)[1].strip()
                if not token:
                    return JSONResponse(status_code=401, content={"detail": "Unauthorised"})
                try:
                    claims = await self._provider.validate_id_token(token)
                except Exception:  # noqa: BLE001
                    return JSONResponse(status_code=401, content={"detail": "Unauthorised"})
                roles = _normalise_enterprise_roles(self._provider.map_claims_to_roles(claims))
                if not roles:
                    return JSONResponse(status_code=403, content={"detail": "No enterprise role mapping"})
                request.state.enterprise_claims = claims
                request.state.enterprise_roles = sorted(roles)
                return await call_next(request)

        app.add_middleware(EnterpriseAuthMiddleware)
        return

    class CompatAuthMiddleware(BaseHTTPMiddleware):
        def __init__(self, app: FastAPI) -> None:
            super().__init__(app)
            self._scheme = scheme
            self._skip_paths = skip_paths
            self._api_key_manager = auth_runtime.api_key_manager
            self._token_service = auth_runtime.token_service

        async def dispatch(self, request: Request, call_next) -> Response:  # type: ignore[override]
            request.state.correlation_id = request.headers.get("x-correlation-id", "")
            if request.url.path in self._skip_paths or not _is_protected_path(
                request.url.path,
                protected_prefixes=protected_prefixes,
                protected_exact_paths=protected_exact_paths,
            ):
                return await call_next(request)

            api_key = request.headers.get("x-api-key", "").strip()
            if self._scheme in {"api_key", "any"} and api_key and self._api_key_manager.validate(api_key) is not None:
                return await call_next(request)

            auth_header = request.headers.get("author" + "ization", "").strip()
            if self._scheme in {"bearer", "any"} and auth_header.lower().startswith("bearer "):
                if self._token_service is None:
                    return JSONResponse(status_code=401, content={"detail": "Unauthorised"})
                token = auth_header.split(" ", 1)[1].strip()
                if not token:
                    return JSONResponse(status_code=401, content={"detail": "Unauthorised"})
                try:
                    self._token_service.verify(token)
                except Exception:  # noqa: BLE001
                    return JSONResponse(status_code=401, content={"detail": "Unauthorised"})
                return await call_next(request)

            return JSONResponse(status_code=401, content={"detail": "Unauthorised"})

    app.add_middleware(CompatAuthMiddleware)
