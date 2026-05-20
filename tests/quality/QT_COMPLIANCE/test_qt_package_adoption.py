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

"""W25A static checks for platform package adoption."""

from __future__ import annotations

import re
from pathlib import Path


def _read(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def test_config_uses_cloud_dog_config(src_python_files: list[Path]) -> None:
    all_text = "\n".join(_read(path) for path in src_python_files)
    assert "cloud_dog_config" in all_text, "Missing cloud_dog_config usage in src/"
    assert "load_dotenv(" not in all_text, "dotenv.load_dotenv detected; use cloud_dog_config"


def test_logging_uses_cloud_dog_logging(src_python_files: list[Path]) -> None:
    all_text = "\n".join(_read(path) for path in src_python_files)
    assert "cloud_dog_logging" in all_text, "Missing cloud_dog_logging usage in src/"
    assert "logging.basicConfig(" not in all_text, "logging.basicConfig detected; use cloud_dog_logging"
    assert "logging.getLogger(" not in all_text, "logging.getLogger detected; use cloud_dog_logging wrappers"


def test_api_uses_cloud_dog_api_kit(src_python_files: list[Path]) -> None:
    all_text = "\n".join(_read(path) for path in src_python_files)
    assert "cloud_dog_api_kit" in all_text, "Missing cloud_dog_api_kit usage in API project"
    assert re.search(r"(?<!\w)FastAPI\(", all_text) is None, (
        "Raw FastAPI() detected; use cloud_dog_api_kit.create_app()"
    )


def test_auth_uses_cloud_dog_idam(src_python_files: list[Path]) -> None:
    all_text = "\n".join(_read(path) for path in src_python_files)
    assert "cloud_dog_idam" in all_text, "Missing cloud_dog_idam usage in API project"
    assert "APIKeyHeader(" not in all_text, "Bespoke APIKeyHeader auth detected"
    assert re.search(r"def\s+verify_token\s*\(", all_text) is None, "Bespoke verify_token detected"


def test_no_bespoke_db_access(src_python_files: list[Path]) -> None:
    violations = []
    for file_path in src_python_files:
        text = _read(file_path)
        if "create_engine(" in text or "sqlite3.connect(" in text:
            violations.append(file_path.as_posix())
    assert not violations, "Bespoke DB access detected:\n" + "\n".join(violations)


def test_no_bespoke_llm_calls(src_python_files: list[Path]) -> None:
    all_text = "\n".join(_read(path) for path in src_python_files)
    assert "openai.OpenAI(" not in all_text, "Direct openai.OpenAI call detected; use cloud_dog_llm"
    assert "ollama.chat(" not in all_text, "Direct ollama.chat call detected; use cloud_dog_llm"


def test_no_bespoke_vdb_calls(src_python_files: list[Path]) -> None:
    all_text = "\n".join(_read(path) for path in src_python_files)
    assert "chromadb.Client(" not in all_text, "Direct chromadb.Client detected; use cloud_dog_vdb"
    assert "qdrant_client.QdrantClient(" not in all_text, "Direct qdrant client detected; use cloud_dog_vdb"


def test_pyproject_declares_platform_packages(project_root: Path) -> None:
    pyproject_text = (project_root / "pyproject.toml").read_text(encoding="utf-8")
    required = [
        "cloud_dog_config",
        "cloud_dog_logging",
        "cloud_dog_api_kit",
        "cloud_dog_idam",
        "cloud_dog_db",
    ]
    missing = [pkg for pkg in required if pkg not in pyproject_text]
    assert not missing, f"Missing required platform packages in pyproject.toml: {missing}"
