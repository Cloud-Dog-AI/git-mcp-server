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

import os
import subprocess
from pathlib import Path

from git_tools.db import runtime as db_runtime_module
from git_tools.db.models import GitPlatformDbState
from git_tools.db.runtime import database_health, initialise_database, shutdown_database


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


def test_ut_db_01_engine_factory_creates_sqlite_engine(monkeypatch, tmp_path: Path) -> None:
    """Requirements: FR-17."""
    db_path = tmp_path / "git-mcp-ut.db"
    _configure_sqlite_env(monkeypatch, db_path)

    runtime = initialise_database(force_reinit=True)
    try:
        assert runtime.engine.url.get_backend_name() == "sqlite"
        health = database_health(runtime)
        assert health["ok"] is True
    finally:
        shutdown_database()


def test_ut_db_02_session_manager_roundtrip(monkeypatch, tmp_path: Path) -> None:
    """Requirements: FR-17."""
    db_path = tmp_path / "git-mcp-ut-roundtrip.db"
    _configure_sqlite_env(monkeypatch, db_path)

    runtime = initialise_database(force_reinit=True)
    try:
        with runtime.session_manager.session() as session:
            session.add(GitPlatformDbState(service="git-mcp-server", status="ready"))

        with runtime.session_manager.session() as session:
            item = session.query(GitPlatformDbState).filter(GitPlatformDbState.service == "git-mcp-server").one()
            assert item.status == "ready"
    finally:
        shutdown_database()


def test_ut_db_03_cloud_dog_db_env_keys_are_consumed(monkeypatch) -> None:
    """Requirements: FR-17."""
    monkeypatch.setenv("CLOUD_DOG_DB__DIALECT", "postgresql")
    monkeypatch.setenv("CLOUD_DOG_DB__HOST", "db.example.test")
    monkeypatch.setenv("CLOUD_DOG_DB__PORT", "5432")
    monkeypatch.setenv("CLOUD_DOG_DB__USERNAME", "gitmcp")
    monkeypatch.setenv("CLOUD_DOG_DB__PASSWORD", "secret-value")
    monkeypatch.setenv("CLOUD_DOG_DB__DATABASE", "git_mcp")
    monkeypatch.delenv("CLOUD_DOG_DB__URL", raising=False)

    settings = db_runtime_module._settings_from_config(None)
    assert settings.dialect == "postgresql"
    assert settings.host == "db.example.test"
    assert str(settings.port) == "5432"
    assert settings.username == "gitmcp"
    assert settings.password_plain() == "secret-value"
    assert settings.database == "git_mcp"


def test_ut_db_04_local_docker_control_keys_are_consumed(tmp_path: Path) -> None:
    """Requirements: FR-17."""
    project_root = Path(__file__).resolve().parents[3]
    script_path = project_root / "local-docker-server.sh"
    runtime_env = tmp_path / "runtime.env"
    compose_file = tmp_path / "compose.yml"
    control_env = tmp_path / "control.env"
    docker_log = tmp_path / "docker.log"
    docker_stub = tmp_path / "docker"

    runtime_env.write_text(
        f"TEST_ENV_TIER=IT\nCLOUD_DOG__API_SERVER__HOST={os.environ['TEST_BIND_HOST']}\nCLOUD_DOG__API_SERVER__PORT=19031\n",
        encoding="utf-8",
    )
    compose_file.write_text("services:\n  all-in-one:\n    image: alpine:3.19\n", encoding="utf-8")
    control_env.write_text(
        "\n".join(
            [
                f"LOCAL_DOCKER_SOURCE_ENV={runtime_env}",
                f"LOCAL_DOCKER_COMPOSE_FILE={compose_file}",
                "LOCAL_DOCKER_PROJECT_NAME=git-mcp-ut",
                "LOCAL_DOCKER_COMPOSE_PROFILES=all-in-one",
                "LOCAL_DOCKER_SERVICES=all-in-one",
            ]
        )
        + "\n",
        encoding="utf-8",
    )
    docker_stub.write_text(
        "#!/usr/bin/env bash\n"
        "set -euo pipefail\n"
        'if [[ "$1" == "info" ]]; then\n'
        "  exit 0\n"
        "fi\n"
        'if [[ "$1" == "compose" ]]; then\n'
        '  echo "$*" >> "${DOCKER_LOG_FILE}"\n'
        "  exit 0\n"
        "fi\n"
        "exit 0\n",
        encoding="utf-8",
    )
    docker_stub.chmod(0o755)

    env = os.environ.copy()
    env["PATH"] = f"{tmp_path}:{env.get('PATH', '')}"
    env["DOCKER_LOG_FILE"] = str(docker_log)
    result = subprocess.run(
        ["bash", str(script_path), "--env", str(control_env), "status", "all"],
        cwd=project_root,
        capture_output=True,
        text=True,
        env=env,
        timeout=30,
        check=False,
    )

    assert result.returncode == 0, result.stderr
    logged = docker_log.read_text(encoding="utf-8")
    resolved_env = project_root / ".run" / f"{runtime_env.name}.compose-resolved"
    assert f"-f {compose_file}" in logged
    assert "--project-name git-mcp-ut" in logged
    assert "--profile all-in-one" in logged
    assert f"--env-file {resolved_env}" in logged
    assert "ps --status running -q all-in-one" in logged
