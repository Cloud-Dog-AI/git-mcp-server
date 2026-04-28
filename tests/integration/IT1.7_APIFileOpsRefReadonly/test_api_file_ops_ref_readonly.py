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
from pathlib import Path

import httpx

from tests.helpers import api_url, create_repo


def _docker_container_exists(name: str) -> bool:
    result = subprocess.run(
        ["docker", "inspect", name],
        check=False,
        capture_output=True,
        text=True,
        timeout=10,
    )
    return result.returncode == 0


def _resolve_container_name() -> str:
    """Resolve the external runtime container name with deterministic fallbacks."""
    configured = os.environ.get("GIT_MCP_CONTAINER_NAME", "").strip()
    candidates = [configured, "git-mcp-server", "git-mcp-all"]
    for candidate in candidates:
        if candidate and _docker_container_exists(candidate):
            return candidate
    return ""


def test_api_file_ops_ref_readonly(tmp_path: Path, integration_server: dict[str, str], api_key: str) -> None:
    """Requirements: FR-07."""
    external = bool(integration_server.get("external_runtime", False))
    container_name = _resolve_container_name()
    use_container_runtime = external and bool(container_name)
    external_repo_path = ""

    if use_container_runtime:
        external_repo_path = f"/app/working/it-readonly-{uuid.uuid4().hex[:8]}"
        subprocess.run(
            [
                "docker",
                "exec",
                container_name,
                "/bin/sh",
                "-lc",
                (
                    "set -e; "
                    f"rm -rf '{external_repo_path}'; "
                    f"git init '{external_repo_path}'; "
                    f"git -C '{external_repo_path}' config user.email 'it@example.com'; "
                    f"git -C '{external_repo_path}' config user.name 'IT Runner'; "
                    f"printf 'hello\\n' > '{external_repo_path}/README.md'; "
                    f"git -C '{external_repo_path}' add README.md; "
                    f"git -C '{external_repo_path}' commit -m 'init'; "
                    f"git -C '{external_repo_path}' tag v1.0.0"
                ),
            ],
            check=True,
            capture_output=True,
            text=True,
            timeout=30,
        )
        repo_source = external_repo_path
    else:
        repo = create_repo(tmp_path / "repo")
        repo.create_tag("v1.0.0")
        repo_source = repo.working_tree_dir

    open_response = httpx.post(
        api_url(integration_server["base_url"], "/tools/repo_open"),
        headers={"x-api-key": api_key},
        json={
            "profile": "repoA",
            "repo_source": repo_source,
            "session_id": "it-readonly",
            "ref": {"type": "tag", "name": "v1.0.0"},
        },
        timeout=20.0,
    )
    assert open_response.status_code == 200, open_response.text
    opened = open_response.json()["result"]
    assert opened["resolved_ref"]["mode"] == "ref_readonly"

    write_response = httpx.post(
        api_url(integration_server["base_url"], "/tools/file_write"),
        headers={"x-api-key": api_key},
        json={"workspace_id": opened["workspace_id"], "path": "README.md", "content": "blocked\n"},
        timeout=10.0,
    )
    assert write_response.status_code == 403
    assert "ref_readonly" in write_response.text

    if use_container_runtime and external_repo_path:
        subprocess.run(
            ["docker", "exec", container_name, "rm", "-rf", external_repo_path],
            check=False,
            capture_output=True,
            text=True,
            timeout=10,
        )
