# 00-reading-proof.md

read_date_utc=2026-06-12T07:07:53Z
READING PROOF: Mandatory files read in full this session.
RULES_REREAD: YES
AGENT-LESSONS-REREAD: YES
AGENT_BOOTSTRAP_DIRECTIVE_REREAD: YES
GATE_0_WARRANT_EMITTED: YES
GATE_0A_ACK_EMITTED: YES
GATE_0B_ACK_EMITTED: YES
GATE_0C_ACK_EMITTED: YES

| file | lines | sha256_12 | newest_anchor |
|---|---:|---|---|
| `RULES.md` | 1192 | `1e04c26f8f81` | `2026-06-11T07:20:13+01:00` |
| `AGENT-LESSONS.md` | 2629 | `0daf9c32432d` | `2026-06-11T15:11:18+01:00` |
| `AGENT-BOOTSTRAP-DIRECTIVE.md` | 714 | `651d0179fc81` | `2026-06-08T18:03:52+01:00` |
| `PLATFORM-TLS-PROXY-GUIDANCE.md` | 145 | `abf232091aec` | `2026-02-22T19:44:59+00:00` |
| `git-mcp RULES.md` | 236 | `165649f2f7ca` | `2026-06-08T11:09:08+01:00` |
| `git-mcp AGENT-LESSONS.md` | 698 | `077d39b6830c` | `2026-06-08T10:54:17+01:00` |
| `COMMON-GATE-0-MANDATORY-READING-WARRANT.md` | 55 | `896f6510c50f` | `2026-06-10T13:39:58+01:00` |
| `IDAM-B2 design` | 243 | `a85a66ca0136` | `2026-06-10T14:10:09+01:00` |
| `IDAM-B6 template` | 243 | `cea1efeba2ee` | `` |
| `IDAM Thread-B instructions` | 169 | `bd6f4a101748` | `2026-06-12T07:38:48+01:00` |
| `W28A-936 accepted audit` | 66 | `c37e20c2f0b6` | `2026-06-11T19:54:52+01:00` |
| `W28A-937 sweep instruction` | 175 | `8c07858afaa4` | `2026-06-11T20:09:22+01:00` |

## CONFIRM rule ids
- CONFIRM §1.4.1: no direct env/Vault/config bypass in runtime src; use platform packages.
- CONFIRM §5.1 / §6.14: PC23 chain requires grep, tests, build, docker, push, deploy, live proof.
- CONFIRM §11: final return must include warranty only if truthfully satisfied.

## Folded acknowledgements
GATE 0A ACK — W28A-745: branch-only/local-only/curl-only proof is not sufficient; current origin/main -> image -> deployed container -> live objective must be proven.
GATE 0B ACK — W28A-745: canonical main/latest, clean scoped repos, deployed preprod built from final origin/main/latest commit.
GATE 0C ACK — W28A-745: W28A-936/937 service-tail rows classified in `00A-936-937-service-tail-classification.tsv`.
