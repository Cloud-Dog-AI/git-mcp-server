# API Reference

`git-mcp-server` exposes Git repository operations through REST, MCP, A2A, and
the local web UI.

## Local Endpoints

Start the service with the public smoke or build instructions in
[../PUBLICATION-SMOKE.md](../PUBLICATION-SMOKE.md) and [../BUILD.md](../BUILD.md).

| Surface | Default local port | Purpose |
| --- | ---: | --- |
| REST API | 8078 | HTTP API for repository operations and health checks. |
| Web UI | 8079 | Browser UI for local repository tooling. |
| MCP | 8084 | MCP tool surface for Git operations. |
| A2A | 8085 | Agent-to-agent event and task surface. |

## Configuration

Use [../.env.example](../.env.example) as the public local template. Keep tokens,
SSH keys, and repository credentials in your shell environment or local secret
store; do not commit them.

## Smoke Check

```bash
./docker-build.sh latest --variant public
```

Then run the command block in [../PUBLICATION-SMOKE.md](../PUBLICATION-SMOKE.md)
to probe the REST, Web, MCP, and A2A endpoints.
