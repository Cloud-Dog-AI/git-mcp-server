# W28A-12 Git MCP Profile Estate Cleanup Report

Date: 2026-05-07

## Scope

Dispatch: `W28A-12-GITMCP-PROFILE-ESTATE-CLEANUP-2026-05-07`

Service: `git-mcp-server`

Preprod host: `https://gitmcpserver0.cloud-dog.net`

## Configuration Checks

- `defaults.yaml` defines canonical profiles `local_test` and `remote_cloud_dog`.
- `local_test` points to `https://git.cloud-dog.net/playgroup/test-project.git`.
- Repository accessibility was verified with `git ls-remote`; `HEAD` and `refs/heads/main` both resolved to `b067825c978afdf12341b66c0438da0798c014c1`.
- No repo-root `config.yaml` exists in this checkout.
- Requested Terraform path `/opt/iac/Development/cloud-dog-ai/terraform/gitmcpserver_containers.tf.json` is absent.
- Actual Terraform path checked: `/opt/iac/cloud-dog-repo/terraform/server0.viewdeck.com/27 MLAgents/gitmcpserver_containers.tf.json`.
- No `CLOUD_DOG__GIT__PROFILES` override or references to the removed UI placeholder profiles were found in the checked Terraform/preprod configuration.

## Live Admin Cleanup

Initial preprod profiles:

- `local_test`
- `remote_cloud_dog`
- `ui-profile-1778088385050`
- `ui-profile-1778090894621`
- `ui-profile-1778095667726`

Admin CRUD verification:

- Created temporary profile `w28a-12-crud-*`.
- Read temporary profile and verified repository source.
- Updated temporary profile.
- Deleted temporary profile.
- Verified deleted temporary profile returned `404`.

Removed unreferenced placeholder profiles:

- `ui-profile-1778088385050`
- `ui-profile-1778090894621`
- `ui-profile-1778095667726`

Final preprod profiles:

- `local_test`
- `remote_cloud_dog`

Evidence:

- `working/preprod-profiles-12.json`
- `working/preprod-profile-crud-cleanup-12.log`
- `working/preprod-profiles-after-cleanup-12.json`
- `working/repo-access-12.log`

## Verification

- Unit tests: `82 passed in 60.73s`
- System tests: `23 passed in 18.14s`

Logs:

- `working/ut-12.log`
- `working/st-12.log`

Note: `working/ut-12.log` includes a shutdown-time shared platform logging warning after pytest completion. Pytest exited successfully with status `0`.
