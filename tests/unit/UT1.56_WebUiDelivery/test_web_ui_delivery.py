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

from pathlib import Path

from fastapi.testclient import TestClient

from git_mcp_server.web_server import create_web_app


def _build_ui_dist(root: Path) -> Path:
    """Create a minimal built SPA tree for UI delivery tests."""
    ui_root = root / "ui-dist"
    assets_root = ui_root / "assets"
    assets_root.mkdir(parents=True, exist_ok=True)
    (ui_root / "index.html").write_text(
        """<!doctype html>
<html lang="en">
  <head><title>Git MCP UI</title></head>
  <body>
    <div id="root"></div>
    <script src="/runtime-config.js"></script>
  </body>
</html>
""",
        encoding="utf-8",
    )
    (assets_root / "app.js").write_text("console.log('ui');\n", encoding="utf-8")
    return ui_root


def test_web_ui_routes_serve_spa_and_runtime_config(monkeypatch, tmp_path: Path) -> None:
    """Requirements: FR-16, FR-17."""
    ui_root = _build_ui_dist(tmp_path)
    monkeypatch.setenv("CLOUD_DOG__WEB__UI_DIST_DIR", ui_root.as_posix())
    # PS-92 (W28A-970c-V2): MCP base path moved to mcp_server.base_path (was web.mcp_proxy_base_path).
    monkeypatch.setenv("CLOUD_DOG__MCP_SERVER__BASE_PATH", "/mcp")
    monkeypatch.setenv("CLOUD_DOG__RUNTIME__A2A_TEST_API_KEY", "12345678")

    app = create_web_app(env_files=["tests/env-UT"])
    client = TestClient(app)

    runtime_config = client.get("/runtime-config.js")
    assert runtime_config.status_code == 200
    assert runtime_config.headers["content-type"].startswith("application/javascript")
    assert 'window.__RUNTIME_CONFIG__ = {' in runtime_config.text
    assert '"API_BASE_URL": __origin' in runtime_config.text
    assert '"MCP_BASE_URL": __origin + "/mcp"' in runtime_config.text
    assert '"A2A_BASE_URL": "http://testserver/a2a"' in runtime_config.text
    assert '"SESSION_TIMEOUT_MINUTES": 30' in runtime_config.text

    root = client.get("/")
    assert root.status_code == 200
    assert "Git MCP UI" in root.text

    login = client.get("/login")
    assert login.status_code == 200
    assert "Git MCP UI" in login.text

    dashboard = client.get("/dashboard")
    assert dashboard.status_code == 200
    assert "Git MCP UI" in dashboard.text

    asset = client.get("/assets/app.js")
    assert asset.status_code == 200
    assert "console.log('ui')" in asset.text

    status = client.get("/status")
    assert status.status_code == 200
    payload = status.json()
    assert payload["uptime_seconds"] >= 0
    assert "memory_mb" in payload
    assert "memory_percent" in payload
    assert "cpu_percent" in payload
    assert "disk_percent" in payload
    assert "active_connections" in payload
    assert payload["service_metrics"]["profile_count"] >= 1
    assert "workspace_count" in payload["service_metrics"]
    assert "total_repo_size_mb" in payload["service_metrics"]


def test_web_ui_runtime_config_uses_forwarded_https_origin(monkeypatch, tmp_path: Path) -> None:
    """Requirements: FR-16, FR-17."""
    ui_root = _build_ui_dist(tmp_path)
    monkeypatch.setenv("CLOUD_DOG__WEB__UI_DIST_DIR", ui_root.as_posix())
    # PS-92 (W28A-970c-V2): MCP base path moved to mcp_server.base_path (was web.mcp_proxy_base_path).
    monkeypatch.setenv("CLOUD_DOG__MCP_SERVER__BASE_PATH", "/git-mcp")
    monkeypatch.setenv("CLOUD_DOG__RUNTIME__A2A_TEST_API_KEY", "12345678")

    app = create_web_app(env_files=["tests/env-UT"])
    client = TestClient(app)

    runtime_config = client.get(
        "/runtime-config.js",
        headers={
            "x-forwarded-proto": "https",
            "x-forwarded-host": "gitmcpserver.example.test",
        },
    )

    assert runtime_config.status_code == 200
    assert '"API_BASE_URL": __origin' in runtime_config.text
    assert '"MCP_BASE_URL": __origin + "/git-mcp"' in runtime_config.text
    assert '"A2A_BASE_URL": "https://gitmcpserver.example.test/a2a"' in runtime_config.text


def test_web_ui_keeps_api_and_mcp_routes_outside_spa(monkeypatch, tmp_path: Path) -> None:
    """Requirements: FR-01, FR-16, FR-17."""
    ui_root = _build_ui_dist(tmp_path)
    monkeypatch.setenv("CLOUD_DOG__WEB__UI_DIST_DIR", ui_root.as_posix())
    # PS-92 (W28A-970c-V2): MCP base path moved to mcp_server.base_path (was web.mcp_proxy_base_path).
    monkeypatch.setenv("CLOUD_DOG__MCP_SERVER__BASE_PATH", "/mcp")
    monkeypatch.setenv("CLOUD_DOG__RUNTIME__A2A_TEST_API_KEY", "12345678")

    app = create_web_app(env_files=["tests/env-UT"])
    client = TestClient(app)

    assert client.get("/app/v1/tools").status_code == 401
    assert client.get("/api/v1/tools").status_code == 401
    assert client.get("/mcp/tools").status_code == 401
    assert client.get("/a2a/health").status_code == 401
    assert client.get("/docs").status_code == 200


def test_web_ui_fallback_excludes_non_spa_route_families(monkeypatch, tmp_path: Path) -> None:
    """Requirements: FR-16, FR-17."""
    ui_root = _build_ui_dist(tmp_path)
    monkeypatch.setenv("CLOUD_DOG__WEB__UI_DIST_DIR", ui_root.as_posix())
    # PS-92 (W28A-970c-V2): MCP base path moved to mcp_server.base_path (was web.mcp_proxy_base_path).
    monkeypatch.setenv("CLOUD_DOG__MCP_SERVER__BASE_PATH", "/mcp")
    monkeypatch.setenv("CLOUD_DOG__RUNTIME__A2A_TEST_API_KEY", "12345678")

    app = create_web_app(env_files=["tests/env-UT"])
    client = TestClient(app)

    mcp = client.get("/mcp/tools")
    assert mcp.status_code == 401
    assert mcp.headers["content-type"].startswith("application/json")
    assert mcp.json() == {"detail": "Not authenticated"}

    admin = client.get("/admin/users")
    assert admin.status_code == 404
    assert admin.headers["content-type"].startswith("application/json")
    assert admin.json() == {"detail": "Not Found"}
