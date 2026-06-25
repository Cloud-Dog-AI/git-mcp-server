# W28A-148E-R5B Git Repo Credential Workflow Closeout

Date: 2026-05-11

## Scope

- Service repo: `git-mcp-server`
- UI app tests: `cloud-dog-ai-ui-monorepo/apps/git-mcp`
- Deployment target: `gitmcpserver0` only
- No IMAP, DB, LLM, Ragflow, generation, full estate rerun, or public publication was run.

## Starting Failure

Focused W28A-870 sections b-f reproduced the original live preprod failure:

```text
api:repo_open status=400 code=CD-UNKNOWN error=Bad Request
git clone -v -- https://git.cloud-dog.net/playgroup/test-project.git /app/data/workspaces/remote_cloud_dog-w28a870-api-1778527319405-7404639f
fatal: could not read Username for 'https://git.cloud-dog.net': terminal prompts disabled
```

Credential source proof, redacted:

```text
approved source: git-mcp-server/private/env-PREPROD
CLOUD_DOG__STORAGE__GITLAB__URL=${vault.dev.storage.gitlab.url}
CLOUD_DOG__STORAGE__GITLAB__DEVELOPER_TOKEN=${vault.dev.storage.gitlab.developer_token}
CLOUD_DOG__STORAGE__GITLAB__MAINTAINER_TOKEN=${vault.dev.storage.gitlab.maintainer_token}
```

Runtime before the Terraform env fix had no `CLOUD_DOG__STORAGE__GITLAB__*` variables present.

## Changes

- `git_tools.git.repo.GitRepository` now primes the existing Vault-backed HTTPS Git credential helper for `fetch`, `pull`, and `push`, matching the existing `repo_open` clone path.
- `gitmcpserver0` Terraform container env now wires the approved Vault-backed GitLab/Gitea URL, developer token, and maintainer token into the runtime config.

Changed files:

```text
git-mcp-server/src/git_tools/git/repo.py
.w28a936-cloud-dog-repo/terraform/server0.viewdeck.com/27 MLAgents/gitmcpserver_containers.tf.json
git-mcp-server/working/W28A-148E-R5B-GIT-REPO-CREDENTIAL-WORKFLOW-CLOSEOUT.md
git-mcp-server/working/W28A-148E-R5B/*
```

## Build, Push, Deploy

Code commit used for image build:

```text
78f627583682af89205689a41314fe3c1aecc0d9 fix: prime git credentials for remote operations
```

Image build/push:

```text
tag: registry.cloud-dog.net:443/cloud-dog/git-mcp-server:w28a-148e-r5b-78f6275
latest: registry.cloud-dog.net:443/cloud-dog/git-mcp-server:latest
local image id: sha256:7a47cfb206385df57a72ba4f9405c7df517ad3a8550a8e6bd34b17f49e65ba5e
registry digest: sha256:951c8466e58749ea49f441864b78545b79639c2ed7cc6afdb0209560805c6716
```

Targeted Terraform only:

```text
terraform plan -target=docker_image.gitmcpserver -target=docker_container.gitmcpserver0 -out=w28a-148e-r5b-gitmcpserver0.tfplan -no-color
terraform apply -auto-approve w28a-148e-r5b-gitmcpserver0.tfplan -no-color
```

The first apply hit the known drift pattern where the live container name existed but `docker_container.gitmcpserver0` was absent from state. Scoped recovery:

```text
terraform import docker_container.gitmcpserver0 f6a5e7403ce03a5dac0d52061b238994b79be3d1d0022dfcb8a59072bdef8483
terraform plan -target=docker_image.gitmcpserver -target=docker_container.gitmcpserver0 -out=w28a-148e-r5b-gitmcpserver0-r2.tfplan -no-color
terraform apply -auto-approve w28a-148e-r5b-gitmcpserver0-r2.tfplan -no-color
terraform plan -target=docker_image.gitmcpserver -target=docker_container.gitmcpserver0 -out=w28a-148e-r5b-gitmcpserver0-r3.tfplan -no-color
terraform apply -auto-approve w28a-148e-r5b-gitmcpserver0-r3.tfplan -no-color
```

Deploy proof:

```text
id=25d5089777af2fae99355186598e3a857c2e60fbb21e61984fb8bdf5b7ffef6f image=sha256:7a47cfb206385df57a72ba4f9405c7df517ad3a8550a8e6bd34b17f49e65ba5e status=running health=healthy started=2026-05-11T19:48:19.612233455Z
health={"status":"ok","application":"git-mcp-server-web","version":"0.1.0","env_file":null,"checks":{}}
```

Runtime credential proof, redacted:

```text
CLOUD_DOG__GIT__DEFAULT_REMOTE=https://git.cloud-dog.net
CLOUD_DOG__STORAGE__GITLAB__DEVELOPER_TOKEN=<redacted>
CLOUD_DOG__RUNTIME__MODE=local-docker
PYTHON_VERSION=3.12.13
CLOUD_DOG__STORAGE__GITLAB__URL=https://git.cloud-dog.net
CLOUD_DOG__STORAGE__GITLAB__MAINTAINER_TOKEN=<redacted>
```

## Test Results

Focused unit regression:

```text
python3 -m pytest tests/unit/UT1.41_GitPull/test_git_pull.py tests/unit/UT1.42_ForcePush/test_force_push.py
3 passed in 8.78s
```

Focused W28A-870 sections b-f:

```text
set -a; source /opt/iac/Development/cloud-dog-ai/env-vault; set +a; E2E_BASE_URL=https://gitmcpserver0.cloud-dog.net npm run e2e -- tests/e2e/w28a870-git-mcp-e2e-testing.spec.ts -g 'sections b-f' --config=playwright.preprod.config.ts --reporter=list
1 passed (10.2s)
```

Full Git shard:

```text
set -a; source /opt/iac/Development/cloud-dog-ai/env-vault; set +a; CI=true E2E_BASE_URL=https://gitmcpserver0.cloud-dog.net npm run e2e -- --config=playwright.preprod.config.ts --workers=1 --reporter=list
57 passed, 6 failed, 4 did not run (5.9m)
```

Full-shard failures are no longer `repo_open`, `git_fetch`, or non-interactive credential failures:

```text
T19 MCP tool browser search: missing Tool Browser heading.
T20 MCP execution panel: missing Tool execution heading.
T21 API docs panel and links: missing API Docs heading.
W28A-119D API docs render MCP and A2A discovery surfaces: missing API Docs heading.
W28A-870 sections q-r tag/stash: tag push status stayed "Created tag ..." instead of "Pushed tag ...".
W28A458 T11 a2a console: browser console recorded a 404 resource.
```

Evidence files:

```text
working/W28A-148E-R5B/docker-build-w28a-148e-r5b-78f6275.log
working/W28A-148E-R5B/push-immutable.log
working/W28A-148E-R5B/push-latest.log
working/W28A-148E-R5B/runtime-container-proof.txt
working/W28A-148E-R5B/runtime-env-redacted-proof.txt
working/W28A-148E-R5B/health.json
working/W28A-148E-R5B/focused-w28a870-b-f.log
working/W28A-148E-R5B/full-git-shard.log
```

## Residual Blockers

- W28A-870 repo_open clone credential failure for `https://git.cloud-dog.net/playgroup/test-project.git` is closed.
- Focused W28A-870 sections b-f is green.
- Full Git shard remains red on six independent UI/workflow residuals listed above; these are outside the original repo credential failure.
- No raw credential values were intentionally printed in closeout evidence; runtime credential proof is redacted.
