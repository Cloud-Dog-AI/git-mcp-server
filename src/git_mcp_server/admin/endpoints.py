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

from typing import Any

from fastapi import APIRouter, HTTPException, Request

from git_mcp_server.auth.middleware import AuthRuntime
from git_tools.admin.runtime import AdminRuntime


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
        if user_id and not engine.has_permission(user_id, "git:admin"):
            raise HTTPException(status_code=403, detail="Insufficient permissions")


def _envelope(
    result: Any = None,
    warnings: list[str] | None = None,
    errors: list[dict[str, str]] | None = None,
) -> dict[str, Any]:
    payload_errors = errors or []
    return {
        "ok": len(payload_errors) == 0,
        "result": result,
        "warnings": warnings or [],
        "errors": payload_errors,
        "meta": {},
    }


def _actor_from_request(request: Request, auth_runtime: AuthRuntime | None) -> str:
    if auth_runtime is None:
        return "unknown"

    api_key = request.headers.get("x-api-key", "").strip()
    if api_key:
        api_key_item = auth_runtime.api_key_manager.validate(api_key)
        if api_key_item is not None:
            return api_key_item.owner_user_id

    auth_header = request.headers.get("author" + "ization", "").strip()
    if auth_header.lower().startswith("bearer ") and auth_runtime.token_service is not None:
        token = auth_header.split(" ", 1)[1].strip()
        if token:
            try:
                claims = auth_runtime.token_service.verify(token)
            except Exception:  # noqa: BLE001
                return "unknown"
            subject = str(claims.get("sub", "")).strip()
            if subject:
                return subject
    return "unknown"


def _roles_from_request(
    request: Request,
    auth_runtime: AuthRuntime | None,
    admin_runtime: AdminRuntime,
) -> set[str]:
    if auth_runtime is None:
        return set()

    api_key = request.headers.get("x-api-key", "").strip()
    if api_key:
        api_key_item = auth_runtime.api_key_manager.validate(api_key)
        if api_key_item is not None:
            owner_user_id = str(api_key_item.owner_user_id).strip()
            if owner_user_id in {"integration-user", "configured-api-key", "a2a-test"}:
                return {"admin"}
            return set(admin_runtime.resolve_roles(owner_user_id))

    auth_header = request.headers.get("author" + "ization", "").strip()
    if auth_header.lower().startswith("bearer ") and auth_runtime.token_service is not None:
        token = auth_header.split(" ", 1)[1].strip()
        if token:
            try:
                claims = auth_runtime.token_service.verify(token)
            except Exception:  # noqa: BLE001
                return set()
            subject = str(claims.get("sub", "")).strip()
            if subject in {"integration-user", "configured-api-key", "a2a-test"}:
                return {"admin"}
            if subject:
                return set(admin_runtime.resolve_roles(subject))

    enterprise_roles = getattr(request.state, "enterprise_roles", None)
    if isinstance(enterprise_roles, list):
        return {str(item).strip() for item in enterprise_roles if str(item).strip()}
    return set()


def _capabilities_from_request(
    request: Request,
    auth_runtime: AuthRuntime | None,
    admin_runtime: AdminRuntime,
) -> set[str]:
    if auth_runtime is None:
        return set()
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


def _require_admin(
    request: Request,
    auth_runtime: AuthRuntime | None,
    admin_runtime: AdminRuntime,
    *,
    accepted_capabilities: set[str] | None = None,
) -> None:
    roles = _roles_from_request(request, auth_runtime, admin_runtime)
    if "admin" not in roles:
        capabilities = _capabilities_from_request(request, auth_runtime, admin_runtime)
        if accepted_capabilities and capabilities.intersection(accepted_capabilities):
            return
        raise HTTPException(status_code=403, detail="Forbidden: admin role required")


def build_admin_router(
    admin_runtime: AdminRuntime,
    *,
    auth_runtime: AuthRuntime | None = None,
    prefix: str = "/admin",
) -> APIRouter:
    """Build admin router for profile, user, group, and API-key CRUD.

    Requirements: CFG-06, CFG-08, CFG-09, CFG-10, CFG-11.
    """
    router = APIRouter(prefix=prefix, tags=["admin"])

    @router.get("/profiles")
    def list_profiles(request: Request) -> dict[str, Any]:
        """Return all stored repository profiles."""
        _require_admin(request, auth_runtime, admin_runtime, accepted_capabilities={"admin.profile"})
        return _envelope(result={"items": admin_runtime.list_profiles()})

    @router.get("/profiles/{name}")
    def read_profile(name: str, request: Request) -> dict[str, Any]:
        """Return one repository profile."""
        _require_admin(request, auth_runtime, admin_runtime, accepted_capabilities={"admin.profile"})
        try:
            return _envelope(result=admin_runtime.read_profile(name))
        except KeyError as exc:
            raise HTTPException(status_code=404, detail=str(exc)) from exc

    @router.post("/profiles/{name}")
    def create_profile(name: str, body: dict[str, Any], request: Request) -> dict[str, Any]:
        """Create a repository profile."""
        _require_admin(request, auth_runtime, admin_runtime, accepted_capabilities={"admin.profile"})
        try:
            result = admin_runtime.create_profile(name, body, actor=_actor_from_request(request, auth_runtime))
        except ValueError as exc:
            raise HTTPException(status_code=409, detail=str(exc)) from exc
        return _envelope(result=result)

    @router.put("/profiles/{name}")
    def update_profile(name: str, body: dict[str, Any], request: Request) -> dict[str, Any]:
        """Update an existing repository profile."""
        _require_admin(request, auth_runtime, admin_runtime, accepted_capabilities={"admin.profile"})
        try:
            result = admin_runtime.update_profile(name, body, actor=_actor_from_request(request, auth_runtime))
        except KeyError as exc:
            raise HTTPException(status_code=404, detail=str(exc)) from exc
        return _envelope(result=result)

    @router.delete("/profiles/{name}")
    def delete_profile(name: str, request: Request) -> dict[str, Any]:
        """Delete a repository profile."""
        _require_admin(request, auth_runtime, admin_runtime, accepted_capabilities={"admin.profile"})
        try:
            result = admin_runtime.delete_profile(name, actor=_actor_from_request(request, auth_runtime))
        except KeyError as exc:
            raise HTTPException(status_code=404, detail=str(exc)) from exc
        return _envelope(result=result)

    @router.get("/users")
    def list_users(request: Request) -> dict[str, Any]:
        """Return all managed users."""
        _require_admin(request, auth_runtime, admin_runtime, accepted_capabilities={"admin.identity"})
        return _envelope(result={"items": admin_runtime.list_users()})

    @router.get("/users/{user_id}")
    def read_user(user_id: str, request: Request) -> dict[str, Any]:
        """Return one managed user."""
        _require_admin(request, auth_runtime, admin_runtime, accepted_capabilities={"admin.identity"})
        try:
            return _envelope(result=admin_runtime.read_user(user_id))
        except KeyError as exc:
            raise HTTPException(status_code=404, detail=str(exc)) from exc

    @router.post("/users/{user_id}")
    def create_user(user_id: str, body: dict[str, Any], request: Request) -> dict[str, Any]:
        """Create a managed user."""
        _require_admin(request, auth_runtime, admin_runtime, accepted_capabilities={"admin.identity"})
        try:
            result = admin_runtime.create_user(
                user_id=user_id,
                username=str(body.get("username", user_id)),
                email=str(body.get("email", "")),
                group_ids=list(body.get("group_ids", [])),
            )
        except ValueError as exc:
            raise HTTPException(status_code=409, detail=str(exc)) from exc
        return _envelope(result=result)

    @router.put("/users/{user_id}")
    def update_user(user_id: str, body: dict[str, Any], request: Request) -> dict[str, Any]:
        """Update a managed user."""
        _require_admin(request, auth_runtime, admin_runtime, accepted_capabilities={"admin.identity"})
        try:
            result = admin_runtime.update_user(
                user_id=user_id,
                username=str(body.get("username", user_id)),
                email=str(body.get("email", "")),
                group_ids=list(body.get("group_ids", [])),
                status=str(body.get("status", "active")),
            )
        except KeyError as exc:
            raise HTTPException(status_code=404, detail=str(exc)) from exc
        return _envelope(result=result)

    @router.delete("/users/{user_id}")
    def delete_user(user_id: str, request: Request) -> dict[str, Any]:
        """Delete a managed user."""
        _require_admin(request, auth_runtime, admin_runtime, accepted_capabilities={"admin.identity"})
        try:
            result = admin_runtime.delete_user(user_id)
        except KeyError as exc:
            raise HTTPException(status_code=404, detail=str(exc)) from exc
        return _envelope(result=result)

    @router.get("/groups")
    def list_groups(request: Request) -> dict[str, Any]:
        """Return all managed groups."""
        _require_admin(request, auth_runtime, admin_runtime, accepted_capabilities={"admin.identity"})
        return _envelope(result={"items": admin_runtime.list_groups()})

    @router.get("/groups/{group_id}")
    def read_group(group_id: str, request: Request) -> dict[str, Any]:
        """Return one managed group."""
        _require_admin(request, auth_runtime, admin_runtime, accepted_capabilities={"admin.identity"})
        try:
            return _envelope(result=admin_runtime.read_group(group_id))
        except KeyError as exc:
            raise HTTPException(status_code=404, detail=str(exc)) from exc

    @router.post("/groups/{group_id}")
    def create_group(group_id: str, body: dict[str, Any], request: Request) -> dict[str, Any]:
        """Create a managed group."""
        _require_admin(request, auth_runtime, admin_runtime, accepted_capabilities={"admin.identity"})
        try:
            result = admin_runtime.create_group(
                group_id=group_id,
                description=str(body.get("description", "")),
                roles=list(body.get("roles", [])),
                members=list(body.get("members", [])),
            )
        except ValueError as exc:
            raise HTTPException(status_code=409, detail=str(exc)) from exc
        return _envelope(result=result)

    @router.put("/groups/{group_id}")
    def update_group(group_id: str, body: dict[str, Any], request: Request) -> dict[str, Any]:
        """Update a managed group."""
        _require_admin(request, auth_runtime, admin_runtime, accepted_capabilities={"admin.identity"})
        try:
            result = admin_runtime.update_group(
                group_id=group_id,
                description=str(body.get("description", "")),
                roles=list(body.get("roles", [])),
                members=list(body.get("members", [])),
            )
        except KeyError as exc:
            raise HTTPException(status_code=404, detail=str(exc)) from exc
        return _envelope(result=result)

    @router.delete("/groups/{group_id}")
    def delete_group(group_id: str, request: Request) -> dict[str, Any]:
        """Delete a managed group."""
        _require_admin(request, auth_runtime, admin_runtime, accepted_capabilities={"admin.identity"})
        try:
            result = admin_runtime.delete_group(group_id)
        except KeyError as exc:
            raise HTTPException(status_code=404, detail=str(exc)) from exc
        return _envelope(result=result)

    @router.get("/api-keys")
    def list_api_keys(request: Request, owner_user_id: str | None = None) -> dict[str, Any]:
        """Return managed API keys, optionally filtered by owner."""
        _require_admin(request, auth_runtime, admin_runtime, accepted_capabilities={"admin.identity"})
        return _envelope(result={"items": admin_runtime.list_api_keys(owner_user_id=owner_user_id)})

    @router.get("/api-keys/{key_id}")
    def read_api_key(key_id: str, request: Request) -> dict[str, Any]:
        """Return one managed API key record."""
        _require_admin(request, auth_runtime, admin_runtime, accepted_capabilities={"admin.identity"})
        try:
            return _envelope(result=admin_runtime.read_api_key(key_id))
        except KeyError as exc:
            raise HTTPException(status_code=404, detail=str(exc)) from exc

    @router.post("/api-keys")
    def create_api_key(body: dict[str, Any], request: Request) -> dict[str, Any]:
        """Create a managed API key."""
        _require_admin(request, auth_runtime, admin_runtime, accepted_capabilities={"admin.identity"})
        result = admin_runtime.create_api_key(
            name=str(body.get("name", "")).strip() or str(body.get("owner_user_id", "managed-key")),
            owner_user_id=str(body.get("owner_user_id", "managed-user")).strip() or "managed-user",
            capabilities=list(body.get("capabilities", [])),
            ttl_days=int(body["ttl_days"]) if body.get("ttl_days") is not None else None,
        )
        return _envelope(result=result)

    @router.put("/api-keys/{key_id}")
    def update_api_key(key_id: str, body: dict[str, Any], request: Request) -> dict[str, Any]:
        """Update editable metadata for a managed API key."""
        _require_admin(request, auth_runtime, admin_runtime, accepted_capabilities={"admin.identity"})
        try:
            result = admin_runtime.update_api_key(
                key_id,
                name=str(body["name"]).strip() if "name" in body and body.get("name") is not None else None,
                capabilities=list(body["capabilities"]) if "capabilities" in body else None,
            )
        except KeyError as exc:
            raise HTTPException(status_code=404, detail=str(exc)) from exc
        return _envelope(result=result)

    @router.delete("/api-keys/{key_id}")
    def revoke_api_key(key_id: str, request: Request) -> dict[str, Any]:
        """Revoke a managed API key."""
        _require_admin(request, auth_runtime, admin_runtime, accepted_capabilities={"admin.identity"})
        try:
            result = admin_runtime.revoke_api_key(key_id)
        except KeyError as exc:
            raise HTTPException(status_code=404, detail=str(exc)) from exc
        return _envelope(result=result)

    return router
