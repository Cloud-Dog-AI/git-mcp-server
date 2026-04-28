# Build Guide — git-mcp-server

## 1. Prerequisites

- Python 3.10+
- `git`
- Docker + Buildx (for container builds)
- Access to private PyPI (`your-package-index`)
- Vault bootstrap file: `.env.local`

## 2. Local Python Environment

```bash
cd ./git-mcp-server
python3 -m venv .venv
source .venv/bin/activate
pip install --upgrade pip
pip install -e ".[dev]" --index-url https://your-package-index/simple/
```

## 3. Build Python Package

```bash
source .venv/bin/activate
python3 -m build --no-isolation
```

## 4. Build Docker Image

Use project-standard build script only:

```bash
cd ./git-mcp-server
set -a; source .env.local
bash docker-build.sh latest
```

## 5. Lint and Type Check

```bash
source .venv/bin/activate
python3 -m ruff check src/ tests/
python3 -m ruff format --check src/ tests/
python3 -m mypy src/
```

## 6. Run Tests By Tier

All test commands must include `--env`:

```bash
source .venv/bin/activate
set -a; source .env.local

python3 -m pytest tests/quality --env tests/env-QT -q
python3 -m pytest tests/unit --env tests/env-UT -q
python3 -m pytest tests/system --env tests/env-ST -q
python3 -m pytest tests/integration --env tests/env-IT -q
python3 -m pytest tests/application --env tests/env-AT -q
```

## 7. Run Services Locally

Use project-standard process control script only:

```bash
./server_control.sh --env tests/env-IT start all
./server_control.sh --env tests/env-IT status all
./server_control.sh --env tests/env-IT stop all
```

## Publication Build Reference

### Dockerfile Location

- Dockerfile: `Dockerfile`
- Build script: `docker-build.sh`
- Primary compose/runtime file: `docker-compose.yml`

### Registry Push

```bash
cd ./git-mcp-server
set -a; source .env.local
bash docker-build.sh latest
docker push registry.example.com/cloud-dog/git-mcp-server:latest
```

### Standard Build Arguments and Prerequisites

- `HTTP_PROXY`, `HTTPS_PROXY`, `NO_PROXY` when required by the host environment
- Cloud-Dog CA bundle if private trust material is needed
- Vault-backed credentials for private package indexes and registry access
- BuildKit-enabled Docker where the project build script expects it
