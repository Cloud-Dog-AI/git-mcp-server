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

# Verification script for git-mcp-server LOGGING migration.
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

echo "=== git-mcp-server LOGGING Migration Verification ==="
echo ""

if grep -q '"cloud_dog_logging>=' "$PROJECT/pyproject.toml" 2>/dev/null; then
    check "QG-LOG-1 cloud_dog_logging declared in pyproject" 0
else
    check "QG-LOG-1 cloud_dog_logging declared in pyproject" 1
fi

if grep -q "from cloud_dog_logging import get_audit_logger, setup_logging" "$PROJECT/src/git_tools/audit/logger.py" 2>/dev/null; then
    check "QG-LOG-2 audit logger wired to cloud_dog_logging" 0
else
    check "QG-LOG-2 audit logger wired to cloud_dog_logging" 1
fi

COUNT=$(grep -RInE "logging\.getLogger|basicConfig\(" "$PROJECT/src" --include='*.py' 2>/dev/null | wc -l)
check "QG-LOG-3 no bespoke logging bootstrap in src (count=${COUNT})" "$COUNT"

COUNT=$(grep -RInE "\bprint\(" "$PROJECT/src" --include='*.py' 2>/dev/null | wc -l)
check "QG-LOG-4 no print() logging in src (count=${COUNT})" "$COUNT"

if [ -f "$PROJECT/src/git_tools/audit/events.py" ]; then
    check "QG-LOG-5 audit event model present" 0
else
    check "QG-LOG-5 audit event model present" 1
fi

echo ""
echo "=== RESULTS: ${PASS} passed, ${FAIL} failed ==="
echo ""
if [ "$FAIL" -eq 0 ]; then
    echo "VERDICT: ALL PASS — git-mcp-server LOGGING migration verifier checks are green."
    exit 0
else
    echo "VERDICT: ${FAIL} gate(s) failed — review failures above."
    exit 1
fi
