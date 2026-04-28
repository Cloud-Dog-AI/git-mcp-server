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

import os
from uuid import uuid4

import httpx

from tests.helpers import api_url


def test_admin_http_crud_contract(
    integration_server: dict[str, str | bool],
    api_key: str,
) -> None:
    """Requirements: FR-15, FR-17, CFG-08, CFG-09, CFG-10, CFG-11."""
    base_url = str(integration_server["base_url"])
    headers = {"x-api-key": api_key}
    user_id = f"cfg-user-{uuid4().hex[:8]}"
    group_id = f"cfg-group-{uuid4().hex[:8]}"

    created_user = httpx.post(
        api_url(base_url, f"/admin/users/{user_id}"),
        headers=headers,
        json={"username": user_id, "email": f"{user_id}@example.test", "group_ids": [group_id]},
        timeout=10.0,
    )
    assert created_user.status_code == 200
    assert created_user.json()["result"]["user_id"] == user_id

    listed_users = httpx.get(api_url(base_url, "/admin/users"), headers=headers, timeout=10.0)
    assert listed_users.status_code == 200
    assert user_id in listed_users.json()["result"]["items"]

    updated_user = httpx.put(
        api_url(base_url, f"/admin/users/{user_id}"),
        headers=headers,
        json={"username": f"{user_id}-updated", "email": f"{user_id}@example.test", "group_ids": []},
        timeout=10.0,
    )
    assert updated_user.status_code == 200
    assert updated_user.json()["result"]["username"] == f"{user_id}-updated"

    created_group = httpx.post(
        api_url(base_url, f"/admin/groups/{group_id}"),
        headers=headers,
        json={"description": "Config admins", "roles": ["admin", "writer"], "members": [user_id]},
        timeout=10.0,
    )
    assert created_group.status_code == 200
    assert created_group.json()["result"]["roles"] == ["admin", "writer"]

    updated_group = httpx.put(
        api_url(base_url, f"/admin/groups/{group_id}"),
        headers=headers,
        json={"description": "Config readers", "roles": ["reader"], "members": [user_id]},
        timeout=10.0,
    )
    assert updated_group.status_code == 200
    assert updated_group.json()["result"]["roles"] == ["reader"]

    created_key = httpx.post(
        api_url(base_url, "/admin/api-keys"),
        headers=headers,
        json={"name": "cfg-http-key", "owner_user_id": user_id, "capabilities": ["admin.profile", "admin.identity"]},
        timeout=10.0,
    )
    assert created_key.status_code == 200
    key_payload = created_key.json()["result"]
    assert key_payload["capabilities"] == ["admin.profile", "admin.identity"]
    assert key_payload["raw_key"]

    raw_key = key_payload["raw_key"]
    using_key = httpx.get(api_url(base_url, "/tools"), headers={"x-api-key": raw_key}, timeout=10.0)
    assert using_key.status_code == 200

    listed_keys = httpx.get(api_url(base_url, "/admin/api-keys"), headers=headers, timeout=10.0)
    assert listed_keys.status_code == 200
    items = listed_keys.json()["result"]["items"]
    assert any(item["key_id"] == key_payload["key_id"] for item in items)

    updated_key = httpx.put(
        api_url(base_url, f"/admin/api-keys/{key_payload['key_id']}"),
        headers=headers,
        json={"name": "cfg-http-key-updated", "capabilities": ["tools:read"]},
        timeout=10.0,
    )
    assert updated_key.status_code == 200
    assert updated_key.json()["result"]["name"] == "cfg-http-key-updated"
    assert updated_key.json()["result"]["capabilities"] == ["tools:read"]

    revoked_key = httpx.delete(api_url(base_url, f"/admin/api-keys/{key_payload['key_id']}"), headers=headers, timeout=10.0)
    assert revoked_key.status_code == 200

    revoked_use = httpx.get(api_url(base_url, "/tools"), headers={"x-api-key": raw_key}, timeout=10.0)
    assert revoked_use.status_code == 401

    deleted_group = httpx.delete(api_url(base_url, f"/admin/groups/{group_id}"), headers=headers, timeout=10.0)
    assert deleted_group.status_code == 200
    deleted_user = httpx.delete(api_url(base_url, f"/admin/users/{user_id}"), headers=headers, timeout=10.0)
    assert deleted_user.status_code == 200


def test_admin_http_requires_admin_role(
    integration_server: dict[str, str | bool],
    api_key: str,
) -> None:
    """Requirements: FR-05, CFG-09, CFG-10, CFG-11."""
    base_url = str(integration_server["base_url"])
    headers = {"x-api-key": api_key}
    user_id = f"cfg-reader-{uuid4().hex[:8]}"

    created_user = httpx.post(
        api_url(base_url, f"/admin/users/{user_id}"),
        headers=headers,
        json={"username": user_id, "email": f"{user_id}@example.test", "group_ids": []},
        timeout=10.0,
    )
    assert created_user.status_code == 200

    created_key = httpx.post(
        api_url(base_url, "/admin/api-keys"),
        headers=headers,
        json={"name": "cfg-reader-key", "owner_user_id": user_id, "capabilities": ["tools:read"]},
        timeout=10.0,
    )
    assert created_key.status_code == 200
    key_payload = created_key.json()["result"]

    bind_role = httpx.post(
        api_url(base_url, "/tools/admin_rbac_bind"),
        headers=headers,
        json={"user_id": user_id, "role": "reader"},
        timeout=10.0,
    )
    assert bind_role.status_code == 200

    restricted_headers = {"x-api-key": key_payload["raw_key"]}
    denied = httpx.post(
        api_url(base_url, f"/admin/users/{user_id}-blocked"),
        headers=restricted_headers,
        json={"username": f"{user_id}-blocked", "email": f"{user_id}-blocked@example.test", "group_ids": []},
        timeout=10.0,
    )
    assert denied.status_code == 403
    assert denied.json()["detail"] == "Forbidden: admin role required"

    cleanup_key = httpx.delete(
        api_url(base_url, f"/admin/api-keys/{key_payload['key_id']}"),
        headers=headers,
        timeout=10.0,
    )
    assert cleanup_key.status_code == 200
    cleanup_user = httpx.delete(api_url(base_url, f"/admin/users/{user_id}"), headers=headers, timeout=10.0)
    assert cleanup_user.status_code == 200


def test_tool_http_requires_resolved_reader_role_for_repo_access(
    integration_server: dict[str, str | bool],
    api_key: str,
    remote_repo_url: str,
) -> None:
    """Requirements: FR-05, CFG-09, CFG-10, CFG-11."""
    base_url = str(integration_server["base_url"])
    headers = {"x-api-key": api_key}
    profile_name = f"cfg-remote-{uuid4().hex[:8]}"
    user_id = f"cfg-reader-{uuid4().hex[:8]}"
    group_id = f"cfg-reader-group-{uuid4().hex[:8]}"
    remote_repo = remote_repo_url

    created_profile = httpx.post(
        api_url(base_url, f"/admin/profiles/{profile_name}"),
        headers=headers,
        json={"repo": {"source": remote_repo, "default_branch": "main"}, "policy": {"allowed_branches": ["main"]}},
        timeout=30.0,
    )
    assert created_profile.status_code == 200, created_profile.text

    created_user = httpx.post(
        api_url(base_url, f"/admin/users/{user_id}"),
        headers=headers,
        json={"username": user_id, "email": f"{user_id}@example.test", "group_ids": []},
        timeout=10.0,
    )
    assert created_user.status_code == 200, created_user.text

    created_key = httpx.post(
        api_url(base_url, "/admin/api-keys"),
        headers=headers,
        json={"name": "cfg-remote-reader-key", "owner_user_id": user_id, "capabilities": ["tools:read"]},
        timeout=10.0,
    )
    assert created_key.status_code == 200, created_key.text
    key_payload = created_key.json()["result"]
    restricted_headers = {"x-api-key": key_payload["raw_key"]}

    created_group = httpx.post(
        api_url(base_url, f"/admin/groups/{group_id}"),
        headers=headers,
        json={"description": "Remote readers", "roles": ["reader"], "members": [user_id]},
        timeout=10.0,
    )
    assert created_group.status_code == 200, created_group.text

    denied = httpx.post(
        api_url(base_url, "/tools/repo_open"),
        headers=restricted_headers,
        json={"profile": profile_name, "session_id": f"cfg-denied-{uuid4().hex[:8]}", "ref": {"type": "branch", "name": "main"}},
        timeout=30.0,
    )
    assert denied.status_code == 403, denied.text
    assert denied.json()["detail"] == f"Access denied to profile '{profile_name}'"

    granted_group = httpx.put(
        api_url(base_url, f"/admin/groups/{group_id}"),
        headers=headers,
        json={"description": "Remote readers", "roles": ["reader", f"profile:{profile_name}"], "members": [user_id]},
        timeout=10.0,
    )
    assert granted_group.status_code == 200, granted_group.text

    allowed_open = httpx.post(
        api_url(base_url, "/tools/repo_open"),
        headers=restricted_headers,
        json={"profile": profile_name, "session_id": f"cfg-allowed-{uuid4().hex[:8]}", "ref": {"type": "branch", "name": "main"}},
        timeout=60.0,
    )
    assert allowed_open.status_code == 200, allowed_open.text
    workspace_id = allowed_open.json()["result"]["workspace_id"]

    allowed_list = httpx.post(
        api_url(base_url, "/tools/dir_list"),
        headers=restricted_headers,
        json={"workspace_id": workspace_id, "path": ".", "recursive": False},
        timeout=30.0,
    )
    assert allowed_list.status_code == 200, allowed_list.text
    assert any(item["path"] == "README.md" for item in allowed_list.json()["result"]["entries"])

    removed_group = httpx.put(
        api_url(base_url, f"/admin/groups/{group_id}"),
        headers=headers,
        json={"description": "Remote readers", "roles": ["reader"], "members": [user_id]},
        timeout=10.0,
    )
    assert removed_group.status_code == 200, removed_group.text

    denied_again = httpx.post(
        api_url(base_url, "/tools/dir_list"),
        headers=restricted_headers,
        json={"workspace_id": workspace_id, "path": ".", "recursive": False},
        timeout=30.0,
    )
    assert denied_again.status_code == 403, denied_again.text
    assert denied_again.json()["detail"] == f"Access denied to profile '{profile_name}'"

    closed = httpx.post(
        api_url(base_url, "/tools/repo_close"),
        headers=headers,
        json={"workspace_id": workspace_id},
        timeout=10.0,
    )
    assert closed.status_code == 200, closed.text

    revoked_key = httpx.delete(
        api_url(base_url, f"/admin/api-keys/{key_payload['key_id']}"),
        headers=headers,
        timeout=10.0,
    )
    assert revoked_key.status_code == 200
    deleted_group = httpx.delete(api_url(base_url, f"/admin/groups/{group_id}"), headers=headers, timeout=10.0)
    assert deleted_group.status_code == 200
    deleted_user = httpx.delete(api_url(base_url, f"/admin/users/{user_id}"), headers=headers, timeout=10.0)
    assert deleted_user.status_code == 200
    deleted_profile = httpx.delete(api_url(base_url, f"/admin/profiles/{profile_name}"), headers=headers, timeout=10.0)
    assert deleted_profile.status_code == 200


def test_admin_mcp_tool_parity(integration_server: dict[str, str | bool]) -> None:
    """Requirements: FR-15, FR-17, CFG-08, CFG-09, CFG-10, CFG-11."""
    mcp_base = str(integration_server["mcp_url"]).rstrip("/")
    user_id = f"cfg-mcp-user-{uuid4().hex[:8]}"
    group_id = f"cfg-mcp-group-{uuid4().hex[:8]}"

    created_user = httpx.post(
        f"{mcp_base}/mcp/tools/admin_user_create",
        json={"user_id": user_id, "username": user_id, "email": f"{user_id}@example.test", "group_ids": [group_id]},
        timeout=10.0,
    )
    assert created_user.status_code == 200
    assert created_user.json()["data"]["user_id"] == user_id

    listed_users = httpx.post(f"{mcp_base}/mcp/tools/admin_user_list", json={}, timeout=10.0)
    assert listed_users.status_code == 200
    assert user_id in listed_users.json()["data"]["items"]

    created_group = httpx.post(
        f"{mcp_base}/mcp/tools/admin_group_create",
        json={"group_id": group_id, "description": "MCP admins", "roles": ["writer"], "members": [user_id]},
        timeout=10.0,
    )
    assert created_group.status_code == 200
    assert created_group.json()["data"]["group_id"] == group_id

    listed_groups = httpx.post(f"{mcp_base}/mcp/tools/admin_group_list", json={}, timeout=10.0)
    assert listed_groups.status_code == 200
    assert group_id in listed_groups.json()["data"]["items"]

    created_key = httpx.post(
        f"{mcp_base}/mcp/tools/admin_api_key_create",
        json={"name": "cfg-mcp-key", "owner_user_id": user_id, "capabilities": ["admin.profile"]},
        timeout=10.0,
    )
    assert created_key.status_code == 200
    key_payload = created_key.json()["data"]
    assert key_payload["owner_user_id"] == user_id
    assert key_payload["capabilities"] == ["admin.profile"]

    listed_keys = httpx.post(f"{mcp_base}/mcp/tools/admin_api_key_list", json={}, timeout=10.0)
    assert listed_keys.status_code == 200
    assert any(item["key_id"] == key_payload["key_id"] for item in listed_keys.json()["data"]["items"])

    revoked_key = httpx.post(
        f"{mcp_base}/mcp/tools/admin_api_key_revoke",
        json={"key_id": key_payload["key_id"]},
        timeout=10.0,
    )
    assert revoked_key.status_code == 200
    assert revoked_key.json()["data"]["revoked"] is True

    deleted_group = httpx.post(
        f"{mcp_base}/mcp/tools/admin_group_delete",
        json={"group_id": group_id},
        timeout=10.0,
    )
    assert deleted_group.status_code == 200
    deleted_user = httpx.post(
        f"{mcp_base}/mcp/tools/admin_user_delete",
        json={"user_id": user_id},
        timeout=10.0,
    )
    assert deleted_user.status_code == 200
