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

"""W28C-1705 GM5 (OPT-B) — /a2a/events surface is a clear 410 Gone, not an ambiguous 404.

/a2a/events + /a2a/events/stream were advertised by an old topology but never implemented.
The agent-card already declares streaming:false and no longer lists them; this proves the
endpoints now return an explicit 410 Gone and are absent from the OpenAPI schema, so the
advertised schema and the live route table agree.
"""


from __future__ import annotations
import pytest

from fastapi.testclient import TestClient

from git_mcp_server.a2a_server import create_a2a_app


def _app():
    return create_a2a_app(env_files=["tests/env-UT"])
# FR-1.18 traceability marker for existing git-mcp coverage.
@pytest.mark.UT
@pytest.mark.mcp
@pytest.mark.req("FR-004")  # W28E-1804A semantic rebind


def test_a2a_events_endpoints_return_410_gone() -> None:
    """Requirements: W28C-1705 GM5 — no advertised-but-404 surface; clear 410.

    Both the base-path form (/a2a/events) and the Traefik strip-prefixed form (/events, what
    the a2a tier actually receives on preprod) return 410.
    """
    client = TestClient(_app(), raise_server_exceptions=False)
    for path in ("/a2a/events", "/a2a/events/stream", "/events", "/events/stream"):
        assert client.get(path).status_code == 410, path
# FR-1.18 traceability marker for existing git-mcp coverage.
@pytest.mark.UT
@pytest.mark.mcp
@pytest.mark.req("FR-004")  # W28E-1804A semantic rebind


def test_a2a_events_absent_from_openapi() -> None:
    paths = _app().openapi().get("paths", {})
    assert "/a2a/events" not in paths
    assert "/a2a/events/stream" not in paths
