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

set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "${ROOT_DIR}"

LOG_DIR="${ROOT_DIR}/.tmp-tests/integrity-guarded"
mkdir -p "${LOG_DIR}"

PYTEST_BIN="${ROOT_DIR}/.venv/bin/pytest"
if [[ ! -x "${PYTEST_BIN}" ]]; then
  echo "Missing ${PYTEST_BIN}" >&2
  exit 2
fi

cleanup() {
  ./server_control.sh --env tests/env-IT stop all >/dev/null 2>&1 || true
  ./server_control.sh --env tests/env-AT stop api >/dev/null 2>&1 || true
}
trap cleanup EXIT

run_step() {
  local name="$1"
  local limit="$2"
  local command="$3"
  local logfile="${LOG_DIR}/${name}.log"

  echo "=== ${name} (timeout ${limit}) ==="
  set +e
  timeout --signal=TERM --kill-after=20s "${limit}" bash -lc "${command}" >"${logfile}" 2>&1
  local rc=$?
  set -e

  if [[ ${rc} -eq 124 ]]; then
    echo "${name}: TIMEOUT"
    tail -40 "${logfile}" || true
    return 124
  fi
  if [[ ${rc} -ne 0 ]]; then
    echo "${name}: FAIL (${rc})"
    tail -40 "${logfile}" || true
    return "${rc}"
  fi

  echo "${name}: PASS"
  tail -5 "${logfile}" || true
  return 0
}

run_step "ut" "8m" "${PYTEST_BIN} tests/unit --env tests/env-UT -v"
run_step "st" "8m" "${PYTEST_BIN} tests/system --env tests/env-ST -v"
run_step "it" "30m" "${PYTEST_BIN} tests/integration --env tests/env-IT -v"
run_step "at" "12m" "${PYTEST_BIN} tests/application --env tests/env-AT -v"
run_step "qt" "8m" "${PYTEST_BIN} tests/security --env tests/env-QT -v"
run_step "it_remote_unset" "10m" "GIT_MCP_REMOTE_REPO='' TEST_ENV_TIER=IT ${PYTEST_BIN} tests/integration/IT1.9_RemoteCloneAndFetch -v --env tests/env-IT"

echo "=== Done ==="
