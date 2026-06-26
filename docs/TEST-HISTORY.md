---
template-id: T-TSH
template-version: 1.0
applies-to: docs/TEST-HISTORY.md
registry: service
required: must-have
when-applicable: ""
template-last-updated: 2026-06-12
template-owner: platform-standards

project: git-mcp-server
doc-last-updated: 2026-06-12
doc-git-commit: 579922dcddd9b6faa97f58b8096e325611289620
doc-git-branch: main
doc-source-shas: []
doc-age-policy: indefinite
doc-conformance-stamp: 2026-06-12T12:00:00Z
---

# git-mcp-server — TEST-HISTORY

> **Template version:** T-TSH v1.0 — appended to by `scripts/update-test-state.py`. Roll-archive to `archive/test-history/<YYYY-MM>.md` when >500 lines.

## Runs (most recent first)

### 2026-06-25T05:40:27Z
- Commit: `342c8c1b336389e2f3afa5e5400ad3ed9b5d33cd` (main)
- Lane: `W28E-1804C` Stream-C WebUI/E2E/local-Docker/preprod/1.0RC01
- Totals: UI full local 109 / P 109 / F 0 / S 9; focused UI 15 / P 15 / F 0; backend focused 41 / P 41 / F 0; backend admin parity 5 / P 5 / F 0; backend API/MCP/A2A/jobs local-Docker 5 / P 5 / F 0; audit unit 7 / P 7 / F 0; live target browser 12 / P 12 / F 0; sibling sentinels 4 / P 4 / F 0
- Delta: release candidate `1.0RC01-git-mcp-server` preprod image deployed from registry digest `sha256:3d0a97e618f6a49bc638c4255ea6b0f52155e93ce7595003764cc1f9034a2f84`; local image ID `sha256:9e712451f6270261a9e57504c77311647a584a3e6b4017a2d10aa14001f8c01b`.

### 2026-06-17T11:09:44.985823+00:00
- Commit: `e7c21dceea17f7882a0e362e40ee768c37b19128` (W28C-1714-100pct-fix)
- Totals: 2 / P 2 / F 0 / S 0
- Delta: new-fails 0 | newly-green 3

### 2026-06-13T10:59:11.580337+00:00
- Commit: `58cc47cee40ce6f62821a69837ec033d2ff00881` (main)
- Totals: 295 / P 292 / F 3 / S 0
- Delta: new-fails 3 | newly-green 3

### 2026-06-13T10:18:36.450899+00:00
- Commit: `58cc47cee40ce6f62821a69837ec033d2ff00881` (main)
- Totals: 286 / P 283 / F 3 / S 0
- Delta: new-fails 3 | newly-green 0

### 2026-06-12T12:00:00Z
- Commit: `579922dcddd9b6faa97f58b8096e325611289620` (main)
- Totals: N / P n / F n / S n
- Delta: new-fails 0 | newly-green 0
