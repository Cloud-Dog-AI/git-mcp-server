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

from tests.helpers import create_repo_with_remote, mcp_url


def test_mcp_tool_execution_remote(tmp_path: Path, integration_server: dict[str, str]) -> None:
    """Requirements: FR-01."""
    daemon_host = urlparse(integration_server["base_url"]).hostname or ""
    assert daemon_host
    work = tmp_path / "mcp-network-remote"
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

        remote_repo = f"git://{daemon_host}:{port}/remote.git"
        open_response = httpx.post(
            mcp_url(integration_server["mcp_url"], "/tools/repo_open"),
            json={
                "profile": "remote-check",
                "repo_source": remote_repo,
                "session_id": "it-remote-open",
            },
            timeout=20.0,
        )
        assert open_response.status_code == 200, open_response.text
        opened = open_response.json()
        assert opened["ok"] is True
        workspace_id = opened["data"]["workspace_id"]

        fetch_response = httpx.post(
            mcp_url(integration_server["mcp_url"], "/tools/git_fetch"),
            json={"workspace_id": workspace_id, "remote": "origin"},
            timeout=20.0,
        )
        assert fetch_response.status_code == 200, fetch_response.text
        fetched = fetch_response.json()
        assert fetched["ok"] is True
    finally:
        daemon.terminate()
        daemon.wait(timeout=5)
