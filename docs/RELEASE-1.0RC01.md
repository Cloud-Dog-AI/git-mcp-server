---
doc-id: RELEASE-1.0RC01
project: git-mcp-server
generated: 2026-06-25T05:40:27Z
release: 1.0RC01-git-mcp-server
lane: W28E-1804C
---

# git-mcp-server — 1.0RC01 Release Notes

## Release Scope

`1.0RC01-git-mcp-server` closes Stream-C for git-mcp-server WebUI, E2E, local Docker, preprod deployment, live browser proof, sibling sentinel regression, and release evidence.

## Delivered

- WebUI source of truth updated in `cloud-dog-ai-ui-monorepo/apps/git-mcp` at commit `66f3c5fd04a4926eb0be0ab2cbad675c01e6d780`.
- Service backend release built from `git-mcp-server` main commit `342c8c1b336389e2f3afa5e5400ad3ed9b5d33cd`.
- Final image pushed to `registry.cloud-dog.net:443/cloud-dog/git-mcp-server:latest`.
- Registry digest: `sha256:3d0a97e618f6a49bc638c4255ea6b0f52155e93ce7595003764cc1f9034a2f84`.
- Runtime image ID: `sha256:9e712451f6270261a9e57504c77311647a584a3e6b4017a2d10aa14001f8c01b`.
- Preprod deployed through Terraform target `docker_image.gitmcpserver` and `docker_container.gitmcpserver0`.

## Validation

- Local full WebUI Playwright: `109 passed, 9 skipped`.
- Local Docker browser proof: `12 passed`.
- Live target browser proof: `12 passed`.
- Live cookie front-door smoke: PASS.
- Live sibling sentinel smoke: `4 passed`.
- Backend focused unit/admin/API/MCP/A2A/audit/job packs: PASS.

## Evidence

Raw closeout artifacts are under:

`cloud-dog-ai-platform-standards/working/evidence/W28E-1804C/current/`

The final validator, checksum replay, requirements map, release tag proof, preprod digest proof, and no-Gitea/GitHub build-boundary proof are the authoritative closeout record.
