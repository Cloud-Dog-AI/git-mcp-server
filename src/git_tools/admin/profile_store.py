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

"""DB-backed, process-shared repository-profile store (W28C-1705 GM2 / 1603-unblocker).

The api / mcp / a2a surfaces each previously held a private in-memory ``dict`` of
profiles, so a profile created through one surface was invisible to the others and
evaporated on restart. ``ProfileStore`` implements the same ``MutableMapping`` interface
those surfaces already use (``store.get(name)`` / ``store[name] = body`` / ``del`` /
``name in store``) but persists to the durable ``git_profile_registry`` table on the
shared container data volume. Every read hits the DB, so a profile created via REST on the
api process is immediately visible to ``repo_open`` on the separate mcp process. Deletes
are soft (``is_active = False``), mirroring file-mcp's ``file_storage_profiles``.
"""

from __future__ import annotations

import json
from collections.abc import Iterator, MutableMapping
from typing import Any
from uuid import uuid4

from sqlalchemy import select

from git_tools.db.models import GitProfileRegistry


def _new_profile_id() -> str:
    return f"prof_{uuid4().hex[:12]}"


def _display_name(name: str, body: dict[str, Any] | None) -> str:
    return str((body or {}).get("display_name") or name)


class ProfileStore(MutableMapping):
    """Durable, cross-surface profile store keyed by profile name."""

    def __init__(
        self,
        session_manager: Any,
        seed_profiles: dict[str, dict[str, Any]] | None = None,
        authoritative_seed_names: set[str] | None = None,
    ) -> None:
        self._session_manager = session_manager
        if seed_profiles:
            self._backfill(seed_profiles, authoritative_seed_names or set())

    def _backfill(
        self,
        seed_profiles: dict[str, dict[str, Any]],
        authoritative_seed_names: set[str],
    ) -> None:
        """Insert any seed profile missing from the table (one-time, idempotent).

        The DB remains authoritative for ordinary profiles. Environment-managed seed
        names (the configured WebUI default profile) are reconciled on startup so a
        legitimate deployment config change cannot leave the browser and tool
        registry resolving different repository sources.
        """
        with self._session_manager.session() as session:
            for name, body in seed_profiles.items():
                existing = session.execute(
                    select(GitProfileRegistry).where(GitProfileRegistry.name == name)
                ).scalar_one_or_none()
                if existing is None:
                    session.add(
                        GitProfileRegistry(
                            id=_new_profile_id(),
                            name=name,
                            display_name=_display_name(name, body),
                            config_json=json.dumps(body),
                            is_active=True,
                        )
                    )
                elif name in authoritative_seed_names:
                    existing.config_json = json.dumps(body)
                    existing.display_name = _display_name(name, body)
                    existing.is_active = True
            session.commit()

    def __getitem__(self, name: str) -> dict[str, Any]:
        with self._session_manager.session() as session:
            row = session.execute(
                select(GitProfileRegistry).where(
                    GitProfileRegistry.name == name,
                    GitProfileRegistry.is_active.is_(True),
                )
            ).scalar_one_or_none()
            if row is None:
                raise KeyError(name)
            return json.loads(row.config_json)

    def __setitem__(self, name: str, value: dict[str, Any]) -> None:
        payload = json.dumps(value)
        display = _display_name(name, value)
        with self._session_manager.session() as session:
            row = session.execute(
                select(GitProfileRegistry).where(GitProfileRegistry.name == name)
            ).scalar_one_or_none()
            if row is None:
                session.add(
                    GitProfileRegistry(
                        id=_new_profile_id(),
                        name=name,
                        display_name=display,
                        config_json=payload,
                        is_active=True,
                    )
                )
            else:
                row.config_json = payload
                row.display_name = display
                row.is_active = True  # un-soft-delete on re-create
            session.commit()

    def __delitem__(self, name: str) -> None:
        with self._session_manager.session() as session:
            row = session.execute(
                select(GitProfileRegistry).where(
                    GitProfileRegistry.name == name,
                    GitProfileRegistry.is_active.is_(True),
                )
            ).scalar_one_or_none()
            if row is None:
                raise KeyError(name)
            row.is_active = False  # soft-delete (mirrors file-mcp file_storage_profiles)
            session.commit()

    def __iter__(self) -> Iterator[str]:
        with self._session_manager.session() as session:
            names = (
                session.execute(
                    select(GitProfileRegistry.name).where(GitProfileRegistry.is_active.is_(True))
                )
                .scalars()
                .all()
            )
        return iter(list(names))

    def __len__(self) -> int:
        with self._session_manager.session() as session:
            names = (
                session.execute(
                    select(GitProfileRegistry.name).where(GitProfileRegistry.is_active.is_(True))
                )
                .scalars()
                .all()
            )
        return len(names)
