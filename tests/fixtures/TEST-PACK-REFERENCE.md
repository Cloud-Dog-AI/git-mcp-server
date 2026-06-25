---
template-id: T-TPR
template-version: 1.0
applies-to: tests/fixtures/TEST-PACK-REFERENCE.md
project: git-mcp-server
doc-last-updated: 2026-06-23
---

# git-mcp-server — Test Pack Reference (PS-TEST-PACKS-REGISTRY v1.0)

This service references central test packs by `pack_id` from
`cloud-dog-ai-platform-standards/test-packs/REGISTRY.tsv`. **This service references central packs;
unpacked dump contents are not copied into this repository.** git-mcp has no service-specific zip in the
Test-Design-Audit-Jun26 dump — its service dump is markdown-only (`gitmcpserver/E2E git-mcp-server.md`,
folded as the supplement E2E acceptance rows `AT-E2E-a..s` in `docs/TESTS.md` §4 per the W28E-1804A
operator NEW-AT decision).

## Pack consumption

| pack_id | pack_kind | source_zip (registry) | sha256 (registry) | unpacked_preview | local REQ/UC/TEST binding |
|---|---|---|---|---|---|
| `TP-COMMON` | shared | `…/common-test-suite.zip` | `3af79a7b19fcd3d4161ad9bff8b79f3fa6dce07e4c8ebf9de74058fd5511c754` | `…/common-test-suite_unpacked/common` | common auth/RBAC/audit negatives → `CS-001`–`CS-020`, `FR-016`, `FR-022`, `FR-023`; tests `UT1.65`, `UT1.56`, `IT1.2`–`IT1.4` |
| `TP-INTEGRATION-EXAMPLES` | cross-service | `…/integration-examples-test-suite.zip` | `50f8aa7463c83635527098ddca8f1f2186085d66cd7516c432aa05052a6d9467` | `…/integration-examples-test-suite_unpacked/integration-examples` | cross-service repo/MCP/A2A flows → `FR-003`, `FR-004`, `FR-009`; tests `IT1.5`, `IT1.6`, `IT1.11`, `IT1.15` |
| _git-mcp service-specific zip_ | — | `N/A` | `N/A` | `N/A` | **N/A** — service dump is markdown-only; folded as `AT-E2E-a..s` design rows (no zip to register; per PS-TEST-PACKS-REGISTRY §6 git-mcp row) |

## Fixture materialization policy (Stream-B)

Repository fixtures are materialised by **environment reference** (gitea test repos / local filesystem
paths declared in `tests/env-*`), not by committed copies. Stream-B records generated fixture paths,
materialization commands, and cleanup proof in `fixture-materialization-ledger.tsv`.

## Cleanup policy

Generated files, ephemeral workspaces, and local test state are removed after each tier run (TTL/GC for
ephemeral workspaces; `tests/env-*` scoped temp dirs cleaned on teardown). No test path reaches outside the
sandbox (see lane `05-no-ext-dep-audit.tsv`).
