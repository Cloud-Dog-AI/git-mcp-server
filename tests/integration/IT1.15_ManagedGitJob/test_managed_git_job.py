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

import time
from pathlib import Path
from uuid import uuid4

import httpx
from git import Repo

from tests.helpers import api_url


def _create_diff_repo(path: Path) -> Path:
    """Create a real repository with two commits so a managed diff is meaningful."""
    path.mkdir(parents=True, exist_ok=True)
    repo = Repo.init(path)
    repo.git.config("user.email", "test@example.com")
    repo.git.config("user.name", "Test User")

    readme = path / "README.md"
    readme.write_text("first\n", encoding="utf-8")
    repo.index.add(["README.md"])
    repo.index.commit("initial")
    if repo.active_branch.name != "main":
        repo.git.branch("-M", "main")

    readme.write_text("first\nsecond\n", encoding="utf-8")
    repo.index.add(["README.md"])
    repo.index.commit("second")
    return path


def _wait_for_job(base_url: str, api_key: str, job_id: str, timeout_seconds: float = 10.0) -> dict[str, object]:
    """Poll the managed-job status endpoint until a terminal state is reached."""
    deadline = time.time() + timeout_seconds
    while time.time() < deadline:
        response = httpx.get(api_url(base_url, f"/jobs/{job_id}"), headers={"x-api-key": api_key}, timeout=5.0)
        assert response.status_code == 200, response.text
        payload = response.json()["result"]
        if payload["status"] in {"succeeded", "failed", "cancelled", "timeout"}:
            return payload
        time.sleep(0.1)
    raise AssertionError(f"Timed out waiting for job {job_id}")


def test_managed_repo_open_and_diff_job(
    integration_server: dict[str, str | bool],
    api_key: str,
    tmp_path: Path,
) -> None:
    """Requirements: FR-01, FR-10, FR-14."""
    base_url = str(integration_server["base_url"])
    repo_path = _create_diff_repo(tmp_path / "jobs-diff-repo")

    open_job = httpx.post(
        api_url(base_url, "/jobs/repo-open"),
        headers={"x-api-key": api_key},
        json={
            "profile": f"managed-job-{uuid4().hex[:8]}",
            "repo_source": repo_path.as_posix(),
            "session_id": "managed-job-session",
        },
        timeout=10.0,
    )
    assert open_job.status_code == 200, open_job.text
    open_job_id = open_job.json()["result"]["job_id"]

    open_detail = _wait_for_job(base_url, api_key, open_job_id)
    assert open_detail["status"] == "succeeded"
    assert open_detail["server_id"]
    open_result = open_detail["result"]
    assert isinstance(open_result, dict)
    workspace_id = str(open_result["workspace_id"])

    diff_job = httpx.post(
        api_url(base_url, "/jobs/git-diff"),
        headers={"x-api-key": api_key},
        json={"workspace_id": workspace_id, "left": "HEAD~1", "right": "HEAD"},
        timeout=10.0,
    )
    assert diff_job.status_code == 200, diff_job.text
    diff_job_id = diff_job.json()["result"]["job_id"]

    diff_detail = _wait_for_job(base_url, api_key, diff_job_id)
    assert diff_detail["status"] == "succeeded"
    diff_result = diff_detail["result"]
    assert isinstance(diff_result, dict)
    assert "second" in diff_result["diff"]

    queue_status = httpx.get(api_url(base_url, "/jobs/queue/status"), headers={"x-api-key": api_key}, timeout=10.0)
    assert queue_status.status_code == 200, queue_status.text
    queue_payload = queue_status.json()["result"]
    assert queue_payload["server_id"]
    assert queue_payload["counts"]["succeeded"] >= 2

    close_result = httpx.post(
        api_url(base_url, "/tools/repo_close"),
        headers={"x-api-key": api_key},
        json={"workspace_id": workspace_id},
        timeout=10.0,
    )
    assert close_result.status_code == 200, close_result.text
