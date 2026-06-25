# Agent Instruction — Docker Build, Test & Run (git-mcp-server)

**Project:** `git-mcp-server`
**Version:** 1.0
**Date:** 2026-02-20
**Standard:** PS-91 (Docker Containerization)
**Ports:** API=8585, MCP=8586 (PORT-REGISTRY block 8585–8589)

---

## RULES COMPLIANCE — NON-NEGOTIABLE

This instruction is governed by PS-91 Docker Containerization Standards and PORT-REGISTRY.md.
You have standing approval to execute all steps without per-step approval. GET ON WITH IT.

---

## 1. Prerequisites

Before starting, confirm:

```bash
cd /opt/iac/Development/cloud-dog-ai/git-mcp-server

# 1. All local tests pass
pytest tests/unit/ --env tests/env-UT -x -q
pytest tests/system/ --env tests/env-ST -x -q
pytest tests/integration/ --env tests/env-IT -x -q
pytest tests/application/ --env tests/env-AT -x -q
pytest tests/security/ --env tests/env-QT -x -q

# 2. Quality gates
ruff check src/ tests/
ruff format --check src/ tests/

# 3. Docker files exist (all 8)
for f in Dockerfile docker-build.sh docker-entrypoint.sh healthcheck.sh \
         docker-compose.yml .dockerignore docker-env.example server_control.sh; do
  test -f "$f" && echo "OK: $f" || echo "MISSING: $f"
done
```

**If any prerequisite fails, STOP. Fix it first.**

---

## 2. Docker Files Inventory

| File | Lines | Purpose |
|------|-------|---------|
| `Dockerfile` | 73 | Multi-stage, proxy/CA, **BuildKit secret for private PyPI**, non-root (appuser UID 10001) |
| `docker-build.sh` | 96 | Build + Vault PyPI creds → pip.conf secret + registry tag + CA cert + log |
| `docker-entrypoint.sh` | 71 | Modes: all/api/mcp/status/test/shell + SIGTERM trap |
| `healthcheck.sh` | 4 | Checks `/health` on API port 8585 |
| `docker-compose.yml` | 59 | Individual (api, mcp) + all-in-one profile |
| `.dockerignore` | 18 | Excludes tests, secrets, caches, `.pip.conf.build` |
| `docker-env.example` | 29 | All CLOUD_DOG__GIT__ variables documented |
| `server_control.sh` | 108 | PID-managed start/stop for api + mcp |

---

## 3. Build the Docker Image

### 3.1 Private PyPI Authentication

The `cloud_dog_*` platform packages are hosted on `pypi.cloud-dog.net` which requires **Basic auth** (HTTP 401 without credentials). The build script handles this automatically:

1. `docker-build.sh` sources credentials from `PYPI_USERNAME`/`PYPI_PASSWORD` env vars, or **auto-resolves from Vault** (`vault.dev.repository.pypi.username` / `.password`).
2. It generates a temporary `.pip.conf.build` file with the authenticated `extra-index-url`.
3. The Dockerfile uses `RUN --mount=type=secret,id=pip_conf,target=/etc/pip.conf` — credentials are available during `pip install` but **never baked into any image layer**.
4. The temp `.pip.conf.build` is deleted after the build completes.

**Security:** `docker history` will NOT reveal any PyPI credentials because BuildKit secret mounts are excluded from image layers.

### 3.2 Run the Build

```bash
cd /opt/iac/Development/cloud-dog-ai/git-mcp-server

chmod +x docker-build.sh

# Option A: Auto-resolve credentials from Vault (recommended)
./docker-build.sh

# Option B: Explicit credentials
PYPI_USERNAME=admin PYPI_PASSWORD=<from-vault> ./docker-build.sh

# Verify image exists
docker images | grep git-mcp-server

# Verify no secrets baked in
docker history cloud-dog/git-mcp-server:latest --no-trunc | grep -i "api_key\|password\|token\|secret\|pypi"
# EXPECTED: NO OUTPUT
```

### 3.3 If the Build Fails

| Symptom | Cause | Fix |
|---------|-------|-----|
| `ERROR: PYPI_USERNAME and PYPI_PASSWORD required` | Vault unreachable or env-vault missing | Set `PYPI_USERNAME`/`PYPI_PASSWORD` env vars manually |
| `401 Unauthorized` during pip install | Secret mount not working | Ensure `DOCKER_BUILDKIT=1` and Docker ≥ 18.09 |
| `Could not find a version that satisfies cloud_dog_config` | Private index not reachable | Check `--network=host` is being used, proxy is set |
| SSL/cert error on pypi.cloud-dog.net | CA cert not installed | Verify `CUSTOM_CA_CERT` path, check `--trusted-host` |
| General pip timeout | Proxy not configured | Export `HTTP_PROXY` / `HTTPS_PROXY` before build |

---

## 4. Create docker-env.local

Generate the local Docker environment file from Vault:

```bash
cd /opt/iac/Development/cloud-dog-ai/git-mcp-server

# Source Vault credentials
source /opt/iac/Development/cloud-dog-ai/env-vault

# Query Vault for API key
API_KEY=$(vault kv get -mount=cloud_dog_ai -format=json config | \
  python3 -c "import json,sys; d=json.load(sys.stdin)['data']['data']['dev']; print(d['keys']['api_key'])" 2>/dev/null || echo "")

# Create docker-env.local (gitignored)
cat > docker-env.local << EOF
# git-mcp-server — Local Docker Environment
# AUTO-GENERATED from Vault — do NOT commit

CLOUD_DOG__GIT__API_SERVER__PORT=8585
CLOUD_DOG__GIT__API_SERVER__HOST=0.0.0.0
CLOUD_DOG__GIT__MCP_SERVER__PORT=8586
CLOUD_DOG__GIT__MCP_SERVER__HOST=0.0.0.0

CLOUD_DOG__GIT__API_KEY=${API_KEY}

CLOUD_DOG__GIT__WORKSPACE_ROOT=/app/data/workspaces
CLOUD_DOG__GIT__DEFAULT_REMOTE=https://git.cloud-dog.net

VAULT_ADDR=https://vault0.cloud-dog.net
VAULT_TOKEN=${VAULT_TOKEN}
CLOUD_DOG__VAULT__MOUNT_POINT=cloud_dog_ai
CLOUD_DOG__VAULT__CONFIG_PATH=config

CLOUD_DOG__GIT__LOG__LEVEL=INFO
CLOUD_DOG__GIT__AUDIT__ENABLED=true
EOF

echo "docker-env.local created. API_KEY=${API_KEY:+SET}${API_KEY:-EMPTY}"
```

**WARNING:** If `API_KEY` is empty, the Vault key `vault.dev.keys.api_key` may not exist. For local testing, use the seed key generated by the server at startup (written to `.tmp-tests/it/seed_api_key.txt`).

---

## 5. Run Docker Container (Local, --network host)

### 5.1 Start All Servers

```bash
docker run -d \
  --name git-mcp-test \
  --network host \
  --env-file docker-env.local \
  -v "$(pwd)/logs:/app/logs" \
  -v "$(pwd)/data:/app/data" \
  cloud-dog/git-mcp-server:latest all
```

### 5.2 Wait for Health

```bash
echo "Waiting for git-mcp-server..."
timeout 30 bash -c 'until curl -fs http://localhost:8585/health >/dev/null 2>&1; do sleep 1; done' \
  && echo "API healthy" || echo "TIMEOUT — check: docker logs git-mcp-test"

timeout 10 bash -c 'until curl -fs http://localhost:8586/health >/dev/null 2>&1; do sleep 1; done' \
  && echo "MCP healthy" || echo "MCP not ready (may be expected if no MCP health endpoint)"
```

### 5.3 Verify Container State

```bash
# Running as non-root?
docker exec git-mcp-test whoami
# EXPECTED: appuser

# Process list
docker exec git-mcp-test ps aux

# Check logs
docker logs git-mcp-test --tail 20
```

---

## 6. Docker Smoke Tests

### 6.1 Health Check

```bash
curl -s http://localhost:8585/health | python3 -m json.tool
# EXPECTED: {"status": "ok", ...}
```

### 6.2 Tool Catalogue

```bash
# Get seed API key from container logs or env
API_KEY=$(grep -oP 'api_key=\K[^ ]+' logs/api.log 2>/dev/null || echo "")

curl -s http://localhost:8585/api/v1/tools \
  -H "x-api-key: ${API_KEY}" | python3 -m json.tool | head -30
# EXPECTED: list of git tools
```

### 6.3 Tool Execution (git_status on empty workspace)

```bash
curl -s -X POST http://localhost:8585/api/v1/tools/git_init \
  -H "x-api-key: ${API_KEY}" \
  -H "Content-Type: application/json" \
  -d '{"path": "/tmp/docker-test-repo"}' | python3 -m json.tool

curl -s -X POST http://localhost:8585/api/v1/tools/git_status \
  -H "x-api-key: ${API_KEY}" \
  -H "Content-Type: application/json" \
  -d '{"workspace": "/tmp/docker-test-repo"}' | python3 -m json.tool
# EXPECTED: clean status of empty repo
```

### 6.4 Authentication Rejection

```bash
curl -s -w "\n%{http_code}\n" http://localhost:8585/api/v1/tools \
  -H "x-api-key: invalid-key"
# EXPECTED: 401 or 403
```

---

## 7. Run Existing Test Suites (Bare Metal — Regression Check)

After Docker testing, confirm existing tests still pass (the port change in server_control.sh log path must not break anything):

```bash
cd /opt/iac/Development/cloud-dog-ai/git-mcp-server

# UT — no server needed
pytest tests/unit/ --env tests/env-UT -x -q
# EXPECTED: 25 passed

# ST — no server needed
pytest tests/system/ --env tests/env-ST -x -q
# EXPECTED: 10 passed

# IT — starts own servers on port 18585 (does NOT conflict with Docker on 8585)
pytest tests/integration/ --env tests/env-IT -x -v
# EXPECTED: 8 passed (IT1.9, IT1.10 may skip if remote unreachable)

# AT — starts own servers on port 18685
pytest tests/application/ --env tests/env-AT -x -v
# EXPECTED: 5 passed

# QT — no server needed
pytest tests/security/ --env tests/env-QT -x -q
# EXPECTED: 4 passed
```

**IMPORTANT:** IT/AT tests start their own servers on ports 18585/18685 via `server_control.sh`. These do NOT conflict with the Docker container on port 8585 because the ports are different. Both can run simultaneously.

---

## 8. Docker Compose Testing

### 8.1 Individual Containers

```bash
cd /opt/iac/Development/cloud-dog-ai/git-mcp-server

# Create .env from docker-env.local
cp docker-env.local .env

# Start individual services
docker compose up -d api mcp

# Verify
docker compose ps
curl -s http://localhost:8585/health
curl -s http://localhost:8586/health

# Stop
docker compose down
```

### 8.2 All-in-One Container

```bash
docker compose --profile all-in-one up -d all-in-one

curl -s http://localhost:8585/health
curl -s http://localhost:8586/health

docker compose --profile all-in-one down
```

---

## 9. Stop and Clean Up

```bash
docker stop git-mcp-test 2>/dev/null; docker rm git-mcp-test 2>/dev/null
```

---

## 10. Quality Gates — All Must Pass

| # | Gate | Command | Expected |
|---|------|---------|----------|
| 1 | Image builds | `./docker-build.sh` | exit 0 |
| 2 | Image exists | `docker images \| grep git-mcp` | 1 row |
| 3 | No secrets in image | `docker history ... \| grep secret` | no output |
| 4 | Container starts | `docker run --network host ...` | running |
| 5 | Non-root user | `docker exec ... whoami` | appuser |
| 6 | Health check passes | `curl http://localhost:8585/health` | 200 |
| 7 | Tool catalogue returns | `curl .../api/v1/tools` | 200 + tools |
| 8 | Auth rejection works | `curl ... -H "x-api-key: bad"` | 401/403 |
| 9 | UT regression | `pytest tests/unit/ --env UT` | 25 passed |
| 10 | IT regression | `pytest tests/integration/ --env IT` | 8+ passed |
| 11 | All tiers pass | UT+ST+IT+AT+QT | 52+ passed |
| 12 | Compose individual | `docker compose up api mcp` | both healthy |

---

## 11. Troubleshooting

| Symptom | Cause | Fix |
|---------|-------|-----|
| Build fails with proxy error | `HTTP_PROXY` not set | `export HTTP_PROXY=...` before build |
| Build fails with cert error | CA cert not found | Check `CUSTOM_CA_CERT` path |
| Container exits immediately | Entrypoint crash | `docker logs git-mcp-test` |
| Health check timeout | Server not starting | Check `/app/logs/api.log` inside container |
| Permission denied on logs | Non-root can't write | `chmod 777 logs/ data/` on host |
| Port already in use | Another service on 8585 | `lsof -ti :8585` and kill it |

---

## 12. Absolute Prohibitions

1. DO NOT bake secrets into the Docker image.
2. DO NOT change the port from 8585/8586 in defaults.yaml (use PORT-REGISTRY.md).
3. DO NOT run the container as root in production.
4. DO NOT skip the health check wait before running tests.
5. DO NOT log to /tmp/ — log to /app/logs/.
6. DO NOT use `docker build` without `--network=host` (proxy required).
