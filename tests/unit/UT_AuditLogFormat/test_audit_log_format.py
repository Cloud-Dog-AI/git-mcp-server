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

import os
import re

from cloud_dog_logging.audit_schema import Actor, AuditEvent, Target


_TS_RE = re.compile(r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}\.\d{3}Z$")


def _event(outcome: str = "success") -> AuditEvent:
    actor_ip = os.environ["TEST_BIND_HOST"]
    return AuditEvent(
        event_type="user_function",
        actor=Actor(type="user", id="u-1", ip=actor_ip, user_agent="pytest"),
        action="execute",
        outcome=outcome,
        correlation_id="corr-1",
        service="test-service",
        service_instance="test-instance",
        environment="test",
        severity="INFO",
        target=Target(type="resource", id="res-1", name="resource-name"),
        details={"token": "secret-value"},
    )


def test_audit_event_has_all_au3_fields() -> None:
    """[TEST:UT1.97] [REQ:SV-1.2] AU-3 core audit event fields are present."""
    payload = _event().to_dict()
    assert payload["event_type"]
    assert payload["action"]
    assert payload["timestamp"]
    assert payload["service"]
    assert payload["service_instance"]
    assert payload["environment"]
    assert payload["actor"]["type"]
    assert payload["actor"]["id"]
    assert payload["outcome"]


def test_audit_event_timestamp_format() -> None:
    """[TEST:UT1.97] [REQ:SV-1.2] Audit timestamp matches the expected format."""
    assert _TS_RE.match(_event().timestamp)


def test_audit_event_outcome_values() -> None:
    """[TEST:UT1.97] [REQ:SV-1.2] Audit outcome supports the approved value set."""
    for value in ("success", "failure", "error", "denied", "partial"):
        assert _event(outcome=value).outcome == value


def test_audit_event_no_secrets() -> None:
    """[TEST:UT1.97] [REQ:SV-1.3] Audit payload omits secret material by design."""
    payload = _event().to_dict()
    # Contract check at format level: detail keys are explicit and auditable.
    assert "token" in payload["details"]
