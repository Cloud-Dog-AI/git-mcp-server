# External Build Guide — git-mcp-server

This guide lets an **external builder** rebuild and smoke-test `git-mcp-server`
from this published source alone, using only public package indexes. It assumes no
access to Cloud-Dog internal infrastructure (no internal PyPI, no internal registry,
no Vault, no preprod hosts).

The public build path uses:

- `Dockerfile.public` — public/external image (single public package index via the `PUBLIC_PYPI_INDEX_URL` build ARG)
- `docker-env.public.example` — example environment with public-safe placeholders
- `docker-build.sh --variant public` — builds `Dockerfile.public`
- `PUBLICATION-SMOKE.md` — local Docker smoke probes
- `requirements.lock` — sealed, index-agnostic pinned dependency lock (reproducible installs; resolves against a single package index that carries the cloud-dog platform packages)

## 1. Prerequisites

| Platform | Requirements |
|----------|--------------|
| Linux    | Docker 24+ with BuildKit; or Python 3.12 for the pure-source path |
| macOS    | Docker Desktop 4.x (BuildKit on by default); or Python 3.12 (`brew install python@3.12`) |
| Windows  | Docker Desktop with WSL2 backend; run the shell snippets from a WSL2 / Git-Bash shell |

The cloud-dog platform packages (`cloud-dog-config`, `cloud-dog-logging`,
`cloud-dog-api-kit`, `cloud-dog-idam`, `cloud-dog-db`, `cloud-dog-jobs`) must be
resolvable from your chosen public index. The default index is public PyPI
(`https://pypi.org/simple/`). If a platform package is not yet on your index,
install it from its public GitHub-mirrored source (`pip install -e .` against
`github.com/cloud-dog-ai/<pkg>`) before building — do NOT add a second index
(`--extra-index-url` is forbidden by the isolation standard, PS-97 v1.1 §3.3 / §4).

## 2. Docker path (recommended)

```bash
# 1. Build the public image (uses Dockerfile.public; default index = public PyPI)
./docker-build.sh latest --variant public

# To point at a different public index (e.g. GitHub Packages or a public mirror):
PUBLIC_PYPI_INDEX_URL=https://pypi.org/simple/ ./docker-build.sh latest --variant public
```

The build ARG `PUBLIC_PYPI_INDEX_URL` is the ONLY package-index input for the
public variant. The default is public PyPI; nothing points at an internal index,
registry, or hostname, and no `--extra-index-url` is used (single `--index-url`).

```bash
# 2. Smoke-test the built image locally (see PUBLICATION-SMOKE.md for the full block)
TAG=latest bash -c "$(sed -n '/^```bash/,/^```/p' PUBLICATION-SMOKE.md | sed '1d;$d')"
```

The smoke run starts the container with `.env.example` and probes the API (8078),
Web (8079), MCP (8084), and A2A (8085) surfaces. Auth-gated `401/403/405` and
redirects count as PASS — they prove the surface is up and routing.

## 3. Pure-source / package path (no Docker)

```bash
python3.12 -m venv .venv
. .venv/bin/activate            # Windows: .venv\Scripts\activate
python -m pip install --upgrade pip
# Reproducible install from the lock (single public index)
python -m pip install --index-url https://pypi.org/simple/ -r requirements.lock
# Editable install of the service itself
python -m pip install --index-url https://pypi.org/simple/ -e .

# Configure and run
cp docker-env.public.example .env
# edit .env: set CLOUD_DOG__GIT__API_KEY, JWT_* issuer/audience, DEFAULT_REMOTE, etc.
./server_control.sh --env .env start all
./server_control.sh --env .env status all
```

`requirements.lock` is sealed and index-agnostic: it carries no index URL and no
credentials. Resolve it against a single package index that publishes the
cloud-dog platform packages; do NOT add a second index (`--extra-index-url` is
forbidden by PS-97 v1.1 §3.3 / §4). To regenerate, run pip-tools `compile` over
`pyproject.toml` (py3.12) with `--index-url` pointed at that single index.

## 4. Where evidence goes / how to return results

Write all build/smoke evidence under `./external-build-evidence/` (create it):

```bash
mkdir -p external-build-evidence
./docker-build.sh latest --variant public 2>&1 | tee external-build-evidence/build.log
# run the smoke block, capturing output:
#   ... | tee external-build-evidence/smoke.log
docker inspect --format '{{.Id}}' cloud-dog/git-mcp-server:latest \
  > external-build-evidence/image-digest.txt
```

Return a tarball + checksum to the requester:

```bash
tar -czf git-mcp-external-build-evidence.tar.gz external-build-evidence/
sha256sum git-mcp-external-build-evidence.tar.gz > git-mcp-external-build-evidence.tar.gz.sha256
```

Include in the tarball: `build.log`, `smoke.log`, `image-digest.txt`, and the host
OS / Docker / Python versions (`docker --version`, `python3 --version`).

## 5. Troubleshooting

- **A platform package fails to resolve from the public index** — STOP. Do not add
  `--extra-index-url`. Publish the missing package to your index, or `pip install -e .`
  it from its public GitHub-mirrored source, then re-run. (The cloud-dog platform
  packages are not yet on public PyPI; expect this until the publication chain
  mirrors them — that is a producer-side step, not a builder defect.)
- **TLS / CA errors behind a corporate proxy** — set `HTTP_PROXY` / `HTTPS_PROXY` and
  mount your CA bundle (`CLOUD_DOG_TLS_CA_BUNDLE` / `REQUESTS_CA_BUNDLE`), per
  `docker-env.public.example`.
- **Smoke probe returns 000** — the service is still starting; the smoke script
  retries for up to `SMOKE_ATTEMPTS` (default 120) seconds. Check `docker logs`.
- **Integration tests bind to a git remote** — the IT1.16 remote-fetch test is
  parameterised per PS-97 v1.1 §1.1.5. Set `GIT_MCP_REMOTE_REPO` and
  `IT1_16_REMOTE_HOST` to a public fixture
  (e.g. `github.com/cloud-dog-ai/git-test-project-fixture.git` /
  `github.com`) for the GitHub boundary.
