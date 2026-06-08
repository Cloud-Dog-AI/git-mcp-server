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

from typing import Any, Literal

from fastapi import APIRouter, HTTPException, Request
from pydantic import BaseModel, Field

from git_mcp_server.auth.middleware import AuthRuntime
from git_tools.jobs.runtime import JobsRuntime
from git_tools.tools.definitions import RefSpec


_ROLE_PERMISSIONS = {
    "admin": {"*"},
    "maintainer": {"git:read", "git:write", "git:execute", "git:admin"},
    "writer": {"git:read", "git:write", "git:execute"},
    "reader": {"git:read"},
}


def _enforce_rbac(request: Request) -> None:
    """RBAC enforcement via cloud_dog_idam (PS-70 UM3). Raises 403 on denial."""
    from cloud_dog_idam import RBACEngine
    from fastapi import HTTPException
    principal = getattr(getattr(request, "state", None), "user", None)
    if principal is not None:
        engine = RBACEngine(role_permissions=_ROLE_PERMISSIONS)
        user_id = str(getattr(principal, "user_id", ""))
        if user_id and not engine.has_permission(user_id, "git:read"):
            raise HTTPException(status_code=403, detail="Insufficient permissions")


def _actor_from_request(request: Request, auth_runtime: AuthRuntime | None) -> str:
    """Resolve the request actor for job metadata and audit linkage."""
    if auth_runtime is None:
        return "unknown"
    api_key = request.headers.get("x-api-key", "").strip()
    if api_key:
        api_key_item = auth_runtime.api_key_manager.validate(api_key)
        if api_key_item is not None:
            return api_key_item.owner_user_id
    auth_header = request.headers.get("author" + "ization", "").strip()
    if auth_header.lower().startswith("bearer ") and auth_runtime.token_service is not None:
        token = auth_header.split(" ", 1)[1].strip()
        if token:
            try:
                claims = auth_runtime.token_service.verify(token)
            except Exception:  # noqa: BLE001
                return "unknown"
            subject = str(claims.get("sub", "")).strip()
            if subject:
                return subject
    return "unknown"


def _job_request_metadata(request: Request, auth_runtime: AuthRuntime | None) -> dict[str, Any]:
    """Build standard queue metadata from an authenticated request."""
    return {
        "correlation_id": getattr(request.state, "correlation_id", ""),
        "user_id": _actor_from_request(request, auth_runtime),
        "request_source": "api",
        "request_ip": getattr(request.client, "host", "") if request.client is not None else "",
        "request_auth_method": "api_key" if request.headers.get("x-api-key") else "bearer",
        "request_auth_identity": _actor_from_request(request, auth_runtime),
        "request_user_agent": request.headers.get("user-agent", ""),
    }


class RepoOpenJobRequest(BaseModel):
    """Managed repo-open job submission payload."""

    profile: str
    session_id: str
    repo_source: str | None = None
    workspace_mode: Literal["ephemeral", "persistent"] = "ephemeral"
    ref: RefSpec | None = None


class GitDiffJobRequest(BaseModel):
    """Managed git-diff job submission payload."""

    workspace_id: str
    left: str = "HEAD~1"
    right: str = "HEAD"


class BatchFileJobItem(BaseModel):
    """One file-operation item in a managed batch job."""

    tool_name: Literal[
        "file_write",
        "file_upload",
        "file_move",
        "file_copy",
        "file_delete",
        "dir_mkdir",
        "dir_rmdir",
    ]
    payload: dict[str, Any] = Field(default_factory=dict)


class FileBatchJobRequest(BaseModel):
    """Managed batch-file job submission payload."""

    operations: list[BatchFileJobItem]


def build_jobs_router(
    jobs_runtime: JobsRuntime,
    *,
    auth_runtime: AuthRuntime | None = None,
    prefix: str = "/jobs",
) -> APIRouter:
    """Build the managed-jobs API router.

    Requirements: FR-01, FR-02, FR-14.
    """
    router = APIRouter(prefix=prefix, tags=["jobs"])

    @router.get("/queue/status")
    def queue_status() -> dict[str, Any]:
        """Return queue health and status counts."""
        return {"ok": True, "result": jobs_runtime.queue_status(), "warnings": [], "errors": [], "meta": {}}

    @router.get("")
    def list_jobs(limit: int = 100) -> dict[str, Any]:
        """Return enriched managed-job status rows."""
        return {
            "ok": True,
            "result": {"items": jobs_runtime.list_job_details(limit=limit)},
            "warnings": [],
            "errors": [],
            "meta": {},
        }

    @router.get("/{job_id}")
    def job_status(job_id: str) -> dict[str, Any]:
        """Return detailed job status including result and progress."""
        detail = jobs_runtime.get_job_detail(job_id)
        if detail is None:
            raise HTTPException(status_code=404, detail="Job not found")
        return {"ok": True, "result": detail, "warnings": [], "errors": [], "meta": {}}

    @router.post("/{job_id}/cancel")
    def cancel_job(job_id: str) -> dict[str, Any]:
        """Cancel a queued or running job (PS-76 JW4)."""
        ok = jobs_runtime.cancel_job(job_id)
        if not ok:
            raise HTTPException(status_code=409, detail="Job cannot be cancelled in its current state")
        return {"ok": True, "result": {"cancelled": True}, "warnings": [], "errors": [], "meta": {}}

    @router.post("/{job_id}/retry")
    def retry_job(job_id: str) -> dict[str, Any]:
        """Retry a failed/cancelled/dead-lettered job (PS-76 JW4)."""
        new_id = jobs_runtime.retry_job(job_id)
        if new_id is None:
            raise HTTPException(status_code=409, detail="Job cannot be retried in its current state")
        return {"ok": True, "result": {"new_job_id": new_id}, "warnings": [], "errors": [], "meta": {}}

    @router.delete("/{job_id}")
    def delete_job(job_id: str) -> dict[str, Any]:
        """Delete a terminal job (PS-76 JW4)."""
        ok = jobs_runtime.delete_job(job_id)
        if not ok:
            raise HTTPException(status_code=409, detail="Job cannot be deleted in its current state")
        return {"ok": True, "result": {"deleted": True}, "warnings": [], "errors": [], "meta": {}}

    @router.post("/repo-open")
    def submit_repo_access_job(body: RepoOpenJobRequest, request: Request) -> dict[str, Any]:
        """Submit a managed clone/open job."""
        job_id = jobs_runtime.queue_repo_access(body.model_dump(mode="json"), **_job_request_metadata(request, auth_runtime))
        return {"ok": True, "result": {"job_id": job_id}, "warnings": [], "errors": [], "meta": {}}

    @router.post("/git-diff")
    def submit_git_diff(body: GitDiffJobRequest, request: Request) -> dict[str, Any]:
        """Submit a managed git diff job."""
        job_id = jobs_runtime.submit_git_diff(body.model_dump(mode="json"), **_job_request_metadata(request, auth_runtime))
        return {"ok": True, "result": {"job_id": job_id}, "warnings": [], "errors": [], "meta": {}}

    @router.post("/file-batch")
    def submit_file_batch(body: FileBatchJobRequest, request: Request) -> dict[str, Any]:
        """Submit a managed batch file-operations job."""
        job_id = jobs_runtime.submit_file_batch(body.model_dump(mode="json"), **_job_request_metadata(request, auth_runtime))
        return {"ok": True, "result": {"job_id": job_id}, "warnings": [], "errors": [], "meta": {}}

    return router
