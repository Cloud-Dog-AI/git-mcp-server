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

from pathlib import Path

FORBIDDEN_US_SPELLINGS = {
    "color": "colour",
    "initialize": "initialise",
    "serialize": "serialise",
    "authorization": "authorisation",
}

# Standards exceptions: HTTP header names are protocol-defined spellings.
_HTTP_HEADER_TOKEN_EXCEPTIONS = {"authorization"}
_PROTOCOL_TOKEN_EXCEPTIONS = {"initialize"}


def test_uk_english_compliance() -> None:
    """Requirements: FR-01."""
    root = Path("src")
    violations: list[str] = []
    for path in root.rglob("*.py"):
        text = path.read_text(encoding="utf-8")
        lowered = text.lower()
        for wrong in FORBIDDEN_US_SPELLINGS:
            if wrong not in lowered:
                continue
            candidate_text = lowered
            if wrong in _HTTP_HEADER_TOKEN_EXCEPTIONS:
                candidate_text = candidate_text.replace('"authorization"', "").replace("'authorization'", "")
            if wrong in _PROTOCOL_TOKEN_EXCEPTIONS:
                candidate_text = candidate_text.replace('"initialize"', "").replace("'initialize'", "")
            if wrong in candidate_text:
                violations.append(f"{path}: {wrong}")
    assert not violations, "US spellings found: " + ", ".join(violations)
