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

# Verification script for git-mcp-server CONFIG migration.
# Exit code 0 = all gates pass. Non-zero = one or more gates failed.

set -uo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT="$(cd "$SCRIPT_DIR/../.." && pwd)"
FAIL=0
PASS=0

check() {
    local gate="$1"
    local result="$2"
    if [ "$result" -eq 0 ]; then
        echo "  PASS  $gate"
        PASS=$((PASS + 1))
    else
        echo "  FAIL  $gate"
        FAIL=$((FAIL + 1))
    fi
}

echo "=== git-mcp-server CONFIG Migration Verification ==="
echo ""

if grep -q '"cloud_dog_config>=' "$PROJECT/pyproject.toml" 2>/dev/null; then
    check "QG-CFG-1 cloud_dog_config declared in pyproject" 0
else
    check "QG-CFG-1 cloud_dog_config declared in pyproject" 1
fi

if grep -q "from cloud_dog_config import GlobalConfig, load_config" "$PROJECT/src/git_tools/config/loader.py" 2>/dev/null; then
    check "QG-CFG-2 loader uses cloud_dog_config.load_config" 0
else
    check "QG-CFG-2 loader uses cloud_dog_config.load_config" 1
fi

COUNT=$(grep -RInE "yaml\.safe_load|dotenv|load_dotenv|overlay_secrets|import hvac" "$PROJECT/src/git_tools/config" --include='*.py' 2>/dev/null | wc -l)
check "QG-CFG-3 no bespoke loader in src/git_tools/config (count=${COUNT})" "$COUNT"

COUNT=$(grep -RIn "os\.getenv" "$PROJECT/src/git_mcp_server" "$PROJECT/src/git_tools/db/runtime.py" --include='*.py' 2>/dev/null | wc -l)
if [ "$COUNT" -le 8 ]; then
    check "QG-CFG-4 runtime env bridge bounded (hits=${COUNT}, max=8)" 0
else
    check "QG-CFG-4 runtime env bridge bounded (hits=${COUNT}, max=8)" 1
fi

if [ -f "$PROJECT/defaults.yaml" ]; then
    check "QG-CFG-5 defaults.yaml present" 0
else
    check "QG-CFG-5 defaults.yaml present" 1
fi

COUNT=$(grep -RInE "sys\.path\.insert|_select_relevant_os_environ" "$PROJECT/src" --include='*.py' 2>/dev/null | wc -l)
check "QG-CFG-6 no private API hacks in src (count=${COUNT})" "$COUNT"

echo ""
echo "=== RESULTS: ${PASS} passed, ${FAIL} failed ==="
echo ""
if [ "$FAIL" -eq 0 ]; then
    echo "VERDICT: ALL PASS — git-mcp-server CONFIG migration verifier checks are green."
    exit 0
else
    echo "VERDICT: ${FAIL} gate(s) failed — review failures above."
    exit 1
fi
