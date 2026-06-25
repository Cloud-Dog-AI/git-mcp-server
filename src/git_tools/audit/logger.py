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

import json
from typing import Any

from cloud_dog_logging import get_audit_logger, setup_logging
from cloud_dog_logging.audit_schema import Actor, AuditEvent, Target
from cloud_dog_logging.correlation import set_environment, set_service_instance, set_service_name
from cloud_dog_storage import path_utils

from git_tools.audit.events import AuditActor, AuditRecord


class AuditWriter:
    """Persist audit events to JSONL via cloud_dog_logging."""

    def __init__(
        self,
        audit_path: str | None = None,
        service_name: str = "git-mcp-server",
        *,
        service_instance: str = "git-mcp-local",
        environment: str = "dev",
        configure_logging: bool = True,
    ) -> None:
        self._service_name = service_name
        self._service_instance = service_instance
        self._environment = environment
        self._jsonl_path = path_utils.as_path(audit_path).resolve() if audit_path else None
        # In reuse mode the cloud_dog_logging sink is fragile (and writes to a different file),
        # so we ALSO write directly; in configure_logging mode the setup_logging sink owns the
        # file, so the direct write would double-write — hence guarded by _reuse_mode.
        self._reuse_mode = not configure_logging
        # GM3 (W28C-1705): when the host app already configured logging (and its audit sink),
        # reuse it via get_audit_logger() rather than re-running setup_logging — which would
        # clobber the app's console/request logging. The api/mcp/a2a surfaces construct with
        # configure_logging=False so per-tool-call audit events land in the app's audit sink.
        if configure_logging:
            if not audit_path:
                raise ValueError("audit_path is required when configure_logging=True")
            path = path_utils.as_path(audit_path).resolve()
            path.parent.mkdir(parents=True, exist_ok=True)
            setup_logging(
                {
                    "service_name": service_name,
                    "service_instance": service_instance,
                    "environment": environment,
                    "log": {
                        "format": "json",
                        "console": False,
                        "audit_log": str(path),
                        "integrity": {"enabled": False},
                    },
                }
            )

    def _bind_context(self) -> None:
        set_service_name(self._service_name)
        set_service_instance(self._service_instance)
        set_environment(self._environment)

    def emit(self, record: AuditRecord) -> None:
        """Emit a typed audit event.

        Re-fetch ``get_audit_logger()`` at emit time rather than caching it at construction:
        under uvicorn the process reconfigures logging AFTER the app (and this writer) are
        built, so a logger captured at construction has stale handlers and silently drops
        events (GM3 / W28C-1705). AuditMiddleware works for the same reason — it re-fetches.
        """
        # Robust primary sink FIRST: append the record directly as a JSON line. This must run
        # BEFORE the AuditEvent construction / cloud_dog_logging emit, which RAISE in uvicorn's
        # live request context (an 'exc_info' LogRecord collision from request-logging) — if we
        # built the event first and it raised, the direct write would be skipped entirely.
        if self._reuse_mode:
            self._append_jsonl(record)
        # Best-effort secondary: also feed the cloud_dog_logging audit_schema sink + integrity.
        try:
            self._bind_context()
            event = AuditEvent(
                event_type=f"git_mcp.{record.operation}",
                actor=Actor(
                    type=record.actor.actor_type,
                    id=record.actor.actor_id,
                    roles=record.actor.roles,
                ),
                action=record.operation,
                outcome=record.status,
                correlation_id=record.correlation_id,
                service=self._service_name,
                service_instance=self._service_instance,
                environment=self._environment,
                target=Target(type="git_operation", id=record.operation, name=record.operation),
                details={
                    "profile": record.profile,
                    "workspace_id": record.workspace_id,
                    "resolved_ref": record.resolved_ref,
                    "params": record.redacted_params(),
                    "warnings": record.warnings,
                    "errors": record.errors,
                },
                timestamp=record.timestamp,
            )
            get_audit_logger().emit(event)
        except Exception:  # noqa: BLE001 — the logging sink must never break audit persistence
            pass

    def _append_jsonl(self, record: AuditRecord) -> None:
        """Append the audit record directly to the JSONL audit sink (robust path)."""
        if self._jsonl_path is None:
            return
        payload = {
            "timestamp": record.timestamp,
            "event_type": f"git_mcp.{record.operation}",
            "action": record.operation,
            "outcome": record.status,
            "actor": {
                "type": record.actor.actor_type,
                "id": record.actor.actor_id,
                "roles": list(record.actor.roles),
            },
            "correlation_id": record.correlation_id,
            "service": self._service_name,
            "service_instance": self._service_instance,
            "environment": self._environment,
            "target": {"type": "git_operation", "id": record.operation, "name": record.operation},
            "details": {
                "profile": record.profile,
                "workspace_id": record.workspace_id,
                "resolved_ref": record.resolved_ref,
                "params": record.redacted_params(),
                "warnings": list(record.warnings),
                "errors": list(record.errors),
            },
        }
        try:
            self._jsonl_path.parent.mkdir(parents=True, exist_ok=True)
            with self._jsonl_path.open("a", encoding="utf-8") as handle:
                handle.write(json.dumps(payload, default=str) + "\n")
        except OSError:
            pass

    def close(self) -> None:
        """Flush and close the underlying audit sink."""
        logger = get_audit_logger()
        flush = getattr(logger, "flush", None)
        if callable(flush):
            flush()
        close = getattr(logger, "close", None)
        if callable(close):
            close()


def tool_audit_jsonl_path(base_dir: str) -> str:
    """Return an app-writable per-tool-call audit JSONL path beside the data volume (GM3).

    The configured ``storage.audit`` dir is root-owned in the deployment (a non-root container cannot
    write it), whereas the data dir — where the DB and workspaces live — IS app-writable. Place
    the per-tool-call audit JSONL there so events are reliably persisted.
    """
    return str(path_utils.as_path(base_dir).resolve().parent / "git-mcp-tool-audit.jsonl")


def build_audit_record(
    operation: str,
    status: str,
    correlation_id: str,
    actor_id: str,
    params: dict[str, Any] | None = None,
) -> AuditRecord:
    """Create an audit record with common defaults."""
    return AuditRecord(
        operation=operation,
        status=status,
        correlation_id=correlation_id,
        actor=AuditActor(actor_id=actor_id),
        params=params or {},
    )
