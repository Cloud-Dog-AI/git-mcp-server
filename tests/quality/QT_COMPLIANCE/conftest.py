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

"""Shared fixtures for W25A QT compliance static-analysis tests."""

from __future__ import annotations

import re
from pathlib import Path

import pytest


@pytest.fixture(scope="session")
def project_root() -> Path:
    """Return repository root path."""
    return Path(__file__).resolve().parents[3]


@pytest.fixture(scope="session")
def src_dir(project_root: Path) -> Path:
    """Return source directory path."""
    return project_root / "src"


@pytest.fixture(scope="session")
def src_python_files(src_dir: Path) -> list[Path]:
    """Return all Python source files."""
    return sorted(src_dir.rglob("*.py"))


@pytest.fixture(scope="session")
def test_python_files(project_root: Path) -> list[Path]:
    """Return all Python test files."""
    return sorted((project_root / "tests").rglob("*.py"))


@pytest.fixture(scope="session")
def requirements_doc(project_root: Path) -> Path:
    """Resolve requirements document path."""
    candidate = project_root / "docs" / "REQUIREMENTS.md"
    if candidate.exists():
        return candidate
    return project_root / "REQUIREMENTS.md"


@pytest.fixture(scope="session")
def tests_doc(project_root: Path) -> Path:
    """Resolve tests document path."""
    candidate = project_root / "docs" / "TESTS.md"
    if candidate.exists():
        return candidate
    return project_root / "TESTS.md"


@pytest.fixture(scope="session")
def requirement_id_pattern() -> re.Pattern[str]:
    """Canonical requirement ID matcher for traceability checks."""
    return re.compile(r"\b(?:FR|UC|NF|CS|BR|BO|SV)-\d+(?:\.\d+)?\b")


@pytest.fixture(scope="session")
def allowlist() -> dict[str, object]:
    """Known exceptions with explicit migration TODO notes."""
    return {
        "hardcoded_url_lines": set(),
        "os_environ_config_adapter_files": {
            # W28A-654 import-time ContextVar defaults must read the process
            # environment before the config loader spins up, otherwise audit
            # tasks inherit the wrong environment/service-instance defaults.
            "src/git_mcp_server/main.py",
        },
        "fixture_env_access_patterns": [],
        "unused_env_keys": set(),
    }
