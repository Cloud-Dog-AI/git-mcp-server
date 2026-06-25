# W28A-148E-R4B Git Deploy Workflow Rerun

Date: 2026-05-11

## Scope

- Service repo: `git-mcp-server`
- Source commit: `793b3ee fix: serve git developer spa deep links`
- Deployment target: `gitmcpserver0` only
- UI app tests run from `cloud-dog-ai-ui-monorepo/apps/git-mcp`
- No IMAP, DB, LLM, Ragflow, generation, full estate rerun, or public publication was run.

## Starting State

- `git-mcp-server` was clean and at `793b3ee`.
- `cloud-dog-ai-ui-monorepo/apps/git-mcp` was clean; unrelated dirty screenshot files existed outside the Git app and were not touched.
- Pre-deploy live route probe:
  - `/mcp-console`: `404 application/json`
  - `/api-docs`: `404 application/json`
  - `/admin/users`: `200 text/html; charset=utf-8`
- Pre-deploy runtime image config: `sha256:10e7d88d71cf9deb3fea61240c81f259d2f6a95d2310e3b0a60c18ba0b6dd5cc`.

## Build, Push, Deploy

- Built image tag: `registry.cloud-dog.net:443/cloud-dog/git-mcp-server:w28a-148e-r4b-793b3ee`
- Latest tag: `registry.cloud-dog.net:443/cloud-dog/git-mcp-server:latest`
- Local image/config digest: `sha256:448f34847698933bf54aa6f6aa094e355b7acaef77b9a842f580a51d3fe0f532`
- Registry manifest digest for immutable and latest tags: `sha256:219908c1a15afddc9916e33d1386dbf6b4617a6b3aee4a426501bb4597f6e023`
- Runtime Python proof: `PYTHON_VERSION=3.12.13`

Targeted Terraform:

```text
terraform plan -target=docker_image.gitmcpserver -target=docker_container.gitmcpserver0 -out=w28a-148e-r4b-gitmcpserver.tfplan
Plan: 2 to add, 0 to change, 1 to destroy.

terraform apply -auto-approve w28a-148e-r4b-gitmcpserver.tfplan
Partial apply: docker_image.gitmcpserver updated; docker_container.gitmcpserver0 create failed because existing live container name was held by c630a5d880d4.

terraform import docker_container.gitmcpserver0 c630a5d880d4317469a7147764cdc774498de22593cb13c82bd605cb7154c7de
Import successful.

terraform plan -target=docker_image.gitmcpserver -target=docker_container.gitmcpserver0 -out=w28a-148e-r4b-gitmcpserver-r2.tfplan
Plan: 1 to add, 0 to change, 1 to destroy.

terraform apply -auto-approve w28a-148e-r4b-gitmcpserver-r2.tfplan
Apply complete! Resources: 1 added, 0 changed, 1 destroyed.
```

Runtime proof after deploy:

```text
container=f6a5e7403ce03a5dac0d52061b238994b79be3d1d0022dfcb8a59072bdef8483
image=sha256:448f34847698933bf54aa6f6aa094e355b7acaef77b9a842f580a51d3fe0f532
status=running
health=healthy
started=2026-05-11T19:13:23.678852697Z
```

## Live Route Verification

Post-deploy route probes:

```text
/mcp-console 200 Content-Type: text/html; charset=utf-8; markers: <div id="root", <script
/api-docs 200 Content-Type: text/html; charset=utf-8; markers: <div id="root", <script
/admin/users 200 Content-Type: text/html; charset=utf-8; markers: <div id="root", <script
```

## Focused Test Results

Focused T19/T20/T21:

```text
E2E_BASE_URL=https://gitmcpserver0.cloud-dog.net npx --no-install playwright test tests/e2e/ui-review2.spec.ts -g 'T19|T20|T21' --config=playwright.preprod.config.ts --reporter=list
3 passed (7.9s)
```

Initial sandboxed run of the same group failed before assertions because Chromium could not launch in the sandbox:

```text
sandbox_host_linux.cc:41 Check failed: . shutdown: Operation not permitted (1)
```

Focused W28A-870 sections b-f:

```text
E2E_BASE_URL=https://gitmcpserver0.cloud-dog.net npx --no-install playwright test tests/e2e/w28a870-git-mcp-e2e-testing.spec.ts -g 'sections b-f' --config=playwright.preprod.config.ts --reporter=list
1 failed
```

Failure:

```text
api:repo_open status=400 code=CD-UNKNOWN error=Bad Request
git clone -v -- https://git.cloud-dog.net/playgroup/test-project.git /app/data/workspaces/remote_cloud_dog-w28a870-api-1778526935813-8b6851be
fatal: could not read Username for 'https://git.cloud-dog.net': terminal prompts disabled
```

## Full Git W28A-102 Shard

Not run. Stop condition applied because focused W28A-870 sections b-f remains red.

## Evidence Files

- `working/W28A-148E-R4B/docker-build-w28a-148e-r4b-793b3ee.log`
- `working/W28A-148E-R4B/local-image-inspect-w28a-148e-r4b-793b3ee.json`
- `working/W28A-148E-R4B/push-immutable.log`
- `working/W28A-148E-R4B/push-latest.log`
- `working/W28A-148E-R4B/runtime-container-proof.txt`
- `working/W28A-148E-R4B/runtime-image-proof.txt`
- `working/W28A-148E-R4B/live-mcp-console.headers`
- `working/W28A-148E-R4B/live-mcp-console.html`
- `working/W28A-148E-R4B/live-api-docs.headers`
- `working/W28A-148E-R4B/live-api-docs.html`
- `working/W28A-148E-R4B/live-admin-users.headers`
- `working/W28A-148E-R4B/live-admin-users.html`
- `working/W28A-148E-R4B/focused-t19-t21.log`
- `working/W28A-148E-R4B/focused-t19-t21-rerun.log`
- `working/W28A-148E-R4B/focused-w28a870-b-f.log`

## Residual Blockers

- Git live SPA deep links are fixed for `/mcp-console`, `/api-docs`, and `/admin/users`.
- Focused T19/T20/T21 is green.
- Focused W28A-870 sections b-f is still blocked at `repo_open`: the preprod workflow cannot clone `https://git.cloud-dog.net/playgroup/test-project.git` because Git credentials are unavailable/non-interactive for that HTTPS remote.
- Full Git W28A-102 shard remains blocked by the focused failure and was not rerun.
