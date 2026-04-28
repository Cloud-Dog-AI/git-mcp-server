# Tasks — git-mcp-server

This task register reflects the delivered capability surface verified on 2026-04-21. It exists to satisfy RULES §6.4 traceability: every requirement in `docs/REQUIREMENTS.md` maps to at least one maintained delivery task.

## Current Delivery Tasks

| Task ID | Status | Delivery scope | Requirement IDs |
|---|---|---|---|
| T001 | Complete | Maintain shared transport wiring for API, MCP, Web, and routed service entry points over the common registry and runtime envelope. | SV1.1, SV1.3, BO1.2, BR1.1, FR1.2, FR1.3, NF1.1, NF1.6 |
| T002 | Complete | Maintain configuration loading, typed binding, and runtime startup values for listeners, storage, auth, and workspace settings. | FR1.1, NF1.2 |
| T003 | Complete | Maintain workspace lifecycle, persistent restore, ref resolution, workspace locks, and read-only ref behaviour. | SV1.2, BO1.1, BR1.2, FR1.5, FR1.6, UC1.1, CS1.3, CS1.4, NF1.3 |
| T004 | Complete | Maintain remote git access, clone or reopen flows, and core git workflow operations including branch-aware write paths. | SV1.2, BO1.1, BR1.2, FR1.7, FR1.10, UC1.1, UC1.3, CS1.4, CS1.5, NF1.4 |
| T005 | Complete | Maintain scoped file, directory, search, structured-edit, and validation helper workflows used by the runtime and the reusable library layer. | SV1.2, SV1.3, BR1.2, BR1.5, FR1.8, FR1.18, UC1.2, CS1.3 |
| T006 | Complete | Maintain merge, rebase, stash, tag, conflict-resolution, and recovery workflows. | SV1.2, BO1.3, BR1.2, FR1.11, UC1.4 |
| T007 | Complete | Maintain surface authentication, RBAC, profile-scoped access, branch-protection checks, and secret-handling rules. | BO1.1, BO1.2, FR1.6, FR1.7, CS1.1, CS1.2, CS1.3, CS1.4, CS1.5, CS1.6 |
| T008 | Complete | Maintain admin runtime behaviour for profile CRUD, user and group CRUD, API-key metadata, RBAC binding, and capability-segmented admin access. | SV1.2, BO1.4, BR1.3, FR1.12, FR1.13, UC1.5, CS1.2, CS1.6 |
| T009 | Complete | Maintain managed-job queue integration, queue status, job lifecycle operations, and batch file-mutation job handling. | SV1.2, BO1.3, BR1.2, FR1.9, UC1.2, NF1.3, NF1.6 |
| T010 | Complete | Maintain audit emission, correlation propagation, audit persistence, log projection, and operator observability paths. | SV1.2, BO1.3, BR1.3, FR1.15, FR1.16, UC1.6, CS1.5, NF1.5 |
| T011 | Complete | Maintain SPA delivery, runtime-config generation, API proxy routes, and routed operator pages for repository and admin workflows. | SV1.1, SV1.2, BO1.2, BO1.5, BR1.4, FR1.14, FR1.15, UC1.2, UC1.3, UC1.4, UC1.5, UC1.6, NF1.7 |
| T012 | Complete | Maintain platform database initialisation, health reporting, and migration behaviour for configured backends. | BO1.4, FR1.17, NF1.5 |
| T013 | Complete | Maintain A2A-compatible root and health routes, config-event streaming, and the delivered A2A skill card. | SV1.1, SV1.3, BO1.2, BR1.3, FR1.4, UC1.6, CS1.1, CS1.6 |
| T014 | Complete | Maintain documentation and traceability integrity across requirements, architecture, tasks, and tests for the delivered surface. | BO1.5, BR1.5, NF1.8 |

## Coverage Check

- Every active requirement prefix in `docs/REQUIREMENTS.md` is assigned to one or more tasks in the table above.
- No task row in this register describes future-only functionality; each row maps to code or routed UI already present in the current source tree.

## Next Review Cycle

1. Refresh this register whenever tool contracts, job contracts, A2A skills, or routed WebUI pages change.
2. Keep `docs/REQUIREMENTS.md`, `docs/ARCHITECTURE.md`, and `docs/TESTS.md` aligned when task ownership or delivered capability moves.
3. Remove or split task rows if the implementation surface changes enough that one row no longer describes a coherent delivered capability family.
