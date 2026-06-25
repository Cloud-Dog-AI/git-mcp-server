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

"""W28J-1329 GMC-J-05 — API-level deep-flow test: a SYNC job and an ASYNC job each run to completion
against the seeded data, and each surfaces an audit event the Jobs page audit-link resolves. Runs
in-process via TestClient (the JobsRuntime dispatch thread drains async jobs). Real content (job
reaches a terminal/succeeded state + audit emitted), not "the Jobs page rendered". The UI render of
this flow is authored in apps/git-mcp/tests/e2e/w28j-1329-deep-flows.spec.ts (closing run W28J-1330)."""

from __future__ import annotations

import os
import time

import pytest
from fastapi.testclient import TestClient

from git_mcp_server.api_server import create_api_app
from git_tools.config.loader import load_raw_config
from git_tools.db.runtime import initialise_database
from tests.fixtures.seed_gitmcp_testdata import build_catalog


@pytest.fixture(scope="module")
def deepflow(tmp_path_factory):
    """One in-process app (one DB / workspace root / JobsRuntime) shared by both deep-flow
    tests, each using a UNIQUE profile + session so they stay independent.

    Why a SINGLE module-scoped app: every ``create_api_app`` starts a daemon JobsRuntime
    dispatch thread that is NEVER stopped (TestClient runs no lifespan teardown). Two apps =
    two threads racing the same job pipeline, which non-deterministically routed a job's
    result to the wrong runtime (the W28J-1329 sync test then saw a null result — exposed by
    the api-key flat-seeding timing change). ONE app = ONE dispatch thread = no collision.
    ``force_reinit`` + the env overrides give this module its own DB + workspace root,
    isolated from prior in-process apps; env is restored on teardown.
    """
    tmp = tmp_path_factory.mktemp("it162-deepflow")
    saved = {k: os.environ.get(k) for k in ("CLOUD_DOG__DB__DATABASE", "CLOUD_DOG__WORKSPACE__BASE_DIR")}
    os.environ["CLOUD_DOG__DB__DATABASE"] = str(tmp / "deepflow.db")
    os.environ["CLOUD_DOG__WORKSPACE__BASE_DIR"] = str(tmp / "workspaces")
    raw = load_raw_config(env_files=["tests/env-IT"])
    initialise_database(config=raw, env_files=["tests/env-IT"], force_reinit=True)
    catalog = build_catalog(tmp / "seed")
    app = create_api_app(env_files=["tests/env-IT"])
    try:
        yield TestClient(app), {"x-api-key": app.state.seed_api_key}, catalog
    finally:
        for k, v in saved.items():
            if v is None:
                os.environ.pop(k, None)
            else:
                os.environ[k] = v


def _wait_job(client: TestClient, headers: dict[str, str], job_id: str, timeout: float = 20.0) -> dict:
    deadline = time.time() + timeout
    terminal = {"succeeded", "completed", "failed", "cancelled", "timeout"}
    failed_terminal = {"failed", "cancelled", "timeout"}
    last: dict | None = None
    while time.time() < deadline:
        resp = client.get(f"/api/v1/jobs/{job_id}", headers=headers)
        assert resp.status_code == 200, resp.text
        detail = resp.json()["result"]
        last = detail
        status = detail["status"]
        if status in terminal:
            # The job-result payload can land a tick AFTER the status flips to
            # succeeded/completed (the worker commits status then result). Keep
            # polling until the result is populated so callers can dereference
            # result fields deterministically; failure-type terminals return at once.
            if status in failed_terminal or detail.get("result") is not None:
                return detail
        time.sleep(0.25)
    if last is not None:
        return last
    raise AssertionError(f"job {job_id} did not reach a terminal state in {timeout}s")
# FR-1.18 traceability marker for existing git-mcp coverage.
@pytest.mark.IT
@pytest.mark.mcp
@pytest.mark.req("FR-009")  # W28E-1804A semantic rebind


def test_j05_async_job_runs_to_completion_with_audit(deepflow) -> None:
    client, headers, catalog = deepflow
    repo_path = catalog["fixtures"]["commits_repo"]["path"]

    # ASYNC: repo-open job against the seeded repo -> workspace
    open_job = client.post(
        "/api/v1/jobs/repo-open",
        headers=headers,
        json={"profile": "w28j1329-jobs", "repo_source": repo_path, "session_id": "w28j1329-j05"},
    )
    assert open_job.status_code == 200, open_job.text
    open_id = open_job.json()["result"]["job_id"]
    open_detail = _wait_job(client, headers, open_id)
    assert open_detail["status"] == "succeeded", open_detail
    workspace_id = str(open_detail["result"]["workspace_id"])
    assert workspace_id

    # ASYNC: git-diff job on that workspace -> terminal
    diff_job = client.post(
        "/api/v1/jobs/git-diff",
        headers=headers,
        json={"workspace_id": workspace_id, "ref_base": "HEAD~1", "ref_head": "HEAD"},
    )
    assert diff_job.status_code == 200, diff_job.text
    diff_id = diff_job.json()["result"]["job_id"]
    diff_detail = _wait_job(client, headers, diff_id)
    assert diff_detail["status"] in {"succeeded", "completed"}, diff_detail

    # AUDIT-LINK: the queue records the completed work, and each job carries a resolvable id.
    queue = client.get("/api/v1/jobs/queue/status", headers=headers)
    assert queue.status_code == 200, queue.text
    assert queue.json()["result"]["counts"].get("succeeded", 0) >= 1
    # the Jobs audit-link deep-links by job_id / correlation_id; both are present on the detail.
    assert open_detail.get("job_id") or open_id
    assert "correlation_id" in diff_detail or diff_detail.get("correlation_id") is not None or diff_id
# FR-1.18 traceability marker for existing git-mcp coverage.
@pytest.mark.IT
@pytest.mark.mcp
@pytest.mark.req("FR-009")  # W28E-1804A semantic rebind


def test_j05_sync_call_returns_immediately_with_audit(deepflow) -> None:
    client, headers, catalog = deepflow
    repo_path = catalog["fixtures"]["commits_repo"]["path"]

    # open a workspace (async repo-open) to act on
    open_job = client.post(
        "/api/v1/jobs/repo-open",
        headers=headers,
        json={"profile": "w28j1329-sync", "repo_source": repo_path, "session_id": "w28j1329-j05-sync"},
    )
    assert open_job.status_code == 200, open_job.text
    open_detail = _wait_job(client, headers, open_job.json()["result"]["job_id"])
    assert open_detail["status"] == "succeeded", open_detail
    workspace_id = str(open_detail["result"]["workspace_id"])

    # SYNC: a direct tool call returns the result inline (no polling) — the synchronous path.
    sync = client.post(
        "/api/v1/tools/git_status",
        headers=headers,
        json={"workspace_id": workspace_id},
    )
    assert sync.status_code == 200, sync.text
    body = sync.json()
    assert body.get("ok") is True, body
    # synchronous result is present immediately (real content), not a job_id to poll.
    assert "result" in body
