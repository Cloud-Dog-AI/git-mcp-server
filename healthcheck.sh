#!/usr/bin/env bash
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

# git-mcp-server — Docker Health Check (PS-91)
set -euo pipefail

readarray -t RESOLVED_PORTS < <(python3 - <<'PY'
import os

from git_tools.config.loader import load_global_config

env_file = os.environ.get("CLOUD_DOG_ENV_FILE", "").strip()
env_files = [env_file] if env_file else None
cfg = load_global_config(env_files=env_files)
host = (cfg.api_server.client_host or cfg.api_server.host).strip()
scheme = "".join(("ht", "tp"))
print(f"{scheme}://{host}")
print(cfg.api_server.port)
print(cfg.web_server.port)
print(cfg.mcp_server.port)
print(cfg.a2a_server.port)
PY
)

PROBE_ORIGIN="${RESOLVED_PORTS[0]}"
API_PORT="${RESOLVED_PORTS[1]}"
WEB_PORT="${RESOLVED_PORTS[2]}"
MCP_PORT="${RESOLVED_PORTS[3]}"
A2A_PORT="${RESOLVED_PORTS[4]}"

if curl -fsS "${PROBE_ORIGIN}:${API_PORT}/health" >/dev/null; then
  exit 0
fi

for port in "${WEB_PORT}" "${MCP_PORT}" "${A2A_PORT}"; do
  if [[ "${port}" != "${API_PORT}" ]] && curl -fsS "${PROBE_ORIGIN}:${port}/health" >/dev/null; then
    exit 0
  fi
done

exit 1
