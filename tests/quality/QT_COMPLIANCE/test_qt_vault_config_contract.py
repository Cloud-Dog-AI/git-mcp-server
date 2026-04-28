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

"""W25A static checks for vault/config/secret contracts."""

from __future__ import annotations

import re
from pathlib import Path


def _load_env_map(path: Path) -> dict[str, str]:
    values: dict[str, str] = {}
    for line in path.read_text(encoding="utf-8").splitlines():
        raw = line.strip()
        if not raw or raw.startswith("#") or "=" not in raw:
            continue
        key, value = raw.split("=", 1)
        values[key.strip()] = value.strip()
    return values


def test_defaults_yaml_exists(project_root: Path) -> None:
    assert (project_root / "defaults.yaml").exists(), "defaults.yaml is required"


def _yaml_has_plaintext_secret(text: str) -> bool:
    for line in text.splitlines():
        stripped = line.strip()
        if not stripped or stripped.startswith("#") or ":" not in stripped:
            continue
        key, value = stripped.split(":", 1)
        if not re.search(r"(?i)\b(password|token|api[_-]?key|secret)\b", key):
            continue
        clean = value.strip().strip('"').strip("'")
        if not clean or clean.startswith("${"):
            continue
        return True
    return False


def test_defaults_yaml_no_secrets(project_root: Path) -> None:
    text = (project_root / "defaults.yaml").read_text(encoding="utf-8")
    hits: list[str] = []
    if _yaml_has_plaintext_secret(text):
        hits.append("plaintext_secret_key")
    literal_patterns = [
        re.compile(r"(?i)\b(glpat-|hvs\.|sk-or-v1-)\b"),
    ]
    hits.extend(pat.pattern for pat in literal_patterns if pat.search(text))
    assert not hits, f"Potential secrets detected in defaults.yaml: {hits}"


def test_config_yaml_no_secrets(project_root: Path) -> None:
    path = project_root / "config.yaml"
    if not path.exists():
        return
    text = path.read_text(encoding="utf-8")
    hits: list[str] = []
    if _yaml_has_plaintext_secret(text):
        hits.append("plaintext_secret_key")
    literal_patterns = [
        re.compile(r"(?i)\b(glpat-|hvs\.|sk-or-v1-)\b"),
    ]
    hits.extend(pat.pattern for pat in literal_patterns if pat.search(text))
    assert not hits, f"Potential secrets detected in config.yaml: {hits}"


def test_env_files_use_vault_expressions(project_root: Path) -> None:
    # Dev/test keys (e.g., TEST_A2A_API_KEY) are allowed in tests/env-* by policy.
    credentials_requiring_vault = re.compile(r"(?i)(PASSWORD|TOKEN|SECRET|USERNAME)")
    allowed_test_prefix = "TEST_"
    violations: list[str] = []

    for env_path in sorted((project_root / "tests").glob("env-IT*")) + sorted((project_root / "tests").glob("env-AT*")):
        values = _load_env_map(env_path)
        for key, value in values.items():
            if not credentials_requiring_vault.search(key):
                continue
            if key.startswith(allowed_test_prefix):
                continue
            if value.startswith("${vault.dev."):
                continue
            violations.append(f"{env_path.as_posix()}::{key}={value}")

    assert not violations, "IT/AT credential keys must use ${vault.dev.*} expressions:\n" + "\n".join(violations)


def test_no_secrets_in_source(src_python_files: list[Path], project_root: Path) -> None:
    patterns = [
        re.compile(r"(?i)\b(glpat-[a-z0-9]{10,}|hvs\.[a-z0-9_-]{10,}|sk-or-v1-[a-z0-9_-]{10,})\b"),
        re.compile(r"(?i)\b(password|token|api[_-]?key|secret)\b\s*=\s*['\"][^'\"]{12,}['\"]"),
    ]
    violations: list[str] = []
    for file_path in src_python_files:
        rel = file_path.resolve().relative_to(project_root.resolve()).as_posix()
        for idx, line in enumerate(file_path.read_text(encoding="utf-8").splitlines(), 1):
            if line.strip().startswith("#"):
                continue
            if any(p.search(line) for p in patterns):
                violations.append(f"{rel}:{idx} -> {line.strip()}")
    assert not violations, "Potential secrets in src/:\n" + "\n".join(violations)


def test_env_files_exist_per_tier(project_root: Path) -> None:
    required = ["env-UT", "env-ST", "env-IT", "env-AT"]
    missing = [name for name in required if not (project_root / "tests" / name).exists()]
    assert not missing, f"Missing required tier env files: {missing}"
