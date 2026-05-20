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

"""W25A static checks for rules compliance."""

from __future__ import annotations

import ast
import re
from collections import defaultdict
from pathlib import Path


def _rel(project_root: Path, file_path: Path) -> str:
    return file_path.resolve().relative_to(project_root.resolve()).as_posix()


def _is_comment_or_empty(line: str) -> bool:
    stripped = line.strip()
    return not stripped or stripped.startswith("#")


def test_no_hardcoded_urls(project_root: Path, src_python_files: list[Path], allowlist: dict[str, object]) -> None:
    patterns = [
        re.compile(r"https?://[^\s\"']+"),
        re.compile(r"\blocalhost\b", re.IGNORECASE),
        re.compile(r"\b127\.0\.0\.1\b"),
        re.compile(r"/app/"),
    ]
    allowed = set(allowlist["hardcoded_url_lines"])
    violations: list[str] = []

    for file_path in src_python_files:
        rel = _rel(project_root, file_path)
        for idx, line in enumerate(file_path.read_text(encoding="utf-8").splitlines(), 1):
            if _is_comment_or_empty(line):
                continue
            if any(p.search(line) for p in patterns):
                marker = f"{rel}:{idx}"
                if marker in allowed:
                    continue
                violations.append(f"{marker} -> {line.strip()}")

    assert not violations, "Hardcoded URL/path findings:\n" + "\n".join(violations)


def test_no_hardcoded_credentials(project_root: Path, src_python_files: list[Path]) -> None:
    cred_re = re.compile(r"\b(password|token|api_key|secret)\b\s*=\s*['\"][^'\"]+['\"]", re.IGNORECASE)
    violations: list[str] = []

    for file_path in src_python_files:
        rel = _rel(project_root, file_path)
        for idx, line in enumerate(file_path.read_text(encoding="utf-8").splitlines(), 1):
            if _is_comment_or_empty(line):
                continue
            if cred_re.search(line):
                violations.append(f"{rel}:{idx} -> {line.strip()}")

    assert not violations, "Hardcoded credential assignments:\n" + "\n".join(violations)


def test_no_direct_external_imports(project_root: Path, src_python_files: list[Path]) -> None:
    external_libs = ("requests", "httpx", "smtplib", "chromadb", "openai", "ollama", "qdrant_client")
    import_sites: dict[str, set[str]] = defaultdict(set)

    for file_path in src_python_files:
        rel = _rel(project_root, file_path)
        text = file_path.read_text(encoding="utf-8")
        for lib in external_libs:
            if re.search(rf"^\s*(import|from)\s+{re.escape(lib)}\b", text, re.MULTILINE):
                import_sites[lib].add(rel)

    violations = []
    for lib, sites in sorted(import_sites.items()):
        if len(sites) > 1:
            violations.append(f"{lib}: {sorted(sites)}")

    assert not violations, "External libs imported in multiple modules:\n" + "\n".join(violations)


def test_no_pytest_skip_in_it_at(project_root: Path, test_python_files: list[Path]) -> None:
    violations: list[str] = []
    for file_path in test_python_files:
        rel = _rel(project_root, file_path)
        if "/integration/" not in rel and "/application/" not in rel:
            continue
        for idx, line in enumerate(file_path.read_text(encoding="utf-8").splitlines(), 1):
            if "pytest.skip(" in line:
                violations.append(f"{rel}:{idx} -> {line.strip()}")
    assert not violations, "pytest.skip found in IT/AT:\n" + "\n".join(violations)


def test_no_mock_in_it_at(project_root: Path, test_python_files: list[Path]) -> None:
    pattern = re.compile(r"MagicMock|MockTransport|local_mode\s*=\s*True")
    violations: list[str] = []
    for file_path in test_python_files:
        rel = _rel(project_root, file_path)
        if "/integration/" not in rel and "/application/" not in rel:
            continue
        for idx, line in enumerate(file_path.read_text(encoding="utf-8").splitlines(), 1):
            if pattern.search(line):
                violations.append(f"{rel}:{idx} -> {line.strip()}")
    assert not violations, "Mocking/local_mode in IT/AT:\n" + "\n".join(violations)


def test_file_headers_present(src_python_files: list[Path], project_root: Path) -> None:
    violations: list[str] = []
    for file_path in src_python_files:
        first_lines = file_path.read_text(encoding="utf-8").splitlines()[:10]
        if not any(line.strip().startswith("#") or '"""' in line for line in first_lines):
            violations.append(_rel(project_root, file_path))
    assert not violations, "Missing file headers:\n" + "\n".join(violations)


def test_functions_have_docstrings(src_python_files: list[Path], project_root: Path) -> None:
    total = 0
    documented = 0
    missing: list[str] = []

    for file_path in src_python_files:
        rel = _rel(project_root, file_path)
        tree = ast.parse(file_path.read_text(encoding="utf-8"))
        for node in ast.walk(tree):
            if not isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                continue
            # Private helpers are excluded from this coverage metric.
            if node.name.startswith("_"):
                continue
            total += 1
            if ast.get_docstring(node):
                documented += 1
            else:
                missing.append(f"{rel}:{node.lineno}::{node.name}")

    pct = 100.0 if total == 0 else (documented / total) * 100
    assert pct >= 80.0, (
        f"Public-function docstring coverage below threshold: {pct:.2f}% (required >= 80%).\n"
        + "\n".join(missing[:200])
    )
