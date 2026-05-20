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
import subprocess
import uuid

import httpx
import pytest

from tests.helpers import api_url


@pytest.mark.integration
def test_remote_branch_push(
    integration_server: dict[str, str],
    api_key: str,
    remote_repo_url: str,
) -> None:
    """Requirements: FR-06, FR-10."""
    """IT1.10 -- Push a test branch to configured remote and delete it."""
    open_timeout = float(os.environ.get("GIT_MCP_REMOTE_OPEN_TIMEOUT_SECONDS", "600"))
    op_timeout = float(os.environ.get("GIT_MCP_REMOTE_OP_TIMEOUT_SECONDS", "180"))
    prefix = os.environ.get("GIT_MCP_REMOTE_BRANCH_PREFIX", "test/git-mcp-")
    branch_name = f"{prefix}{uuid.uuid4().hex[:8]}"
    base = integration_server["base_url"]
    headers = {"x-api-key": api_key}
    external = bool(integration_server.get("external_runtime", False))

    # 1. Open workspace from real remote
    open_resp = httpx.post(
        api_url(base, "/tools/repo_open"),
        headers=headers,
        json={
            "profile": "remote_cloud_dog",
            "repo_source": remote_repo_url,
            "session_id": "it-remote-push",
        },
        timeout=open_timeout,
    )
    assert open_resp.status_code == 200, f"repo_open failed: {open_resp.text}"
    assert open_resp.json()["ok"] is True, f"repo_open not ok: {open_resp.json()}"
    workspace_id = open_resp.json()["result"]["workspace_id"]
    workspace_path = open_resp.json()["result"]["path"]

    # 2. Create branch, checkout, and push
    steps: list[tuple[str, dict]] = [
        ("git_branch_create", {"workspace_id": workspace_id, "name": branch_name}),
        ("git_checkout", {"workspace_id": workspace_id, "ref": branch_name}),
        (
            "git_push",
            {
                "workspace_id": workspace_id,
                "remote": "origin",
                "branch": branch_name,
                "force_with_lease": False,
            },
        ),
    ]
    for tool, payload in steps:
        resp = httpx.post(
            api_url(base, f"/tools/{tool}"),
            headers=headers,
            json=payload,
            timeout=op_timeout,
        )
        assert resp.status_code == 200, f"{tool} HTTP failed: {resp.text}"
        assert resp.json()["ok"] is True, f"{tool} not ok: {resp.json()}"

    # 3. Cleanup: delete the remote branch via raw git
    #    (independent of tool under test to avoid masking failures)
    if external:
        container_name = os.environ.get("GIT_MCP_CONTAINER_NAME", "git-mcp-server")
        subprocess.run(
            ["docker", "exec", container_name, "git", "-C", workspace_path, "push", "origin", "--delete", branch_name],
            capture_output=True,
            timeout=30,
            check=False,
        )
    else:
        subprocess.run(
            ["git", "push", "origin", "--delete", branch_name],
            cwd=workspace_path,
            capture_output=True,
            timeout=30,
        )

    # 4. Workspace cleanup is handled by integration fixture teardown.
