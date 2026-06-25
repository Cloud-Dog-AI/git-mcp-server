# W28A-148E-R6B Git UI Workflow Final Closeout

Date: 2026-05-11

## Scope

- Service repo: `git-mcp-server`
- UI app: `cloud-dog-ai-ui-monorepo/apps/git-mcp`
- Deployment target: `gitmcpserver0` only
- No IMAP, DB, LLM, Ragflow, generation, public publication, or full estate rerun was run.

## Changes

- Preserved A2A routed health and agent-card paths in the web proxy to avoid UI console 404s.
- Routed `/mcp-console`, `/api-docs`, and `/a2a-console` to the web service with exact high-priority Traefik rules so API/MCP/A2A `PathPrefix` routers do not steal SPA deep links.
- Removed the optional A2A console agent-card fetch that caused browser-level 404 noise.
- Surfaced tag push status immediately in the tag manager so the W28A-870 q-r workflow observes the push action status.

## Commits

- `git-mcp-server`: `1d76e54` `fix: preserve a2a health proxy route`
- `git-mcp-server`: `41910c9` `fix: preserve a2a agent card proxy route`
- `cloud-dog-ai-ui-monorepo`: `4befc4d` `fix(git-mcp): avoid a2a agent card 404`
- `cloud-dog-ai-ui-monorepo`: `890aed3` `fix(git-mcp): surface tag push status immediately`
- Deployment repo: `383b8693` `fix: route git mcp ui deep links to web`

Note: UI commits `1f69b38` and `129ce52` were an intermediate duplicate-heading attempt and revert; the final passing state relies on the deployment deep-link route and shared `McpConsole` headings.

## Deploy Proof

- Final image tag: `registry.cloud-dog.net:443/cloud-dog/git-mcp-server:w28a-148e-r6b5-41910c9`
- Final registry digest: `sha256:6032bf05fde9d1b3a598d0ba21c24d92aa9d8e943194513fd16c6dae45225409`
- Final container: `d89e054e32ab09cd411db5bc421082b3550c6ff322091632e095fc7418057784`
- Runtime image: `sha256:7ed66836bd001011f0f45d248eaab1e3fb96d4254b5be94c4131aa414c4a4f2a`
- Runtime state: `status=running health=healthy started=2026-05-12T05:35:04.812008931Z`
- Health: `{"status":"ok","application":"git-mcp-server-web","version":"0.1.0","env_file":null,"checks":{}}`

Targeted Terraform only:

```text
terraform plan/apply -target=docker_image.gitmcpserver -target=docker_container.gitmcpserver0
terraform plan/apply -target=docker_container.gitmcpserver0
```

## Test Results

Focused:

```text
T19/T20/T21 ui-review2: 3 passed (7.9s)
W28A-119D API docs: 1 passed (4.6s)
W28A458 T11 a2a console: 1 passed (4.2s)
W28A-870 sections q-r: 1 passed (11.2s)
```

Supporting checks:

```text
pytest tests/unit/UT1.46_TagPush/test_tag_push.py: 1 passed in 3.14s
pytest tests/unit/UT1.56_WebUiDelivery/test_web_ui_delivery.py: 4 passed in 4.30s
npm run build: passed
```

Full Git W28A-102 shard:

```text
../../node_modules/.bin/playwright test -c playwright.preprod.config.ts --workers=1 --reporter=list
67 passed (3.4m)
```

## Residual Blockers

- None for the six R6B residual Git full-shard failures.
- `npm run typecheck` remains blocked by pre-existing Git UI type errors in `GroupsPage.tsx`, `RepositoryBrowserPage.tsx`, and `TagManagerPage.tsx` field variant typings; this did not block build or the passing shard.
