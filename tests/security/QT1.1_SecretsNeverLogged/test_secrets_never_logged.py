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


def test_secrets_never_logged(tmp_path: Path) -> None:
    """Requirements: FR-06."""
    audit_path = tmp_path / "audit.jsonl"
    writer = AuditWriter(audit_path.as_posix())
    writer.emit(
        AuditRecord(
            operation="admin_credentials_set",
            status="success",
            correlation_id="qt-1",
            actor={"actor_id": "admin"},
            params={"password": "super-secret", "api_key": "abc123"},
        )
    )
    writer.close()

    payload = json.loads(audit_path.read_text(encoding="utf-8"))
    text = json.dumps(payload)
    assert "super-secret" not in text
    assert "abc123" not in text
