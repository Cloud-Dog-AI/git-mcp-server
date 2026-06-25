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

import ast
import json
from pathlib import Path
from uuid import uuid4

import httpx
import pytest

from tests.helpers import a2a_url, api_url, create_repo


def _repo_source(path: Path) -> str:
    repo = create_repo(path)
    return Path(repo.working_tree_dir).resolve().as_posix()


def _post_api_tool(base_url: str, raw_key: str, tool: str, payload: dict) -> httpx.Response:
    return httpx.post(
        api_url(base_url, f"/tools/{tool}"),
        headers={"x-api-key": raw_key},
        json=payload,
        timeout=30.0,
    )


def _post_mcp_tool(mcp_base: str, raw_key: str, tool: str, payload: dict) -> httpx.Response:
    return httpx.post(
        f"{mcp_base.rstrip('/')}/mcp/tools/{tool}",
        headers={"x-api-key": raw_key},
        json=payload,
        timeout=30.0,
    )


def _post_a2a_task(base_url: str, raw_key: str | None, skill: str, payload: dict) -> httpx.Response:
    headers = {"Authorization": f"Bearer {raw_key}"} if raw_key is not None else {}
    return httpx.post(
        a2a_url(base_url, "/tasks"),
        headers=headers,
        json={"id": f"task-{uuid4().hex[:8]}", "skill_id": skill, "input": {"text": json.dumps(payload)}},
        timeout=30.0,
    )


def _a2a_result_payload(response: httpx.Response) -> dict:
    text = response.json()["output"]["text"]
    parsed = ast.literal_eval(text)
    assert isinstance(parsed, dict)
    return parsed


@pytest.mark.IT
@pytest.mark.api
@pytest.mark.mcp
@pytest.mark.a2a
@pytest.mark.negative
@pytest.mark.req("FR-004")
@pytest.mark.req("FR-019")
@pytest.mark.req("FR-023")
@pytest.mark.req("CS-011")
def test_idam_group_profile_cascade_denies_unbound_and_revokes_live_across_surfaces(
    integration_server: dict[str, str | bool],
    api_key: str,
    tmp_path: Path,
) -> None:
    """FR-019: group profile grants apply, isolate unbound profiles, and revoke without restart."""
    base_url = str(integration_server["base_url"])
    mcp_base = str(integration_server["mcp_url"])
    admin_headers = {"x-api-key": api_key}
    suffix = uuid4().hex[:8]
    profile_a = f"idam-prof-a-{suffix}"
    profile_b = f"idam-prof-b-{suffix}"
    user_id = f"idam-user-{suffix}"
    group_id = f"idam-group-{suffix}"
    raw_key = ""
    key_id = ""
    opened_workspaces: list[str] = []

    try:
        for profile_name, repo_dir in (
            (profile_a, tmp_path / "source-a"),
            (profile_b, tmp_path / "source-b"),
        ):
            created_profile = httpx.post(
                api_url(base_url, f"/admin/profiles/{profile_name}"),
                headers=admin_headers,
                json={"repo": {"source": _repo_source(repo_dir), "default_branch": "master"}},
                timeout=10.0,
            )
            assert created_profile.status_code == 200, created_profile.text

        created_user = httpx.post(
            api_url(base_url, f"/admin/users/{user_id}"),
            headers=admin_headers,
            json={"username": user_id, "email": f"{user_id}@example.test", "group_ids": []},
            timeout=10.0,
        )
        assert created_user.status_code == 200, created_user.text

        created_group = httpx.post(
            api_url(base_url, f"/admin/groups/{group_id}"),
            headers=admin_headers,
            json={"description": "IDAM cascade readers", "roles": ["reader"], "members": [user_id]},
            timeout=10.0,
        )
        assert created_group.status_code == 200, created_group.text

        created_key = httpx.post(
            api_url(base_url, "/admin/api-keys"),
            headers=admin_headers,
            json={"name": f"idam-key-{suffix}", "owner_user_id": user_id, "capabilities": ["tools:read"]},
            timeout=10.0,
        )
        assert created_key.status_code == 200, created_key.text
        key_payload = created_key.json()["result"]
        raw_key = key_payload["raw_key"]
        key_id = key_payload["key_id"]

        no_a2a_auth = _post_a2a_task(base_url, None, "repo_open", {"profile": profile_a})
        assert no_a2a_auth.status_code == 401
        wrong_a2a_auth = _post_a2a_task(base_url, "wrong-key", "repo_open", {"profile": profile_a})
        assert wrong_a2a_auth.status_code == 401

        denied_before_grant = _post_api_tool(
            base_url,
            raw_key,
            "repo_open",
            {"profile": profile_a, "session_id": f"api-denied-{suffix}"},
        )
        assert denied_before_grant.status_code == 403, denied_before_grant.text
        assert denied_before_grant.json()["detail"] == f"Access denied to profile '{profile_a}'"

        granted_group = httpx.put(
            api_url(base_url, f"/admin/groups/{group_id}"),
            headers=admin_headers,
            json={
                "description": "IDAM cascade readers",
                "roles": ["reader", f"profile:{profile_a}"],
                "members": [user_id],
            },
            timeout=10.0,
        )
        assert granted_group.status_code == 200, granted_group.text

        api_open = _post_api_tool(
            base_url,
            raw_key,
            "repo_open",
            {"profile": profile_a, "session_id": f"api-allowed-{suffix}"},
        )
        assert api_open.status_code == 200, api_open.text
        api_workspace = api_open.json()["result"]["workspace_id"]
        opened_workspaces.append(api_workspace)

        api_other_profile = _post_api_tool(
            base_url,
            raw_key,
            "repo_open",
            {"profile": profile_b, "session_id": f"api-other-{suffix}"},
        )
        assert api_other_profile.status_code == 403, api_other_profile.text
        assert api_other_profile.json()["detail"] == f"Access denied to profile '{profile_b}'"

        mcp_open = _post_mcp_tool(
            mcp_base,
            raw_key,
            "repo_open",
            {"profile": profile_a, "session_id": f"mcp-allowed-{suffix}"},
        )
        assert mcp_open.status_code == 200, mcp_open.text
        mcp_workspace = mcp_open.json()["data"]["workspace_id"]
        opened_workspaces.append(mcp_workspace)

        mcp_other_profile = _post_mcp_tool(
            mcp_base,
            raw_key,
            "repo_open",
            {"profile": profile_b, "session_id": f"mcp-other-{suffix}"},
        )
        assert mcp_other_profile.status_code == 403, mcp_other_profile.text

        a2a_open = _post_a2a_task(
            base_url,
            raw_key,
            "repo_open",
            {"profile": profile_a, "session_id": f"a2a-allowed-{suffix}"},
        )
        assert a2a_open.status_code == 200, a2a_open.text
        a2a_workspace = _a2a_result_payload(a2a_open)["workspace_id"]
        opened_workspaces.append(a2a_workspace)

        a2a_other_profile = _post_a2a_task(
            base_url,
            raw_key,
            "repo_open",
            {"profile": profile_b, "session_id": f"a2a-other-{suffix}"},
        )
        assert a2a_other_profile.status_code == 403, a2a_other_profile.text

        revoked_group = httpx.put(
            api_url(base_url, f"/admin/groups/{group_id}"),
            headers=admin_headers,
            json={"description": "IDAM cascade readers", "roles": ["reader"], "members": [user_id]},
            timeout=10.0,
        )
        assert revoked_group.status_code == 200, revoked_group.text

        api_after_revoke = _post_api_tool(
            base_url,
            raw_key,
            "dir_list",
            {"workspace_id": api_workspace, "path": ".", "recursive": False},
        )
        assert api_after_revoke.status_code == 403, api_after_revoke.text

        mcp_after_revoke = _post_mcp_tool(
            mcp_base,
            raw_key,
            "dir_list",
            {"workspace_id": mcp_workspace, "path": ".", "recursive": False},
        )
        assert mcp_after_revoke.status_code == 403, mcp_after_revoke.text

        a2a_after_revoke = _post_a2a_task(base_url, raw_key, "git_status", {"workspace_id": a2a_workspace})
        assert a2a_after_revoke.status_code == 403, a2a_after_revoke.text

    finally:
        for workspace_id in opened_workspaces:
            _post_api_tool(base_url, api_key, "repo_close", {"workspace_id": workspace_id})
        if key_id:
            httpx.delete(
                api_url(base_url, f"/admin/api-keys/{key_id}"),
                headers=admin_headers,
                timeout=10.0,
            )
        httpx.delete(api_url(base_url, f"/admin/groups/{group_id}"), headers=admin_headers, timeout=10.0)
        httpx.delete(api_url(base_url, f"/admin/users/{user_id}"), headers=admin_headers, timeout=10.0)
        httpx.delete(api_url(base_url, f"/admin/profiles/{profile_a}"), headers=admin_headers, timeout=10.0)
        httpx.delete(api_url(base_url, f"/admin/profiles/{profile_b}"), headers=admin_headers, timeout=10.0)
