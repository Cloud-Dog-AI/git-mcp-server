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

import httpx
import pytest

from tests.helpers import api_url


@pytest.mark.integration
def test_remote_clone_and_fetch(
    integration_server: dict[str, str],
    api_key: str,
    remote_repo_url: str,
) -> None:
    """Requirements: FR-06, FR-10."""
    """IT1.9 -- Clone from configured remote via repo_open, then git_fetch."""
    open_timeout = float(os.environ.get("GIT_MCP_REMOTE_OPEN_TIMEOUT_SECONDS", "600"))
    op_timeout = float(os.environ.get("GIT_MCP_REMOTE_OP_TIMEOUT_SECONDS", "180"))
    base = integration_server["base_url"]
    headers = {"x-api-key": api_key}

    # 1. Open workspace from real remote using the remote_cloud_dog profile
    open_resp = httpx.post(
        api_url(base, "/tools/repo_open"),
        headers=headers,
        json={
            "profile": "remote_cloud_dog",
            "repo_source": remote_repo_url,
            "session_id": "it-remote-clone",
        },
        timeout=open_timeout,
    )
    assert open_resp.status_code == 200, f"repo_open failed: {open_resp.text}"
    opened = open_resp.json()
    assert opened["ok"] is True, f"repo_open not ok: {opened}"
    workspace_id = opened["result"]["workspace_id"]

    # 2. Verify resolved ref is present and is a branch
    assert opened["result"]["resolved_ref"] is not None, "resolved_ref missing"
    assert opened["result"]["resolved_ref"]["type"] == "branch"

    # 3. Fetch from origin (should succeed even if nothing new)
    fetch_resp = httpx.post(
        api_url(base, "/tools/git_fetch"),
        headers=headers,
        json={"workspace_id": workspace_id, "remote": "origin"},
        timeout=op_timeout,
    )
    assert fetch_resp.status_code == 200, f"git_fetch failed: {fetch_resp.text}"
    assert fetch_resp.json()["ok"] is True, f"git_fetch not ok: {fetch_resp.json()}"

    # 4. List repository root to prove clone has real content
    list_resp = httpx.post(
        api_url(base, "/tools/dir_list"),
        headers=headers,
        json={"workspace_id": workspace_id, "path": ".", "recursive": False},
        timeout=op_timeout,
    )
    assert list_resp.status_code == 200, f"dir_list failed: {list_resp.text}"
    entries = list_resp.json()["result"]["entries"]
    assert len(entries) > 0, "Repository root should contain at least one entry after clone"

    # 5. Workspace cleanup is handled by integration fixture teardown.
