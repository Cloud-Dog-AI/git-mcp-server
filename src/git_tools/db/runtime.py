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

"""cloud_dog_db runtime integration for git-mcp-server."""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from threading import Lock
from typing import Any

from cloud_dog_config import reload_config
from cloud_dog_storage import path_utils
from cloud_dog_db import (
    DatabaseSettings,
    MigrationRunner,
    SyncSessionManager,
    build_sync_engine,
    probe_database,
)
from cloud_dog_db.migrations.runner import MigrationConfig
from sqlalchemy import Engine
from sqlalchemy.engine import make_url


@dataclass(slots=True)
class PlatformDatabaseRuntime:
    settings: DatabaseSettings
    engine: Engine
    session_manager: SyncSessionManager
    migration_runner: MigrationRunner


_RUNTIME_LOCK = Lock()
_RUNTIME: PlatformDatabaseRuntime | None = None


def _project_root():
    current = path_utils.as_path(__file__).resolve()
    for candidate in current.parents:
        if (candidate / "pyproject.toml").exists():
            return candidate
    return current.parents[3]


def _default_sqlite_path() -> str:
    return "./data/git_mcp.db"


def _tree_from_config(config: Any | None, env_files: list[str] | None = None) -> dict[str, Any]:
    """Normalise config inputs into a plain mapping tree."""
    if config is None:
        return dict(
            reload_config(
                env_files=list(env_files) if env_files else None,
                config_yaml="config.yaml",
                defaults_yaml="defaults.yaml",
            ).data
        )
    if isinstance(config, dict):
        return config
    data = getattr(config, "data", None)
    if data is not None:
        return dict(data)
    dump = getattr(config, "model_dump", None)
    if callable(dump):
        return dict(dump(mode="python"))
    return {}


def _settings_from_config(config: Any | None, env_files: list[str] | None = None) -> DatabaseSettings:
    tree = _tree_from_config(config, env_files=env_files)

    payload: dict[str, Any] = {}
    for key in ("db", "cloud_dog_db"):
        db_node = tree.get(key)
        if not isinstance(db_node, Mapping):
            continue
        explicit_url = str(db_node.get("url", "") or "").strip()
        if explicit_url:
            return DatabaseSettings(url=explicit_url)

        for field in (
            "dialect",
            "driver",
            "host",
            "port",
            "username",
            "password",
            "database",
            "path",
            "schema_name",
        ):
            value = db_node.get(field)
            if value is None:
                continue
            value_text = str(value).strip()
            if value_text:
                payload[field] = value_text

    if payload:
        if not str(payload.get("database") or "").strip() and not str(payload.get("url") or "").strip():
            payload["database"] = _default_sqlite_path()
        return DatabaseSettings.model_validate(payload)

    storage_node = tree.get("storage")
    if isinstance(storage_node, Mapping):
        db_storage = storage_node.get("db")
        if isinstance(db_storage, Mapping):
            configured_url = str(db_storage.get("url", "") or "").strip()
            if configured_url:
                return DatabaseSettings(url=configured_url)

    return DatabaseSettings(dialect="sqlite", database=_default_sqlite_path())


def _sqlite_path(settings: DatabaseSettings):
    url = make_url(settings.to_sync_url())
    if url.get_backend_name() != "sqlite":
        return None
    if not url.database or url.database == ":memory:":
        return None
    path = path_utils.as_path(url.database)
    if not path.is_absolute():
        path = _project_root() / path
    return path


def _migration_script_location() -> str:
    return str((_project_root() / "database" / "migrations" / "cloud_dog_db").resolve())


def initialise_database(
    config: Any | None = None,
    *,
    env_files: list[str] | None = None,
    force_reinit: bool = False,
) -> PlatformDatabaseRuntime:
    """Initialise engine/session/migrations through cloud_dog_db."""
    global _RUNTIME
    with _RUNTIME_LOCK:
        if _RUNTIME is not None and not force_reinit:
            return _RUNTIME

        settings = _settings_from_config(config, env_files=env_files)
        sqlite_path = _sqlite_path(settings)
        if sqlite_path is not None:
            sqlite_path.parent.mkdir(parents=True, exist_ok=True)

        engine = build_sync_engine(settings)
        session_manager = SyncSessionManager(engine)
        runner = MigrationRunner(
            MigrationConfig(
                script_location=_migration_script_location(),
                sqlalchemy_url=settings.to_sync_url(),
            )
        )
        runner.upgrade("head")

        _RUNTIME = PlatformDatabaseRuntime(
            settings=settings,
            engine=engine,
            session_manager=session_manager,
            migration_runner=runner,
        )
        return _RUNTIME


def database_health(runtime: PlatformDatabaseRuntime | None = None) -> dict[str, Any]:
    """Return DB probe details for health handlers."""
    active = runtime or _RUNTIME
    if active is None:
        return {"ok": False, "status": "not_initialised"}
    try:
        probe = probe_database(active.engine)
        return {"ok": bool(probe.get("ok", False)), "probe": probe}
    except Exception as exc:  # noqa: BLE001
        return {"ok": False, "error": str(exc)}


def shutdown_database() -> None:
    """Dispose database engine."""
    global _RUNTIME
    with _RUNTIME_LOCK:
        if _RUNTIME is None:
            return
        _RUNTIME.engine.dispose()
        _RUNTIME = None
