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
        audit_path: str,
        service_name: str = "git-mcp-server",
        *,
        service_instance: str = "git-mcp-local",
        environment: str = "dev",
    ) -> None:
        path = path_utils.as_path(audit_path).resolve()
        path.parent.mkdir(parents=True, exist_ok=True)
        self._service_instance = service_instance
        self._environment = environment
        setup_logging(
            {
                "service_name": service_name,
                "service_instance": service_instance,
                "environment": environment,
                "log": {
                    "format": "json",
                    "console": False,
                    "audit_log": str(path),
                },
            }
        )
        self._logger = get_audit_logger()
        self._service_name = service_name

    def _bind_context(self) -> None:
        set_service_name(self._service_name)
        set_service_instance(self._service_instance)
        set_environment(self._environment)

    def emit(self, record: AuditRecord) -> None:
        """Emit a typed audit event."""
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
        self._logger.emit(event)

    def close(self) -> None:
        """Flush and close the underlying audit sink."""
        flush = getattr(self._logger, "flush", None)
        if callable(flush):
            flush()
        close = getattr(self._logger, "close", None)
        if callable(close):
            close()


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
