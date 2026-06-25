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

from pathlib import Path

from alembic.config import Config
from alembic.script import ScriptDirectory
from sqlalchemy import text

from git_tools.db.models import GitPlatformDbState
from git_tools.db.runtime import (
    _migration_script_location,
    initialise_database,
    shutdown_database,
)
import pytest


def _alembic_head_revision() -> str:
    """Return the CURRENT alembic head from the shipped migration scripts.

    Derived dynamically (not hardcoded) so the assertion tracks the real head
    and does not re-stale every time a new migration lands (it previously pinned
    ``20260305_0001`` and broke when W28C-1705 GM2 added ``20260609_0002``).
    """
    cfg = Config()
    cfg.set_main_option("script_location", _migration_script_location())
    return ScriptDirectory.from_config(cfg).get_current_head()


def _configure_sqlite_env(monkeypatch, db_path: Path) -> None:
    monkeypatch.setenv("CLOUD_DOG__DB__DIALECT", "sqlite")
    monkeypatch.setenv("CLOUD_DOG__DB__DATABASE", str(db_path))
    monkeypatch.setenv("CLOUD_DOG_DB__DIALECT", "sqlite")
    monkeypatch.setenv("CLOUD_DOG_DB__DATABASE", str(db_path))
    monkeypatch.delenv("CLOUD_DOG__DB__URL", raising=False)
    monkeypatch.delenv("CLOUD_DOG_DB__URL", raising=False)
    monkeypatch.delenv("CLOUD_DOG_DB__HOST", raising=False)
    monkeypatch.delenv("CLOUD_DOG_DB__PORT", raising=False)
    monkeypatch.delenv("CLOUD_DOG_DB__USERNAME", raising=False)
    monkeypatch.delenv("CLOUD_DOG_DB__PASSWORD", raising=False)
@pytest.mark.ST
@pytest.mark.mcp
@pytest.mark.req("FR-020")  # W28E-1804A semantic rebind


def test_st_db_01_migration_upgrade_on_fresh_sqlite(monkeypatch, tmp_path: Path) -> None:
    """Requirements: FR-17."""
    db_path = tmp_path / "git-mcp-st-migration.db"
    _configure_sqlite_env(monkeypatch, db_path)

    runtime = initialise_database(force_reinit=True)
    try:
        assert db_path.exists() is True
        with runtime.engine.connect() as conn:
            revision = conn.execute(text("SELECT version_num FROM alembic_version")).scalar_one()
        assert revision == _alembic_head_revision()
    finally:
        shutdown_database()
@pytest.mark.ST
@pytest.mark.mcp
@pytest.mark.req("FR-020")  # W28E-1804A semantic rebind


def test_st_db_02_crud_via_session_manager(monkeypatch, tmp_path: Path) -> None:
    """Requirements: FR-17."""
    db_path = tmp_path / "git-mcp-st-crud.db"
    _configure_sqlite_env(monkeypatch, db_path)

    runtime = initialise_database(force_reinit=True)
    try:
        with runtime.session_manager.session() as session:
            session.add(GitPlatformDbState(service="git-st", status="ready"))

        with runtime.session_manager.session() as session:
            row = session.query(GitPlatformDbState).filter_by(service="git-st").one()
            row.status = "verified"

        with runtime.session_manager.session() as session:
            verified = session.query(GitPlatformDbState).filter_by(service="git-st").one()
            assert verified.status == "verified"
    finally:
        shutdown_database()
