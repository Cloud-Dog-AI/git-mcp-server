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

# Verification script for git-mcp-server API-KIT migration.
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

echo "=== git-mcp-server API-KIT Migration Verification ==="
echo ""

if grep -q '"cloud_dog_api_kit>=' "$PROJECT/pyproject.toml" 2>/dev/null; then
    check "QG-API-1 cloud_dog_api_kit declared in pyproject" 0
else
    check "QG-API-1 cloud_dog_api_kit declared in pyproject" 1
fi

if grep -q "from cloud_dog_api_kit import create_app" "$PROJECT/src/git_mcp_server/api_server.py" 2>/dev/null; then
    check "QG-API-2 api_server uses create_app" 0
else
    check "QG-API-2 api_server uses create_app" 1
fi

if grep -q "from cloud_dog_api_kit import create_app" "$PROJECT/src/git_mcp_server/mcp_server.py" 2>/dev/null; then
    check "QG-API-3 mcp_server uses create_app" 0
else
    check "QG-API-3 mcp_server uses create_app" 1
fi

COUNT=$(grep -RIn "FastAPI(" "$PROJECT/src" --include='*.py' 2>/dev/null | wc -l)
check "QG-API-4 no raw FastAPI() construction in src (count=${COUNT})" "$COUNT"

COUNT=$(grep -RIn "register_tool_router" "$PROJECT/src/git_mcp_server" --include='*.py' 2>/dev/null | wc -l)
if [ "$COUNT" -ge 1 ]; then
    check "QG-API-5 tool-router registration path present (hits=${COUNT})" 0
else
    check "QG-API-5 tool-router registration path present (hits=${COUNT})" 1
fi

echo ""
echo "=== RESULTS: ${PASS} passed, ${FAIL} failed ==="
echo ""
if [ "$FAIL" -eq 0 ]; then
    echo "VERDICT: ALL PASS — git-mcp-server API-KIT migration verifier checks are green."
    exit 0
else
    echo "VERDICT: ${FAIL} gate(s) failed — review failures above."
    exit 1
fi
