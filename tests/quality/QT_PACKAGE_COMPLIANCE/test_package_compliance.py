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

"""Automated package compliance checks for platform package adoption."""

from __future__ import annotations

from pathlib import Path
import re


PROJECT_ROOT = Path(__file__).resolve().parents[3]
SRC_DIR = PROJECT_ROOT / "src"


def _read(path: Path) -> str:
    return path.read_text(encoding="utf-8", errors="ignore")


def _iter_python_files(root: Path) -> list[Path]:
    return sorted(
        path
        for path in root.rglob("*.py")
        if "__pycache__" not in path.parts and ".venv" not in path.parts
    )


def _scan(pattern: re.Pattern[str], *, root: Path = SRC_DIR) -> list[str]:
    hits: list[str] = []
    for path in _iter_python_files(root):
        rel = path.relative_to(PROJECT_ROOT).as_posix()
        for line_no, line in enumerate(_read(path).splitlines(), 1):
            if pattern.search(line):
                hits.append(f"{rel}:{line_no}: {line.strip()}")
    return hits


def test_package_compliance_logging_uses_platform() -> None:
    """Requirements: FR-01."""
    all_text = "\n".join(_read(path) for path in _iter_python_files(SRC_DIR))
    assert "cloud_dog_logging" in all_text, "Missing cloud_dog_logging usage in src/"

    hits = _scan(re.compile(r"\blogging\.(?:getLogger|basicConfig)\s*\("))
    assert not hits, "Bespoke stdlib logging calls detected:\n" + "\n".join(hits[:20])


def test_package_compliance_config_uses_platform() -> None:
    """Requirements: FR-01."""
    all_text = "\n".join(_read(path) for path in _iter_python_files(SRC_DIR))
    assert "cloud_dog_config" in all_text, "Missing cloud_dog_config usage in src/"

    hits = _scan(re.compile(r"\bload_dotenv\s*\(|\b(?:ConfigManager|config_manager)\b"))
    real_hits = [hit for hit in hits if "cloud_dog_config" not in hit]
    assert not real_hits, "Bespoke config helpers detected:\n" + "\n".join(real_hits[:20])


def test_package_compliance_auth_uses_platform() -> None:
    """Requirements: FR-01."""
    auth_files = _iter_python_files(SRC_DIR / "git_mcp_server" / "auth")
    auth_text = "\n".join(_read(path) for path in auth_files)
    assert "cloud_dog_idam" in auth_text, "git_mcp_server auth stack must delegate to cloud_dog_idam"

    hits = _scan(re.compile(r"\bAPIKeyHeader\s*\(|\bdef\s+verify_token\s*\("))
    assert not hits, "Bespoke auth entry points detected:\n" + "\n".join(hits[:20])


def test_package_compliance_jobs_avoid_bespoke_queue_primitives() -> None:
    """Requirements: FR-01."""
    hits = _scan(re.compile(r"\bThreadPoolExecutor\b|\basyncio\.Queue\b"))
    assert not hits, "Bespoke queue/thread primitives detected:\n" + "\n".join(hits[:20])


def test_package_compliance_no_direct_llm_calls() -> None:
    """Requirements: FR-01."""
    hits = _scan(
        re.compile(
            r"\bopenai\.OpenAI\s*\(|\bopenai\.ChatCompletion\b|\bollama\.chat\s*\(|httpx\.(?:AsyncClient|Client).*(?:ollama|openai)"
        )
    )
    assert not hits, "Direct LLM client calls detected:\n" + "\n".join(hits[:20])


def test_package_compliance_no_hardcoded_runtime_secrets() -> None:
    """Requirements: FR-06."""
    pattern = re.compile(
        r"\b[a-zA-Z_]*(?:password|secret|token|api_key|client_secret)\b\s*(?::[^=\n]+)?=\s*['\"][^'\"]+['\"]"
    )
    hits = _scan(pattern)
    real_hits = [
        hit
        for hit in hits
        if not any(
            marker in hit.lower()
            for marker in (
                "example",
                "placeholder",
                "changeme",
                "test_api_key",
                "headers.get(",
            )
        )
    ]
    assert not real_hits, "Hardcoded runtime secrets detected:\n" + "\n".join(real_hits[:20])


def test_package_compliance_no_internal_hostnames() -> None:
    """Requirements: FR-01."""
    hits = _scan(re.compile(r"cloud-dog\.net|viewdeck\.com|vault0\.|server0\.|db1\.app"))
    assert not hits, "Internal hostnames must not appear in src/: \n" + "\n".join(hits[:20])


def test_package_compliance_pyproject_declares_platform_packages() -> None:
    """Requirements: FR-01."""
    pyproject_text = (PROJECT_ROOT / "pyproject.toml").read_text(encoding="utf-8")
    required = [
        "cloud_dog_config",
        "cloud_dog_logging",
        "cloud_dog_api_kit",
        "cloud_dog_idam",
        "cloud_dog_db",
        "cloud_dog_jobs",
    ]
    missing = [package for package in required if package not in pyproject_text]
    assert not missing, "Missing required platform packages in pyproject.toml: " + ", ".join(missing)


def test_package_compliance_server_scripts_and_docs_exist() -> None:
    """Requirements: FR-01, FR-17."""
    required_paths = [
        PROJECT_ROOT / "server_control.sh",
        PROJECT_ROOT / "LICENCE",
        PROJECT_ROOT / "README.md",
    ]
    missing = [path.name for path in required_paths if not path.exists()]
    assert not missing, "Required project control/docs files missing: " + ", ".join(missing)
