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

"""W25A static checks for requirements/tests/code traceability."""

from __future__ import annotations

import re
from pathlib import Path


def _requirement_ids(requirements_text: str, pattern: re.Pattern[str]) -> list[str]:
    ordered: list[str] = []
    seen: set[str] = set()
    for match in pattern.finditer(requirements_text):
        req_id = match.group(0)
        if req_id in seen:
            continue
        seen.add(req_id)
        ordered.append(req_id)
    return ordered


def _match_any_pattern(value: str, patterns: list[str]) -> bool:
    return any(re.match(pattern, value) for pattern in patterns)


def _docs_test_entries(tests_text: str) -> list[tuple[str, str]]:
    entries: list[tuple[str, str]] = []
    for line in tests_text.splitlines():
        raw = line.strip()
        if not raw.startswith("|"):
            continue
        cols = [col.strip() for col in raw.strip("|").split("|")]
        if not cols:
            continue
        test_id = cols[0]
        if re.match(r"^(UT|ST|IT|AT|QT)\d", test_id):
            entries.append((test_id, raw))
    return entries


def _requirement_test_status(
    req_id: str,
    src_text: str,
    tests_doc_text: str,
    tests_py_text: str,
) -> tuple[bool, bool]:
    has_code_ref = req_id in src_text
    has_test_ref = req_id in tests_doc_text or req_id in tests_py_text
    return has_code_ref, has_test_ref


def test_all_requirements_have_tests(
    requirements_doc: Path,
    tests_doc: Path,
    test_python_files: list[Path],
    requirement_id_pattern: re.Pattern[str],
) -> None:
    requirements_text = requirements_doc.read_text(encoding="utf-8")
    tests_doc_text = tests_doc.read_text(encoding="utf-8")
    tests_py_text = "\n".join(path.read_text(encoding="utf-8") for path in test_python_files)
    req_ids = _requirement_ids(requirements_text, requirement_id_pattern)

    missing = []
    for req_id in req_ids:
        has_code_ref, has_test_ref = _requirement_test_status(req_id, "", tests_doc_text, tests_py_text)
        if not has_test_ref:
            missing.append(req_id)

    assert not missing, "Requirements with zero test references:\n" + "\n".join(missing)


def test_all_tests_have_requirements(
    tests_doc: Path,
    requirement_id_pattern: re.Pattern[str],
) -> None:
    tests_doc_text = tests_doc.read_text(encoding="utf-8")
    entries = _docs_test_entries(tests_doc_text)

    violations: list[str] = []
    for test_id, raw_line in entries:
        if requirement_id_pattern.search(raw_line):
            continue
        violations.append(f"{test_id} -> {raw_line}")

    assert not violations, "Tests without requirement IDs in TESTS.md:\n" + "\n".join(violations)


def test_all_requirements_have_code(
    requirements_doc: Path,
    src_python_files: list[Path],
    requirement_id_pattern: re.Pattern[str],
) -> None:
    requirements_text = requirements_doc.read_text(encoding="utf-8")
    req_ids = _requirement_ids(requirements_text, requirement_id_pattern)
    src_text = "\n".join(path.read_text(encoding="utf-8") for path in src_python_files)
    missing = [req_id for req_id in req_ids if req_id not in src_text]
    assert not missing, "Requirements without src code references:\n" + "\n".join(missing)


def test_delivery_matrix_complete(
    project_root: Path,
    requirements_doc: Path,
    tests_doc: Path,
    src_python_files: list[Path],
    test_python_files: list[Path],
    requirement_id_pattern: re.Pattern[str],
) -> None:
    requirements_text = requirements_doc.read_text(encoding="utf-8")
    tests_doc_text = tests_doc.read_text(encoding="utf-8")
    src_text = "\n".join(path.read_text(encoding="utf-8") for path in src_python_files)
    tests_py_text = "\n".join(path.read_text(encoding="utf-8") for path in test_python_files)
    req_ids = _requirement_ids(requirements_text, requirement_id_pattern)

    rows: list[tuple[str, str]] = []
    fr_total = 0
    fr_delivered = 0
    for req_id in req_ids:
        has_code_ref, has_test_ref = _requirement_test_status(req_id, src_text, tests_doc_text, tests_py_text)
        if has_code_ref and has_test_ref:
            status = "DELIVERED"
        elif has_code_ref and not has_test_ref:
            status = "UNTESTABLE"
        elif (not has_code_ref) and has_test_ref:
            status = "PARTIAL"
        else:
            status = "NOT_STARTED"

        if req_id.startswith("FR-"):
            fr_total += 1
            if status == "DELIVERED":
                fr_delivered += 1

        rows.append((req_id, status))

    ratio = 100.0 if fr_total == 0 else (fr_delivered / fr_total) * 100

    matrix_lines = [
        "# W25A Delivery Matrix (Auto-Generated)",
        "",
        "| Req ID | Code | Test | Status |",
        "|---|---|---|---|",
    ]
    for req_id, status in rows:
        has_code_ref, has_test_ref = _requirement_test_status(req_id, src_text, tests_doc_text, tests_py_text)
        matrix_lines.append(
            f"| {req_id} | {'Y' if has_code_ref else 'N'} | {'Y' if has_test_ref else 'N'} | {status} |"
        )
    matrix_lines.append("")
    matrix_lines.append(f"FR delivered ratio: {ratio:.2f}% ({fr_delivered}/{fr_total})")

    output = project_root / "working" / "W25A-traceability-matrix.md"
    output.write_text("\n".join(matrix_lines), encoding="utf-8")

    assert ratio >= 80.0, (
        f"FR delivered ratio below 80%: {ratio:.2f}% ({fr_delivered}/{fr_total}). See {output.as_posix()}"
    )


def test_all_test_functions_have_requirements(
    project_root: Path,
    requirement_id_pattern: re.Pattern[str],
) -> None:
    """Ensure every non-QT-compliance test function carries a requirement marker."""
    function_pattern = re.compile(r"^\s*def\s+(test_[a-zA-Z0-9_]+)\s*\(", re.MULTILINE)
    violations: list[str] = []

    for test_file in sorted((project_root / "tests").rglob("test_*.py")):
        rel = test_file.resolve().relative_to(project_root.resolve()).as_posix()
        if rel.startswith("tests/quality/QT_COMPLIANCE/"):
            continue

        text = test_file.read_text(encoding="utf-8")
        for match in function_pattern.finditer(text):
            start = max(0, match.start() - 300)
            end = min(len(text), match.end() + 300)
            window = text[start:end]
            if requirement_id_pattern.search(window):
                continue
            violations.append(f"{rel}::{match.group(1)}")

    assert not violations, "Test functions without requirement marker/docstring:\n" + "\n".join(violations)


def test_no_orphan_test_files(project_root: Path, tests_doc: Path) -> None:
    tests_doc_text = tests_doc.read_text(encoding="utf-8")
    id_re = re.compile(r"(?:UT|ST|IT|AT|QT)\d+(?:\.\d+)?[a-z]?")
    violations: list[str] = []

    for test_file in sorted((project_root / "tests").rglob("test_*.py")):
        rel = test_file.resolve().relative_to(project_root.resolve()).as_posix()
        full_ids = id_re.findall(rel)
        if full_ids:
            if not any(test_id in tests_doc_text for test_id in full_ids):
                violations.append(rel)
            continue

        # Fallback for newly generated compliance files named by module role, not numeric ID.
        if test_file.stem not in tests_doc_text:
            violations.append(rel)

    assert not violations, "Test files not referenced in TESTS.md:\n" + "\n".join(violations)


def test_w18a03_webui_accessibility_evidence(project_root: Path) -> None:
    """Validate W18A-03 evidence for WebUI accessibility delivery."""
    # Covers: NFR-08
    report_path = project_root / "working" / "w18a03" / "W18A-03-GIT-MCP-UI-PHASE-B-REPORT.md"
    assert report_path.exists(), f"Missing W18A-03 report: {report_path.as_posix()}"

    report_text = report_path.read_text(encoding="utf-8")
    assert "a11y: `1 passed, 0 failed, 0 skipped`" in report_text, (
        "W18A-03 report does not contain required a11y PASS evidence."
    )
    assert "E2E: `10 passed, 0 failed, 0 skipped`" in report_text, (
        "W18A-03 report does not contain required local-stage E2E PASS evidence."
    )
