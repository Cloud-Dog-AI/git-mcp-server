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

import socket
import subprocess
import time
from pathlib import Path
from urllib.parse import urlparse

import httpx
import pytest
from git import Repo

from tests.helpers import api_url, create_repo_with_remote


def _tool_call(base_url: str, api_key: str, tool: str, payload: dict[str, object]) -> dict[str, object]:
    response = httpx.post(
        api_url(base_url, f"/tools/{tool}"),
        headers={"x-api-key": api_key},
        json=payload,
        timeout=20.0,
    )
    assert response.status_code == 200, response.text
    data = response.json()
    assert data["ok"] is True
    return data["result"]


@pytest.mark.integration
def test_api_rbac_enforce_remote(tmp_path: Path, integration_server: dict[str, str], api_key: str) -> None:
    # Use a network remote (git daemon) to validate push over transport, not filesystem path.
    """Requirements: FR-05."""
    daemon_host = urlparse(integration_server["base_url"]).hostname or ""
    assert daemon_host
    work = tmp_path / "network-remote"
    local, _ = create_repo_with_remote(work / "seed-local", work / "remote.git")
    _ = local

    with socket.socket() as probe:
        probe.bind((daemon_host, 0))
        port = int(probe.getsockname()[1])

    daemon = subprocess.Popen(
        [
            "git",
            "daemon",
            "--reuseaddr",
            f"--base-path={work.as_posix()}",
            "--export-all",
            "--enable=receive-pack",
            f"--listen={daemon_host}",
            f"--port={port}",
            work.as_posix(),
        ],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
    )

    try:
        ready = False
        deadline = time.time() + 10
        while time.time() < deadline:
            if daemon.poll() is not None:
                break
            with socket.socket() as sock:
                if sock.connect_ex((daemon_host, port)) == 0:
                    ready = True
                    break
            time.sleep(0.2)
        if not ready:
            stderr = daemon.stderr.read() if daemon.stderr is not None else ""
            raise AssertionError(f"git daemon failed to start on port {port}: {stderr}")

        remote_url = f"git://{daemon_host}:{port}/remote.git"
        opened = _tool_call(
            integration_server["base_url"],
            api_key,
            "repo_open",
            {
                "profile": "network",
                "repo_source": remote_url,
                "session_id": "it-rbac-1",
            },
        )
        workspace_id = str(opened["workspace_id"])

        _tool_call(
            integration_server["base_url"],
            api_key,
            "git_branch_create",
            {"workspace_id": workspace_id, "name": "test/git-mcp-rbac"},
        )
        _tool_call(
            integration_server["base_url"],
            api_key,
            "git_checkout",
            {"workspace_id": workspace_id, "ref": "test/git-mcp-rbac"},
        )
        _tool_call(
            integration_server["base_url"],
            api_key,
            "file_write",
            {
                "workspace_id": workspace_id,
                "path": "README.md",
                "content": "updated via integration test\n",
                "overwrite": True,
            },
        )
        _tool_call(
            integration_server["base_url"],
            api_key,
            "git_add",
            {"workspace_id": workspace_id, "paths": ["README.md"]},
        )
        _tool_call(
            integration_server["base_url"],
            api_key,
            "git_commit",
            {"workspace_id": workspace_id, "message": "integration network push"},
        )
        _tool_call(
            integration_server["base_url"],
            api_key,
            "git_push",
            {
                "workspace_id": workspace_id,
                "remote": "origin",
                "branch": "test/git-mcp-rbac",
                "force_with_lease": False,
            },
        )

        remote_repo = Repo((work / "remote.git").as_posix())
        refs = {ref.name for ref in remote_repo.references}
        assert "test/git-mcp-rbac" in refs
    finally:
        daemon.terminate()
        daemon.wait(timeout=5)
