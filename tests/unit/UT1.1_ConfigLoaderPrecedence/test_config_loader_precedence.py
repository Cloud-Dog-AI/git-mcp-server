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
from pathlib import Path

from git_tools.config.loader import load_global_config


def test_config_loader_precedence(tmp_path: Path, monkeypatch, unused_tcp_port_factory) -> None:
    """Requirements: FR-02."""
    bind_host = os.environ["TEST_BIND_HOST"]
    api_port = unused_tcp_port_factory()
    config_port = unused_tcp_port_factory()
    env_port = unused_tcp_port_factory()
    override_port = unused_tcp_port_factory()
    web_port = unused_tcp_port_factory()
    mcp_port = unused_tcp_port_factory()
    a2a_port = unused_tcp_port_factory()
    defaults = tmp_path / "defaults.yaml"
    config = tmp_path / "config.yaml"
    env_file = tmp_path / "env-test"

    defaults.write_text(
        """
api_server:
  host: {bind_host}
  port: {api_port}
web_server:
  host: {bind_host}
  port: {web_port}
mcp_server:
  host: {bind_host}
  port: {mcp_port}
  transport: stdio
a2a_server:
  host: {bind_host}
  port: {a2a_port}
auth:
  mode: api_key
  jwt: {{issuer: '', audience: '', public_keys_url: ''}}
storage:
  db: {{url: sqlite:///tmp.db}}
  audit: {{path: ./audit.jsonl}}
workspace:
  base_dir: ./work
  default_mode: ephemeral
  default_ttl_seconds: 10
  cleanup_interval_seconds: 10
profiles: {{}}
rbac:
  enabled: true
  default_deny: true
  roles: {{}}
""".format(
            bind_host=bind_host,
            api_port=api_port,
            web_port=web_port,
            mcp_port=mcp_port,
            a2a_port=a2a_port,
        ),
        encoding="utf-8",
    )
    config.write_text(f"api_server:\n  port: {config_port}\n", encoding="utf-8")
    env_file.write_text(f"CLOUD_DOG__API_SERVER__PORT={env_port}\n", encoding="utf-8")
    monkeypatch.setenv("CLOUD_DOG__API_SERVER__PORT", str(override_port))

    loaded = load_global_config(
        env_files=[env_file.as_posix()],
        config_yaml=config.as_posix(),
        defaults_yaml=defaults.as_posix(),
    )
    assert loaded.api_server.port == override_port


def test_config_loader_resolves_web_login_password_from_env(tmp_path: Path, monkeypatch, unused_tcp_port_factory) -> None:
    """Requirements: FR-02."""
    bind_host = os.environ["TEST_BIND_HOST"]
    api_port = unused_tcp_port_factory()
    web_port = unused_tcp_port_factory()
    mcp_port = unused_tcp_port_factory()
    a2a_port = unused_tcp_port_factory()
    defaults = tmp_path / "defaults.yaml"
    config = tmp_path / "config.yaml"

    defaults.write_text(
        """
api_server:
  host: {bind_host}
  port: {api_port}
web_server:
  host: {bind_host}
  port: {web_port}
mcp_server:
  host: {bind_host}
  port: {mcp_port}
  transport: stdio
a2a_server:
  host: {bind_host}
  port: {a2a_port}
web_login:
  username: "${{CLOUD_DOG_WEB_LOGIN_USERNAME:admin}}"
  password: "${{CLOUD_DOG_WEB_LOGIN_PASSWORD:''}}"
auth:
  mode: api_key
  jwt: {{issuer: '', audience: '', public_keys_url: '', secret: ''}}
storage:
  db: {{url: sqlite:///tmp.db}}
  audit: {{path: ./audit.jsonl}}
workspace:
  base_dir: ./work
  default_mode: ephemeral
  default_ttl_seconds: 10
  cleanup_interval_seconds: 10
profiles: {{}}
rbac:
  enabled: true
  default_deny: true
  roles: {{}}
""".format(
            bind_host=bind_host,
            api_port=api_port,
            web_port=web_port,
            mcp_port=mcp_port,
            a2a_port=a2a_port,
        ),
        encoding="utf-8",
    )
    monkeypatch.setenv("CLOUD_DOG_WEB_LOGIN_USERNAME", "admin")
    monkeypatch.setenv("CLOUD_DOG_WEB_LOGIN_PASSWORD", "OrangeRiverTable")
    config.write_text("", encoding="utf-8")

    loaded = load_global_config(defaults_yaml=defaults.as_posix(), config_yaml=config.as_posix())

    assert loaded.web_login.username == "admin"
    assert loaded.web_login.password == "OrangeRiverTable"
