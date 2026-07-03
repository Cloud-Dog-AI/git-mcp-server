# Git MCP Server

`git-mcp-server` exposes Git repository tooling over REST, Web UI, MCP, and A2A-compatible endpoints.

## Publication Quick Start

Prerequisites:

- Docker 24 or newer with BuildKit enabled
- Python 3.12 if you run the package locally
- Public package source: `https://pypi.org/simple/` (override with `PUBLIC_PYPI_INDEX_URL`)

Build the public image (see [EXTERNAL-BUILD.md](EXTERNAL-BUILD.md) for full guidance):

```bash
./docker-build.sh latest --variant public
```

Run the local smoke by executing the shell block in [PUBLICATION-SMOKE.md](PUBLICATION-SMOKE.md).

The smoke run uses [.env.example](.env.example) and probes:

- API: `8078`
- Web: `8079`
- MCP: `8084`
- A2A: `8085`

## Local Development

```bash
python3 -m venv .venv
. .venv/bin/activate
pip install --upgrade pip
pip install --index-url https://pypi.org/simple/ -r requirements.lock
pip install --index-url https://pypi.org/simple/ -e ".[dev]"
```

The cloud-dog platform packages must be resolvable from the active public index.
See [EXTERNAL-BUILD.md](EXTERNAL-BUILD.md) if they are not yet on your public index.

Runtime configuration is loaded from the env file passed to `server_control.sh`, then from shell environment variables, then from `defaults.yaml`.

## Documentation

- [docs/API-REFERENCE.md](docs/API-REFERENCE.md)
- [EXTERNAL-BUILD.md](EXTERNAL-BUILD.md)
- [BUILD.md](BUILD.md)
- [PUBLICATION-SMOKE.md](PUBLICATION-SMOKE.md)
- [.env.example](.env.example)

## Licence

Apache-2.0 - Copyright (c) 2026 Cloud-Dog, Viewdeck Engineering Limited

## Security & Publication Notes

Authentication and authorisation use the platform IDAM credential/cert model; do not commit secrets.
This public source mirror excludes internal operations material; build artefacts (e.g. the UI bundle) are regenerated at build time.
