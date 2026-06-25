# Agent Instruction — Build git-mcp-server

**Project:** `git-mcp-server`  
**Version:** 0.1.0  
**Date:** 2026-02-18  
**Estimated effort:** 5–8 days  
**Platform packages:** `cloud_dog_config`, `cloud_dog_logging`, `cloud_dog_api_kit`, `cloud_dog_idam`

---

## Current State

Documentation is **100% complete**. No source code exists yet.

| Deliverable | Status |
|-------------|--------|
| `README.md` | ✅ Complete |
| `REQUIREMENTS.md` | ✅ Complete (344 lines, FRs fully defined) |
| `ARCHITECTURE.md` | ✅ Complete (276 lines, module layout defined) |
| `TESTS.md` | ✅ Complete (52 tests: 25 UT + 10 ST + 8 IT + 5 AT + 4 QT) |
| `RULES.md` | ✅ Complete |
| `CONTEXT-SUMMARY.md` | ✅ Complete |
| `pyproject.toml` | ✅ Complete (line-length=120) |
| `defaults.yaml` | ✅ Complete |
| `.env.example` | ✅ Complete |
| `.platform-standards.yml` | ✅ Complete (baseline 1.0.0) |
| `.gitignore` | ✅ Complete |
| `src/` | ❌ **Not started** |
| `tests/` | ❌ **Not started** |
| `Dockerfile` | ❌ **Not started** |
| `server_control.sh` | ❌ **Not started** |
| `STANDARDS.md` | ❌ **Not started** |

---

## Governing Documents (READ ALL before writing any code)

Read in this order:

1. **Platform standards** (normative):
   - `/opt/iac/Development/cloud-dog-ai/cloud-dog-ai-platform-standards/RULES.md`
   - `/opt/iac/Development/cloud-dog-ai/cloud-dog-ai-platform-standards/docs/standards/00-engineering-principles.md`
   - `/opt/iac/Development/cloud-dog-ai/cloud-dog-ai-platform-standards/docs/standards/10-architecture.md`
   - `/opt/iac/Development/cloud-dog-ai/cloud-dog-ai-platform-standards/docs/standards/20-api-contracts.md`
   - `/opt/iac/Development/cloud-dog-ai/cloud-dog-ai-platform-standards/docs/standards/40-logging-observability.md`
   - `/opt/iac/Development/cloud-dog-ai/cloud-dog-ai-platform-standards/docs/standards/70-user-management-idam.md`
   - `/opt/iac/Development/cloud-dog-ai/cloud-dog-ai-platform-standards/docs/standards/80-config-management.md`
   - `/opt/iac/Development/cloud-dog-ai/cloud-dog-ai-platform-standards/docs/standards/90-security.md`
   - `/opt/iac/Development/cloud-dog-ai/cloud-dog-ai-platform-standards/docs/standards/95-testing.md`

2. **Platform package APIs** (read REQUIREMENTS.md + ARCHITECTURE.md for each):
   - `/opt/iac/Development/cloud-dog-ai/cloud-dog-ai-platform-standards/packages/backend/platform-config/`
   - `/opt/iac/Development/cloud-dog-ai/cloud-dog-ai-platform-standards/packages/backend/platform-logging/`
   - `/opt/iac/Development/cloud-dog-ai/cloud-dog-ai-platform-standards/packages/backend/platform-api-kit/`
   - `/opt/iac/Development/cloud-dog-ai/cloud-dog-ai-platform-standards/packages/backend/platform-idam/`

3. **Reference designs** (golden-path implementation guides):
   - `/opt/iac/Development/cloud-dog-ai/cloud-dog-ai-platform-standards/docs/reference-designs/config-reference.md`
   - `/opt/iac/Development/cloud-dog-ai/cloud-dog-ai-platform-standards/docs/reference-designs/logging-reference.md`
   - `/opt/iac/Development/cloud-dog-ai/cloud-dog-ai-platform-standards/docs/reference-designs/api-reference.md`
   - `/opt/iac/Development/cloud-dog-ai/cloud-dog-ai-platform-standards/docs/reference-designs/idam-reference.md`
   - `/opt/iac/Development/cloud-dog-ai/cloud-dog-ai-platform-standards/docs/reference-designs/testing-reference.md`

4. **This project's own docs:**
   - `REQUIREMENTS.md`, `ARCHITECTURE.md`, `TESTS.md`, `RULES.md`

5. **Cross-project guidelines:**
   - `/opt/iac/Development/cloud-dog-ai/cloud-dog-ai-platform-standards/migration/NEW-PROJECT-GUIDELINES.md`

6. **MCP server template** (starter files):
   - `/opt/iac/Development/cloud-dog-ai/cloud-dog-ai-platform-standards/templates/mcp-server/`

---

## Vault & Config Delegation

### Config Delegation Rule (ZERO TOLERANCE)

This project MUST NOT:
1. Read `os.environ` directly for config/credentials in library code
2. Import `hvac` or create Vault clients
3. Parse `CLOUD_DOG_*_VAULT_JSON` env vars
4. Have a `secrets/` module or `config/vault.py`

All config loading is handled by `cloud_dog_config`. The project's `config/loader.py` calls `cloud_dog_config.load()` which handles the full precedence chain including Vault resolution.

### Vault Environment Setup

Before running IT/AT/QT tests or the server itself, source the Vault credentials:

```bash
set -a; source /opt/iac/Development/cloud-dog-ai/env-vault; set +a
```

This sets: `VAULT_ADDR`, `VAULT_TOKEN`, `VAULT_MOUNT_POINT`, `VAULT_CONFIG_PATH`.

### Vault Expression Patterns

In `defaults.yaml` and `config.yaml`, secrets are referenced using `${vault.<section>.<key>}` expressions that `cloud_dog_config` resolves at load time:

```yaml
# Example — NOT for this project, illustrative only:
auth:
  api_key: "${vault.dev.keys.api_key}"
  jwt:
    issuer: "${vault.dev.keys.jwt_issuer}"

database:
  url: "${vault.dev.databases.providers.postgresql.url}"
```

The Vault structure is at `cloud_dog_ai/config/dev.*`. Key sections:
- `dev.keys` — API keys, JWT secrets
- `dev.databases.providers` — DB connection strings
- `dev.models` — LLM/embedding model configs (24 models)
- `dev.storage` — S3, WebDAV, FTP, Google Drive credentials
- `dev.channels` — notification channels
- `dev.email` — SMTP credentials
- `dev.redis` — Redis/Valkey connection details

For git-mcp-server specifically, you will need:
- `dev.keys.api_key` — for API key auth
- `dev.databases.providers` — if using PostgreSQL for profile/audit persistence

---

## Build Order (implement in this exact sequence)

### Phase 1 — Scaffold (Day 1)

1. **Create `src/git_tools/__init__.py`** and all sub-package `__init__.py` files per ARCHITECTURE.md § 2
2. **Create `src/git_mcp_server/__init__.py`** and server sub-packages
3. **Create `tests/` directory structure** matching TESTS.md (UT/ST/IT/AT/QT hierarchy with test IDs)
4. **Create `tests/conftest.py`** — copy from template at `templates/mcp-server/tests/conftest.py`, adapt for this project. MUST enforce `--env` flag.
5. **Create `tests/env-UT`** and `tests/env-ST`** — non-secret config for unit and system tests
6. **Create `Dockerfile`** — copy from `templates/mcp-server/Dockerfile`, adapt
7. **Create `server_control.sh`** — copy from `templates/mcp-server/server_control.sh`, adapt
8. **Create `STANDARDS.md`** — document which PS standards are followed

### Phase 2 — Config & Logging (Day 2)

9. **`src/git_tools/config/loader.py`** — `cloud_dog_config` integration:
   ```python
   from cloud_dog_config import load as load_config
   
   def get_config() -> GlobalConfig:
       return load_config(
           defaults_yaml="defaults.yaml",
           config_yaml="config.yaml",
       )
   ```
10. **`src/git_tools/config/models.py`** — Pydantic config models for all sections in `defaults.yaml` (server, auth, storage, workspace, profiles, rbac)
11. **`src/git_tools/audit/logger.py`** — `cloud_dog_logging` audit writer (JSONL)
12. **`src/git_tools/audit/events.py`** — typed audit event definitions
13. **Write UT1.1–UT1.4** (config tests) and **UT1.12–UT1.13** (audit tests)
14. **Run:** `ruff check src/ && pytest tests/unit/ --env UT`

### Phase 3 — Security & RBAC (Day 3)

15. **`src/git_tools/security/rbac.py`** — `cloud_dog_idam` RBAC integration
16. **`src/git_tools/security/scope.py`** — path scope + protected branches policy
17. **Write UT1.9–UT1.11** (security tests)
18. **Run:** `ruff check src/ && pytest tests/unit/ --env UT`

### Phase 4 — Workspaces & Git (Days 3–4)

19. **`src/git_tools/workspaces/manager.py`** — create/lease/cleanup workspaces
20. **`src/git_tools/workspaces/locks.py`** — per-workspace filelock
21. **`src/git_tools/workspaces/ref_context.py`** — branch/tag/commit → mode resolver
22. **`src/git_tools/git/repo.py`** — GitPython abstraction
23. **`src/git_tools/git/operations.py`** — branch/commit/push/pull
24. **`src/git_tools/git/tags.py`** — tag CRUD
25. **`src/git_tools/git/conflicts.py`** — conflict detection/resolution
26. **`src/git_tools/git/recovery.py`** — stash/recovery-branch/patch bundle
27. **Write UT1.5–UT1.8** (workspace tests) and **UT1.14–UT1.20** (git tests)
28. **Run:** `ruff check src/ && pytest tests/unit/ --env UT`

### Phase 5 — File Operations (Day 5)

29. **`src/git_tools/files/io.py`** — safe IO, atomic writes, locking
30. **`src/git_tools/files/search.py`** — content search with regex/glob
31. **`src/git_tools/files/edit/text.py`** — text edits
32. **`src/git_tools/files/edit/json_yaml.py`** — structured JSON/YAML edits
33. **`src/git_tools/files/edit/xml_html.py`** — XML/HTML edits
34. **`src/git_tools/files/edit/markdown.py`** — Markdown section edits
35. **Write UT1.21–UT1.24** (file tests)
36. **Run:** `ruff check src/ && pytest tests/unit/ --env UT`

### Phase 6 — Tool Definitions & Server (Day 6)

37. **`src/git_tools/tools/`** — all MCP tool definitions with Pydantic schemas
38. **`src/git_mcp_server/api_server.py`** — FastAPI via `cloud_dog_api_kit.create_app()`
39. **`src/git_mcp_server/mcp_server.py`** — MCP transport (stdio/HTTP-SSE)
40. **`src/git_mcp_server/auth/middleware.py`** — `cloud_dog_idam` auth middleware
41. **`src/git_mcp_server/admin/endpoints.py`** — profile CRUD admin endpoints
42. **`src/git_mcp_server/main.py`** — entrypoint
43. **Write UT1.25** (tool schema test) + **ST1.1–ST1.10** (system tests)
44. **Run:** `ruff check src/ && pytest tests/ --env UT --env ST`

### Phase 7 — Integration & Quality (Days 7–8)

45. **Write IT1.1–IT1.8** (integration tests — require git remote)
46. **Write AT1.1–AT1.5** (application workflow tests)
47. **Write QT1.1–QT1.4** (security/quality tests)
48. **Run full suite:** `pytest tests/ --env UT --env ST --env IT --env AT --env QT`

---

## Verification Commands (run after EVERY phase)

```bash
cd /opt/iac/Development/cloud-dog-ai/git-mcp-server

# 1. Lint
ruff check src/ tests/

# 2. Format
ruff format --check src/ tests/

# 3. Type check
mypy src/

# 4. Config delegation check — MUST return zero hits
grep -rn "os\.environ\|import hvac\|overlay_secrets" src/git_tools/ --include="*.py" | grep -v __pycache__ | grep -v conftest

# 5. No hardcoded values
grep -rn "127\.0\.0\.1\|localhost\|password.*=.*['\"]" src/ --include="*.py" | grep -v __pycache__ | grep -v "# " | grep -v defaults

# 6. Tests (progressively expand tiers)
pytest tests/unit/ --env UT -v
pytest tests/ --env UT --env ST -v
# IT/AT/QT require: source /opt/iac/Development/cloud-dog-ai/env-vault
pytest tests/ --env UT --env ST --env IT --env AT --env QT -v

# 7. Build
python -m build --no-isolation
```

---

## Quality Checks (must ALL pass before declaring done)

### Standards Compliance

- [ ] Every `.py` file has the standard file header (licence, ownership, description, standard)
- [ ] UK English throughout (code, docs, comments, error messages)
- [ ] `src/git_tools/` has NO imports from FastAPI, uvicorn, or MCP transport
- [ ] `src/git_mcp_server/` has NO business logic (only dispatch + auth)
- [ ] Config loads via `cloud_dog_config` — no bespoke loader
- [ ] Logging via `cloud_dog_logging` — no `print()`, no bespoke logger
- [ ] Auth via `cloud_dog_idam` — no bespoke auth middleware
- [ ] API via `cloud_dog_api_kit` — no bespoke FastAPI factory
- [ ] All error responses match PS-20 envelope: `{ok, result, warnings, errors, meta}`
- [ ] Health endpoint at `GET /health` per PS-20
- [ ] Correlation IDs propagate through all layers

### Package Adoption Checks

Run these greps to verify platform package usage:

```bash
# cloud_dog_config used for config loading
grep -r "cloud_dog_config" src/git_tools/config/ --include="*.py"
# Expected: at least loader.py imports from cloud_dog_config

# cloud_dog_logging used for logging
grep -r "cloud_dog_logging" src/git_tools/audit/ --include="*.py"
# Expected: logger.py imports from cloud_dog_logging

# cloud_dog_api_kit used for FastAPI
grep -r "cloud_dog_api_kit" src/git_mcp_server/ --include="*.py"
# Expected: api_server.py imports create_app or similar

# cloud_dog_idam used for auth
grep -r "cloud_dog_idam" src/ --include="*.py"
# Expected: rbac.py and middleware.py import from cloud_dog_idam
```

### Test Quality

- [ ] All 52 tests defined in TESTS.md have corresponding test files
- [ ] UT tests use mocks — no external services
- [ ] ST tests use real git repos — no mocking of git
- [ ] IT tests use real git remote + API
- [ ] All tests require `--env` flag
- [ ] Each test directory follows `UT1.1_<TestName>/test_<name>.py` convention

---

## Done Criteria

You are done when ALL of the following are true:

1. `ruff check src/ tests/` — "All checks passed!"
2. `ruff format --check src/ tests/` — no reformatting needed
3. `mypy src/` — no errors
4. Config delegation grep returns zero hits
5. All 52 tests have corresponding test files
6. UT + ST tests pass locally
7. `python -m build` produces a wheel
8. `STANDARDS.md` exists documenting PS alignment
9. `.platform-standards.yml` exists with baseline 1.0.0
10. `Dockerfile` exists and follows PS-90 (non-root, healthcheck)
11. `server_control.sh` exists and works
12. Library/server separation enforced (grep confirms no FastAPI in `git_tools/`)
13. All 4 platform packages are imported and used correctly
14. Health endpoint returns structured response
15. Audit events written in JSONL format with correlation IDs

---

## Anti-Patterns (DO NOT)

1. **DO NOT** create a bespoke config loader — use `cloud_dog_config`
2. **DO NOT** create a bespoke auth system — use `cloud_dog_idam`
3. **DO NOT** use `print()` for logging — use `cloud_dog_logging`
4. **DO NOT** create a bespoke FastAPI app — use `cloud_dog_api_kit.create_app()`
5. **DO NOT** read `os.environ` directly in library code for config/credentials
6. **DO NOT** hardcode any values (ports, paths, credentials, URLs)
7. **DO NOT** put business logic in the server layer
8. **DO NOT** skip the `--env` enforcement in conftest.py
9. **DO NOT** use American English (colour not color, serialise not serialize)
10. **DO NOT** fabricate test results or skip writing real test assertions
