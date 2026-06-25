# git-mcp-server — RULES.md

**Version:** 4.0 (W28A-882 trim)
**Date:** 2026-06-08
**Supersedes:** v3.0 (2026-04-13)

## Common Rules

This project follows the [Cloud-Dog AI Platform Common Rules](../cloud-dog-ai-platform-standards/RULES.md) v2.7+.
Common rules are NOT restated here; consult central for: integrity (§1), environment+config (§2),
server+process management (§3), code+change management (§4), testing (§5), documentation (§6),
repo structure (§7), operational controls (§8), security boundaries (§9), infrastructure
protection (§10), Vault path verification (§11), implementation truthfulness (§12),
sandbox dispatch preconditions (§13, W28A-882 Phase F), completion standards (§14), mandatory reading (§15).

Mandatory reading before any work in this repository:

1. Platform RULES.md — `../cloud-dog-ai-platform-standards/RULES.md` (binding contract)
2. Platform AGENT-LESSONS.md — `../cloud-dog-ai-platform-standards/AGENT-LESSONS.md` (cross-platform knowledge)
3. This file — project-specific rules below
4. AGENT-BOOTSTRAP-DIRECTIVE.md — `../cloud-dog-ai-platform-standards/working/AGENT-BOOTSTRAP-DIRECTIVE.md`
5. This project's `AGENT-LESSONS.md` (git-mcp-specific incidents, including Gitea/GitLab token
   wiring (A131-FIX-1), seed API key regeneration on container rebuild, and Traefik `/api/` cookie-vs-API-key
   routing).

Cross-references to roll-ups in central AGENT-LESSONS.md:

- Docker verification checklist (build, managed-stack, health, endpoints, `pip show`, bespoke grep)
  is centralised in `cloud-dog-ai-platform-standards/AGENT-LESSONS.md` §4.11 (rolled up from
  git-mcp's former §13).
- Non-root container + bind-mount writability discipline is centralised in
  `cloud-dog-ai-platform-standards/AGENT-LESSONS.md` §4.12 (rolled up from git-mcp's former §1-7).

## Project-Specific Rules

### Verified port assignments

Verified against [defaults.yaml](/opt/iac/Development/cloud-dog-ai/git-mcp-server/defaults.yaml):

- API server: `8078`
- Web server: `8079`
- MCP server: `8084`
- A2A server: `8085`

### Library/server separation

- `git_tools/` MUST NOT import FastAPI, uvicorn, or MCP transport code.
- `git_mcp_server/` MUST NOT contain git logic beyond dispatch and auth.
- All domain logic MUST be testable without starting a server.

### Git safety

- Disable git hooks in cloned/managed workspaces by default.
- Deny `.git/**` access from file tools.
- Prevent symlink escape from workspace root.
- Submodule policy: disallow unless explicitly enabled per profile.
- Force push requires explicit `force_with_lease` AND admin role; never run plain `--force` to
  any branch this server manages.
- Never bypass hooks (`--no-verify`, `--no-gpg-sign`, etc.) from server-side flows; this
  echoes the central git-safety rule and applies recursively to managed workspaces.

### Workspace isolation

- Ephemeral workspaces MUST be cleaned up on session close or TTL expiry.
- Persistent workspaces MUST use per-workspace locks for concurrent access.
- NEVER share a workspace between concurrent sessions without explicit locking.
- Workspace roots are confined to the configured `data/workspaces/` tree; no path may escape
  it via symlink, `..`, or absolute-path argument.

### Repository management primitives

- `clone`, `open`, `fetch`, `pull`, `commit`, `push` MUST flow through `ToolRegistry` so audit
  logging and RBAC enforcement (W28A-704/745) are guaranteed on every call path.
- `stash`, `branch`, `tag`, `merge` operations MUST be RBAC-scoped per profile and refuse to
  operate on protected refs without the maintainer/admin role.
- Direct calls into `git_tools/` that bypass `ToolRegistry` are forbidden in production code
  paths (test fixtures may exercise the library layer directly).

### Protected branches and RBAC

- Protected branch patterns are enforced by `cloud_dog_idam` RBAC plus per-profile policy.
- Direct pushes to protected branches require maintainer/admin role.
- Force push requires explicit `force_with_lease` AND admin role.
- Tool-name authorisation uses `fnmatch` patterns via
  `cloud_dog_idam.RBACEngine` + `can_execute_tool()` (per W28A-704 — no wrapper class).

### Gitea / GitLab token wiring

- GitLab tokens (`gitmcp_gitlab_token`, `gitmcp_gitlab_maintainer_token`) MUST reach the runtime
  via `CLOUD_DOG__STORAGE__GITLAB__DEVELOPER_TOKEN` and `CLOUD_DOG__STORAGE__GITLAB__MAINTAINER_TOKEN`
  env-var overrides wired in the container's Terraform `env` block. A Terraform variable that
  is never referenced in the container `env` block is a no-op (see project AGENT-LESSONS.md
  A131-FIX-1).
- Gitea/GitLab credentials MUST NOT be embedded in committed `defaults.yaml` or `config.yaml`;
  the only acceptable source is the env-var indirection above, populated from the test-service
  `terraform.tfvars` (test-service creds are not Vault-managed — see central RULES §2.3 +
  feedback `feedback_test_service_no_vault.md`).

### Seed API key regeneration on container rebuild

- Each container rebuild generates a new seed API key at `/app/data/seed_api_key.txt`. After
  any `terraform apply` that recreates the container, the local IT seed file
  (`working/it/seed_api_key.txt`) MUST be re-synced from the container:
  ```bash
  docker -H tcp://server2.viewdeck.com:2375 exec gitmcpserver0 cat /app/data/seed_api_key.txt
  ```
  Stale local seed keys cause every E2E sign-in to fail with "Login failed."

### Credential handling (project-local extensions over central §2.3 / §9.2)

- `tests/env-UT`, `tests/env-ST`, `tests/env-IT`, `tests/env-AT`, `tests/env-QT` — tier env files
  used by pytest (resolve `${vault.*}` per central §2.3).
- `private/` (optional, git-ignored) — local operator env overlays for non-test workflows.
- Git remote credentials MUST use either session-provided tokens (pass-through) or
  encrypted-at-rest stored credentials (profile config); never embedded in command lines.
- NEVER commit real tokens, SSH keys, or passwords.
- Audit-log redaction (W28A-745): parameters named `content`, `password`, `secret`, `token`,
  or `body` are automatically redacted by `ToolRegistry._call_with_audit()`. Do NOT add new
  credential-bearing parameter names without extending the redaction allowlist.

### Vault sections used by this project

- `dev.databases` — PostgreSQL connection (optional, for profile/audit persistence).
- `dev.repository` — PyPI/NPM registry credentials.

Load via central pattern:
```bash
set -a; source /opt/iac/Development/cloud-dog-ai/env-vault; set +a
bash scripts/validate-vault.sh
```

### Testing (project-specific extensions over central §5)

- Integration tests run against live API/MCP processes started by
  `tests/integration/conftest.py` — not in-process mocks.
- Integration remote tests MUST use git network transport (not in-process mocks).
- NEVER mock git operations in ST/IT/AT tests.
- See `TESTS.md` for the complete test plan.

### W28A-704 — IDAM compliance (binding implementation contract)

- `RBACAuthoriser` wrapper class is DELETED. Authorisation flows via
  `cloud_dog_idam.RBACEngine` + the direct functions `can_execute_tool()` and
  `require_tool_access()`, both of which take an `RBACEngine` instance as a parameter.
- `fnmatch` tool-name pattern matching is preserved in the direct functions.
- `api_server.py` imports `RBACEngine` directly from `cloud_dog_idam` and creates instances
  per-request for tool authorisation. There is no intermediate factory or singleton.
- `git_auth.py` in `git_tools/security/` is **git credential management** (HTTPS clone
  GitLab token injection via `git credential approve`). It is NOT identity/access management
  and MUST NOT be deleted under IDAM-compliance refactors.
- Baseline: 74 passed, 8 failed unit tests (pre-existing failures in UT1.27/UT1.56/UT1.57);
  regressions below this baseline block the lane.

### W28A-745 — MCP audit logging (binding implementation contract)

- Audit logging is centralised in `ToolRegistry._call_with_audit()` inside
  `git_tools/tools/registry.py`. Both `call()` and `call_with_access()` delegate through this
  single method; every tool invocation is logged regardless of entry path.
- Adding a new call path that bypasses `_call_with_audit()` is a §1.4 violation.
- `ToolRegistry` (in `git_tools/tools/registry.py`) is the central class for tool lifecycle:
  registration, dispatch, audit logging, and profile-scoped access enforcement.
- HTTP MCP tool registration uses `register_tool_router` from `cloud_dog_api_kit`.

### Security — forbidden repository access (CRITICAL — ZERO TOLERANCE)

This is local because the incident in §"Incident Records" below is git-mcp-specific.

**NEVER clone, fetch, ls-remote, or access ANY repository that is not explicitly listed in
the test configuration as an authorised test target.**

Specifically FORBIDDEN:

- `clouddog/cloud-dog-repo` — infrastructure repo containing AWS keys, TLS certificates, and
  production secrets.
- Any repository containing production credentials, SSH keys, PEM files, or infrastructure
  configuration.
- Any repository outside the `cloud-dog-ai/` GitLab group unless explicitly authorised in
  writing.

If `GIT_MCP_REMOTE_REPO` is empty or unset, remote tests MUST fail explicitly — NOT fall
back to a default URL.

Credential handling in tests:

- NEVER clone or access repositories using SSH keys that provide access to production
  infrastructure.
- NEVER store cloned repository content containing credentials on disk beyond the test
  session.
- NEVER leave workspace directories containing sensitive material after test completion.
- Test workspaces MUST be cleaned up automatically on session close or TTL expiry.
- If a test workspace contains credential material (PEM files, SSH keys, tokens), it MUST be
  securely deleted immediately.

## Incident Records

### Platform incidents directly relevant to this service

- Central RULES.md §1.1 Falsification — relevant to git workflow evidence, RBAC proofs,
  workspace behaviour, and report claims.
- Central RULES.md §1.3 Fabrication — relevant to repo URLs, branch/tag names, protected-branch
  policies, workspace roots, and port assignments.
- Central RULES.md §1.5 Production Firewall — relevant to all Docker/Terraform deployment work
  for this service.

### Security incident — unauthorised infrastructure-repo cloning (2026-02-22)

**Breach:** The git-mcp-server agent cloned
`git@gitlab.com:clouddog/cloud-dog-repo.git` into test workspaces during IT test execution.
This repository contains:

- AWS VPC PEM keys (`us-east-1`, `eu-west-2`)
- Let's Encrypt certificate private keys (16 certbot key files)
- Full Python environment with cryptographic libraries
- Production infrastructure configuration

**Impact:** 184 workspace directories created (39 GB), sensitive material exposed on disk.

**Root cause:** `GIT_MCP_REMOTE_REPO` was set to the infrastructure repo URL instead of an
authorised test-only repository. The agent and test framework did not validate whether the
target repository was authorised.

**Remediation required:**

1. All 184 workspace directories in `data/workspaces/` MUST be securely deleted.
2. `GIT_MCP_REMOTE_REPO` MUST be empty by default and MUST only point to authorised test
   repositories.
3. Test framework MUST validate the remote URL against an allowlist before cloning.
4. SSH keys used by the agent MUST be rotated.

This incident is the binding rationale for the "Security — forbidden repository access"
rules above. Do not weaken those rules; do not delete this record.

---

*Last updated: 2026-06-08 (W28A-882 trim — pre-existing content unchanged in substance;
restatement of central §1-4 removed.)*
