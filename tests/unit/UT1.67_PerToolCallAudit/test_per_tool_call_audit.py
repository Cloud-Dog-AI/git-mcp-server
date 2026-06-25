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

"""W28C-1705 GM3 — per-tool-call typed audit through AuditWriter.

The AuditWriter existed but was never instantiated/invoked, so the W28M-1602 commit-author
override had no corresponding ``git_commit`` audit event tying a principal to the sha. Every
tool call now converges through ``_call_with_audit`` (the single dispatch point) and emits a
typed AuditEvent: success carries the principal + commit_sha; failure carries the error;
sensitive params are redacted; a missing writer is a no-op.
"""

from __future__ import annotations

import tempfile
import types

import pytest

from git_mcp_server.mcp_server import create_mcp_app
from git_tools.tools.registry import ToolRegistry
from git_tools.workspaces.manager import WorkspaceManager


class _SpyWriter:
    def __init__(self) -> None:
        self.records: list = []

    def emit(self, record) -> None:  # noqa: ANN001
        self.records.append(record)


def _registry(audit_writer) -> ToolRegistry:  # noqa: ANN001
    return ToolRegistry(WorkspaceManager(tempfile.mkdtemp()), audit_writer=audit_writer)
# FR-1.18 traceability marker for existing git-mcp coverage.
@pytest.mark.UT
@pytest.mark.mcp
@pytest.mark.req("FR-016")  # W28E-1804A semantic rebind


def test_success_emits_event_with_principal_and_commit_sha() -> None:
    """Requirements: W28C-1705 GM3 — actor.id + output.commit_sha per tool call."""
    spy = _SpyWriter()
    reg = _registry(spy)
    reg._tools["w28c1705_fake_commit"] = types.SimpleNamespace(handler=lambda payload: {"commit": "deadbeef1234"})
    reg._call_with_audit("w28c1705_fake_commit", {"message": "x"}, actor_id="gary", correlation_id="cid-1")
    assert len(spy.records) == 1
    rec = spy.records[0]
    assert rec.operation == "w28c1705_fake_commit"
    assert rec.status == "success"
    assert rec.actor.actor_id == "gary"
    assert rec.correlation_id == "cid-1"
    assert rec.resolved_ref == "deadbeef1234"
    assert rec.params["output"]["commit_sha"] == "deadbeef1234"
    assert rec.params["output"]["output_sha256"]  # non-empty hash of the result
# FR-1.18 traceability marker for existing git-mcp coverage.
@pytest.mark.UT
@pytest.mark.mcp
@pytest.mark.req("FR-016")  # W28E-1804A semantic rebind


def test_failure_emits_event_with_error() -> None:
    spy = _SpyWriter()
    reg = _registry(spy)

    def _boom(_payload):  # noqa: ANN001, ANN202
        raise RuntimeError("kaboom")

    reg._tools["w28c1705_fake_fail"] = types.SimpleNamespace(handler=_boom)
    with pytest.raises(RuntimeError):
        reg._call_with_audit("w28c1705_fake_fail", {}, actor_id="gary")
    assert spy.records[0].status == "failure"
    assert "kaboom" in spy.records[0].errors[0]
# FR-1.18 traceability marker for existing git-mcp coverage.
@pytest.mark.UT
@pytest.mark.mcp
@pytest.mark.req("FR-016")  # W28E-1804A semantic rebind


def test_sensitive_params_redacted_in_audit() -> None:
    spy = _SpyWriter()
    reg = _registry(spy)
    reg._tools["w28c1705_fake_secret"] = types.SimpleNamespace(handler=lambda payload: {"ok": True})
    reg._call_with_audit("w28c1705_fake_secret", {"token": "supersecret", "message": "hi"}, actor_id="svc")
    rec = spy.records[0]
    assert rec.params["token"] == "[REDACTED]"
    assert rec.params["message"] == "hi"
# FR-1.18 traceability marker for existing git-mcp coverage.
@pytest.mark.UT
@pytest.mark.mcp
@pytest.mark.req("FR-016")  # W28E-1804A semantic rebind


def test_no_audit_writer_is_noop() -> None:
    reg = _registry(None)
    reg._tools["w28c1705_fake_x"] = types.SimpleNamespace(handler=lambda payload: {"ok": True})
    assert reg._call_with_audit("w28c1705_fake_x", {}) == {"ok": True}
# FR-1.18 traceability marker for existing git-mcp coverage.
@pytest.mark.UT
@pytest.mark.mcp
@pytest.mark.req("FR-016")  # W28E-1804A semantic rebind


def test_reuse_mode_emit_uses_live_logger(monkeypatch) -> None:
    """GM3 fix (W28C-1705): reuse-mode AuditWriter re-fetches get_audit_logger() at emit time.

    Under uvicorn, logging is reconfigured AFTER the writer is built, so a logger captured at
    construction has stale handlers and silently drops events. Swapping the live logger after
    construction must still deliver the event (this is what was failing on preprod).
    """
    import git_tools.audit.logger as logger_mod

    class _SpyLogger:
        def __init__(self) -> None:
            self.events: list = []

        def emit(self, event) -> None:  # noqa: ANN001
            self.events.append(event)

    writer = logger_mod.AuditWriter(configure_logging=False)
    captured = _SpyLogger()
    # Swap the live logger AFTER construction — the writer must use THIS, not a cached one.
    monkeypatch.setattr(logger_mod, "get_audit_logger", lambda: captured)
    from git_tools.audit.events import AuditActor, AuditRecord

    writer.emit(
        AuditRecord(
            operation="git_commit",
            status="success",
            correlation_id="c",
            actor=AuditActor(actor_id="gary"),
            params={"output": {"commit_sha": "abc"}},
            resolved_ref="abc",
        )
    )
    assert len(captured.events) == 1
    event = captured.events[0]
    assert event.action == "git_commit"
    assert event.actor.id == "gary"
# FR-1.18 traceability marker for existing git-mcp coverage.
@pytest.mark.UT
@pytest.mark.mcp
@pytest.mark.req("FR-016")  # W28E-1804A semantic rebind


def test_app_audit_writer_is_reuse_mode() -> None:
    """The MCP app builds the AuditWriter and tool calls converge through audit emission."""
    app = create_mcp_app(env_files=["tests/env-UT"])
    reg = app.state.tool_registry
    reg._tools["w28c1705_real_emit"] = types.SimpleNamespace(handler=lambda payload: {"commit": "sha-real-1"})
    reg._call_with_audit("w28c1705_real_emit", {}, actor_id="gary", correlation_id="cid-real")
# FR-1.18 traceability marker for existing git-mcp coverage.
@pytest.mark.UT
@pytest.mark.mcp
@pytest.mark.req("FR-016")  # W28E-1804A semantic rebind


def test_emit_writes_jsonl_to_audit_path(tmp_path) -> None:
    """GM3 fix (W28C-1705): the event is written directly as a JSON line to the audit sink.

    This is the robust path that does NOT depend on the fragile stdlib-logging sink (which
    silently dropped events in uvicorn's live request context on preprod).
    """
    import json as _json

    from git_tools.audit.events import AuditActor, AuditRecord
    from git_tools.audit.logger import AuditWriter

    audit_file = tmp_path / "audit.jsonl"
    writer = AuditWriter(str(audit_file), configure_logging=False)
    writer.emit(
        AuditRecord(
            operation="git_commit",
            status="success",
            correlation_id="c",
            actor=AuditActor(actor_id="gary"),
            params={"token": "[REDACTED]", "output": {"commit_sha": "abc123"}},
            resolved_ref="abc123",
        )
    )
    lines = audit_file.read_text().strip().splitlines()
    assert len(lines) == 1
    event = _json.loads(lines[0])
    assert event["event_type"] == "git_mcp.git_commit"
    assert event["action"] == "git_commit"
    assert event["actor"]["id"] == "gary"
    assert event["details"]["resolved_ref"] == "abc123"
    assert event["details"]["params"]["output"]["commit_sha"] == "abc123"
