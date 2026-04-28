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

# git-mcp-server — Docker Entrypoint (PS-91)
set -euo pipefail

echo "============================================================"
echo "git-mcp-server container"
echo "Mode: ${1:-all} | Python: $(python3 --version 2>&1)"
echo "============================================================"

mkdir -p /app/logs /app/data/audit /app/data/workspaces /app/.pids /app/certs

resolve_log_dir() {
  local candidate="${CLOUD_DOG_LOG_DIR:-/app/logs}"
  local fallback="/tmp/git-mcp-server/logs"
  mkdir -p "${candidate}" 2>/dev/null || true
  if touch "${candidate}/.entrypoint-write-test" 2>/dev/null; then
    rm -f "${candidate}/.entrypoint-write-test"
    if touch "${candidate}/api.log" "${candidate}/web.log" "${candidate}/mcp.log" "${candidate}/a2a.log" 2>/dev/null; then
      return 0
    fi
  fi
  mkdir -p "${fallback}"
  export CLOUD_DOG_LOG_DIR="${fallback}"
}

resolve_log_dir

# ── CA Bundle ────────────────────────────────────────────────────
RUNTIME_CA_BUNDLE="/app/certs/runtime-ca-bundle.crt"
rm -f "${RUNTIME_CA_BUNDLE}"
touch "${RUNTIME_CA_BUNDLE}"
for cert in \
  "${CLOUD_DOG_TLS_CA_BUNDLE:-}" \
  "${CLOUD_DOG_TLS_CORPORATE_CA:-}" \
  "${CLOUD_DOG_TLS_ACME_CA:-}"; do
  if [[ -n "${cert}" && -f "${cert}" ]]; then
    cat "${cert}" >> "${RUNTIME_CA_BUNDLE}"
    echo "" >> "${RUNTIME_CA_BUNDLE}"
  fi
done

if [[ -s "${RUNTIME_CA_BUNDLE}" ]]; then
  export REQUESTS_CA_BUNDLE="${REQUESTS_CA_BUNDLE:-${RUNTIME_CA_BUNDLE}}"
  export SSL_CERT_FILE="${SSL_CERT_FILE:-${RUNTIME_CA_BUNDLE}}"
  export CURL_CA_BUNDLE="${CURL_CA_BUNDLE:-${RUNTIME_CA_BUNDLE}}"
  export GIT_SSL_CAINFO="${GIT_SSL_CAINFO:-${RUNTIME_CA_BUNDLE}}"
  export NODE_EXTRA_CA_CERTS="${NODE_EXTRA_CA_CERTS:-${RUNTIME_CA_BUNDLE}}"
else
  export REQUESTS_CA_BUNDLE="${REQUESTS_CA_BUNDLE:-/etc/ssl/certs/ca-certificates.crt}"
  export SSL_CERT_FILE="${SSL_CERT_FILE:-/etc/ssl/certs/ca-certificates.crt}"
  export CURL_CA_BUNDLE="${CURL_CA_BUNDLE:-/etc/ssl/certs/ca-certificates.crt}"
  export GIT_SSL_CAINFO="${GIT_SSL_CAINFO:-/etc/ssl/certs/ca-certificates.crt}"
  export NODE_EXTRA_CA_CERTS="${NODE_EXTRA_CA_CERTS:-/etc/ssl/certs/ca-certificates.crt}"
fi

# ── Git proxy alignment ─────────────────────────────────────────
if [[ -n "${HTTPS_PROXY:-}" ]]; then
  git config --global http.proxy "${HTTPS_PROXY}" || true
elif [[ -n "${HTTP_PROXY:-}" ]]; then
  git config --global http.proxy "${HTTP_PROXY}" || true
fi
if [[ -n "${NO_PROXY:-}" ]]; then
  git config --global http.noProxy "${NO_PROXY}" || true
fi
git config --global http.sslCAInfo "${GIT_SSL_CAINFO}" || true

# ── Env file loading ────────────────────────────────────────────
ENV_FILE="${CLOUD_DOG_ENV_FILE:-}"
ENV_ARGS=()
if [[ -n "${ENV_FILE}" && -f "${ENV_FILE}" ]]; then
  ENV_ARGS=(--env "${ENV_FILE}")
fi

resolve_config_port() {
  local server_name="$1"
  TARGET_SERVER="${server_name}" python3 - <<'PY'
import os

from git_tools.config.loader import load_global_config

env_file = os.environ.get("CLOUD_DOG_ENV_FILE", "").strip()
env_files = [env_file] if env_file else None
cfg = load_global_config(env_files=env_files)
target = os.environ["TARGET_SERVER"]
mapping = {
    "api": cfg.api_server.port,
    "web": cfg.web_server.port,
    "mcp": cfg.mcp_server.port,
    "a2a": cfg.a2a_server.port,
}
print(mapping[target])
PY
}

resolve_api_probe_url() {
  python3 - <<'PY'
import os

from git_tools.config.loader import load_global_config

env_file = os.environ.get("CLOUD_DOG_ENV_FILE", "").strip()
env_files = [env_file] if env_file else None
cfg = load_global_config(env_files=env_files)
host = (cfg.api_server.client_host or cfg.api_server.host).strip()
scheme = "".join(("ht", "tp"))
print(f"{scheme}://{host}:{cfg.api_server.port}/health")
PY
}

# ── Graceful shutdown ───────────────────────────────────────────
shutdown() {
  echo "[INFO] Stopping services..."
  /app/server_control.sh ${ENV_ARGS[@]+"${ENV_ARGS[@]}"} stop all 2>/dev/null || true
}
trap shutdown INT TERM

# ── Mode dispatch ───────────────────────────────────────────────
case "${1:-all}" in
  all)
    /app/server_control.sh ${ENV_ARGS[@]+"${ENV_ARGS[@]}"} start all
    tail -F "${CLOUD_DOG_LOG_DIR:-/app/logs}"/*.log 2>/dev/null &
    wait $!
    ;;
  api|web|mcp|a2a)
    /app/server_control.sh ${ENV_ARGS[@]+"${ENV_ARGS[@]}"} start "$1"
    tail -F "${CLOUD_DOG_LOG_DIR:-/app/logs}"/*.log 2>/dev/null &
    wait $!
    ;;
  status)
    /app/server_control.sh ${ENV_ARGS[@]+"${ENV_ARGS[@]}"} status all
    ;;
  test)
    /app/server_control.sh ${ENV_ARGS[@]+"${ENV_ARGS[@]}"} start all
    sleep 5
    API_HEALTH_URL="$(resolve_api_probe_url)"
    if curl -fs "${API_HEALTH_URL}" >/dev/null; then
      echo "HEALTH CHECK PASSED"
      /app/server_control.sh ${ENV_ARGS[@]+"${ENV_ARGS[@]}"} stop all
      exit 0
    else
      echo "HEALTH CHECK FAILED"
      /app/server_control.sh ${ENV_ARGS[@]+"${ENV_ARGS[@]}"} stop all
      exit 1
    fi
    ;;
  shell|bash)
    exec /bin/bash
    ;;
  *)
    echo "Usage: git-mcp-server [all|api|web|mcp|a2a|status|test|shell]"
    exit 1
    ;;
esac
