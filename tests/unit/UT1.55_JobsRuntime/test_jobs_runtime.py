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

from git_tools.jobs.runtime import JobsRuntime
from git_tools.tools.registry import ToolRegistry
from git_tools.workspaces.manager import WorkspaceManager
from tests.helpers import create_repo


def _wait_for_terminal_job(jobs_runtime: JobsRuntime, job_id: str, timeout_seconds: float = 5.0) -> dict[str, object]:
    """Poll job status until a terminal state is reached."""
    deadline = time.time() + timeout_seconds
    while time.time() < deadline:
        detail = jobs_runtime.get_job_detail(job_id)
        if detail is not None and detail["status"] in {"succeeded", "failed", "cancelled", "timeout"}:
            return detail
        time.sleep(0.05)
    raise AssertionError(f"Timed out waiting for job {job_id}")


def test_jobs_runtime_repo_open_job_lifecycle(tmp_path: Path) -> None:
    """Requirements: FR-01, FR-10, FR-14."""
    repo_path = tmp_path / "source-repo"
    repo = create_repo(repo_path)

    workspace_manager = WorkspaceManager(tmp_path / "workspaces")
    tool_registry = ToolRegistry(workspace_manager)
    jobs_runtime = JobsRuntime(
        tool_registry,
        server_id="unit-server-1",
        queue_name="unit-jobs",
        database_url=f"sqlite:///{tmp_path / 'jobs-runtime-1.db'}",
        run_timeout_seconds=10.0,
    )

    job_id = jobs_runtime.queue_repo_access(
        {
            "profile": "unit-job-profile",
            "repo_source": repo_path.as_posix(),
            "session_id": "job-session",
        },
        correlation_id="corr-unit-1",
        user_id="unit-user",
        request_source="unit",
    )

    detail = _wait_for_terminal_job(jobs_runtime, job_id)
    assert detail["status"] == "succeeded"
    assert detail["server_id"] == "unit-server-1"
    result = detail["result"]
    assert isinstance(result, dict)
    workspace_id = str(result["workspace_id"])
    assert result["resolved_ref"]["type"] == "branch"
    assert result["resolved_ref"]["name"] == repo.active_branch.name
    assert jobs_runtime.queue_status()["counts"]["succeeded"] >= 1

    close_result = tool_registry.call("repo_close", {"workspace_id": workspace_id})
    assert close_result["closed"] is True


def test_jobs_runtime_file_batch_job_records_result(tmp_path: Path) -> None:
    """Requirements: FR-01, FR-08, FR-14."""
    repo_path = tmp_path / "batch-repo"
    create_repo(repo_path)

    workspace_manager = WorkspaceManager(tmp_path / "workspaces")
    tool_registry = ToolRegistry(workspace_manager)
    opened = tool_registry.call(
        "repo_open",
        {
            "profile": "unit-batch-profile",
            "repo_source": repo_path.as_posix(),
            "session_id": "batch-session",
        },
    )
    workspace_id = str(opened["workspace_id"])

    jobs_runtime = JobsRuntime(
        tool_registry,
        server_id="unit-server-2",
        queue_name="unit-jobs",
        database_url=f"sqlite:///{tmp_path / 'jobs-runtime-2.db'}",
        run_timeout_seconds=10.0,
    )
    job_id = jobs_runtime.submit_file_batch(
        {
            "operations": [
                {"tool_name": "dir_mkdir", "payload": {"workspace_id": workspace_id, "path": "notes", "parents": True}},
                {
                    "tool_name": "file_write",
                    "payload": {
                        "workspace_id": workspace_id,
                        "path": "notes/todo.txt",
                        "content": "queued write\n",
                        "overwrite": False,
                    },
                },
            ]
        },
        correlation_id="corr-unit-2",
        user_id="unit-user",
        request_source="unit",
    )

    detail = _wait_for_terminal_job(jobs_runtime, job_id)
    assert detail["status"] == "succeeded"
    result = detail["result"]
    assert isinstance(result, dict)
    assert result["count"] == 2
    assert (Path(opened["path"]) / "notes" / "todo.txt").read_text(encoding="utf-8") == "queued write\n"

    close_result = tool_registry.call("repo_close", {"workspace_id": workspace_id})
    assert close_result["closed"] is True


def test_jobs_runtime_git_diff_job_uses_internal_diff(tmp_path: Path) -> None:
    """Requirements: FR-01, FR-10, FR-14."""
    repo_path = tmp_path / "diff-repo"
    repo = create_repo(repo_path)
    readme = repo_path / "README.md"
    readme.write_text("hello\nsecond\n", encoding="utf-8")
    repo.index.add(["README.md"])
    repo.index.commit("second")

    workspace_manager = WorkspaceManager(tmp_path / "workspaces")
    tool_registry = ToolRegistry(workspace_manager)
    jobs_runtime = JobsRuntime(
        tool_registry,
        server_id="unit-server-3",
        queue_name="unit-jobs",
        database_url=f"sqlite:///{tmp_path / 'jobs-runtime-3.db'}",
        run_timeout_seconds=10.0,
    )

    open_job_id = jobs_runtime.queue_repo_access(
        {
            "profile": "unit-diff-profile",
            "repo_source": repo_path.as_posix(),
            "session_id": "diff-session",
        }
    )
    open_detail = _wait_for_terminal_job(jobs_runtime, open_job_id)
    assert open_detail["status"] == "succeeded"
    workspace_id = str(open_detail["result"]["workspace_id"])

    diff_job_id = jobs_runtime.submit_git_diff({"workspace_id": workspace_id, "left": "HEAD~1", "right": "HEAD"})
    diff_detail = _wait_for_terminal_job(jobs_runtime, diff_job_id)
    assert diff_detail["status"] == "succeeded"
    assert "second" in str(diff_detail["result"]["diff"])

    close_result = tool_registry.call("repo_close", {"workspace_id": workspace_id})
    assert close_result["closed"] is True
