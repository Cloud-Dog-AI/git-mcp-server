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

"""Shared pytest environment fixtures.

Requirements: NFR-07.
"""

from __future__ import annotations

import os
import re
import sys
from contextlib import suppress
from functools import lru_cache
from pathlib import Path

import pytest
from cloud_dog_config import load_config
from cloud_dog_config.compiler.vault_resolver import resolve_vault_identifier
from cloud_dog_config.vault.client import VaultClient, VaultConnectionConfig

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
TESTS_DIR = ROOT / "tests"
_KNOWN_TIERS = {"UT", "ST", "IT", "AT", "QT"}
_VAULT_REF_PATTERN = re.compile(r"^\$\{(vault\.[^}]+)\}$")
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))


def pytest_addoption(parser: pytest.Parser) -> None:
    """Add --env option for test environment selection."""
    with suppress(ValueError):
        parser.addoption(
            "--env",
            action="append",
            required=False,
            help="Test environment(s): tier IDs (UT/ST/IT/AT/QT) or env file paths.",
        )


def pytest_configure(config: pytest.Config) -> None:
    """Avoid basetemp collisions across concurrent pytest processes."""
    basetemp = str(getattr(config.option, "basetemp", "") or "")
    if basetemp == "working/pytest-tmp":
        config.option.basetemp = f"working/pytest-tmp-{os.getpid()}"


def _resolve_env_file(value: str) -> Path:
    raw = value.strip()
    if not raw:
        raise FileNotFoundError("Empty --env value")

    token = raw.upper()
    if token in _KNOWN_TIERS:
        path = TESTS_DIR / f"env-{token}"
        if path.exists():
            return path
        raise FileNotFoundError(f"Tier env file not found: {path}")

    candidate = Path(raw)
    if not candidate.is_absolute():
        candidate = ROOT / candidate
    candidate = candidate.resolve()
    if candidate.exists():
        return candidate

    named = (TESTS_DIR / raw).resolve()
    if named.exists():
        return named
    raise FileNotFoundError(f"Env file not found: {raw}")


def _tier_from_env_file(path: Path) -> str | None:
    for line in path.read_text(encoding="utf-8").splitlines():
        raw = line.strip()
        if not raw or raw.startswith("#") or "=" not in raw:
            continue
        key, value = raw.split("=", 1)
        if key.strip() != "TEST_ENV_TIER":
            continue
        tier = value.strip().upper()
        if tier in _KNOWN_TIERS:
            return tier
        return None
    if path.name.startswith("env-"):
        inferred = path.name.removeprefix("env-").split("-", 1)[0].upper()
        if inferred in _KNOWN_TIERS:
            return inferred
    return None


def _is_unresolved_env_value(value: str | None) -> bool:
    if value is None:
        return True
    candidate = value.strip()
    if not candidate:
        return True
    return bool(_VAULT_REF_PATTERN.match(candidate))


@lru_cache(maxsize=1)
def _vault_client() -> VaultClient | None:
    addr = os.environ.get("VAULT_ADDR", "").strip().rstrip("/")
    token = os.environ.get("VAULT_TOKEN", "").strip()
    mount = os.environ.get("VAULT_MOUNT_POINT", "").strip().strip("/")
    config_path = os.environ.get("VAULT_CONFIG_PATH", "").strip().strip("/")
    if config_path:
        mount = "/".join([part for part in (mount, config_path) if part])
    if addr and token and mount:
        try:
            return VaultClient(
                VaultConnectionConfig(
                    server=addr,
                    token=token,
                    timeout_seconds=10.0,
                    mount_point=mount,
                )
            )
        except Exception:
            return None

    try:
        snapshot = load_config(config_yaml="config.yaml", defaults_yaml="defaults.yaml")
    except Exception:
        return None

    tree = dict(snapshot.data)
    vault_node = tree.get("vault")
    if not isinstance(vault_node, dict):
        return None

    addr = str(vault_node.get("server", "") or "").strip().rstrip("/")
    token = str(vault_node.get("key", "") or "").strip()
    if not addr or not token:
        return None

    mount = str(vault_node.get("mount_point", "") or "").strip().strip("/")
    config_path = str(vault_node.get("config_path", "") or "").strip().strip("/")
    if config_path:
        mount = "/".join([part for part in (mount, config_path) if part])

    try:
        return VaultClient(
            VaultConnectionConfig(
                server=addr,
                token=token,
                timeout_seconds=10.0,
                mount_point=mount,
            )
        )
    except Exception:
        return None


def _resolve_env_value(raw_value: str) -> str:
    value = raw_value.strip()
    if not value:
        return value
    match = _VAULT_REF_PATTERN.match(value)
    if match is None:
        return value
    client = _vault_client()
    if client is None:
        return value
    resolved = resolve_vault_identifier(match.group(1), vault=client)
    if isinstance(resolved, (str, int, float, bool)):
        resolved_text = str(resolved).strip()
        if resolved_text:
            return resolved_text
    return value


def _is_qt_compliance_only_run(config: pytest.Config) -> bool:
    """Return True when current invocation targets QT compliance static-analysis tests only."""
    args = [str(item) for item in config.invocation_params.args]
    selected_paths = [item for item in args if item and not item.startswith("-")]
    if not selected_paths:
        return False
    normalised = [item.replace("\\", "/") for item in selected_paths]
    marker = "/tests/quality/QT_COMPLIANCE"
    return all(path.startswith("tests/quality/QT_COMPLIANCE") or marker in f"/{path}" for path in normalised)


def _is_unit_only_run(config: pytest.Config) -> bool:
    """Return True when current invocation targets unit tests only."""
    args = [str(item) for item in config.invocation_params.args]
    selected_paths = [item for item in args if item and not item.startswith("-")]
    if not selected_paths:
        return False
    normalised = [item.replace("\\", "/") for item in selected_paths]
    marker = "/tests/unit"
    return all(path.startswith("tests/unit") or marker in f"/{path}" for path in normalised)


@pytest.fixture(scope="session")
def env_files(request: pytest.FixtureRequest) -> list[Path]:
    """Resolve --env values to concrete env files."""
    values = request.config.getoption("--env")
    items: list[str]
    if isinstance(values, str):
        items = [values]
    elif isinstance(values, list):
        items = values
    else:
        items = []

    if not items:
        if _is_qt_compliance_only_run(request.config):
            return []
        if _is_unit_only_run(request.config):
            return [_resolve_env_file("UT")]
        pytest.fail("--env is required unless running tests/quality/QT_COMPLIANCE/")

    resolved: list[Path] = []
    for item in items:
        try:
            resolved.append(_resolve_env_file(item))
        except FileNotFoundError as exc:
            pytest.fail(str(exc))
    unique: list[Path] = []
    seen: set[str] = set()
    for path in resolved:
        token = str(path)
        if token in seen:
            continue
        seen.add(token)
        unique.append(path)
    return unique


@pytest.fixture(scope="session")
def envs(env_files: list[Path]) -> list[str]:
    """Return canonical env IDs (UT/ST/IT/AT/QT) from resolved env files."""
    resolved: list[str] = []
    for env_file in env_files:
        tier = _tier_from_env_file(env_file)
        if tier is not None:
            resolved.append(tier)
    if resolved:
        return list(dict.fromkeys(resolved))
    return []


@pytest.fixture(scope="session", autouse=True)
def load_env_files(env_files: list[Path]) -> dict[str, str]:
    """Load configured env files before tests run."""
    loaded: dict[str, str] = {}
    if env_files:
        os.environ["TEST_ENV_FILE"] = str(env_files[0])
        os.environ["TEST_ENV_FILES"] = ",".join(str(path) for path in env_files)

    for env_file in env_files:
        for line in env_file.read_text(encoding="utf-8").splitlines():
            raw = line.strip()
            if not raw or raw.startswith("#") or "=" not in raw:
                continue
            key, value = raw.split("=", 1)
            env_key = key.strip()
            env_value = _resolve_env_value(value.strip())
            existing = os.environ.get(env_key)
            # Treat blank process env values as unset so env files can provide real test config.
            if existing is not None and existing.strip() and not _is_unresolved_env_value(existing):
                loaded[env_key] = existing
                continue
            os.environ[env_key] = env_value
            loaded[env_key] = env_value
    return loaded


@pytest.fixture(scope="session")
def env(envs: list[str]) -> str:
    """Keep backwards compatibility with single-env fixtures."""
    return envs[0]
