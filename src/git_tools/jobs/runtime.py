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

from copy import deepcopy
from threading import Lock, Thread
from typing import Any

from cloud_dog_jobs import (
    AdminService, FallbackAction, FallbackPolicy, FallbackPolicyManager,
    JobQueue, JobRequest, JobStatus, SQLQueueBackend, Worker,
)
from cloud_dog_jobs.maintenance.reaper import MaintenanceReaper
from cloud_dog_jobs.observability.audit import AuditEmitter
from cloud_dog_jobs.worker.context import JobContext
from cloud_dog_logging import get_audit_logger
from cloud_dog_logging.audit_schema import Actor, Target

from git_tools.tools.registry import ToolRegistry


class _PlatformAuditEmitter(AuditEmitter):
    """Bridge cloud_dog_jobs AuditEmitter to cloud_dog_logging audit logger."""

    def __init__(self) -> None:
        super().__init__()
        self._audit_logger = get_audit_logger()

    def emit(self, action: str, outcome: str, *, service: str = "git-mcp-server") -> dict:
        event = super().emit(action, outcome, service=service)
        actor = Actor(type="service", id=service)
        target = Target(type="queue", id="git-mcp")
        self._audit_logger.log_crud(actor=actor, action=action, target=target, outcome=outcome)
        return event


class JobsRuntime:
    """Managed-jobs facade for long-running git operations.

    Requirements: FR-01, FR-02, FR-14.
    """

    _FILE_BATCH_TOOLS = {
        "file_write",
        "file_upload",
        "file_move",
        "file_copy",
        "file_delete",
        "dir_mkdir",
        "dir_rmdir",
    }

    def __init__(
        self,
        tool_registry: ToolRegistry,
        *,
        server_id: str,
        queue_name: str,
        database_url: str,
        payload_max_bytes: int = 16384,
        run_timeout_seconds: float = 300.0,
        claim_timeout_seconds: int = 120,
        max_retries: int = 3,
        dead_letter_queue: str = "git_mcp_dead_letter",
    ) -> None:
        self._tool_registry = tool_registry
        self._server_id = server_id
        self._queue_name = queue_name
        self._max_retries = max_retries
        self._dead_letter_queue = dead_letter_queue
        self._backend = SQLQueueBackend(database_url)
        audit_emitter = _PlatformAuditEmitter()
        self._queue = JobQueue(self._backend, payload_max_bytes=payload_max_bytes, audit_emitter=audit_emitter)
        self._admin = AdminService(self._backend)
        self._fallback = FallbackPolicyManager(
            policies={
                jt: FallbackPolicy(action=FallbackAction.DEAD_LETTER, dead_letter_queue=dead_letter_queue)
                for jt in ("git.repo_open", "git.diff", "files.batch")
            },
        )
        self._worker = Worker(
            self._backend,
            host_id=server_id,
            worker_id="git-mcp-jobs",
            run_timeout_seconds=run_timeout_seconds,
            fallback_policies=self._fallback,
        )
        self._reaper = MaintenanceReaper(self._backend, claim_timeout_seconds=claim_timeout_seconds)
        self._audit_logger = get_audit_logger()
        self._dispatch_lock = Lock()
        self._state_lock = Lock()
        self._state: dict[str, dict[str, Any]] = {}
        self._register_handlers()

    def _register_handlers(self) -> None:
        """Register package worker handlers for service-specific jobs."""
        self._worker.register_handler("git.repo_open", self._handle_repo_access)
        self._worker.register_handler("git.diff", self._handle_git_diff)
        self._worker.register_handler("files.batch", self._handle_file_batch)

    # ------------------------------------------------------------------
    # PS-75 audit (JQ15)
    # ------------------------------------------------------------------

    def _emit_audit(
        self, action: str, outcome: str, *, job_id: str = "", details: dict[str, Any] | None = None,
    ) -> None:
        actor = Actor(type="service", id=self._server_id)
        target = Target(type="queue", id=str(job_id or self._queue_name))
        self._audit_logger.log_crud(
            actor=actor, action=action, target=target, outcome=outcome,
            **({"details": details} if details else {}),
        )

    # ------------------------------------------------------------------
    # Cancellation (JQ8.4)
    # ------------------------------------------------------------------

    def cancel_job(self, job_id: str) -> bool:
        """Cancel a queued or running job."""
        ok = self._queue.cancel(job_id)
        if ok:
            self._emit_audit("job.cancel", "success", job_id=job_id)
        return ok

    def is_cancelled(self, job_id: str) -> bool:
        """Check cooperative cancellation status."""
        job = self._backend.get(job_id)
        return job is not None and job.status == JobStatus.CANCELLED

    # ------------------------------------------------------------------
    # Retry / Resubmit (PS-76 JW4)
    # ------------------------------------------------------------------

    def retry_job(self, job_id: str) -> str | None:
        """Resubmit a failed/cancelled/dead-lettered job with same payload."""
        job = self._backend.get(job_id)
        if job is None:
            return None
        terminal = {JobStatus.FAILED, JobStatus.CANCELLED, JobStatus.DEAD_LETTERED}
        if hasattr(JobStatus, "TIMED_OUT"):
            terminal.add(JobStatus.TIMED_OUT)
        if job.status not in terminal:
            return None
        from cloud_dog_jobs.models import SubmitRequest
        request = SubmitRequest(
            queue_name=job.queue_name,
            job_type=job.job_type,
            payload=job.payload or {},
            priority=job.priority,
            correlation_id=getattr(job, "correlation_id", None) or "",
            user_id=getattr(job, "user_id", None) or "",
        )
        new_id = self._queue.submit(request)
        self._emit_audit("job.retry", "success", job_id=new_id, details={"original_job_id": job_id})
        return new_id

    # ------------------------------------------------------------------
    # Delete (PS-76 JW4)
    # ------------------------------------------------------------------

    def delete_job(self, job_id: str) -> bool:
        """Delete a terminal job from the backend."""
        job = self._backend.get(job_id)
        if job is None:
            return False
        terminal = {JobStatus.SUCCEEDED, JobStatus.FAILED, JobStatus.CANCELLED, JobStatus.DEAD_LETTERED}
        for attr in ("TIMED_OUT", "TTL_EXPIRED", "ARCHIVED", "COMPLETED"):
            if hasattr(JobStatus, attr):
                terminal.add(getattr(JobStatus, attr))
        if job.status not in terminal:
            return False
        if hasattr(self._backend, "delete"):
            self._backend.delete(job_id)
        elif hasattr(self._backend, "remove"):
            self._backend.remove(job_id)
        else:
            return False
        self._emit_audit("job.delete", "success", job_id=job_id)
        return True

    # ------------------------------------------------------------------
    # Maintenance (JQ9)
    # ------------------------------------------------------------------

    def recover_stale_jobs(self) -> dict[str, int]:
        """Run reaper sweep for stuck/TTL-expired jobs."""
        return self._reaper.run_sweep()

    def _store_state(self, job_id: str, **payload: Any) -> None:
        """Merge result/progress/error state for a job."""
        with self._state_lock:
            current = self._state.setdefault(job_id, {})
            current.update(payload)

    def _set_progress(
        self,
        ctx: JobContext,
        percentage: float,
        *,
        stage: str,
        counters: dict[str, int] | None = None,
        current_item: str | None = None,
    ) -> None:
        """Persist a progress snapshot for status polling."""
        progress = ctx.update_progress(
            percentage=percentage,
            stage=stage,
            counters=counters,
            current_item=current_item,
        )
        self._store_state(ctx.job.job_id, progress=progress)

    def _tool_call(self, tool_name: str, payload: dict[str, Any]) -> dict[str, Any]:
        """Dispatch a tool call through the shared service registry."""
        return self._tool_registry.call(tool_name, payload)

    def _handle_repo_access(self, ctx: JobContext) -> dict[str, Any]:
        """Execute a queued repository-open operation.

        Requirements: FR-01, FR-10.
        """
        self._set_progress(ctx, 10.0, stage="queue.dispatch")
        result = self._tool_call("repo_open", deepcopy(ctx.job.payload))
        self._set_progress(ctx, 100.0, stage="completed")
        self._store_state(ctx.job.job_id, result=result, error=None)
        return result

    def _handle_git_diff(self, ctx: JobContext) -> dict[str, Any]:
        """Execute a queued git diff operation.

        Requirements: FR-01, FR-10.
        """
        self._set_progress(ctx, 10.0, stage="queue.dispatch")
        result = self._tool_call("git_diff", deepcopy(ctx.job.payload))
        self._set_progress(ctx, 100.0, stage="completed")
        self._store_state(ctx.job.job_id, result=result, error=None)
        return result

    def _handle_file_batch(self, ctx: JobContext) -> dict[str, Any]:
        """Execute a queued batch of file operations.

        Requirements: FR-01, FR-08.
        """
        payload = deepcopy(ctx.job.payload)
        operations = payload.get("operations", [])
        if not isinstance(operations, list) or not operations:
            raise ValueError("files.batch job requires a non-empty operations list")

        results: list[dict[str, Any]] = []
        total = len(operations)
        for index, item in enumerate(operations, start=1):
            if not isinstance(item, dict):
                raise ValueError("Each batch operation must be an object")
            tool_name = str(item.get("tool_name", "")).strip()
            if tool_name not in self._FILE_BATCH_TOOLS:
                raise PermissionError(f"Unsupported batch file tool: {tool_name}")
            raw_payload = item.get("payload", {})
            if not isinstance(raw_payload, dict):
                raise ValueError(f"Batch payload for {tool_name} must be an object")
            self._set_progress(
                ctx,
                percentage=(100.0 * (index - 1)) / total,
                stage="batch.execute",
                counters={"completed": index - 1, "total": total},
                current_item=tool_name,
            )
            results.append({"tool_name": tool_name, "result": self._tool_call(tool_name, deepcopy(raw_payload))})

        summary = {"items": results, "count": len(results)}
        self._set_progress(
            ctx,
            100.0,
            stage="completed",
            counters={"completed": total, "total": total},
        )
        self._store_state(ctx.job.job_id, result=summary, error=None)
        return summary

    def _dispatch(self) -> None:
        """Kick the background worker to drain queued jobs."""

        def _runner() -> None:
            with self._dispatch_lock:
                while True:
                    try:
                        processed = self._worker.run_once()
                    except Exception as exc:  # noqa: BLE001
                        processed = True
                        failed_job_id = self._current_failed_job_id()
                        if failed_job_id:
                            self._store_state(failed_job_id, error=str(exc))
                            self._emit_audit(
                                "job.transition", "failure", job_id=failed_job_id,
                                details={"to_state": "failed", "error": str(exc)[:200]},
                            )
                    if not processed:
                        return

        Thread(target=_runner, name="git-mcp-jobs-dispatch", daemon=True).start()

    def _current_failed_job_id(self) -> str:
        """Return the most recently updated failed/running job when worker raises."""
        jobs = self._backend.all_jobs()
        if not jobs:
            return ""
        job = sorted(jobs, key=lambda item: item.updated_at, reverse=True)[0]
        return job.job_id

    def _submit(self, job_type: str, payload: dict[str, Any], **metadata: Any) -> str:
        """Submit a job to the configured backend and trigger dispatch."""
        request = JobRequest(
            job_type=job_type,
            queue_name=self._queue_name,
            payload=payload,
            priority=int(metadata.get("priority", 0)),
            app_id="git-mcp-server",
            correlation_id=metadata.get("correlation_id"),
            user_id=metadata.get("user_id"),
            session_id=metadata.get("session_id"),
            request_source=metadata.get("request_source"),
            request_ip=metadata.get("request_ip"),
            request_auth_method=metadata.get("request_auth_method"),
            request_auth_identity=metadata.get("request_auth_identity"),
            request_user_agent=metadata.get("request_user_agent"),
        )
        job_id = self._queue.submit(request)
        self._store_state(job_id, result=None, error=None, progress=None)
        self._emit_audit("job.submit", "success", job_id=job_id, details={"job_type": job_type})
        self._dispatch()
        return job_id

    def queue_repo_access(self, payload: dict[str, Any], **metadata: Any) -> str:
        """Submit a managed repo-open job."""
        return self._submit("git.repo_open", payload, **metadata)

    def submit_git_diff(self, payload: dict[str, Any], **metadata: Any) -> str:
        """Submit a managed git-diff job."""
        return self._submit("git.diff", payload, **metadata)

    def submit_file_batch(self, payload: dict[str, Any], **metadata: Any) -> str:
        """Submit a managed batch-file job."""
        return self._submit("files.batch", payload, **metadata)

    def queue_status(self) -> dict[str, Any]:
        """Return queue-level status data for the job status endpoint."""
        return {
            "server_id": self._server_id,
            "backend": "cloud_dog_jobs",
            "queue_name": self._queue_name,
            "health": self._queue.health(),
            "counts": self._admin.queue_status(),
        }

    def get_job_detail(self, job_id: str) -> dict[str, Any] | None:
        """Return a status view enriched with result, error, and progress."""
        job = self._admin.get_job(job_id)
        if job is None:
            return None
        with self._state_lock:
            state = deepcopy(self._state.get(job_id, {}))
        return {
            "job_id": job.job_id,
            "job_type": job.job_type,
            "queue_name": job.queue_name,
            "status": job.status.value,
            "priority": job.priority,
            "server_id": self._server_id,
            "claimed_by": job.claimed_by,
            "created_at": job.created_at.isoformat(),
            "updated_at": job.updated_at.isoformat(),
            "correlation_id": job.correlation_id,
            "user_id": job.user_id,
            "request_source": job.request_source,
            "request_auth_method": job.request_auth_method,
            "request_auth_identity": job.request_auth_identity,
            "progress": state.get("progress"),
            "result": state.get("result"),
            "error": state.get("error"),
        }

    def list_job_details(self, limit: int = 100) -> list[dict[str, Any]]:
        """Return enriched job status rows for recent jobs."""
        items: list[dict[str, Any]] = []
        jobs = sorted(self._backend.all_jobs(), key=lambda item: item.updated_at, reverse=True)[:limit]
        for job in jobs:
            detail = self.get_job_detail(job.job_id)
            if detail is not None:
                items.append(detail)
        return items
