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

import json
import os
from pathlib import Path
from uuid import uuid4

import httpx
import websocket
from git import Repo

from tests.helpers import api_url, test_a2a_base_path as a2a_base_path


def _ws_url(base_url: str, api_key: str) -> str:
    """Build the authenticated A2A config-event WebSocket URL."""
    target_base = os.environ.get("TEST_A2A_BASE_URL", "").strip() or base_url
    ws_base = target_base.replace("http://", "ws://", 1).replace("https://", "wss://", 1)
    return f"{ws_base.rstrip('/')}{a2a_base_path()}/events/config?token={api_key}"


def _tool_url(base_url: str, tool_name: str) -> str:
    """Build the authenticated tool endpoint URL for API-backed tool execution."""
    return api_url(base_url, f"/tools/{tool_name}")


def _tool_call(base_url: str, api_key: str, tool_name: str, payload: dict[str, object]) -> httpx.Response:
    """Execute one authenticated tool call over the API tool router."""
    return httpx.post(
        _tool_url(base_url, tool_name),
        headers={"x-api-key": api_key},
        json=payload,
        timeout=10.0,
    )


def _create_profile_repo(path: Path) -> Path:
    """Create a real repository with distinct `main` and `develop` branch content."""
    path.mkdir(parents=True, exist_ok=True)
    repo = Repo.init(path)
    repo.git.config("user.email", "test@example.com")
    repo.git.config("user.name", "Test User")

    readme = path / "README.md"
    readme.write_text("main branch\n", encoding="utf-8")
    repo.index.add(["README.md"])
    repo.index.commit("initial main commit")

    if repo.active_branch.name != "main":
        repo.git.branch("-M", "main")

    repo.git.checkout("-b", "develop")
    develop_marker = path / "DEVELOP.txt"
    develop_marker.write_text("develop branch\n", encoding="utf-8")
    repo.index.add(["DEVELOP.txt"])
    repo.index.commit("add develop marker")

    repo.git.checkout("main")
    main_marker = path / "MAIN.txt"
    main_marker.write_text("main only\n", encoding="utf-8")
    repo.index.add(["MAIN.txt"])
    repo.index.commit("add main marker")
    return path


def test_repo_profile_lifecycle(
    application_server: str,
    application_api_key: str,
    tmp_path: Path,
) -> None:
    """Requirements: FR-01, FR-07, FR-15, CFG-06, CFG-08, CFG-10, CFG-11, CFG-13."""
    admin_headers = {"x-api-key": application_api_key}
    user_id = f"w28a258-user-{uuid4().hex[:8]}"
    profile_name = f"test-repo-w28a258-{uuid4().hex[:8]}"
    repo_path = _create_profile_repo(tmp_path / "restricted-repo")

    create_user = httpx.post(
        api_url(application_server, f"/admin/users/{user_id}"),
        headers=admin_headers,
        json={"username": user_id, "email": f"{user_id}@example.test", "group_ids": []},
        timeout=10.0,
    )
    assert create_user.status_code == 200, create_user.text
    assert create_user.json()["result"]["user_id"] == user_id

    created_key = httpx.post(
        api_url(application_server, "/admin/api-keys"),
        headers=admin_headers,
        json={"name": "w28a258-profile-key", "owner_user_id": user_id, "capabilities": ["admin.profile"]},
        timeout=10.0,
    )
    assert created_key.status_code == 200, created_key.text
    raw_key = created_key.json()["result"]["raw_key"]
    assert raw_key

    tool_probe = httpx.get(api_url(application_server, "/tools"), headers={"x-api-key": raw_key}, timeout=10.0)
    assert tool_probe.status_code == 200, tool_probe.text

    profile_body = {
        "repo": {"source": repo_path.as_posix(), "default_branch": "main"},
        "policy": {"allowed_branches": ["main"], "read_only": True},
    }
    create_profile = httpx.post(
        api_url(application_server, f"/admin/profiles/{profile_name}"),
        headers={"x-api-key": raw_key},
        json=profile_body,
        timeout=10.0,
    )
    assert create_profile.status_code == 200, create_profile.text

    read_profile = httpx.get(
        api_url(application_server, f"/admin/profiles/{profile_name}"),
        headers={"x-api-key": raw_key},
        timeout=10.0,
    )
    assert read_profile.status_code == 200, read_profile.text
    assert read_profile.json()["result"]["policy"]["allowed_branches"] == ["main"]
    assert read_profile.json()["result"]["policy"]["read_only"] is True

    open_workspace = _tool_call(
        application_server,
        raw_key,
        "repo_open",
        {"profile": profile_name, "session_id": f"w28a258-{uuid4().hex[:8]}"},
    )
    assert open_workspace.status_code == 200, open_workspace.text
    workspace_id = open_workspace.json()["result"]["workspace_id"]
    resolved_ref = open_workspace.json()["result"]["resolved_ref"]
    assert resolved_ref["type"] == "branch"
    assert resolved_ref["name"] == "main"

    list_root = _tool_call(
        application_server,
        raw_key,
        "dir_list",
        {"workspace_id": workspace_id, "path": ".", "recursive": False},
    )
    assert list_root.status_code == 200, list_root.text
    entry_names = {Path(entry["path"]).name for entry in list_root.json()["result"]["entries"]}
    assert "README.md" in entry_names
    assert "MAIN.txt" in entry_names
    assert "DEVELOP.txt" not in entry_names

    blocked_branch = _tool_call(
        application_server,
        raw_key,
        "repo_set_ref",
        {"workspace_id": workspace_id, "ref": {"type": "branch", "name": "develop"}},
    )
    assert blocked_branch.status_code == 403
    assert "not allowed" in blocked_branch.text

    blocked_write = _tool_call(
        application_server,
        raw_key,
        "file_write",
        {"workspace_id": workspace_id, "path": "blocked.txt", "content": "nope\n", "overwrite": False},
    )
    assert blocked_write.status_code == 403
    assert "blocked" in blocked_write.text

    client = websocket.create_connection(_ws_url(application_server, raw_key), timeout=10)
    try:
        updated_profile_body = {
            "repo": {"source": repo_path.as_posix(), "default_branch": "main"},
            "policy": {"allowed_branches": ["main", "develop"], "read_only": False},
        }
        update_profile = httpx.put(
            api_url(application_server, f"/admin/profiles/{profile_name}"),
            headers={"x-api-key": raw_key},
            json=updated_profile_body,
            timeout=10.0,
        )
        assert update_profile.status_code == 200, update_profile.text

        update_event = json.loads(client.recv())
        assert update_event["event_type"] == "config_change"
        assert update_event["action"] == "update"
        assert update_event["profile_name"] == profile_name
        assert update_event["actor"] == user_id
    finally:
        client.close()

    allow_develop = _tool_call(
        application_server,
        raw_key,
        "repo_set_ref",
        {"workspace_id": workspace_id, "ref": {"type": "branch", "name": "develop"}},
    )
    assert allow_develop.status_code == 200, allow_develop.text
    assert allow_develop.json()["result"]["resolved_ref"]["name"] == "develop"

    read_develop = _tool_call(
        application_server,
        raw_key,
        "file_read",
        {"workspace_id": workspace_id, "path": "DEVELOP.txt"},
    )
    assert read_develop.status_code == 200, read_develop.text
    assert read_develop.json()["result"]["content"] == "develop branch\n"

    write_develop = _tool_call(
        application_server,
        raw_key,
        "file_write",
        {"workspace_id": workspace_id, "path": "notes.txt", "content": "write enabled\n", "overwrite": False},
    )
    assert write_develop.status_code == 200, write_develop.text
    assert write_develop.json()["result"]["path"] == "notes.txt"

    close_workspace = _tool_call(application_server, raw_key, "repo_close", {"workspace_id": workspace_id})
    assert close_workspace.status_code == 200, close_workspace.text

    delete_profile = httpx.delete(
        api_url(application_server, f"/admin/profiles/{profile_name}"),
        headers={"x-api-key": raw_key},
        timeout=10.0,
    )
    assert delete_profile.status_code == 200, delete_profile.text

    missing_profile = httpx.get(
        api_url(application_server, f"/admin/profiles/{profile_name}"),
        headers=admin_headers,
        timeout=10.0,
    )
    assert missing_profile.status_code == 404

    delete_user = httpx.delete(
        api_url(application_server, f"/admin/users/{user_id}"),
        headers=admin_headers,
        timeout=10.0,
    )
    assert delete_user.status_code == 200, delete_user.text
