# git-mcp-server migration verifiers

Run from project root:

```bash
bash migration/verify/verify-git-mcp-server-CONFIG.sh
bash migration/verify/verify-git-mcp-server-LOGGING.sh
bash migration/verify/verify-git-mcp-server-API-KIT.sh
bash migration/verify/verify-git-mcp-server-IDAM.sh
bash migration/verify/verify-git-mcp-server-DB.sh
```

Migration completeness table:

| Adopted package | Verifier script |
|---|---|
| `cloud_dog_config` | `verify-git-mcp-server-CONFIG.sh` |
| `cloud_dog_logging` | `verify-git-mcp-server-LOGGING.sh` |
| `cloud_dog_api_kit` | `verify-git-mcp-server-API-KIT.sh` |
| `cloud_dog_idam` | `verify-git-mcp-server-IDAM.sh` |
| `cloud_dog_db` | `verify-git-mcp-server-DB.sh` |
