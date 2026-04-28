# git-mcp-server

git-mcp-server is the Cloud-Dog AI Git workflow service, exposing repository/session operations, branch-scoped file tooling, and administrative profile/RBAC controls through REST, MCP, and A2A interfaces backed by platform packages.

## 1. Quick Start

### Prerequisites

- Python 3.11+
- Git
- Docker + Buildx (for container build/deploy)
- Access to the internal PyPI registry and Vault bootstrap file (`<workspace>/env-vault`)

### Install

```bash
cd <workspace>/git-mcp-server
python3 -m venv .venv
source .venv/bin/activate
pip install --upgrade pip
pip install -e ".[dev]" --index-url https://<internal-pypi>/simple/
```

### Run

```bash
set -a; source <workspace>/env-vault; set +a
./server_control.sh --env tests/env-IT start all
./server_control.sh --env tests/env-IT status all
```

### Test

```bash
set -a; source <workspace>/env-vault; set +a
python3 -m pytest tests/quality tests/security --env tests/env-QT -v
python3 -m pytest tests/unit --env tests/env-UT -v
python3 -m pytest tests/integration --env tests/env-IT -v
python3 -m pytest tests/application --env tests/env-AT -v
```

### Full WebUI Gate

```bash
cd <workspace>/cloud-dog-ai-ui-monorepo/apps/git-mcp
CI=true npx playwright test --workers=1
cd <workspace>/git-mcp-server
```

### Build Container Image

```bash
set -a; source <workspace>/env-vault; set +a
./docker-build.sh latest
```

### Build Web UI Bundle

```bash
cd <workspace>/cloud-dog-ai-ui-monorepo
npm run build --workspace=apps/git-mcp

cd <workspace>/git-mcp-server
mkdir -p ui
rm -rf ui/dist
cp -r ./apps/git-mcp/dist ui/dist
```

## 2. Architecture Overview

The project is split into transport/runtime (`src/git_mcp_server/`) and domain/tooling (`src/git_tools/`) layers, with all Git/file logic testable without booting HTTP servers.

- Architecture detail: [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md)

## 3. API Interfaces

| Interface | Base Path | Contract Doc |
|---|---|---|
| REST API | `/api/v1` (canonical), `/app/v1` (compatibility) | [docs/API-REFERENCE.md](docs/API-REFERENCE.md) |
| MCP HTTP transport | `/mcp/tools` | [docs/API-REFERENCE.md](docs/API-REFERENCE.md) |
| A2A endpoint | `/a2a/health` | [docs/API-REFERENCE.md](docs/API-REFERENCE.md) |
| OpenAPI | `/openapi.json` | [docs/openapi.json](docs/openapi.json) |

## 4. Configuration

- Environment variables and precedence: [docs/ENV-REFERENCE.md](docs/ENV-REFERENCE.md)
- Deployment configuration (Docker, bare metal, Vault): [docs/DEPLOY.md](docs/DEPLOY.md)
- Build setup and validation workflow: [docs/BUILD.md](docs/BUILD.md)

## 5. Platform Packages

| Package | Version Constraint | Role |
|---|---|---|
| `cloud_dog_config` | `>=0.1.0` | Layered config loading and Vault expression resolution |
| `cloud_dog_logging` | `>=0.1.0` | Structured logging and audit integration |
| `cloud_dog_api_kit` | `>=0.1.0` | FastAPI app factory + middleware baseline |
| `cloud_dog_idam` | `>=0.1.0` | API-key/JWT middleware and RBAC engine |
| `cloud_dog_db` | `>=0.1.0` | Database runtime abstraction and health checks |

## 6. Standards Alignment

| Standard Range | Status |
|---|---|
| PS-00 .. PS-19 | ✅ |
| PS-20 .. PS-39 | ✅ |
| PS-40 .. PS-59 | ✅ |
| PS-60 .. PS-79 | ✅ |
| PS-80 .. PS-95 | ✅ |

Primary evidence is maintained in quality/compliance test suites and `working/` run logs.

## 7. Documentation Links

| Document | Path |
|---|---|
| Requirements | [docs/REQUIREMENTS.md](docs/REQUIREMENTS.md) |
| Architecture | [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md) |
| Tests catalogue | [docs/TESTS.md](docs/TESTS.md) |
| Build guide | [docs/BUILD.md](docs/BUILD.md) |
| Deploy guide | [docs/DEPLOY.md](docs/DEPLOY.md) |
| API reference | [docs/API-REFERENCE.md](docs/API-REFERENCE.md) |
| Env reference | [docs/ENV-REFERENCE.md](docs/ENV-REFERENCE.md) |
| OpenAPI snapshot | [docs/openapi.json](docs/openapi.json) |
| Project rules | [RULES.md](RULES.md) |
| Current context summary | [CONTEXT-SUMMARY.md](CONTEXT-SUMMARY.md) |

## 8. Licence

Apache 2.0 — © 2026 Cloud-Dog, Viewdeck Engineering Limited
