# W28A-731-R5 — Mandatory Reading Proof (GATE 0 / GATE 0A)

- RULES.md (platform): `/opt/iac/Development/cloud-dog-ai/cloud-dog-ai-platform-standards/RULES.md`
- AGENT-LESSONS.md (platform): `/opt/iac/Development/cloud-dog-ai/cloud-dog-ai-platform-standards/AGENT-LESSONS.md`
- AGENT-BOOTSTRAP-DIRECTIVE.md: `/opt/iac/Development/cloud-dog-ai/cloud-dog-ai-platform-standards/AGENT-BOOTSTRAP-DIRECTIVE.md`
- git-mcp RULES.md: `/opt/iac/Development/cloud-dog-ai/git-mcp-server/RULES.md`
- git-mcp AGENT-LESSONS.md: `/opt/iac/Development/cloud-dog-ai/git-mcp-server/AGENT-LESSONS.md`
- PLATFORM-TLS-PROXY-GUIDANCE.md: `/opt/iac/Development/cloud-dog-ai/cloud-dog-ai-platform-standards/PLATFORM-TLS-PROXY-GUIDANCE.md`

RULES_REREAD: YES
AGENT_LESSONS_REREAD: YES

## Mandatory Reading — version / verifiable anchor (re-read in full this session)

| File | LINES (wc -l) | SHA256(12) | Newest anchor (proves current) |
|---|---|---|---|
| RULES.md | 1192 | 1e04c26f8f81 | §1.2.2 ASSURANCE = coordinator PRIMARY function (binding 2026-06-11) |
| AGENT-LESSONS.md | 2633 | 976cef14a8a4 | §6.109 publication manifest hygiene (W28A-864-R6, 2026-06-11) |
| AGENT-BOOTSTRAP-DIRECTIVE.md | 714 | 651d0179fc81 | v5.4 2026-06-08 (GATE 0 warrant block) |
| git-mcp RULES.md | 236 | 165649f2f7ca | v4.0 W28A-882 trim 2026-06-08 |
| git-mcp AGENT-LESSONS.md | 698 | 077d39b6830c | A131-FIX Traefik /api→API cookie/key routing (2026-05-06) |
| PLATFORM-TLS-PROXY-GUIDANCE.md | 145 | abf232091aec | 2026-02-22 (transparent ICAP proxy; corporate CA in trust store) |

RULES.md version string: v2.7. AGENT-LESSONS.md version string: v3.17.

## READING PROOF — five lane-specific answers copied from the files

1. RULES §3.2 (delivery order): native/local tests → local `docker-build.sh` + local Docker smoke → commit/merge to canonical `origin/main` → ONLY THEN explicitly authorised preprod deploy/proof; a remote Docker daemon is NOT build/test proof.
2. RULES §3.2.1/§3.2.2: firewall/network changes ONLY via Terraform (remote-shorewall module); NEVER iptables/shorewall/nftables directly.
3. RULES §1.4.1: `grep -rn "os.environ.get\|os.environ\[\|os.getenv" src/` MUST return 0; config via `cloud_dog_config` only (carve-outs: 4 bootstrap VAULT_* names + CLOUD_DOG_ENV_FILES).
4. AGENT-LESSONS §6.94: a green evidence pack is not delivery — the build must succeed, the feature must be in the BUILT image, and it must render LIVE (origin/main commit → registry digest → terraform-deployed container → live browser).
5. git-mcp AGENT-LESSONS (A131-FIX / Cluster-B): Traefik routes `/api/v1/*` directly to the API server, bypassing the web-server cookie proxy — the API tier must independently validate the cookie session and enforce RBAC.

## GATE 0A acknowledgement (reopened username/password lane)

- Read the reopened coordinator-audit decision (2026-06-11 login-mismatch reopening): `cloud-dog-ai-platform-standards/working/evidence/W28A-731-R5-COORDINATOR-AUDIT-...-GITMCP-LOGIN-MISMATCH-2026-06-11.md`.
- Required live outcome: username/password login on https://gitmcpserver0.cloud-dog.net (not an API-key-only form). DONE + live-proven.
- No new auth mode / new credentials / new Vault path / new Terraform env / new sidecar were invented. The read-write/read-only demo defaults (BlueRiverChair/GreenRiverDesk) mirror accepted chat-client (727-R5) + notification-agent (730-R5).
- The deployed proof chain is origin/main commit `e486098` → registry digest `sha256:30288f97…` → terraform-deployed `gitmcpserver0` → live browser screenshots/traces.

## Commands used to read / verify

```bash
wc -l RULES.md AGENT-LESSONS.md AGENT-BOOTSTRAP-DIRECTIVE.md git-mcp-server/RULES.md git-mcp-server/AGENT-LESSONS.md PLATFORM-TLS-PROXY-GUIDANCE.md
sha256sum <each> | cut -c1-12
```
