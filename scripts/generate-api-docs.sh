#!/usr/bin/env bash
# Generate docs/openapi.json and docs/API-REFERENCE.md from the OpenAPI spec.
# Usage: ./scripts/generate-api-docs.sh [--check]
#   --check: verify docs are fresh (exit 1 if stale)
set -euo pipefail

DOCS_DIR="$(cd "$(dirname "$0")/.." && pwd)/docs"
OPENAPI_JSON="$DOCS_DIR/openapi.json"
API_REF="$DOCS_DIR/API-REFERENCE.md"

# Source: running service or local server
OPENAPI_URL="${OPENAPI_SOURCE_URL:-https://gitmcpserver0.cloud-dog.net/openapi.json}"

CHECK_MODE=false
[[ "${1:-}" == "--check" ]] && CHECK_MODE=true

echo "[docs] Fetching OpenAPI spec from $OPENAPI_URL"
TEMP_SPEC=$(mktemp)
curl -sk "$OPENAPI_URL" > "$TEMP_SPEC" 2>/dev/null

# Validate JSON
python3 -c "import json; json.load(open('$TEMP_SPEC'))" || { echo "FATAL: invalid JSON from $OPENAPI_URL"; rm -f "$TEMP_SPEC"; exit 1; }

if $CHECK_MODE; then
    # Compare normalized JSON (ignore formatting differences)
    STALE=$(python3 -c "
import json, sys
live = json.load(open('$TEMP_SPEC'))
saved = json.load(open('$OPENAPI_JSON'))
# Compare paths and info (ignore server-specific fields)
if set(live.get('paths',{}).keys()) != set(saved.get('paths',{}).keys()):
    print('STALE: path sets differ')
elif live.get('info',{}).get('version') != saved.get('info',{}).get('version'):
    print('STALE: version differs')
else:
    print('FRESH')
" 2>/dev/null)
    echo "[docs] $STALE"
    rm -f "$TEMP_SPEC"
    [[ "$STALE" == "FRESH" ]] && exit 0 || exit 1
fi

# Save openapi.json
python3 -c "import json; json.dump(json.load(open('$TEMP_SPEC')), open('$OPENAPI_JSON','w'), indent=2)"
echo "[docs] Saved $OPENAPI_JSON"

# Generate API-REFERENCE.md from the spec
python3 - "$TEMP_SPEC" "$API_REF" <<'PY'
import json, sys
spec = json.load(open(sys.argv[1]))
out = open(sys.argv[2], "w")

info = spec.get("info", {})
out.write(f"# API Reference — {info.get('title', 'git-mcp-server')}\n\n")
out.write(f"OpenAPI version: {spec.get('openapi', '?')}\n")
out.write(f"Service version: {info.get('version', '?')}\n\n")
out.write("This document is auto-generated from the live OpenAPI spec.\n\n")
out.write("---\n\n")

paths = spec.get("paths", {})
out.write(f"## Endpoints ({len(paths)})\n\n")
for path in sorted(paths):
    methods = paths[path]
    for method in sorted(methods):
        if method in ("parameters", "servers", "summary", "description"):
            continue
        detail = methods[method]
        summary = detail.get("summary", detail.get("operationId", ""))
        out.write(f"### `{method.upper()} {path}`\n\n")
        if summary:
            out.write(f"{summary}\n\n")
        params = detail.get("parameters", [])
        if params:
            out.write("**Parameters:**\n\n")
            for p in params:
                out.write(f"- `{p.get('name', '?')}` ({p.get('in', '?')}): {p.get('description', '')}\n")
            out.write("\n")
        responses = detail.get("responses", {})
        if responses:
            out.write("**Responses:**\n\n")
            for code in sorted(responses):
                desc = responses[code].get("description", "")
                out.write(f"- `{code}`: {desc}\n")
            out.write("\n")
        out.write("---\n\n")

schemas = spec.get("components", {}).get("schemas", {})
if schemas:
    out.write(f"## Schemas ({len(schemas)})\n\n")
    for name in sorted(schemas):
        out.write(f"### `{name}`\n\n")
        props = schemas[name].get("properties", {})
        for pname, pdef in props.items():
            ptype = pdef.get("type", pdef.get("$ref", "?"))
            out.write(f"- `{pname}`: {ptype}\n")
        out.write("\n")

out.close()
print(f"[docs] Generated {sys.argv[2]}")
PY

rm -f "$TEMP_SPEC"
echo "[docs] Done"
