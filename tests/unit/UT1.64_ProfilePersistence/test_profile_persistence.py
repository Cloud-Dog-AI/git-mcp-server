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

"""W28C-1705 GM2 — durable, cross-surface profile store (1603-unblocker).

The api / mcp / a2a surfaces previously each held a private in-memory dict, so a
profile created via REST was invisible to ``/mcp repo_open`` and evaporated on restart.
``ProfileStore`` persists to the ``git_profile_registry`` table on the shared ``/app/data``
volume. This proves: (1) a profile survives a fresh store instance (restart simulation);
(2) two independent stores over one DB see each other's writes (cross-surface unification);
(3) delete is a soft-delete and re-create restores; (4) create_api_app builds on the
DB-backed store and lists the seeded profiles.
"""


from __future__ import annotations
import pytest

from fastapi.testclient import TestClient

from git_tools.admin.profile_store import ProfileStore
from git_tools.db import initialise_database
from git_mcp_server.api_server import create_api_app


def _session_manager():
    return initialise_database(env_files=["tests/env-UT"]).session_manager


_BODY = {"repo": {"source": "https://git.example.test/playgroup/w28c1705.git"}, "display_name": "W28C-1705 UT"}
# FR-1.18 traceability marker for existing git-mcp coverage.
@pytest.mark.UT
@pytest.mark.mcp
@pytest.mark.req("FR-023")  # W28E-1804A semantic rebind


def test_profile_persists_across_store_restart() -> None:
    """Requirements: CFG-09, persistence (W28C-1705 GM2 / 1603-unblocker)."""
    sm = _session_manager()
    writer = ProfileStore(sm)
    writer["w28c1705-ut-persist"] = _BODY
    # Simulate a container restart: a brand-new store instance over the same durable DB.
    reopened = ProfileStore(sm)
    assert "w28c1705-ut-persist" in reopened
    assert reopened["w28c1705-ut-persist"]["repo"]["source"] == _BODY["repo"]["source"]
# FR-1.18 traceability marker for existing git-mcp coverage.
@pytest.mark.UT
@pytest.mark.mcp
@pytest.mark.req("FR-023")  # W28E-1804A semantic rebind


def test_cross_surface_visibility_via_shared_db() -> None:
    """A write through one surface's store is visible to another surface's store."""
    sm = _session_manager()
    store_api = ProfileStore(sm)  # stands in for the api process
    store_mcp = ProfileStore(sm)  # stands in for the separate mcp process
    store_api["w28c1705-ut-xapp"] = _BODY
    assert "w28c1705-ut-xapp" in store_mcp
    assert store_mcp.get("w28c1705-ut-xapp", {}).get("repo", {}).get("source") == _BODY["repo"]["source"]
# FR-1.18 traceability marker for existing git-mcp coverage.
@pytest.mark.UT
@pytest.mark.mcp
@pytest.mark.req("FR-023")  # W28E-1804A semantic rebind


def test_soft_delete_then_recreate() -> None:
    """Delete hides the profile (soft-delete); re-create restores it."""
    sm = _session_manager()
    store = ProfileStore(sm)
    store["w28c1705-ut-del"] = _BODY
    assert "w28c1705-ut-del" in store
    del store["w28c1705-ut-del"]
    assert "w28c1705-ut-del" not in store
    assert store.get("w28c1705-ut-del") is None
    store["w28c1705-ut-del"] = _BODY  # re-create un-soft-deletes the same row
    assert "w28c1705-ut-del" in store
# FR-1.18 traceability marker for existing git-mcp coverage.
@pytest.mark.UT
@pytest.mark.mcp
@pytest.mark.req("FR-023")  # W28E-1804A semantic rebind


def test_api_app_builds_on_db_backed_store_and_lists_seeds() -> None:
    """create_api_app wires the DB-backed store; seeded profiles list and serialise."""
    app = create_api_app(env_files=["tests/env-UT"])
    assert isinstance(app.state.profile_store, ProfileStore)
    client = TestClient(app, raise_server_exceptions=False)
    resp = client.get("/api/v1/admin/profiles", headers={"x-api-key": app.state.seed_api_key})
    assert resp.status_code == 200, resp.text
    items = resp.json()["result"]["items"]
    assert isinstance(items, dict)  # materialised snapshot, JSON-serialisable
