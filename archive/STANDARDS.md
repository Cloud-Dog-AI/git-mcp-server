# git-mcp-server Standards Alignment

## Adopted Platform Standards

- PS-00 Engineering principles
- PS-10 Architecture
- PS-20 API contracts
- PS-40 Logging and observability
- PS-70 User management and IDAM
- PS-80 Configuration management
- PS-90 Security
- PS-95 Testing

## Implementation Notes

- Configuration is loaded through `cloud_dog_config` in `src/git_tools/config/loader.py`.
- Logging and audit event emission are provided via `cloud_dog_logging` in `src/git_tools/audit/logger.py`.
- API application factory uses `cloud_dog_api_kit.create_app` in `src/git_mcp_server/api_server.py`.
- Authentication and RBAC wiring use `cloud_dog_idam` in `src/git_tools/security/rbac.py` and `src/git_mcp_server/auth/middleware.py`.
- Unit, system, integration, application, and quality tests are present with enforced `--env` selection in `tests/conftest.py`.
