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

"""W25A static checks for migration completeness."""

from __future__ import annotations

import re
from pathlib import Path


def _rel(project_root: Path, file_path: Path) -> str:
    return file_path.resolve().relative_to(project_root.resolve()).as_posix()


def test_no_yaml_safe_load_for_config(project_root: Path, src_python_files: list[Path]) -> None:
    violations: list[str] = []
    for file_path in src_python_files:
        rel = _rel(project_root, file_path)
        text = file_path.read_text(encoding="utf-8")
        if "yaml.safe_load(" not in text and "yaml.load(" not in text:
            continue
        # Only flag config loading paths. Non-config document parsing (edit/validate tools) is out of scope.
        if "/config/" in rel or "config" in file_path.stem:
            violations.append(rel)
    assert not violations, "yaml.safe_load/yaml.load used for config paths:\n" + "\n".join(violations)


def test_no_raw_fastapi(src_python_files: list[Path], project_root: Path) -> None:
    violations: list[str] = []
    pattern = re.compile(r"(?<!\w)FastAPI\(")
    for file_path in src_python_files:
        rel = _rel(project_root, file_path)
        for idx, line in enumerate(file_path.read_text(encoding="utf-8").splitlines(), 1):
            if pattern.search(line):
                violations.append(f"{rel}:{idx} -> {line.strip()}")
    assert not violations, "Raw FastAPI() instantiation detected:\n" + "\n".join(violations)


def test_no_bespoke_auth(src_python_files: list[Path], project_root: Path) -> None:
    patterns = [
        re.compile(r"\bAPIKeyHeader\("),
        re.compile(r"def\s+verify_token\s*\("),
    ]
    violations: list[str] = []
    for file_path in src_python_files:
        rel = _rel(project_root, file_path)
        for idx, line in enumerate(file_path.read_text(encoding="utf-8").splitlines(), 1):
            if any(p.search(line) for p in patterns):
                violations.append(f"{rel}:{idx} -> {line.strip()}")
    assert not violations, "Bespoke auth implementation detected:\n" + "\n".join(violations)


def test_no_os_environ_for_config(
    src_python_files: list[Path],
    project_root: Path,
    allowlist: dict[str, object],
) -> None:
    allowed_files = set(allowlist["os_environ_config_adapter_files"])
    pattern = re.compile(r"os\.getenv\(|os\.environ(\[|\.get\()")
    violations: list[str] = []

    for file_path in src_python_files:
        rel = _rel(project_root, file_path)
        for idx, line in enumerate(file_path.read_text(encoding="utf-8").splitlines(), 1):
            if not pattern.search(line):
                continue
            if rel in allowed_files:
                continue
            violations.append(f"{rel}:{idx} -> {line.strip()}")

    assert not violations, "os.environ/os.getenv config access outside adapter allowlist:\n" + "\n".join(violations)
