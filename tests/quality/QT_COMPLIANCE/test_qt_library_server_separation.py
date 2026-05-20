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

"""QT2 separation gate for library/server boundaries.

Requirements: FR-01, NFR-06. UCs: UC-097.
"""

from __future__ import annotations

import ast
from pathlib import Path


def _import_modules(file_path: Path) -> set[str]:
    tree = ast.parse(file_path.read_text(encoding="utf-8"), filename=file_path.as_posix())
    modules: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            modules.update(alias.name for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module:
            modules.add(node.module)
    return modules


def test_qt_library_layer_has_no_transport_imports(project_root: Path) -> None:
    violations: list[str] = []
    for py_file in sorted((project_root / "src" / "git_tools").rglob("*.py")):
        modules = _import_modules(py_file)
        for module in sorted(modules):
            if module.startswith("fastapi") or module.startswith("starlette") or module.startswith("uvicorn"):
                rel = py_file.resolve().relative_to(project_root.resolve()).as_posix()
                violations.append(f"{rel} imports {module}")
            if module.startswith("cloud_dog_api_kit"):
                rel = py_file.resolve().relative_to(project_root.resolve()).as_posix()
                violations.append(f"{rel} imports {module}")
    assert not violations, "Library layer imports transport/runtime modules:\n" + "\n".join(violations)


def test_qt_server_layer_has_no_direct_gitpython_imports(project_root: Path) -> None:
    violations: list[str] = []
    for py_file in sorted((project_root / "src" / "git_mcp_server").rglob("*.py")):
        modules = _import_modules(py_file)
        for module in sorted(modules):
            if module == "git" or module.startswith("git."):
                rel = py_file.resolve().relative_to(project_root.resolve()).as_posix()
                violations.append(f"{rel} imports {module}")
    assert not violations, "Server layer imports GitPython directly:\n" + "\n".join(violations)
