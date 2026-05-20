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

from cloud_dog_config import load_config


def test_config_vault_integration_handles_vault_block_without_resolution(tmp_path: Path, unused_tcp_port_factory) -> None:
    """Requirements: FR-02."""
    bind_host = os.environ["TEST_BIND_HOST"]
    api_port = unused_tcp_port_factory()
    web_port = unused_tcp_port_factory()
    mcp_port = unused_tcp_port_factory()
    a2a_port = unused_tcp_port_factory()
    defaults = tmp_path / "defaults.yaml"
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
vault:
  enabled: false
""".format(
            bind_host=bind_host,
            api_port=api_port,
            web_port=web_port,
            mcp_port=mcp_port,
            a2a_port=a2a_port,
        ),
        encoding="utf-8",
    )

    cfg = load_config(
        defaults_yaml=defaults.as_posix(),
        config_yaml=(tmp_path / "missing.yaml").as_posix(),
        vault_enabled=False,
    )
    assert cfg.get("vault.enabled") is False
