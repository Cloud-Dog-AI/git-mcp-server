# Copyright 2026 Cloud-Dog, Viewdeck Engineering Limited
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

from __future__ import annotations

import os
import re
import subprocess
import time
from functools import lru_cache
from pathlib import Path
from urllib.parse import urlparse

import httpx
import pytest
from cloud_dog_config.vault.client import (  # type: ignore[import-untyped]
    VaultClient,
    VaultConnectionConfig,
)

from tests.helpers import api_url

_RUNTIME_EXTERNAL_DETECTED = False


def _process_env_value(key: str, default: str = "") -> str:
    """Read a process environment variable using index lookup only."""
    if key not in os.environ:
        return default
    value = os.environ[key].strip()
    return value if value else default


def _integration_sort_key(item: pytest.Item) -> tuple[int, int, str]:
    """Sort IT tests numerically (IT1.1 .. IT1.10) instead of lexicographically."""
    nodeid = item.nodeid
    match = re.search(r"/IT(\d+)\.(\d+)_", nodeid)
    if match is None:
        return (999, 999, nodeid)
    major = int(match.group(1))
    minor = int(match.group(2))
    # Remote push is less stable immediately after remote clone+fetch in this environment.
    # Run IT1.10 before IT1.9 so each test still runs, but with lower cross-test interference.
    if major == 1 and minor == 10:
        minor = 9
    elif major == 1 and minor == 9:
        minor = 10
    return (major, minor, nodeid)


def pytest_collection_modifyitems(items: list[pytest.Item]) -> None:
    """Apply stable numeric ordering to integration tests."""
    items.sort(key=_integration_sort_key)


def _load_env_file(path: str) -> dict[str, str]:
    values: dict[str, str] = {}
    for line in Path(path).read_text(encoding="utf-8").splitlines():
        raw = line.strip()
        if not raw or raw.startswith("#") or "=" not in raw:
            continue
        key, value = raw.split("=", 1)
        values[key.strip()] = value.strip()
    return values


@lru_cache(maxsize=1)
def _integration_env_defaults() -> dict[str, str]:
    """Load baseline IT env values used when overlay env files omit remote settings."""
    path = Path("tests/env-IT")
    if not path.exists():
        return {}
    return _load_env_file(path.as_posix())


def _active_env_file(default_path: str) -> str:
    value = _process_env_value("TEST_ENV_FILE", "")
    if not value:
        return default_path
    path = Path(value)
    name = path.name.lower()
    if name.startswith("env-db-"):
        return default_path
    if "private" in {part.lower() for part in path.parts}:
        return value
    if not name.startswith("env-it"):
        return default_path
    return value


def _setting(env_map: dict[str, str], key: str, default: str) -> str:
    """Resolve setting from process env, then env file, then default."""
    from_process = _process_env_value(key, "")
    if from_process:
        return from_process
    from_file = env_map.get(key, "").strip()
    if from_file:
        return from_file
    return default


def _required_setting(env_map: dict[str, str], key: str) -> str:
    """Resolve a mandatory setting from env file values or process env."""
    value = _setting(env_map, key, "").strip()
    if not value:
        raise RuntimeError(f"Missing required setting: {key}")
    return value


def _required_port(env_map: dict[str, str], key: str) -> int:
    """Resolve a mandatory integer port from env values."""
    return int(_required_setting(env_map, key))


def _export_runtime_base_urls(
    *,
    base_url: str,
    web_url: str,
    mcp_url: str,
    a2a_url: str,
) -> dict[str, str | None]:
    """Export resolved runtime URLs so helper functions see the active server split."""
    previous = {
        "TEST_API_BASE_URL": os.environ.get("TEST_API_BASE_URL"),
        "TEST_WEB_BASE_URL": os.environ.get("TEST_WEB_BASE_URL"),
        "TEST_MCP_BASE_URL": os.environ.get("TEST_MCP_BASE_URL"),
        "TEST_A2A_BASE_URL": os.environ.get("TEST_A2A_BASE_URL"),
    }
    os.environ["TEST_API_BASE_URL"] = base_url
    os.environ["TEST_WEB_BASE_URL"] = web_url
    os.environ["TEST_MCP_BASE_URL"] = mcp_url
    os.environ["TEST_A2A_BASE_URL"] = a2a_url
    return previous


def _restore_runtime_base_urls(previous: dict[str, str | None]) -> None:
    """Restore process-level runtime URL overrides after each test."""
    for key, value in previous.items():
        if value is None:
            os.environ.pop(key, None)
            continue
        os.environ[key] = value


def _runtime_mode() -> str:
    mode = _process_env_value("TEST_RUNTIME_MODE", "local-server").lower()
    if mode in {"local-server", "local-docker", "remote-runtime"}:
        return mode
    return "local-server"


def _use_external_runtime() -> bool:
    flag = _process_env_value("TEST_USE_EXTERNAL_RUNTIME", "").lower()
    if flag in ("1", "true", "yes"):
        return True
    if flag in ("0", "false", "no"):
        return False
    return _runtime_mode() in {"local-docker", "remote-runtime"}


def _external_precheck_timeout_seconds() -> float:
    raw = _process_env_value("TEST_EXTERNAL_ENDPOINT_PRECHECK_TIMEOUT_SECONDS", "")
    if raw:
        try:
            value = float(raw)
            if value > 0:
                return value
        except ValueError:
            pass
    return 20.0


def _git_ls_remote(url: str, timeout: int = 15) -> subprocess.CompletedProcess[bytes]:
    return subprocess.run(
        ["git", "ls-remote", "--exit-code", url],
        capture_output=True,
        timeout=timeout,
    )


def _wait_for(url: str, timeout_seconds: float = 30.0) -> None:
    deadline = time.time() + timeout_seconds
    last_error: Exception | None = None
    while time.time() < deadline:
        try:
            response = httpx.get(url, timeout=2.0)
            if response.status_code < 500:
                return
        except Exception as exc:  # noqa: BLE001
            last_error = exc
        time.sleep(0.4)
    if last_error is not None:
        raise RuntimeError(f"Timed out waiting for {url}: {last_error}")
    raise RuntimeError(f"Timed out waiting for {url}")


def _pid_is_active(pid: int) -> bool:
    try:
        os.kill(pid, 0)
    except OSError:
        return False
    stat_path = Path(f"/proc/{pid}/stat")
    if not stat_path.exists():
        return False
    parts = stat_path.read_text(encoding="utf-8").split()
    return not (len(parts) >= 3 and parts[2].startswith("Z"))


def _server_pid_active(name: str) -> bool:
    pid_file = Path(".pids") / f"{name}.pid"
    if not pid_file.exists():
        return False
    raw = pid_file.read_text(encoding="utf-8").strip()
    if not raw.isdigit():
        return False
    return _pid_is_active(int(raw))


def _server_control_runtime_active() -> bool:
    return (
        _server_pid_active("api")
        and _server_pid_active("web")
        and _server_pid_active("mcp")
        and _server_pid_active("a2a")
    )


def _seed_key_validates(base_url: str, key_file: Path, timeout_seconds: float = 3.0) -> bool:
    deadline = time.time() + timeout_seconds
    while time.time() < deadline:
        if key_file.exists():
            candidate = key_file.read_text(encoding="utf-8").strip()
            if candidate:
                try:
                    probe = httpx.get(
                        api_url(base_url, "/tools"),
                        headers={"x-api-key": candidate},
                        timeout=2.0,
                    )
                    if probe.status_code == 200:
                        return True
                except Exception:  # noqa: BLE001
                    pass
        time.sleep(0.2)
    return False


def _start_servers_with_retry(
    *,
    env_file: str,
    base_url: str,
    web_url: str,
    mcp_url: str,
    a2a_url: str,
    key_file: Path,
    server_control_env: dict[str, str],
    attempts: int = 3,
) -> str:
    """Start local integration servers and wait for a stable, validated runtime."""
    last_error: Exception | None = None
    for attempt in range(1, attempts + 1):
        subprocess.run(
            ["./server_control.sh", "--env", env_file, "stop", "all"],
            check=False,
            env=server_control_env,
        )
        started = subprocess.run(
            ["./server_control.sh", "--env", env_file, "start", "all"],
            check=False,
            env=server_control_env,
        )
        if started.returncode != 0:
            last_error = RuntimeError(f"server_control start failed on attempt {attempt} (rc={started.returncode})")
            time.sleep(float(attempt))
            continue
        try:
            _wait_for(f"{base_url}/health")
            _wait_for(web_url)
            _wait_for(f"{mcp_url}/health")
            _wait_for(f"{a2a_url}/health")
            stable_deadline = time.time() + 2.0
            while time.time() < stable_deadline:
                if not _server_control_runtime_active():
                    raise RuntimeError("server_control runtime lost tracked PIDs during startup stabilisation")
                time.sleep(0.2)
            if not _seed_key_validates(base_url, key_file, timeout_seconds=5.0):
                raise RuntimeError(f"Seed API key did not validate after local startup: {key_file}")
            return "local"
        except Exception as exc:  # noqa: BLE001
            last_error = exc
            subprocess.run(
                ["./server_control.sh", "--env", env_file, "stop", "all"],
                check=False,
                env=server_control_env,
            )
            time.sleep(float(attempt))
    if last_error is not None:
        raise RuntimeError(f"Failed to start integration servers after {attempts} attempts: {last_error}")
    raise RuntimeError(f"Failed to start integration servers after {attempts} attempts")


def _is_external_server_mode() -> bool:
    legacy = _process_env_value("GIT_MCP_USE_EXTERNAL_SERVER", "").lower()
    if legacy in ("1", "true", "yes"):
        return True
    if legacy in ("0", "false", "no"):
        return False
    return _use_external_runtime()


def _allowed_remote_prefixes() -> list[str]:
    raw = _process_env_value("GIT_MCP_ALLOWED_REMOTE_PREFIXES", "")
    if not raw:
        raw = _integration_env_defaults().get("GIT_MCP_ALLOWED_REMOTE_PREFIXES", "").strip()
    if not raw:
        return []
    return [item.strip() for item in raw.split(",") if item.strip()]


def _candidate_remote_urls() -> list[str]:
    urls: list[str] = []
    primary = _process_env_value("GIT_MCP_REMOTE_REPO", "")
    if not primary:
        primary = _integration_env_defaults().get("GIT_MCP_REMOTE_REPO", "").strip()
    if primary:
        urls.append(primary)
    raw = _process_env_value("GIT_MCP_REMOTE_REPOS", "")
    if not raw:
        raw = _integration_env_defaults().get("GIT_MCP_REMOTE_REPOS", "").strip()
    if raw:
        urls.extend(item.strip() for item in raw.split(",") if item.strip())
    # Keep deterministic order while dropping duplicates.
    return list(dict.fromkeys(urls))


def _load_vault_config_json() -> dict[str, object]:
    """Load Vault config payload using cloud_dog_config Vault client."""
    addr = _process_env_value("VAULT_ADDR", "").rstrip("/")
    token = _process_env_value("VAULT_TOKEN", "")
    mount = _process_env_value("VAULT_MOUNT_POINT", "cloud_dog_ai").strip("/")
    config_path = _process_env_value("VAULT_CONFIG_PATH", "config").strip("/")
    if not addr or not token:
        return {}

    try:
        client = VaultClient(
            VaultConnectionConfig(
                server=addr,
                token=token,
                timeout_seconds=20.0,
                mount_point=mount,
            )
        )
        # _split_mount expects path to include mount prefix as first segment;
        # pass mount/config_path so it splits correctly to (mount, config_path).
        payload = client.read(f"{mount}/{config_path}") or {}
    except Exception:  # noqa: BLE001
        return {}
    if not isinstance(payload, dict):
        return {}
    return payload.get("json") or payload


def _inject_git_config_env(key: str, value: str) -> None:
    """Append a git runtime config key/value via GIT_CONFIG_* env variables."""
    raw_count = _process_env_value("GIT_CONFIG_COUNT", "0") or "0"
    try:
        count = int(raw_count)
    except ValueError:
        count = 0
    for index in range(count):
        if (
            _process_env_value(f"GIT_CONFIG_KEY_{index}", "") == key
            and _process_env_value(f"GIT_CONFIG_VALUE_{index}", "") == value
        ):
            return
    os.environ[f"GIT_CONFIG_KEY_{count}"] = key
    os.environ[f"GIT_CONFIG_VALUE_{count}"] = value
    os.environ["GIT_CONFIG_COUNT"] = str(count + 1)


def _configure_vault_gitlab_credentials(remote_url: str) -> tuple[bool, str]:
    """Prime git credential cache from Vault gitlab token for HTTPS remotes."""
    parsed_remote = urlparse(remote_url)
    if parsed_remote.scheme not in {"http", "https"} or not parsed_remote.hostname:
        return False, "unsupported remote URL scheme for Vault gitlab auth"

    cfg = _load_vault_config_json()
    gitlab_cfg = ((cfg.get("dev") or {}).get("storage") or {}).get("gitlab") or {}
    if not isinstance(gitlab_cfg, dict):
        return False, "Vault gitlab credentials block missing"

    gitlab_url = str(gitlab_cfg.get("url", "")).strip()
    token = str(gitlab_cfg.get("developer_token", "") or gitlab_cfg.get("maintainer_token", "")).strip()
    if not gitlab_url or not token:
        return False, "Vault gitlab url/token missing"

    parsed_vault_gitlab = urlparse(gitlab_url)
    if parsed_vault_gitlab.hostname != parsed_remote.hostname:
        # PS-97 v1.1 §1.1.5 public boundary fixtures (staging-gitea/test-fixtures/*,
        # github.com/cloud-dog-ai/*) are public-anonymous-readable by design. When the
        # candidate remote host does not match the Vault gitlab host, we treat this as
        # "no Vault auth required" and let the caller fall through to anonymous
        # `git ls-remote`. The allowlist check (`_remote_authorisation_error`) has
        # already gated which hosts are acceptable in this env.
        return True, "anonymous: remote host does not match Vault gitlab host; attempting unauthenticated access"

    _inject_git_config_env("credential.helper", "cache --timeout=900")
    _inject_git_config_env("credential.useHttpPath", "true")
    # Ignore host/global git config during test runs so remote auth is Vault-backed.
    os.environ["GIT_CONFIG_GLOBAL"] = "/dev/null"
    os.environ["GIT_TERMINAL_PROMPT"] = "0"

    path_value = parsed_remote.path.lstrip("/")
    approve_payload = (
        f"protocol={parsed_remote.scheme}\n"
        f"host={parsed_remote.hostname}\n"
        f"path={path_value}\n"
        "username=oauth2\n"
        f"password={token}\n\n"
    )
    result = subprocess.run(
        ["git", "credential", "approve"],
        input=approve_payload,
        text=True,
        capture_output=True,
        timeout=10,
        check=False,
        env=os.environ.copy(),
    )
    if result.returncode != 0:
        return False, "failed to prime git credential cache from Vault"
    return True, "Vault gitlab token configured for remote auth"


def _remote_authorisation_error(url: str, tier: str) -> str | None:
    blocked_markers = ("clouddog/cloud-dog-repo",)
    if any(marker in url for marker in blocked_markers):
        return f"GIT_MCP_REMOTE_REPO '{url}' is forbidden by RULES.md section 7.1."

    prefixes = _allowed_remote_prefixes()
    if tier in ("IT", "AT") and not prefixes:
        return (
            "GIT_MCP_ALLOWED_REMOTE_PREFIXES is required for IT/AT. "
            "Set a comma-separated allowlist of authorised remote URL prefixes."
        )
    if prefixes and not any(url.startswith(prefix) for prefix in prefixes):
        return f"GIT_MCP_REMOTE_REPO '{url}' is not in allowlist. Allowed prefixes: {prefixes}"
    return None


def _docker_container_exists(name: str) -> bool:
    """Check whether a docker container exists by name."""
    if not name:
        return False
    try:
        result = subprocess.run(
            ["docker", "inspect", name],
            capture_output=True,
            text=True,
            timeout=10,
            check=False,
        )
    except FileNotFoundError:
        return False
    return result.returncode == 0


def _resolve_container_name() -> str:
    """Resolve the runtime container using env override plus stable fallbacks."""
    configured = _process_env_value("GIT_MCP_CONTAINER_NAME", "")
    candidates = [configured, "git-mcp-server", "git-mcp-all"]
    for candidate in candidates:
        if candidate and _docker_container_exists(candidate):
            return candidate
    return ""


def _sync_seed_api_key_from_container(key_file: Path) -> bool:
    """Refresh the local seed API key from an already running container, if available."""
    container_name = _resolve_container_name()
    if not container_name:
        return False
    configured_path = _process_env_value("GIT_MCP_CONTAINER_KEY_PATH", "")
    candidate_paths: list[str] = []
    if configured_path:
        candidate_paths.append(configured_path)
    candidate_paths.extend(
        [
            "/app/working/it/seed_api_key.txt",
            "/app/data/seed_api_key.txt",
        ]
    )
    candidate_paths = list(dict.fromkeys(candidate_paths))
    for container_key_path in candidate_paths:
        try:
            result = subprocess.run(
                ["docker", "exec", container_name, "cat", container_key_path],
                capture_output=True,
                text=True,
                timeout=10,
                check=False,
            )
        except FileNotFoundError:
            return False
        if result.returncode == 0 and result.stdout.strip():
            key_file.parent.mkdir(parents=True, exist_ok=True)
            key_file.write_text(result.stdout.strip(), encoding="utf-8")
            return True
    return False


def _normalise_host_seed_key_path(path: Path) -> Path:
    """Map container-only absolute key paths to host-writable test paths."""
    if path.is_absolute() and path.as_posix().startswith("/app/"):
        return Path("./working/it/seed_api_key.txt")
    return path


@pytest.fixture(scope="session", autouse=True)
def _integration_external_runtime_precheck() -> None:
    """Fail fast once when external runtime endpoints are not reachable."""
    if not _is_external_server_mode():
        return
    env_file = _active_env_file("tests/env-IT")
    env = _load_env_file(env_file)
    api_host = _required_setting(env, "CLOUD_DOG__API_SERVER__HOST")
    web_host = env.get("CLOUD_DOG__WEB_SERVER__HOST", api_host)
    mcp_host = env.get("CLOUD_DOG__MCP_SERVER__HOST", api_host)
    a2a_host = env.get("CLOUD_DOG__A2A_SERVER__HOST", api_host)
    api_port = _required_port(env, "CLOUD_DOG__API_SERVER__PORT")
    web_port = _required_port(env, "CLOUD_DOG__WEB_SERVER__PORT")
    mcp_port = _required_port(env, "CLOUD_DOG__MCP_SERVER__PORT")
    a2a_port = _required_port(env, "CLOUD_DOG__A2A_SERVER__PORT")
    base_url = _process_env_value("TEST_API_BASE_URL", "") or f"http://{api_host}:{api_port}"
    web_url = _process_env_value("TEST_WEB_BASE_URL", "") or f"http://{web_host}:{web_port}"
    mcp_url = _process_env_value("TEST_MCP_BASE_URL", "") or f"http://{mcp_host}:{mcp_port}"
    a2a_url = _process_env_value("TEST_A2A_BASE_URL", "") or f"http://{a2a_host}:{a2a_port}"
    timeout_seconds = _external_precheck_timeout_seconds()
    try:
        _wait_for(f"{base_url}/health", timeout_seconds=timeout_seconds)
        _wait_for(web_url, timeout_seconds=timeout_seconds)
        _wait_for(f"{mcp_url}/health", timeout_seconds=timeout_seconds)
        _wait_for(f"{a2a_url}/health", timeout_seconds=timeout_seconds)
    except Exception as exc:  # noqa: BLE001
        pytest.fail(
            "BLOCKED: external runtime endpoint precondition failed for integration tests. "
            f"mode={_runtime_mode()} api={base_url} web={web_url} mcp={mcp_url} a2a={a2a_url} error={exc}"
        )


@pytest.fixture(scope="function")
def integration_server() -> dict[str, str | bool]:
    global _RUNTIME_EXTERNAL_DETECTED
    env_file = _active_env_file("tests/env-IT")
    env = _load_env_file(env_file)
    api_host = _required_setting(env, "CLOUD_DOG__API_SERVER__HOST")
    web_host = _setting(env, "CLOUD_DOG__WEB_SERVER__HOST", api_host)
    mcp_host = _setting(env, "CLOUD_DOG__MCP_SERVER__HOST", api_host)
    a2a_host = _setting(env, "CLOUD_DOG__A2A_SERVER__HOST", api_host)
    api_port = _required_port(env, "CLOUD_DOG__API_SERVER__PORT")
    web_port = _required_port(env, "CLOUD_DOG__WEB_SERVER__PORT")
    mcp_port = _required_port(env, "CLOUD_DOG__MCP_SERVER__PORT")
    a2a_port = _required_port(env, "CLOUD_DOG__A2A_SERVER__PORT")
    base_url = _process_env_value("TEST_API_BASE_URL", "") or f"http://{api_host}:{api_port}"
    web_url = _process_env_value("TEST_WEB_BASE_URL", "") or f"http://{web_host}:{web_port}"
    mcp_url = _process_env_value("TEST_MCP_BASE_URL", "") or f"http://{mcp_host}:{mcp_port}"
    a2a_url = _process_env_value("TEST_A2A_BASE_URL", "") or f"http://{a2a_host}:{a2a_port}"
    key_file = Path(env.get("GIT_MCP_SEED_KEY_FILE", "./working/it/seed_api_key.txt"))
    _RUNTIME_EXTERNAL_DETECTED = False
    server_control_env = os.environ.copy()
    server_control_env["CLOUD_DOG__API_SERVER__HOST"] = api_host
    server_control_env["CLOUD_DOG__API_SERVER__PORT"] = str(api_port)
    server_control_env["CLOUD_DOG__WEB_SERVER__HOST"] = web_host
    server_control_env["CLOUD_DOG__WEB_SERVER__PORT"] = str(web_port)
    server_control_env["CLOUD_DOG__MCP_SERVER__HOST"] = mcp_host
    server_control_env["CLOUD_DOG__MCP_SERVER__PORT"] = str(mcp_port)
    server_control_env["CLOUD_DOG__A2A_SERVER__HOST"] = a2a_host
    server_control_env["CLOUD_DOG__A2A_SERVER__PORT"] = str(a2a_port)
    server_control_env["GIT_MCP_SEED_KEY_FILE"] = str(key_file)
    server_control_env["CLOUD_DOG__RUNTIME__SEED_KEY_FILE"] = str(key_file)
    if not server_control_env.get("TEST_RUNTIME_MODE", "").strip():
        server_control_env["TEST_RUNTIME_MODE"] = "local-server"
    if not server_control_env.get("CLOUD_DOG__RUNTIME__MODE", "").strip():
        server_control_env["CLOUD_DOG__RUNTIME__MODE"] = server_control_env["TEST_RUNTIME_MODE"]
    if not server_control_env.get("TEST_A2A_API_KEY", "").strip():
        server_control_env["TEST_A2A_API_KEY"] = "12345678"
    if not server_control_env.get("CLOUD_DOG__RUNTIME__A2A_TEST_API_KEY", "").strip():
        server_control_env["CLOUD_DOG__RUNTIME__A2A_TEST_API_KEY"] = server_control_env["TEST_A2A_API_KEY"]
    if not _process_env_value("TEST_A2A_API_KEY", ""):
        os.environ["TEST_A2A_API_KEY"] = server_control_env["TEST_A2A_API_KEY"]
    previous_base_urls = _export_runtime_base_urls(
        base_url=base_url,
        web_url=web_url,
        mcp_url=mcp_url,
        a2a_url=a2a_url,
    )

    if _is_external_server_mode():
        _RUNTIME_EXTERNAL_DETECTED = True
        yield {
            "base_url": base_url,
            "web_url": web_url,
            "mcp_url": mcp_url,
            "a2a_url": a2a_url,
            "external_runtime": True,
            "runtime_mode": _runtime_mode(),
            "env_file": env_file,
        }
        _restore_runtime_base_urls(previous_base_urls)
        _RUNTIME_EXTERNAL_DETECTED = False
        return

    resolved_runtime = _start_servers_with_retry(
        env_file=env_file,
        base_url=base_url,
        web_url=web_url,
        mcp_url=mcp_url,
        a2a_url=a2a_url,
        key_file=key_file,
        server_control_env=server_control_env,
        attempts=3,
    )
    _RUNTIME_EXTERNAL_DETECTED = resolved_runtime == "external"

    yield {
        "base_url": base_url,
        "web_url": web_url,
        "mcp_url": mcp_url,
        "a2a_url": a2a_url,
        "external_runtime": _RUNTIME_EXTERNAL_DETECTED,
        "runtime_mode": resolved_runtime,
        "env_file": env_file,
    }

    _restore_runtime_base_urls(previous_base_urls)
    if not _RUNTIME_EXTERNAL_DETECTED:
        subprocess.run(
            ["./server_control.sh", "--env", env_file, "stop", "all"],
            check=False,
            env=server_control_env,
        )
    _RUNTIME_EXTERNAL_DETECTED = False


@pytest.fixture(scope="function")
def api_key(integration_server: dict[str, str | bool]) -> str:
    base_url = str(integration_server["base_url"])
    env_file = _active_env_file("tests/env-IT")
    env = _load_env_file(env_file)
    key_file = _normalise_host_seed_key_path(
        Path(env.get("GIT_MCP_SEED_KEY_FILE", "./working/it/seed_api_key.txt"))
    )
    external = _is_external_server_mode() or _RUNTIME_EXTERNAL_DETECTED
    sync_from_container = external and bool(_resolve_container_name())

    if external and sync_from_container:
        # Always refresh once from container to avoid stale host-side seed keys.
        _sync_seed_api_key_from_container(key_file)

    deadline = time.time() + 15.0
    configured_keys = [
        env.get("CLOUD_DOG__GIT__API_KEY", "").strip(),
        _process_env_value("CLOUD_DOG__GIT__API_KEY", "").strip(),
        env.get("TEST_A2A_API_KEY", "").strip(),
        _process_env_value("TEST_A2A_API_KEY", "").strip(),
    ]
    while time.time() < deadline:
        if not external and not _server_control_runtime_active():
            external = True
        for candidate in configured_keys:
            if not candidate:
                continue
            try:
                probe = httpx.get(
                    api_url(base_url, "/tools"),
                    headers={"x-api-key": candidate},
                    timeout=3.0,
                )
                if probe.status_code == 200:
                    return candidate
            except Exception:  # noqa: BLE001
                pass
        if key_file.exists():
            candidate = key_file.read_text(encoding="utf-8").strip()
            if candidate:
                try:
                    probe = httpx.get(
                        api_url(base_url, "/tools"),
                        headers={"x-api-key": candidate},
                        timeout=3.0,
                    )
                    if probe.status_code == 200:
                        return candidate
                except Exception:  # noqa: BLE001
                    pass
        if external and sync_from_container:
            _sync_seed_api_key_from_container(key_file)
        time.sleep(0.2)
    raise RuntimeError(f"Seed API key did not validate against running API: {key_file}")


@pytest.fixture(scope="session")
def remote_repo_url() -> str:
    """Return the real remote repo URL from active IT env, failing explicitly when unavailable."""
    urls = _candidate_remote_urls()
    tier = _process_env_value("TEST_ENV_TIER", "")
    if not urls:
        pytest.fail(
            "GIT_MCP_REMOTE_REPO is required for integration remote tests. "
            "Set an authorised remote explicitly in env (or GIT_MCP_REMOTE_REPOS)."
        )

    failures: list[str] = []
    for url in urls:
        auth_error = _remote_authorisation_error(url, tier)
        if auth_error is not None:
            failures.append(f"{url} -> {auth_error}")
            continue

        vault_auth_ok, vault_auth_note = _configure_vault_gitlab_credentials(url)
        if not vault_auth_ok:
            failures.append(f"{url} -> {vault_auth_note}")
            continue

        result = _git_ls_remote(url, timeout=15)
        if result.returncode == 0:
            return url

        stderr = result.stderr.decode(errors="replace").strip()
        detail = stderr or f"ls-remote exit code {result.returncode}"
        failures.append(f"{url} -> unreachable ({detail})")

    details = "\n".join(f"  - {item}" for item in failures)
    pytest.fail(
        f"No authorised reachable remote configured for integration remote tests.\nAttempted remotes:\n{details}"
    )
