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

# git-mcp-server — Server control script
# Usage: ./server_control.sh --env tests/env-UT {start|stop|restart|status} {api|web|mcp|a2a|all}

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PID_DIR="${SCRIPT_DIR}/.pids"
mkdir -p "${PID_DIR}"
export PYTHONPATH="${SCRIPT_DIR}/src:${PYTHONPATH:-}"
LOG_DIR="${CLOUD_DOG_LOG_DIR:-/app/logs}"
if ! mkdir -p "${LOG_DIR}" 2>/dev/null; then
  LOG_DIR="${SCRIPT_DIR}/logs"
  mkdir -p "${LOG_DIR}"
fi

ensure_log_file_writable() {
  local candidate="$1"
  if : >> "${candidate}" 2>/dev/null; then
    return 0
  fi
  local fallback_dir="${TMPDIR:-/tmp}/git-mcp-server/logs"
  mkdir -p "${fallback_dir}"
  LOG_DIR="${fallback_dir}"
  : >> "${LOG_DIR}/$(basename "${candidate}")"
}

VAULT_ENV_FILE="/opt/iac/Development/cloud-dog-ai/env-vault"
if [[ -f "${VAULT_ENV_FILE}" ]] && [[ -z "${VAULT_ADDR:-}" || -z "${VAULT_TOKEN:-}" ]]; then
  set -a
  # Shared read-only Vault bootstrap for native service control.
  source "${VAULT_ENV_FILE}"
  set +a
fi

PYTHON_BIN="${SCRIPT_DIR}/.venv/bin/python"
if [[ ! -x "${PYTHON_BIN}" ]]; then
  PYTHON_BIN="python3"
fi

ENV_FILE=""
if [[ "${1:-}" == "--env" ]]; then
  ENV_FILE="${2:-}"
  if [[ -z "${ENV_FILE}" || ! -f "${ENV_FILE}" ]]; then
    echo "Missing or invalid --env file" >&2
    exit 1
  fi
  export CLOUD_DOG_ENV_FILES="${ENV_FILE}"
  shift 2
fi

ACTION="${1:-status}"
TARGET="${2:-all}"

declare -A MODULES=(
  [api]="git_mcp_server.api_server"
  [web]="git_mcp_server.web_server"
  [mcp]="git_mcp_server.mcp_server"
  [a2a]="git_mcp_server.a2a_server"
)

is_pid_active() {
  local target_pid="$1"
  if ! kill -0 "${target_pid}" 2>/dev/null; then
    return 1
  fi
  local stat
  stat="$(ps -p "${target_pid}" -o stat= 2>/dev/null | awk '{print $1}')"
  if [[ -z "${stat}" ]]; then
    return 1
  fi
  # Zombie processes still satisfy kill -0; treat them as inactive.
  if [[ "${stat}" == Z* ]]; then
    return 1
  fi
  return 0
}

start_server() {
  local name="$1"
  local module="${MODULES[$name]}"
  local pid_file="${PID_DIR}/${name}.pid"
  local log_file="${LOG_DIR}/${name}.log"
  local env_args=()
  local start_attempt
  local pid=""
  ensure_log_file_writable "${log_file}"
  log_file="${LOG_DIR}/${name}.log"
  if [[ -n "${ENV_FILE}" ]]; then
    env_args=(--env-file "${ENV_FILE}")
  fi
  if [[ -f "${pid_file}" ]] && is_pid_active "$(cat "${pid_file}")"; then
    echo "${name}: running (PID $(cat "${pid_file}"))"
    return
  fi
  rm -f "${pid_file}"
  for start_attempt in 1 2 3; do
    PYTHONUNBUFFERED=1 PYTHONFAULTHANDLER=1 nohup "${PYTHON_BIN}" -m "${module}" "${env_args[@]}" >"${log_file}" 2>&1 < /dev/null &
    pid=$!
    echo "${pid}" > "${pid_file}"
    sleep 0.5
    if is_pid_active "${pid}"; then
      echo "${name}: started (PID ${pid})"
      return
    fi
    rm -f "${pid_file}"
    if [[ "${start_attempt}" -lt 3 ]]; then
      sleep "${start_attempt}"
    fi
  done
  echo "${name}: failed to start (see ${log_file})" >&2
  return 1
}

stop_server() {
  local name="$1"
  local module="${MODULES[$name]}"
  local pid_file="${PID_DIR}/${name}.pid"
  local -a tracked_pids=()
  local -a module_pids=()
  local pid=""

  terminate_pid() {
    local target_pid="$1"
    if ! is_pid_active "${target_pid}"; then
      return
    fi
    kill "${target_pid}" 2>/dev/null || true
    for _ in {1..20}; do
      if ! is_pid_active "${target_pid}"; then
        return
      fi
      sleep 0.1
    done
    kill -9 "${target_pid}" 2>/dev/null || true
  }

  if [[ -f "${pid_file}" ]]; then
    pid="$(cat "${pid_file}")"
    if [[ "${pid}" =~ ^[0-9]+$ ]]; then
      tracked_pids+=("${pid}")
    fi
    rm -f "${pid_file}"
  fi

  while IFS= read -r pid; do
    [[ "${pid}" =~ ^[0-9]+$ ]] || continue
    module_pids+=("${pid}")
  done < <(ps -eo pid=,args= | awk -v module="${module}" '$0 ~ ("-m " module "($| )") {print $1}')

  for pid in "${tracked_pids[@]}" "${module_pids[@]}"; do
    [[ -n "${pid}" ]] || continue
    terminate_pid "${pid}"
  done
  echo "${name}: stopped"
}

status_server() {
  local name="$1"
  local pid_file="${PID_DIR}/${name}.pid"
  if [[ -f "${pid_file}" ]] && is_pid_active "$(cat "${pid_file}")"; then
    echo "${name}: running (PID $(cat "${pid_file}"))"
  else
    echo "${name}: stopped"
  fi
}

if [[ "${TARGET}" == "all" ]]; then
  TARGETS=(api web mcp a2a)
else
  TARGETS=("${TARGET}")
fi

for server in "${TARGETS[@]}"; do
  case "${ACTION}" in
    start) start_server "${server}" ;;
    stop) stop_server "${server}" ;;
    restart) stop_server "${server}"; sleep 1; start_server "${server}" ;;
    status) status_server "${server}" ;;
    *)
      echo "Usage: $0 [--env <file>] {start|stop|restart|status} {api|web|mcp|a2a|all}" >&2
      exit 1
      ;;
  esac
done
