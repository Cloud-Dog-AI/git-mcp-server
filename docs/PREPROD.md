# PREPROD Deployment — Git MCP Server

This document describes the pre-production operator/deployment overlay for this service. The Terraform container environment is the runtime source of truth, and `private/env-PREPROD` is the operator/test overlay used for local control commands and pytest runs against the deployed preprod service. Defaults and non-preprod settings remain documented in `docs/ENV-REFERENCE.md`, `docs/ARCHITECTURE.md`, and `defaults.yaml`.

## 1. Overview
- Service URL: `https://gitmcpserver0.your-domain.com`
- Container hostname: `gitmcpserver0.internal.example`
- Health endpoint verified during W28A-241: `https://gitmcpserver0.your-domain.com/health`
- Docker image: `registry.example.com/cloud-dog/git-mcp-server:latest`
- Active Terraform container definition: `terraform/primary-environment/gitmcpserver_containers.tf.json`
- Legacy/parallel Terraform definition to cross-check when investigating drift: `terraform/legacy-environment/gitmcpserver_containers.tf.json`
- Operator overlay file: `./git-mcp-server/private/env-PREPROD`

### Port allocation
| Surface | Internal port | External URL |
|---|---:|---|
| API | 8083 | `https://gitmcpserver0.your-domain.com/api/v1` |
| MCP | 8081 | `https://gitmcpserver0.your-domain.com/mcp` |
| Health | API process | `https://gitmcpserver0.your-domain.com/health` |

## 2. Configuration
Section 2 documents the full preprod environment surface that differs from or materially specialises the defaults. Use it together with `defaults.yaml` and `docs/ENV-REFERENCE.md` when tracing a value through the precedence chain `os.environ -> --env file -> config.yaml -> defaults.yaml`.

### Server and workspace settings
| Setting(s) | Default / baseline | Preprod source | Preprod change? | Notes |
|---|---|---|---|---|
| `CLOUD_DOG_ENVIRONMENT` | `dev` via log defaults | `private/env-PREPROD` | Yes | Marks preprod logs and audit output. |
| `CLOUD_DOG__SERVER__HOST/PORT`, `CLOUD_DOG__SERVER__MCP__PORT` | `127.0.0.1:8585/8586` | Terraform + `private/env-PREPROD` | Yes | Container binds API and MCP on the shared preprod ports. |
| `CLOUD_DOG__GIT__API_SERVER__HOST/PORT`, `...MCP_SERVER__HOST/PORT` | local defaults | Terraform + `private/env-PREPROD` | Yes | Explicit internal split between API and MCP processes. |
| `CLOUD_DOG__GIT__WORKSPACE_ROOT`, `GIT_MCP_SEED_KEY_FILE` | repo-local paths | Terraform + `private/env-PREPROD` | Yes | Preprod persists workspaces under `/app/data/workspaces`. |

### Auth, Vault, and network settings
| Setting(s) | Default / baseline | Preprod source | Preprod change? | Notes |
|---|---|---|---|---|
| `CLOUD_DOG__GIT__API_KEY`, `CLOUD_DOG__RUNTIME__A2A_TEST_API_KEY` | blank | Vault-backed Terraform + `private/env-PREPROD` | Yes | API and A2A smoke checks use the same service key. |
| `VAULT_ADDR`, `VAULT_MOUNT_POINT`, `VAULT_CONFIG_PATH`, `CLOUD_DOG__VAULT__*` | unset | Terraform + `private/env-PREPROD` | Yes | Required if runtime needs Vault-resolved config. |
| `CLOUD_DOG__AUTH__MODE`, `...JWT__ISSUER/AUDIENCE/SECRET` | `api_key` with blank JWT values | `private/env-PREPROD` | Yes | Operator overlay enables combined API-key/JWT auth for preprod checks. |
| `NO_PROXY`, CA bundle variables, `CLOUD_DOG_TLS_CA_BUNDLE` | unset | Terraform + `private/env-PREPROD` | Yes | Keeps internal `.cloud-dog.net` calls off the proxy and trusts the shared CA bundle. |
| `CLOUD_DOG__GIT__DEFAULT_REMOTE` | `https://git.cloud-dog.net` | Terraform + `private/env-PREPROD` | Yes | Preprod uses the real Gitea instance; defaults.yaml profiles also point to real repos. |

## 3. Preprod-Specific Overrides
Only settings that differ materially from defaults or that must be supplied for preprod are listed here. The literal operator/test overlay is `./git-mcp-server/private/env-PREPROD`.

| Override | Why preprod differs | Source of truth |
|---|---|---|
| API/MCP ports and host binding | Preprod uses all-in-one container port allocations instead of local 8585/8586. | Terraform 60-container file |
| Workspace root and seed key path | Container storage differs from repo-local paths. | Terraform 60-container file |
| Service API keys and optional JWT secret | Non-dev auth must be backed by Vault secrets. | Vault + Terraform |
| Default remote URL | `defaults.yaml` profiles now point to `https://git.cloud-dog.net/playgroup/test-project.git`; operators may override per-environment. | `private/env-PREPROD` + run-specific overlays |
| Proxy/CA bundle settings | Needed for internal service-to-service traffic and trusted corporate TLS. | Terraform + `private/env-PREPROD` |

## 4. Vault Configuration
This service reads preprod secrets from the shared Vault config blob at `cloud_dog_ai/config`.

### Required Vault paths
- `dev.services.gitmcpserver0` for API/A2A keys
- `dev.idp.*` only if JWT/enterprise auth is enabled in preprod
- `dev.repository.pypi` for build-time package registry credentials

### Operator setup
```bash
set -a; source .env.local
vault kv get -mount=cloud_dog_ai config
```

### Populate or refresh missing entries
Use a merged JSON payload rather than editing Terraform or the running container.

```bash
vault kv put -mount=cloud_dog_ai config   content=@/tmp/cloud-dog-ai-config.preprod.json
```

Example payload fragment:
```json
{
  "dev": {
    "services": {"gitmcpserver0": {"api_key": "<API_KEY>"}},
    "idp": {"keycloak": {"admin_password": "<JWT_OR_IDP_SECRET>"}}
  }
}
```

## 5. Deployment Steps
The project rules forbid ad-hoc `docker build`; use the repo entrypoint script.

1. Load Vault-backed build credentials.
```bash
set -a; source .env.local
```
2. Build the image.
```bash
cd ./git-mcp-server && bash docker-build.sh latest
```
3. Tag and push the image.
```bash
docker tag cloud-dog/git-mcp-server:latest registry.example.com/cloud-dog/git-mcp-server:latest
docker push registry.example.com/cloud-dog/git-mcp-server:latest
```
4. Plan and apply the Terraform update from the shared preprod workspace.
```bash
cd 'terraform/60 Cloud-Dog AI Containers'
terraform plan -out=tfplan.out
terraform apply tfplan.out
```
5. Verify the deployed service.
```bash
curl -fsS https://gitmcpserver0.your-domain.com/health
```

## 6. Testing Against Preprod
Use the committed tier env file plus `private/env-PREPROD` as the environment-specific overlay.

1. `pytest tests/system --env tests/env-ST --env private/env-PREPROD -q`
2. `pytest tests/integration --env tests/env-IT --env private/env-PREPROD -q`
3. Remote-repo scenarios still need an authorised repo-specific overlay in `private/` to satisfy the project security rules.

Known limitations:
- Never point preprod tests at unauthorised repositories; the project rules explicitly forbid this.
- Git write/destructive scenarios should only run against disposable test repositories.

## 7. Troubleshooting
- `curl -fsS https://gitmcpserver0.your-domain.com/health` should return `status=ok`.
- A bare `GET /` returns `401` by design; use `/health` for unauthenticated liveness.
- `docker -H your-docker-host logs gitmcpserver0.internal.example` for runtime logs.
