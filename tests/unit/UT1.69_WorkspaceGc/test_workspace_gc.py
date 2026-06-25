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

"""W28C-1705 GM4 — workspace GC, stuck-merge reaper, disk-pressure refusal, admin endpoints.

/app/data filled to 91% with 699 workspaces (41 stuck in MERGE) because nothing reaped them.
This proves: disk usage reporting; a disk scan that classifies merge state; GC that reaps
stale ephemeral + old ephemeral stuck-merges while keeping fresh/persistent ones; a traversal-
guarded explicit reap; repo_open refusal under critical disk pressure; and the
/api/v1/admin/workspaces list + delete endpoints.
"""

from __future__ import annotations

import json
import os
import tempfile
import time
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from git_mcp_server.api_server import create_api_app
from git_tools.tools.registry import ToolRegistry
from git_tools.workspaces.gc import run_gc_cycle
from git_tools.workspaces.manager import WorkspaceManager


def _mk_ws(base: Path, name: str, mode: str, age_seconds: float, *, merge: bool = False) -> Path:
    d = base / name
    (d / ".git").mkdir(parents=True, exist_ok=True)
    (d / ".workspace-meta.json").write_text(json.dumps({"mode": mode, "profile": "p"}))
    if merge:
        (d / ".git" / "MERGE_HEAD").write_text("deadbeef")
    old = time.time() - age_seconds
    os.utime(d, (old, old))
    return d
# FR-1.18 traceability marker for existing git-mcp coverage.
@pytest.mark.UT
@pytest.mark.mcp
@pytest.mark.req("FR-005")  # W28E-1804A semantic rebind


def test_disk_usage_percent_is_sane() -> None:
    wm = WorkspaceManager(tempfile.mkdtemp())
    assert 0.0 <= wm.disk_usage_percent() <= 100.0
# FR-1.18 traceability marker for existing git-mcp coverage.
@pytest.mark.UT
@pytest.mark.mcp
@pytest.mark.req("FR-005")  # W28E-1804A semantic rebind


def test_gc_reaps_stale_and_stuck_keeps_fresh_and_persistent() -> None:
    base = Path(tempfile.mkdtemp())
    _mk_ws(base, "eph-old", "ephemeral", 2 * 86400)
    _mk_ws(base, "eph-fresh", "ephemeral", 60)
    _mk_ws(base, "eph-stuck", "ephemeral", 8 * 86400, merge=True)
    _mk_ws(base, "persist-old", "persistent", 10 * 86400)
    wm = WorkspaceManager(base)
    result = wm.gc_disk(ttl_seconds=86400, stuck_merge_reap_seconds=7 * 86400)
    reaped = set(result["reaped"])
    assert {"eph-old", "eph-stuck"} <= reaped
    assert "eph-fresh" not in reaped and "persist-old" not in reaped
    assert "persist-old" in result["warned_persistent"]
    assert not (base / "eph-old").exists()
    assert (base / "eph-fresh").exists() and (base / "persist-old").exists()
# FR-1.18 traceability marker for existing git-mcp coverage.
@pytest.mark.UT
@pytest.mark.mcp
@pytest.mark.req("FR-005")  # W28E-1804A semantic rebind


def test_scan_disk_reports_merge_state() -> None:
    base = Path(tempfile.mkdtemp())
    _mk_ws(base, "ws-merge", "ephemeral", 100, merge=True)
    wm = WorkspaceManager(base)
    assert any(w["id"] == "ws-merge" and w["state"] == "merge" for w in wm.scan_disk_workspaces())
    assert any(w["id"] == "ws-merge" for w in wm.find_stuck_merges())
# FR-1.18 traceability marker for existing git-mcp coverage.
@pytest.mark.UT
@pytest.mark.mcp
@pytest.mark.req("FR-005")  # W28E-1804A semantic rebind


def test_delete_workspace_dir_with_traversal_guard() -> None:
    base = Path(tempfile.mkdtemp())
    _mk_ws(base, "ws-del", "ephemeral", 10)
    wm = WorkspaceManager(base)
    assert wm.delete_workspace_dir("ws-del") is True
    assert not (base / "ws-del").exists()
    assert wm.delete_workspace_dir("ws-del") is False
    with pytest.raises(ValueError):
        wm.delete_workspace_dir("../escape")
# FR-1.18 traceability marker for existing git-mcp coverage.
@pytest.mark.UT
@pytest.mark.mcp
@pytest.mark.req("FR-005")  # W28E-1804A semantic rebind


def test_run_gc_cycle() -> None:
    base = Path(tempfile.mkdtemp())
    _mk_ws(base, "eph-old", "ephemeral", 2 * 86400)
    result = run_gc_cycle(WorkspaceManager(base), ttl_seconds=86400, stuck_merge_reap_seconds=7 * 86400)
    assert "eph-old" in result["reaped"]
# FR-1.18 traceability marker for existing git-mcp coverage.
@pytest.mark.UT
@pytest.mark.mcp
@pytest.mark.req("FR-005")  # W28E-1804A semantic rebind


def test_repo_open_refused_under_critical_disk(monkeypatch) -> None:
    wm = WorkspaceManager(tempfile.mkdtemp())
    reg = ToolRegistry(wm)
    monkeypatch.setattr(wm, "disk_usage_percent", lambda: 96.0)
    with pytest.raises(RuntimeError) as exc:
        reg._repo_access(
            {"profile": "x", "repo_source": "https://git.example.test/playgroup/x.git", "session_id": "s"}
        )
    assert "refused" in str(exc.value).lower()
# FR-1.18 traceability marker for existing git-mcp coverage.
@pytest.mark.UT
@pytest.mark.mcp
@pytest.mark.req("FR-005")  # W28E-1804A semantic rebind


def test_admin_workspaces_list_and_delete() -> None:
    app = create_api_app(env_files=["tests/env-UT"])
    wm = app.state.workspace_manager
    _mk_ws(wm.base_dir, "w28c1705-adm-ws", "ephemeral", 100, merge=True)
    client = TestClient(app, raise_server_exceptions=False)
    key = app.state.seed_api_key

    listed = client.get("/api/v1/admin/workspaces", headers={"x-api-key": key})
    assert listed.status_code == 200, listed.text
    body = listed.json()["result"]
    assert any(w["id"] == "w28c1705-adm-ws" for w in body["items"])
    assert body["stuck_merges"] >= 1
    assert 0.0 <= body["disk_percent"] <= 100.0

    assert client.get("/api/v1/admin/workspaces").status_code == 401  # unauth gated

    deleted = client.delete("/api/v1/admin/workspaces/w28c1705-adm-ws", headers={"x-api-key": key})
    assert deleted.status_code == 200, deleted.text
    assert deleted.json()["result"]["deleted"] is True
    assert not (wm.base_dir / "w28c1705-adm-ws").exists()
