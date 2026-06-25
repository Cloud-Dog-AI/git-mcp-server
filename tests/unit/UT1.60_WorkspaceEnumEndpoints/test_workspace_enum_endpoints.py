# Copyright 2026 Cloud-Dog, Viewdeck Engineering Limited
# SPDX-License-Identifier: Apache-2.0
# W28J-1308 — UT/IT for workspace enumeration + audit-filter endpoints.

from __future__ import annotations

import os
import subprocess
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from git_mcp_server.api_server import create_api_app

API = "/api/v1"

_GIT_ENV = {
    **os.environ,
    "GIT_AUTHOR_NAME": "Tess Ter",
    "GIT_AUTHOR_EMAIL": "tess@example.invalid",
    "GIT_COMMITTER_NAME": "Tess Ter",
    "GIT_COMMITTER_EMAIL": "tess@example.invalid",
    "GIT_CONFIG_GLOBAL": "/dev/null",
    "GIT_CONFIG_SYSTEM": "/dev/null",
}


def _git(cwd: Path, *args: str) -> str:
    out = subprocess.run(
        ["git", *args], cwd=str(cwd), check=True, capture_output=True, text=True, env=_GIT_ENV
    )
    return out.stdout


@pytest.fixture(scope="module")
def origin_repo(tmp_path_factory: pytest.TempPathFactory) -> Path:
    repo = tmp_path_factory.mktemp("origin_repo")
    _git(repo, "init", "-b", "main")
    (repo / "README.md").write_text("# Test Project\n")
    (repo / "src").mkdir()
    (repo / "src" / "app.py").write_text("print('hello')\n")
    _git(repo, "add", "-A")
    _git(repo, "commit", "-m", "initial commit")
    (repo / "CHANGELOG.md").write_text("- first\n")
    _git(repo, "add", "-A")
    _git(repo, "commit", "-m", "second commit")
    _git(repo, "tag", "v1.0")
    _git(repo, "branch", "dev")
    return repo


@pytest.fixture(scope="module")
def client_env(origin_repo: Path, tmp_path_factory: pytest.TempPathFactory):
    ws_base = tmp_path_factory.mktemp("ws_base")
    prev = os.environ.get("CLOUD_DOG__WORKSPACE__BASE_DIR")
    os.environ["CLOUD_DOG__WORKSPACE__BASE_DIR"] = str(ws_base)
    app = create_api_app(env_files=["tests/env-UT"])
    client = TestClient(app)
    headers = {"x-api-key": app.state.seed_api_key}
    # Inject a profile pointing at the local origin repo (same dict the router closed over).
    app.state.profile_store["testprofile"] = {
        "repo": {"source": str(origin_repo), "default_branch": "main"}
    }
    yield client, headers, app
    if prev is None:
        os.environ.pop("CLOUD_DOG__WORKSPACE__BASE_DIR", None)
    else:
        os.environ["CLOUD_DOG__WORKSPACE__BASE_DIR"] = prev


@pytest.fixture(scope="module")
def workspace_id(client_env) -> str:
    client, headers, _ = client_env
    resp = client.post(f"{API}/workspaces", json={"profile_id": "testprofile", "mode": "persistent"}, headers=headers)
    assert resp.status_code == 200, resp.text
    return resp.json()["result"]["workspace_id"]


# --- create (POST /v1/workspaces) ---
# FR-1.18 traceability marker for existing git-mcp coverage.
@pytest.mark.UT
@pytest.mark.mcp
@pytest.mark.req("FR-018")  # W28E-1804A semantic rebind

def test_create_workspace_happy(client_env, workspace_id: str) -> None:
    assert workspace_id  # created + cloned by the fixture
    assert "-" in workspace_id  # deterministic "{profile}-{slug}" shape
# FR-1.18 traceability marker for existing git-mcp coverage.
@pytest.mark.UT
@pytest.mark.mcp
@pytest.mark.req("FR-018")  # W28E-1804A semantic rebind


def test_create_workspace_missing_profile_id(client_env) -> None:
    client, headers, _ = client_env
    resp = client.post(f"{API}/workspaces", json={}, headers=headers)
    assert resp.status_code == 400
# FR-1.18 traceability marker for existing git-mcp coverage.
@pytest.mark.UT
@pytest.mark.mcp
@pytest.mark.req("FR-018")  # W28E-1804A semantic rebind


def test_create_workspace_unknown_profile(client_env) -> None:
    client, headers, _ = client_env
    resp = client.post(f"{API}/workspaces", json={"profile_id": "nope"}, headers=headers)
    assert resp.status_code == 404
# FR-1.18 traceability marker for existing git-mcp coverage.
@pytest.mark.UT
@pytest.mark.mcp
@pytest.mark.req("FR-018")  # W28E-1804A semantic rebind


def test_create_requires_auth(client_env) -> None:
    client, _, _ = client_env
    resp = client.post(f"{API}/workspaces", json={"profile_id": "testprofile"})
    assert resp.status_code in (401, 403)


# --- list (GET /v1/workspaces) owner-scoped (F-1302-B) ---
# FR-1.18 traceability marker for existing git-mcp coverage.
@pytest.mark.UT
@pytest.mark.mcp
@pytest.mark.req("FR-018")  # W28E-1804A semantic rebind

def test_list_workspaces_owner_me_includes_created(client_env, workspace_id: str) -> None:
    client, headers, _ = client_env
    resp = client.get(f"{API}/workspaces", params={"owner": "me"}, headers=headers)
    assert resp.status_code == 200, resp.text
    ids = [w["workspace_id"] for w in resp.json()["result"]["items"]]
    assert workspace_id in ids
    row = next(w for w in resp.json()["result"]["items"] if w["workspace_id"] == workspace_id)
    assert row["profile_id"] == "testprofile"
    assert row["is_open"] is True
    assert row["owner"] == "integration-user"  # seed-key owner
# FR-1.18 traceability marker for existing git-mcp coverage.
@pytest.mark.UT
@pytest.mark.mcp
@pytest.mark.req("FR-018")  # W28E-1804A semantic rebind


def test_list_workspaces_other_owner_excludes(client_env, workspace_id: str) -> None:
    client, headers, _ = client_env
    resp = client.get(f"{API}/workspaces", params={"owner": "someone-else"}, headers=headers)
    assert resp.status_code == 200
    ids = [w["workspace_id"] for w in resp.json()["result"]["items"]]
    assert workspace_id not in ids  # owner scoping excludes other users' workspaces
# FR-1.18 traceability marker for existing git-mcp coverage.
@pytest.mark.UT
@pytest.mark.mcp
@pytest.mark.req("FR-018")  # W28E-1804A semantic rebind


def test_list_workspaces_profile_filter(client_env, workspace_id: str) -> None:
    client, headers, _ = client_env
    resp = client.get(f"{API}/workspaces", params={"profile_id": "no-such-profile"}, headers=headers)
    assert resp.status_code == 200
    assert resp.json()["result"]["items"] == []


# --- refs (GET /v1/workspaces/{id}/refs) ---
# FR-1.18 traceability marker for existing git-mcp coverage.
@pytest.mark.UT
@pytest.mark.mcp
@pytest.mark.req("FR-018")  # W28E-1804A semantic rebind

def test_refs_branches_include_local_and_remote(client_env, workspace_id: str) -> None:
    client, headers, _ = client_env
    resp = client.get(f"{API}/workspaces/{workspace_id}/refs", params={"type": "branch"}, headers=headers)
    assert resp.status_code == 200, resp.text
    names = {r["ref_name"] for r in resp.json()["result"]["items"]}
    assert "main" in names  # local
    assert "dev" in names  # remote (GMC-P-08)
# FR-1.18 traceability marker for existing git-mcp coverage.
@pytest.mark.UT
@pytest.mark.mcp
@pytest.mark.req("FR-018")  # W28E-1804A semantic rebind


def test_refs_tags(client_env, workspace_id: str) -> None:
    client, headers, _ = client_env
    resp = client.get(f"{API}/workspaces/{workspace_id}/refs", params={"type": "tag"}, headers=headers)
    assert resp.status_code == 200
    names = {r["ref_name"] for r in resp.json()["result"]["items"]}
    assert "v1.0" in names
# FR-1.18 traceability marker for existing git-mcp coverage.
@pytest.mark.UT
@pytest.mark.mcp
@pytest.mark.req("FR-018")  # W28E-1804A semantic rebind


def test_refs_commits(client_env, workspace_id: str) -> None:
    client, headers, _ = client_env
    resp = client.get(f"{API}/workspaces/{workspace_id}/refs", params={"type": "commit"}, headers=headers)
    assert resp.status_code == 200
    items = resp.json()["result"]["items"]
    assert len(items) >= 2
    assert all(r["ref_type"] == "commit" for r in items)
# FR-1.18 traceability marker for existing git-mcp coverage.
@pytest.mark.UT
@pytest.mark.mcp
@pytest.mark.req("FR-018")  # W28E-1804A semantic rebind


def test_refs_invalid_type(client_env, workspace_id: str) -> None:
    client, headers, _ = client_env
    resp = client.get(f"{API}/workspaces/{workspace_id}/refs", params={"type": "bogus"}, headers=headers)
    assert resp.status_code == 400
# FR-1.18 traceability marker for existing git-mcp coverage.
@pytest.mark.UT
@pytest.mark.mcp
@pytest.mark.req("FR-018")  # W28E-1804A semantic rebind


def test_refs_unknown_workspace(client_env) -> None:
    client, headers, _ = client_env
    resp = client.get(f"{API}/workspaces/ghost-xyz/refs", params={"type": "branch"}, headers=headers)
    assert resp.status_code == 404


# --- paths / authors / stashes ---
# FR-1.18 traceability marker for existing git-mcp coverage.
@pytest.mark.UT
@pytest.mark.mcp
@pytest.mark.req("FR-018")  # W28E-1804A semantic rebind

def test_paths(client_env, workspace_id: str) -> None:
    client, headers, _ = client_env
    resp = client.get(f"{API}/workspaces/{workspace_id}/paths", headers=headers)
    assert resp.status_code == 200, resp.text
    items = resp.json()["result"]["items"]
    paths = {i["path"] for i in items}
    assert "README.md" in paths
    assert "src/app.py" in paths
    assert any(i["path"] == "src" and i["kind"] == "dir" for i in items)
# FR-1.18 traceability marker for existing git-mcp coverage.
@pytest.mark.UT
@pytest.mark.mcp
@pytest.mark.req("FR-018")  # W28E-1804A semantic rebind


def test_paths_prefix_filter(client_env, workspace_id: str) -> None:
    client, headers, _ = client_env
    resp = client.get(f"{API}/workspaces/{workspace_id}/paths", params={"prefix": "src/"}, headers=headers)
    assert resp.status_code == 200
    paths = {i["path"] for i in resp.json()["result"]["items"]}
    assert "src/app.py" in paths
    assert "README.md" not in paths
# FR-1.18 traceability marker for existing git-mcp coverage.
@pytest.mark.UT
@pytest.mark.mcp
@pytest.mark.req("FR-018")  # W28E-1804A semantic rebind


def test_authors(client_env, workspace_id: str) -> None:
    client, headers, _ = client_env
    resp = client.get(f"{API}/workspaces/{workspace_id}/authors", headers=headers)
    assert resp.status_code == 200
    authors = resp.json()["result"]["items"]
    assert any(a["author"] == "Tess Ter" and a["email"] == "tess@example.invalid" for a in authors)
# FR-1.18 traceability marker for existing git-mcp coverage.
@pytest.mark.UT
@pytest.mark.mcp
@pytest.mark.req("FR-018")  # W28E-1804A semantic rebind


def test_stashes(client_env, workspace_id: str) -> None:
    client, headers, app = client_env
    # Create a stash inside the workspace (clones do not carry stashes).
    ws_path = Path(app.state.workspace_manager.get_workspace(workspace_id).path)
    (ws_path / "README.md").write_text("# Test Project (edited)\n")
    _git(ws_path, "stash", "push", "-m", "wip work")
    resp = client.get(f"{API}/workspaces/{workspace_id}/stashes", headers=headers)
    assert resp.status_code == 200, resp.text
    items = resp.json()["result"]["items"]
    assert len(items) >= 1
    assert items[0]["stash_id"].startswith("stash@{")
    assert "wip work" in items[0]["message"]


# --- audit filter logic (_audit_row_matches) — deterministic, no app ---

from git_mcp_server.ui_endpoints import _audit_row_matches  # noqa: E402

_EMPTY = {k: "" for k in ("correlation_id", "entity_kind", "entity_id", "user", "workspace_id", "profile_id", "job_id")}


def _row(**kw: object) -> dict:
    raw = {"correlation_id": kw.get("correlation_id", ""), "actor": {"actor_id": kw.get("user", "")},
           "workspace_id": kw.get("workspace_id", ""), "profile": kw.get("profile_id", ""), "params": {}}
    return {
        "correlation_id": kw.get("correlation_id", ""),
        "actor_id": kw.get("user", ""),
        "details": {},
        "raw": raw,
    }
# FR-1.18 traceability marker for existing git-mcp coverage.
@pytest.mark.UT
@pytest.mark.mcp
@pytest.mark.req("FR-018")  # W28E-1804A semantic rebind


def test_audit_match_correlation_id() -> None:
    row = _row(correlation_id="cid-A", user="alice")
    assert _audit_row_matches(row, {**_EMPTY, "correlation_id": "cid-A"}) is True
    assert _audit_row_matches(row, {**_EMPTY, "correlation_id": "cid-Z"}) is False
# FR-1.18 traceability marker for existing git-mcp coverage.
@pytest.mark.UT
@pytest.mark.mcp
@pytest.mark.req("FR-018")  # W28E-1804A semantic rebind


def test_audit_match_user() -> None:
    row = _row(correlation_id="cid-A", user="alice")
    assert _audit_row_matches(row, {**_EMPTY, "user": "alice"}) is True
    assert _audit_row_matches(row, {**_EMPTY, "user": "bob"}) is False
# FR-1.18 traceability marker for existing git-mcp coverage.
@pytest.mark.UT
@pytest.mark.mcp
@pytest.mark.req("FR-018")  # W28E-1804A semantic rebind


def test_audit_match_workspace_and_profile_and_combined() -> None:
    ws1_y = _row(workspace_id="ws-1", profile_id="prof-y")
    ws1_x = _row(workspace_id="ws-1", profile_id="prof-x")
    # AND-combined: ws-1 AND prof-y matches only ws1_y
    assert _audit_row_matches(ws1_y, {**_EMPTY, "workspace_id": "ws-1", "profile_id": "prof-y"}) is True
    assert _audit_row_matches(ws1_x, {**_EMPTY, "workspace_id": "ws-1", "profile_id": "prof-y"}) is False
# FR-1.18 traceability marker for existing git-mcp coverage.
@pytest.mark.UT
@pytest.mark.mcp
@pytest.mark.req("FR-018")  # W28E-1804A semantic rebind


def test_audit_match_empty_filter_passes_all() -> None:
    assert _audit_row_matches(_row(correlation_id="anything"), dict(_EMPTY)) is True
# FR-1.18 traceability marker for existing git-mcp coverage.
@pytest.mark.UT
@pytest.mark.mcp
@pytest.mark.req("FR-018")  # W28E-1804A semantic rebind


def test_audit_match_unemitted_dimension_excludes() -> None:
    # job_id is not emitted on this row -> a job_id filter matches nothing (F-1304-A)
    assert _audit_row_matches(_row(correlation_id="cid-A"), {**_EMPTY, "job_id": "job-9"}) is False
# FR-1.18 traceability marker for existing git-mcp coverage.
@pytest.mark.UT
@pytest.mark.mcp
@pytest.mark.req("FR-018")  # W28E-1804A semantic rebind


def test_audit_endpoint_accepts_filter_params(client_env) -> None:
    # The extended /audit endpoint accepts all 7 filter params (no 422).
    client, headers, _ = client_env
    resp = client.get(
        f"{API}/audit",
        params={"correlation_id": "zzz", "user": "nobody", "workspace_id": "ws-x", "profile_id": "p", "job_id": "j", "entity_kind": "branch", "entity_id": "main"},
        headers=headers,
    )
    assert resp.status_code == 200, resp.text
    # Synthetic non-existent filters -> no matching rows.
    assert resp.json()["result"]["items"] == []


# --- W28J-1327: profile branches (ls-remote) + sync-status ---
# FR-1.18 traceability marker for existing git-mcp coverage.
@pytest.mark.UT
@pytest.mark.mcp
@pytest.mark.req("FR-018")  # W28E-1804A semantic rebind

def test_profile_branches_ls_remote(client_env, workspace_id: str) -> None:
    client, headers, _ = client_env
    resp = client.get(f"{API}/profiles/testprofile/branches", headers=headers)
    assert resp.status_code == 200, resp.text
    items = resp.json()["result"]["items"]
    names = {r["ref_name"] for r in items}
    assert "main" in names
    assert "dev" in names  # enumerated WITHOUT an open workspace (GMC-P-08/11)
    assert any(r["is_default"] for r in items if r["ref_name"] == "main")
# FR-1.18 traceability marker for existing git-mcp coverage.
@pytest.mark.UT
@pytest.mark.mcp
@pytest.mark.req("FR-018")  # W28E-1804A semantic rebind


def test_profile_branches_unknown_profile(client_env) -> None:
    client, headers, _ = client_env
    resp = client.get(f"{API}/profiles/nope/branches", headers=headers)
    assert resp.status_code == 404
# FR-1.18 traceability marker for existing git-mcp coverage.
@pytest.mark.UT
@pytest.mark.mcp
@pytest.mark.req("FR-018")  # W28E-1804A semantic rebind


def test_profile_sync_status_open_workspace(client_env, workspace_id: str) -> None:
    client, headers, _ = client_env
    resp = client.get(f"{API}/profiles/testprofile/sync-status", headers=headers)
    assert resp.status_code == 200, resp.text
    result = resp.json()["result"]
    # A fresh clone is level with its upstream.
    assert result["status"] == "ok"
    assert result["remote_ahead"] == 0
    assert result["remote_behind"] == 0
    assert result["last_sync_at"]
# FR-1.18 traceability marker for existing git-mcp coverage.
@pytest.mark.UT
@pytest.mark.mcp
@pytest.mark.req("FR-018")  # W28E-1804A semantic rebind


def test_profile_sync_status_no_open_workspace(client_env, origin_repo) -> None:
    client, headers, app = client_env
    app.state.profile_store["lonelyprofile"] = {"repo": {"source": str(origin_repo), "default_branch": "main"}}
    resp = client.get(f"{API}/profiles/lonelyprofile/sync-status", headers=headers)
    assert resp.status_code == 200
    assert resp.json()["result"]["status"] == "no_open_workspace"
