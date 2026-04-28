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

from tests.integration.conftest import _remote_authorisation_error


def test_remote_url_allowlist_enforced(monkeypatch) -> None:
    """Requirements: FR-06. UCs: UC-043."""
    monkeypatch.setenv("GIT_MCP_ALLOWED_REMOTE_PREFIXES", "https://git.example.test/playgroup/")

    allowed = _remote_authorisation_error("https://git.example.test/playgroup/test-project.git", tier="IT")
    assert allowed is None

    disallowed = _remote_authorisation_error("https://evil.example.com/repo.git", tier="IT")
    assert disallowed is not None
    assert "not in allowlist" in disallowed

    forbidden = _remote_authorisation_error("https://gitlab.com/clouddog/cloud-dog-repo.git", tier="IT")
    assert forbidden is not None
    assert "forbidden" in forbidden.lower()
