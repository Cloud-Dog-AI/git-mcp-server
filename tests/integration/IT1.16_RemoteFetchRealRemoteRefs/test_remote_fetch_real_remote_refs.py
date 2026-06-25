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
from urllib.parse import urlparse

import httpx
import pytest

from tests.helpers import api_url


def _git_output(workspace_path: str, *args: str, container_name: str | None = None) -> str:
    """Run a git command inside the test workspace and return stdout."""
    command = ["git", *args]
    cwd = workspace_path
    if container_name:
        command = ["docker", "exec", container_name, "git", "-C", workspace_path, *args]
        cwd = None
    result = subprocess.run(
        command,
        cwd=cwd,
        text=True,
        capture_output=True,
        timeout=30,
        check=False,
    )
    assert result.returncode == 0, result.stderr or result.stdout
    return result.stdout.strip()
@pytest.mark.IT
@pytest.mark.mcp
@pytest.mark.req("FR-007")  # W28E-1804A semantic rebind


@pytest.mark.integration
def test_git_fetch_restores_real_remote_tracking_ref(
    integration_server: dict[str, str],
    api_key: str,
    remote_repo_url: str,
) -> None:
    """Requirements: FR-06, FR-10.

    IT1.16 -- Fetch from a real remote and restore a deleted remote-tracking ref.

    PS-97 v1.1 §1.1.5 closed-loop boundary-fixture pattern:

    The remote host used by this test is parameterised via env. Callers pick
    the fixture that matches their deployment boundary:

    - Gitea boundary (internal dev + IT tier):
        GIT_MCP_REMOTE_REPO=https://git.cloud-dog.net/playgroup/test-project.git
        IT1_16_REMOTE_HOST=git.cloud-dog.net

    - GitHub boundary (public mirror / external CI):
        GIT_MCP_REMOTE_REPO=https://github.com/cloud-dog-ai/git-test-project-fixture.git
        IT1_16_REMOTE_HOST=github.com

    - Env unset (dev fallback): accepts the ``git.cloud-dog.net`` default
      inherited from the legacy IT env files, preserving the current dev
      workflow without requiring any new env setup.

    NOTE: The boundary fixture repos themselves (Gitea ``test-fixtures/git-test-project``,
    GitHub ``cloud-dog-ai/git-test-project-fixture``) are coordinator/operational
    artefacts — they must exist before this test can run in boundary mode.
    See ``working/w28a-f34-c-apply-logs/phase-f-fixture-repos-needed.md``.
    """
    # PS-97 v1.1 §1.1.5 — remote host is parameterised. Default preserves
    # the pre-PS-97 assertion so the dev workflow does not regress.
    expected_host = os.environ.get("IT1_16_REMOTE_HOST", "git.cloud-dog.net")

    parsed = urlparse(remote_repo_url)
    assert parsed.hostname == expected_host, (
        f"Unexpected remote host: {remote_repo_url} (expected host: {expected_host}; "
        "set IT1_16_REMOTE_HOST to switch boundary fixtures per PS-97 v1.1 §1.1.5)"
    )

    open_timeout = float(os.environ.get("GIT_MCP_REMOTE_OPEN_TIMEOUT_SECONDS", "600"))
    op_timeout = float(os.environ.get("GIT_MCP_REMOTE_OP_TIMEOUT_SECONDS", "180"))
    base = integration_server["base_url"]
    headers = {"x-api-key": api_key}

    open_resp = httpx.post(
        api_url(base, "/tools/repo_open"),
        headers=headers,
        json={
            "profile": "remote_cloud_dog",
            "repo_source": remote_repo_url,
            "session_id": "it-remote-fetch-real-ref",
        },
        timeout=open_timeout,
    )
    assert open_resp.status_code == 200, f"repo_open failed: {open_resp.text}"
    opened = open_resp.json()
    assert opened["ok"] is True, f"repo_open not ok: {opened}"

    workspace_id = opened["result"]["workspace_id"]
    workspace_path = opened["result"]["path"]
    container_name = (
        os.environ.get("GIT_MCP_CONTAINER_NAME", "git-mcp-server")
        if bool(integration_server.get("external_runtime", False))
        else None
    )

    remote_refs = [
        line.strip()
        for line in _git_output(
            workspace_path,
            "for-each-ref",
            "refs/remotes/origin",
            "--format=%(refname:short)",
            container_name=container_name,
        ).splitlines()
        if line.strip().startswith("origin/") and line.strip() != "origin/HEAD"
    ]
    assert remote_refs, "Expected at least one real remote-tracking ref after clone"
    tracked_ref = remote_refs[0]
    tracked_ref_path = f"refs/remotes/{tracked_ref}"

    _git_output(workspace_path, "update-ref", "-d", tracked_ref_path, container_name=container_name)
    remote_refs_after_delete = {
        line.strip()
        for line in _git_output(
            workspace_path,
            "for-each-ref",
            "refs/remotes/origin",
            "--format=%(refname:short)",
            container_name=container_name,
        ).splitlines()
        if line.strip().startswith("origin/")
    }
    assert tracked_ref not in remote_refs_after_delete, f"Expected {tracked_ref} to be deleted locally before fetch"

    fetch_resp = httpx.post(
        api_url(base, "/tools/git_fetch"),
        headers=headers,
        json={"workspace_id": workspace_id, "remote": "origin"},
        timeout=op_timeout,
    )
    assert fetch_resp.status_code == 200, f"git_fetch failed: {fetch_resp.text}"
    fetched = fetch_resp.json()
    assert fetched["ok"] is True, f"git_fetch not ok: {fetched}"

    fetch_result = str(fetched["result"]["result"]).strip()
    assert fetch_result, "Expected git_fetch to return real remote fetch output"
    print(f"git_fetch output: {fetch_result}")
    assert tracked_ref in fetch_result, f"Expected fetch output to mention {tracked_ref}: {fetch_result}"
    lowered = fetch_result.lower()
    assert "auth" not in lowered, f"Unexpected auth failure in fetch output: {fetch_result}"
    assert "refused" not in lowered, f"Unexpected network failure in fetch output: {fetch_result}"

    remote_refs_after_fetch = {
        line.strip()
        for line in _git_output(
            workspace_path,
            "for-each-ref",
            "refs/remotes/origin",
            "--format=%(refname:short)",
            container_name=container_name,
        ).splitlines()
        if line.strip().startswith("origin/")
    }
    assert tracked_ref in remote_refs_after_fetch, f"Expected {tracked_ref} to be restored by git_fetch"
    assert "origin/" in fetch_result, f"Expected remote branch information in fetch output: {fetch_result}"
