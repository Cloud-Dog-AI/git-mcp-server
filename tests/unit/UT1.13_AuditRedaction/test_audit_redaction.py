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
from pathlib import Path

from git_tools.audit.events import AuditRecord
from git_tools.audit.logger import AuditWriter


def test_audit_redaction_masks_sensitive_fields(tmp_path: Path) -> None:
    """Requirements: FR-14."""
    audit_file = tmp_path / "audit.jsonl"
    writer = AuditWriter(audit_file.as_posix())

    record = AuditRecord(
        operation="tool.call",
        status="success",
        correlation_id="cid-2",
        actor={"actor_id": "user-1"},
        params={"api_key": "secret", "path": "README.md"},
    )
    writer.emit(record)
    writer.close()

    payload = json.loads(audit_file.read_text(encoding="utf-8").strip())
    event = payload
    if "details" not in payload and "message" in payload:
        event = json.loads(payload["message"])
    params = event["details"]["params"]
    assert params["api_key"] == "***REDACTED***"
    assert params["path"] == "README.md"
