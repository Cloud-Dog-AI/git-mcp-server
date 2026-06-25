# QUALITY GATE — git-mcp-server

**Date:** 2026-02-19  
**Package version:** 0.1.0  
**Scope:** Source quality, tool coverage, tests, build, config-delegation compliance

## Summary

- Result: PASS
- Evidence source: direct command execution in this repository

## Verification Evidence

### 1. Tool coverage

Command:
```bash
python3 - <<'PY'
import sys, tempfile, pathlib
sys.path.insert(0, 'src')
from git_tools.tools.registry import ToolRegistry
from git_tools.workspaces.manager import WorkspaceManager
wm = WorkspaceManager(pathlib.Path(tempfile.mkdtemp()))
r = ToolRegistry(wm)
print('tools', len(r.list_tools()))
PY
```

Output:
```text
tools 50
```

### 2. Lint

Command:
```bash
python3 -m ruff check src/ tests/
```

Output:
```text
All checks passed!
```

### 3. Format

Command:
```bash
python3 -m ruff format --check src/ tests/
```

Output:
```text
99 files already formatted
```

### 4. Type checking

Command:
```bash
python3 -m mypy src/
```

Output:
```text
Success: no issues found in 42 source files
```

### 5. Full test suite

Command:
```bash
python3 -m pytest tests/ --env UT --env ST --env IT --env AT --env QT -q
```

Output:
```text
....................................................                     [100%]
52 passed in 10.42s
```

### 6. Config delegation guardrail

Command:
```bash
grep -rn "os\.environ\|import hvac\|overlay_secrets" src/git_tools/ --include="*.py" | grep -v __pycache__ | grep -v conftest
```

Output:
```text
# no output (zero hits)
```

### 7. Build

Command:
```bash
python3 -m build --no-isolation
ls -lh dist
```

Output:
```text
Successfully built git_mcp_server-0.1.0.tar.gz and git_mcp_server-0.1.0-py3-none-any.whl
total 72K
-rw-r--r-- 1 gary gary 7.6K ... git_mcp_server-0.1.0-py3-none-any.whl
-rw-r--r-- 1 gary gary  61K ... git_mcp_server-0.1.0.tar.gz
```

### 8. Import check

Command:
```bash
python3 - <<'PY'
import sys
sys.path.insert(0, 'src')
import git_mcp_server
print('import-ok', git_mcp_server.__version__)
PY
```

Output:
```text
import-ok 0.1.0
```

## Notes

- Integration tests run against live API/MCP processes started by `tests/integration/conftest.py`.
- Integration remote scenarios use Git network transport via `git daemon` on localhost.
