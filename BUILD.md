# Build Instructions

## Project
`git-mcp-server` - Git workspace automation service with API, Web, MCP, and A2A interfaces.

## Prerequisites
- Python 3.10+
- Git
- Docker with BuildKit support

## Development Setup
```bash
python3 -m venv .venv
source .venv/bin/activate
pip install --upgrade pip
pip install -e ".[dev]"
```

Install the cloud-dog platform packages from your active public index
(default: public PyPI). Use a single `--index-url`; do not add a second index.
```bash
pip install --index-url https://pypi.org/simple/ -e ".[dev]"
```

## Local Configuration
```bash
cat > .env.local <<'ENV'
CLOUD_DOG__API_SERVER__PORT=8078
CLOUD_DOG__WEB_SERVER__PORT=8079
CLOUD_DOG__MCP_SERVER__PORT=8084
CLOUD_DOG__A2A_SERVER__PORT=8085
WORKSPACE_BASE_DIR=./data/workspaces
DEFAULT_REPO_URL=https://example.com/your-repo.git
ENV
```

## Run Locally
```bash
./server_control.sh --env ./.env.local start all
./server_control.sh --env ./.env.local status all
./server_control.sh --env ./.env.local stop all
```

## Run Tests
```bash
python -m pytest tests/quality --env ./.env.test -v
python -m pytest tests/unit --env ./.env.test -v
python -m pytest tests/system --env ./.env.test -v
python -m pytest tests/integration --env ./.env.test -v
python -m pytest tests/application --env ./.env.test -v
```

## Build
### Python Package
```bash
python -m pip install build
python -m build
```

### Docker Container
```bash
./docker-build.sh latest --variant public
```

Build with an explicit public package index and CA inputs:
```bash
PUBLIC_PYPI_INDEX_URL=https://pypi.org/simple/ \
PYPI_USERNAME=build-user \
PYPI_PASSWORD=build-password \
CUSTOM_CA_CERT=./certs/ca.pem \
./docker-build.sh latest --variant public
```

## Docker Push
```bash
docker tag cloud-dog/git-mcp-server:latest registry.example.com/team/git-mcp-server:latest
docker push registry.example.com/team/git-mcp-server:latest
```

## Configuration
This service resolves configuration from shell variables, the env file supplied to `server_control.sh`, and `defaults.yaml`.

## Secret-Backed Configuration
Keep deployment secrets outside the repository. For local runs, pass a
project-owned env file with `./server_control.sh --env ./path/to/env-file ...`
or set `GIT_MCP_BOOTSTRAP_ENV_FILE` to an operator-managed env file.
