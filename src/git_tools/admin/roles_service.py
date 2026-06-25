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

"""SQL-backed admin roles service for git-mcp-server (PS-71 §IW3A).

License: Apache 2.0
Ownership: Cloud-Dog, Viewdeck Engineering Limited
Description: Persistent CRUD for admin roles backed by the canonical
    cloud_dog_idam SqlAlchemyRoleStore (roles / permissions / role_permissions).
Tasks: W28A-876 (Gate 4b)
Architecture: 4.1 Authentication
"""

from __future__ import annotations

from typing import Any, Iterable

from cloud_dog_idam.domain.models import Role  # type: ignore[import-not-found,import-untyped]
from cloud_dog_idam.storage.sqlalchemy.role_store import (  # type: ignore[import-not-found,import-untyped]
    BaselineRoleProtected,
    SqlAlchemyRoleStore,
)


class RolesServiceError(RuntimeError):
    """Structured roles error carrying an HTTP status and code."""

    def __init__(self, code: str, message: str, *, status: int = 400) -> None:
        super().__init__(message)
        self.code = code
        self.status = status


class RolesService:
    """Persistent roles CRUD backed by the canonical cloud_dog_idam role store.

    Mirrors the file-mcp roles surface: baseline admin/user seeding, the
    PS-71 §IW3A.1 list shape (role_id/name/description/permissions/created/baseline),
    and a 403 for attempts to delete a protected baseline role.
    """

    def __init__(self, *, session_manager: Any) -> None:
        self.session_manager = session_manager

    def _role_store(self, session: Any) -> SqlAlchemyRoleStore:
        return SqlAlchemyRoleStore(session)

    @staticmethod
    def _role_payload(role: Role) -> dict[str, Any]:
        return {
            "role_id": role.role_id,
            "name": role.name,
            "description": role.description,
            "permissions": sorted(role.permissions),
        }

    def ensure_roles_seed(self) -> None:
        """Seed the baseline admin/user roles (IW3A.4). Idempotent."""
        with self.session_manager.session() as session:
            self._role_store(session).seed_baseline()

    def list_roles(self) -> list[dict[str, Any]]:
        with self.session_manager.session() as session:
            store = self._role_store(session)
            store.seed_baseline()
            return store.list_response()

    def get_role(self, role_id: str) -> dict[str, Any]:
        with self.session_manager.session() as session:
            for row in self._role_store(session).list_response():
                if row["role_id"] == role_id:
                    return row
            raise RolesServiceError("NOT_FOUND", f"unknown role: {role_id}", status=404)

    def create_role(
        self,
        *,
        name: str,
        description: str = "",
        permissions: Iterable[str] | None = None,
    ) -> dict[str, Any]:
        clean_name = (name or "").strip()
        if not clean_name:
            raise RolesServiceError("VALIDATION_ERROR", "name is required")
        with self.session_manager.session() as session:
            store = self._role_store(session)
            if store.get_by_name(clean_name) is not None:
                raise RolesServiceError(
                    "CONFLICT", f"role already exists: {clean_name}", status=409
                )
            role = store.save(
                Role(
                    name=clean_name,
                    description=str(description or ""),
                    permissions={
                        str(p).strip() for p in (permissions or []) if str(p).strip()
                    },
                )
            )
            return self._role_payload(role)

    def update_role(self, role_id: str, *, data: dict[str, Any]) -> dict[str, Any]:
        with self.session_manager.session() as session:
            store = self._role_store(session)
            if store.get(role_id) is None:
                raise RolesServiceError("NOT_FOUND", f"unknown role: {role_id}", status=404)
            raw_perms = data.get("permissions")
            perms = (
                {str(p).strip() for p in raw_perms if str(p).strip()}
                if raw_perms is not None
                else None
            )
            role = store.update(
                role_id, description=data.get("description"), permissions=perms
            )
            return self._role_payload(role)

    def delete_role(self, role_id: str) -> dict[str, Any]:
        with self.session_manager.session() as session:
            store = self._role_store(session)
            try:
                removed = store.delete(role_id)
            except BaselineRoleProtected as exc:
                raise RolesServiceError(
                    "FORBIDDEN",
                    f"baseline role cannot be deleted: {exc}",
                    status=403,
                )
            if not removed:
                raise RolesServiceError("NOT_FOUND", f"unknown role: {role_id}", status=404)
            return {"deleted": role_id}
