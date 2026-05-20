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

from git_tools.audit.events import AuditRecord


def test_audit_event_shape_contains_required_fields() -> None:
    """Requirements: FR-14."""
    event = AuditRecord(
        operation="git_commit",
        status="success",
        correlation_id="cid-1",
        actor={"actor_id": "user-1"},
    )
    assert event.timestamp
    assert event.actor.actor_id == "user-1"
    assert event.operation == "git_commit"
    assert event.correlation_id == "cid-1"
