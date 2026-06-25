---
lane: W28C-1710a
service: git-mcp-server
date: 2026-06-14T17:37:15Z
---

# git-mcp-server — Knowledge Preservation Warranty (W28C-1710a)

## Programme summary for this service

| Metric | Value |
|---|---:|
| Archived docs merged | 2 |
| Total archived-lines carried forward | 73 |
| Topics preserved (PRESENT) | 35 |
| Topics lost (residual) | 0 |
| Successor docs updated | 2 |
| Lines added to successor docs | +91 |
| Lines removed from successor docs | -0 |
| **residual-loss-lines** | **0** |

## Per-doc SHA256 chain (successor pre/post)

| Successor canonical | pre-sha256(12) | post-sha256(12) | pre-lines | post-lines | +lines | -lines | residual-loss-lines |
|---|---|---|---:|---:|---:|---:|---:|
| `docs/API-REFERENCE.md` | `04e0e9d73167` | `7f12b39f63f7` | 52 | 101 | +49 | -0 | 0 |
| `docs/CHANGELOG.md` | `02ce17ac499c` | `cf46cbf4255f` | 11 | 53 | +42 | -0 | 0 |

## Per-archived-doc topic preservation

| Archived | archived-lines | archived-sha256(12) | Successor | topics-recorded | topics-present | residual-loss-topics |
|---|---:|---|---|---:|---:|---:|
| `archive/2026-06-12/API.md` | 40 | `75ac77532ba9` | `docs/API-REFERENCE.md` | 16 | 16 | 0 |
| `archive/2026-06-12/TASKS.md` | 33 | `9d891ac46dd0` | `docs/CHANGELOG.md` | 19 | 19 | 0 |

## Attestation

I warrant that:

1. Every archived doc under `git-mcp-server/archive/2026-06-12/` has been merged verbatim into the named successor canonical doc(s) — full content preserved as a marked `## Recovered domain content` section.
2. Archive contents have NOT been modified during this lane (sha256 of every archived file matches the pre-merge fingerprint).
3. No successor doc had any line removed during this lane (delta-lines-removed = 0 per row).
4. residual-loss-lines = 0 for this service.
5. No `tests/` file modified; no CI-critical file modified.
6. Per-doc topic checklists at `cloud-dog-ai-platform-standards/working/evidence/W28C-1710a/per-doc/git-mcp-server/<archived-name>.topics.tsv` — every row marked PRESENT.

**HAVE_ALL_REQUIREMENTS_BEEN_MET_FOR_GIT_MCP_SERVER_RECOVERY**: YES

---
Operator countersignature: ___________________________ Date: __________
