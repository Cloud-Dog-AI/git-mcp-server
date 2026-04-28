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

from git_mcp_server.logging import configure_service_logging


def test_configure_service_logging_binds_surface_specific_app_log(monkeypatch) -> None:
    """[Req: NF-08, SV-01] Surface logging selects the matching per-server file."""
    captured: dict[str, object] = {}

    def _fake_setup_logging(config: object) -> None:
        assert isinstance(config, dict)
        captured.update(config)

    monkeypatch.setattr("git_mcp_server.logging.setup_logging", _fake_setup_logging)

    config = {
        "log": {
            "api_server_log": "./logs/api_server.log",
            "web_server_log": "./logs/web_server.log",
            "mcp_server_log": "./logs/mcp_server.log",
            "a2a_server_log": "./logs/a2a_server.log",
        }
    }

    expected = {
        "api": "./logs/api_server.log",
        "web": "./logs/web_server.log",
        "mcp": "./logs/mcp_server.log",
        "a2a": "./logs/a2a_server.log",
    }

    for surface, path in expected.items():
        captured.clear()
        configure_service_logging(
            config,
            service_name=f"git-mcp-server-{surface}",
            server_id="test-node",
            surface=surface,
        )
        log_config = captured["log"]
        assert isinstance(log_config, dict)
        assert log_config["app_log"] == path
        assert log_config["service_instance"] == "test-node"


def test_configure_service_logging_preserves_existing_app_log_without_surface(monkeypatch) -> None:
    """[Req: NF-08, SV-01] Existing app_log remains stable when no surface is provided."""
    captured: dict[str, object] = {}

    def _fake_setup_logging(config: object) -> None:
        assert isinstance(config, dict)
        captured.update(config)

    monkeypatch.setattr("git_mcp_server.logging.setup_logging", _fake_setup_logging)

    configure_service_logging(
        {"log": {"app_log": "./logs/app.log"}},
        service_name="git-mcp-server",
        server_id="test-node",
    )

    log_config = captured["log"]
    assert isinstance(log_config, dict)
    assert log_config["app_log"] == "./logs/app.log"
    assert log_config["service_instance"] == "test-node"
