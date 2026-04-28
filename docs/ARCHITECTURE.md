# Git MCP Server — Architecture

**Version:** 2.0  
**Date:** 2026-04-21  
**Scope:** Current delivered architecture verified from `src/`, `defaults.yaml`, and the linked UI routes and tests.

## OV1. Overview

### OV1.1 Service Purpose
`git-mcp-server` is the platform's controlled repository-operations boundary. It exposes Git, workspace, file, admin, job, and operator-observability capabilities across API, MCP, Web, and A2A surfaces while keeping repository logic in the shared `git_tools` domain layer.

Requirements: `SV1.1`, `SV1.2`, `SV1.3`, `BO1.2`, `BR1.1`  
Tests: `IT1.5`, `IT1.6`, `PW1.1`, `PW1.9`

## SA1. System Architecture

### SA1.1 Runtime Topology
The system is composed of four runtime surfaces:

- API: authenticated REST routes for tool execution, admin CRUD, jobs, and UI support
- MCP: HTTP and JSON-RPC-compatible tool discovery and execution over the shared registry
- Web: SPA delivery, auth endpoints, reverse-proxy style API forwarding, and routed operator pages
- A2A: authenticated compatibility surface with config-event streaming and a bounded skill card

Each surface depends on the same configuration, workspace, admin, and registry runtime families instead of carrying duplicated repository logic.

Requirements: `SV1.1`, `BO1.2`, `FR1.2`, `FR1.3`, `FR1.4`, `FR1.14`  
Tests: `IT1.1`, `IT1.5`, `IT1.11`, `PW1.1`, `PW1.8`

## CC1. Core Components

### CC1.1 Transport Adapters
Transport adapters live under `src/git_mcp_server/`:

- `api_server.py` wires configuration, auth, admin routes, jobs routes, and UI support routes
- `mcp_server.py` exposes MCP root discovery, JSON-RPC compatibility, and `/mcp/tools`
- `web_server.py` serves auth, status, and API-proxy behaviour for the browser runtime
- `web_ui.py` serves the SPA build and `/runtime-config.js`
- `a2a_server.py` exposes A2A root, health, config events, and skill-card handlers

Requirements: `SV1.1`, `BR1.1`, `FR1.2`, `FR1.3`, `FR1.4`, `FR1.14`, `NF1.1`  
Tests: `IT1.1`, `IT1.5`, `IT1.11`, `UT1.56`, `PW1.1`, `PW1.8`

### CC1.2 Shared Domain Runtime
Shared domain components live under `src/git_tools/`:

- `tools/registry.py` defines the 63 delivered tool contracts and shared dispatch
- `workspaces/manager.py` and `workspaces/ref_context.py` manage workspace lifecycle and refs
- `git/*` implements repository workflows
- `files/*` implements scoped file, directory, search, and reusable edit or validation helpers
- `security/*` implements profile access, RBAC helpers, git auth, and scope enforcement

Requirements: `SV1.2`, `BR1.2`, `BR1.5`, `FR1.5` through `FR1.11`, `FR1.18`, `NF1.1`  
Tests: `UT1.5` through `UT1.50`, `ST1.1` through `ST1.8`, `AT1.1`, `AT1.3`, `AT1.5`

### CC1.3 Admin, Jobs, and Persistence Runtime
Administrative state and long-running work are handled by:

- `admin/runtime.py` for profiles, users, groups, managed API keys, role bindings, and config events
- `jobs/runtime.py` for queue-backed repo-open, git-diff, and file-batch work
- `db/runtime.py` and `db/models.py` for platform DB initialisation and runtime state

Requirements: `BO1.4`, `BR1.3`, `FR1.9`, `FR1.12`, `FR1.13`, `FR1.17`, `CS1.6`  
Tests: `IT1.13`, `IT1.14`, `IT1.15`, `UT1.54`, `UT1.55`, `UT1.27`, `ST1.11`

## DM1. Data Model

### DM1.1 Persistent and Derived State
Persistent relational state is intentionally small:

- `GitPlatformDbState` records platform database runtime state
- managed API-key metadata, users, groups, and profile state are runtime-managed structures
- audit records are persisted through the logging and audit layer
- workspace state is filesystem-backed, with persistent workspace metadata stored beside workspace directories

Requirements: `BO1.4`, `FR1.17`, `NF1.5`  
Tests: `UT1.27`, `ST1.10`, `ST1.11`, `ST1.12`

## SW1. State Machines and Workflows

### SW1.1 Workspace and Ref Lifecycle
The workspace flow is:

1. resolve profile and repository source
2. create or restore workspace
3. optionally resolve branch, tag, or commit ref
4. execute file or git operations under the current ref mode
5. close or retain workspace based on workspace mode and TTL

Branch refs remain writable; tag and commit refs are read-only. Persistent workspaces reuse deterministic IDs and are restored on restart.

Requirements: `BO1.1`, `BR1.2`, `FR1.5`, `FR1.6`, `UC1.1`, `CS1.4`, `NF1.3`  
Tests: `UT1.4`, `UT1.5`, `UT1.6`, `UT1.7`, `ST1.1`, `ST1.2`, `ST1.12`, `AT_PROFILE_LIFECYCLE`

### SW1.2 Repository Mutation Workflows
Repository mutation workflows are implemented as explicit tool calls for stage or reset, commit, branch operations, merge or rebase control, stash operations, tags, and recovery restore. Conflict handling is explicit through list, resolve, continue, and abort operations.

Requirements: `FR1.7`, `FR1.8`, `FR1.10`, `FR1.11`, `UC1.2`, `UC1.3`, `UC1.4`, `CS1.4`, `NF1.4`  
Tests: `UT1.14` through `UT1.21`, `UT1.38` through `UT1.50`, `ST1.3` through `ST1.8`, `AT1.1`, `AT1.2`, `AT1.3`, `AT1.5`

## CP1. Critical Processes

### CP1.1 Tool Execution Pipeline
API and MCP calls both follow the same critical path:

1. authenticate request
2. resolve roles and capabilities
3. enforce profile and tool access
4. resolve workspace and scope
5. dispatch to the shared tool registry
6. emit audit metadata
7. return a structured envelope

Requirements: `BR1.1`, `FR1.2`, `FR1.3`, `FR1.8`, `UC1.2`, `CS1.2`  
Tests: `IT1.4`, `IT1.5`, `IT1.6`, `IT1.7`, `PW1.1`

### CP1.2 Managed Job Pipeline
Longer-running work is routed through `cloud_dog_jobs`:

1. submit repo-open, git-diff, or file-batch job
2. persist queue metadata and audit
3. dispatch through the worker
4. expose status, progress, cancel, retry, and delete controls

Requirements: `BO1.3`, `FR1.9`, `NF1.3`, `NF1.6`  
Tests: `IT1.15`, `UT1.55`, `UT1.57`

## DF1. Data Flow

### DF1.1 Audit, Log, and Config-Event Flow
Tool and job actions emit structured audit metadata. UI support endpoints project audit and operational logs back to the SPA. Profile CRUD publishes config-change events through the admin event hub, and A2A subscribers consume those events through `/a2a/events/config`.

Requirements: `BR1.3`, `FR1.4`, `FR1.15`, `FR1.16`, `UC1.6`, `NF1.5`  
Tests: `IT1.8`, `IT1.13`, `ST1.10`, `PW1.7`

## IP1. Integration Points

### IP1.1 External Dependencies
The service integrates with:

- Git remotes for clone, fetch, pull, push, and tag transport
- the workspace filesystem for cloned repositories and persistent metadata
- SQL backends for platform DB state and queue storage
- Vault-backed or environment-backed configuration inputs
- built SPA assets from the Git MCP UI app

Requirements: `FR1.7`, `FR1.14`, `FR1.17`, `NF1.2`  
Tests: `IT1.9`, `IT1.10`, `IT1.16`, `ST1.11`, `UT1.56`

## SE1. Security Architecture

### SE1.1 Authentication, Authorisation, and Secret Handling
Security controls are layered:

- authentication modes vary by surface and include API key, JWT, bearer token, cookie session, and enterprise roles
- authorisation combines admin roles, tool-category RBAC, profile-scoped access, protected-branch checks, and managed API-key capabilities
- workspace and file access enforce scope and deny-pattern boundaries
- secret-like fields are redacted from audit and log output

Requirements: `BO1.1`, `BO1.4`, `CS1.1`, `CS1.2`, `CS1.3`, `CS1.4`, `CS1.5`, `CS1.6`  
Tests: `IT1.2`, `IT1.3`, `IT1.4`, `IT1.7`, `QT1.1`, `QT1.2`, `UT1.10`, `UT1.11`, `UT1.13`, `UT1.51`

## SP1. Scalability and Performance

### SP1.1 Bounded Execution Model
The service favours bounded, operator-oriented execution:

- request timeouts are configured through the runtime model
- workspace and path scope constrain search and mutation breadth
- long-running work is moved into the managed jobs runtime
- A2A capability is intentionally bounded to a small delivered skill card

Requirements: `SV1.3`, `FR1.9`, `NF1.6`  
Tests: `UT1.49`, `UT1.55`, `IT1.15`

## RR1. Reliability and Resilience

### RR1.1 Restore and Recovery Behaviour
Reliability is provided through persistent workspace metadata, explicit recovery flows, stash-backed recovery support, audit retention controls, and database migration discipline.

Requirements: `BO1.3`, `FR1.5`, `FR1.11`, `FR1.17`, `NF1.3`, `NF1.4`, `NF1.5`  
Tests: `ST1.8`, `ST1.9`, `ST1.10`, `ST1.11`, `ST1.12`, `UT1.20`, `UT1.50`

## MO1. Monitoring and Observability

### MO1.1 Operator Visibility
Observability is surfaced through:

- health and status routes
- audit persistence and operational logs
- UI support endpoints for version, settings, audit, and logs
- routed browser pages for audit and system operations

Requirements: `BO1.3`, `BO1.5`, `FR1.15`, `FR1.16`, `UC1.6`, `NF1.5`  
Tests: `IT1.1`, `IT1.8`, `ST1.10`, `UT1.57`, `PW1.7`, `PW1.9`

## CM1. Configuration Management

### CM1.1 Configuration Precedence
Configuration is loaded with deterministic precedence from environment variables, env files, config files, defaults, and Vault-backed values, then bound into the global model used by all runtimes.

Requirements: `FR1.1`, `NF1.2`  
Tests: `UT1.1`, `UT1.2`, `UT1.3`, `QT_VAULT`

## DA1. Deployment Architecture

### DA1.1 Runtime Packaging and Routed Delivery
The project supports local and containerised deployment with separate listeners for API, MCP, Web, and A2A. The web runtime serves the built SPA and proxies API-family paths while preserving reserved service routes outside the SPA fallback.

Requirements: `FR1.14`, `FR1.17`, `NF1.7`  
Tests: `UT1.56`, `UT1.57`, `ST1.11`, `PW1.8`

## AI1. API and Interface Specifications

### AI1.1 API Surface
The API surface includes health, tool catalogue and execution, admin CRUD, managed jobs, and UI support endpoints such as `/ui/version`, `/ui/status`, `/settings`, `/settings/runtime-config`, `/audit`, and `/logs`.

Requirements: `FR1.2`, `FR1.9`, `FR1.12`, `FR1.15`  
Tests: `IT1.1`, `IT1.14`, `IT1.15`, `UT1.57`

### AI1.2 MCP Surface
The MCP surface includes `/mcp`, JSON-RPC `initialize` or `tools/list`, and `/mcp/tools` execution over the 63 delivered tool contracts.

Requirements: `FR1.3`, `BR1.1`  
Tests: `IT1.5`, `IT1.6`, `UT1.25`, `PW1.1`

### AI1.3 A2A Surface
The A2A surface includes `/a2a`, `/a2a/health`, `/a2a/events/config`, and the delivered A2A skill card.

Requirements: `FR1.4`, `BR1.3`, `UC1.6`, `CS1.1`  
Tests: `AT1.6`, `IT1.11`, `IT1.13`

### AI1.4 Web Surface
The Web surface includes `/runtime-config.js`, SPA fallback delivery, and routed operator pages for repository, admin, developer, and system workflows.

Requirements: `BO1.5`, `BR1.4`, `FR1.14`, `FR1.15`, `UC1.2`, `UC1.3`, `UC1.4`, `UC1.5`, `UC1.6`, `NF1.7`  
Tests: `UT1.56`, `UT1.57`, `PW1.8`, `PW1.9`

## TS1. Testing Strategy

### TS1.1 Test Layers
The implementation is covered through unit, system, integration, and application tests in this repository, plus Playwright browser workflows in the linked UI monorepo. Library helpers are covered directly in unit tests even when they are not exposed as standalone runtime contracts.

Requirements: `BR1.5`, `FR1.18`, `NF1.8`  
Tests: `UT1.23`, `UT1.24`, `UT1.35`, `UT1.36`, `UT1.37`, `QT_DOCS`, `QT_TRACEABILITY`

## RD1. Related Documentation

### RD1.1 Traceability Set
The canonical traceability set for this release is:

- `docs/REQUIREMENTS.md`
- `docs/TASKS.md`
- `docs/TESTS.md`
- `docs/API-REFERENCE.md`
- `docs/PARAMETERS.md`
- `docs/ENV-REFERENCE.md`
- `README.md`

Requirements: `NF1.8`  
Tests: `QT_DOCS`, `QT_TRACEABILITY`
