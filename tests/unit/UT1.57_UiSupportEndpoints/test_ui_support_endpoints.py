from __future__ import annotations

from pathlib import Path

from fastapi.testclient import TestClient

from git_mcp_server.api_server import create_api_app


def test_ui_support_endpoints_expose_version_status_settings_and_audit(monkeypatch, tmp_path: Path) -> None:
    """Requirements: FR-16, FR-17, UI-R5, UI-R6, UI-R7, UI-R10."""
    events_path = tmp_path / "events.jsonl"
    audit_path = tmp_path / "audit.jsonl"
    a2a_log_path = tmp_path / "a2a.log"
    events_path.write_text(
        '{"action":"create","profile_name":"ui-profile","timestamp":"2026-03-26T10:00:00Z"}\n',
        encoding="utf-8",
    )
    audit_path.write_text(
        '{"type":"Audit","level":"info","message":"audit-ready","timestamp":"2026-03-26T10:01:00Z"}\n',
        encoding="utf-8",
    )
    a2a_log_path.write_text(
        '{"level":"info","message":"a2a-ready","timestamp":"2026-03-26T10:02:00Z"}\n',
        encoding="utf-8",
    )

    monkeypatch.setenv("CLOUD_DOG__STORAGE__EVENTS__PATH", events_path.as_posix())
    monkeypatch.setenv("CLOUD_DOG__STORAGE__AUDIT__PATH", audit_path.as_posix())
    monkeypatch.setenv("CLOUD_DOG__LOG__A2A_SERVER_LOG", a2a_log_path.as_posix())
    monkeypatch.setenv("CLOUD_DOG__WEB__SESSION_TIMEOUT_MINUTES", "45")

    app = create_api_app(env_files=["tests/env-UT"])
    client = TestClient(app)
    headers = {"x-api-key": app.state.seed_api_key}

    version = client.get("/api/v1/ui/version", headers=headers)
    assert version.status_code == 200
    assert version.json()["result"]["version"]

    status = client.get("/api/v1/ui/status", headers=headers)
    assert status.status_code == 200
    payload = status.json()["result"]
    assert len(payload["services"]) == 3
    assert payload["uptime_seconds"] >= 0
    assert "memory_mb" in payload
    assert "memory_percent" in payload
    assert "cpu_percent" in payload
    assert "disk_percent" in payload
    assert "active_connections" in payload
    assert payload["service_metrics"]["profile_count"] >= 1
    assert payload["service_metrics"]["workspace_count"] >= 0
    assert "total_repo_size_mb" in payload["service_metrics"]
    assert len(payload["metrics"]) >= 8

    settings = client.get("/api/v1/settings", headers=headers)
    assert settings.status_code == 200
    groups = settings.json()["result"]["groups"]
    labels = {item["label"] for item in groups}
    assert {"Server", "Auth", "Git", "Repository", "Logging"} <= labels

    update = client.put(
        "/api/v1/settings",
        headers=headers,
        json={"key": "repository.default_profile", "value": "ui-updated-profile"},
    )
    assert update.status_code == 200
    updated = update.json()["result"]["updated"][0]
    assert updated["key"] == "repository.default_profile"
    assert updated["value"] == "ui-updated-profile"

    audit = client.get("/api/v1/audit", headers=headers)
    assert audit.status_code == 200
    items = audit.json()["result"]["items"]
    assert any(item["type"] == "Audit" for item in items)

    a2a_logs = client.get("/api/v1/logs", headers=headers, params={"log_type": "a2a"})
    assert a2a_logs.status_code == 200
    assert any(item["type"] == "A2A" for item in a2a_logs.json()["result"]["items"])
