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
import subprocess
import time
from pathlib import Path

import httpx
import pytest

from tests.helpers import api_url


def _process_env_value(key: str, default: str = "") -> str:
    """Read a process environment variable using index lookup only."""
    if key not in os.environ:
        return default
    value = os.environ[key].strip()
    return value if value else default


def _load_env_file(path: str) -> dict[str, str]:
    values: dict[str, str] = {}
    for line in Path(path).read_text(encoding="utf-8").splitlines():
        raw = line.strip()
        if not raw or raw.startswith("#") or "=" not in raw:
            continue
        key, value = raw.split("=", 1)
        values[key.strip()] = value.strip()
    return values


def _active_env_file(default_path: str) -> str:
    value = _process_env_value("TEST_ENV_FILE", "")
    if not value:
        return default_path
    name = Path(value).name.lower()
    if name.startswith("env-db-"):
        return default_path
    if not name.startswith("env-at"):
        return default_path
    return value


def _setting(env_map: dict[str, str], key: str, default: str) -> str:
    """Resolve setting from env file values, then process env, then default."""
    from_file = env_map.get(key, "").strip()
    if from_file:
        return from_file
    from_process = _process_env_value(key, "")
    if from_process:
        return from_process
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
    """Restore process-level runtime URL overrides after the application session."""
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
    legacy = _process_env_value("GIT_MCP_USE_EXTERNAL_SERVER", "").lower()
    if legacy in ("1", "true", "yes"):
        return True
    if legacy in ("0", "false", "no"):
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
            "/app/working/at/seed_api_key.txt",
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


def _wait_for(url: str, timeout_seconds: float = 30.0) -> None:
    deadline = time.time() + timeout_seconds
    while time.time() < deadline:
        try:
            response = httpx.get(url, timeout=2.0)
            if response.status_code < 500:
                return
        except Exception:  # noqa: BLE001
            pass
        time.sleep(0.4)
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
) -> None:
    """Start local application servers and wait for a stable, validated runtime."""
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
            return
        except Exception as exc:  # noqa: BLE001
            last_error = exc
            subprocess.run(
                ["./server_control.sh", "--env", env_file, "stop", "all"],
                check=False,
                env=server_control_env,
            )
            time.sleep(float(attempt))
    if last_error is not None:
        raise RuntimeError(f"Failed to start application servers after {attempts} attempts: {last_error}")
    raise RuntimeError(f"Failed to start application servers after {attempts} attempts")


@pytest.fixture(scope="session", autouse=True)
def _application_external_runtime_precheck() -> None:
    """Fail fast once when external application endpoint is not reachable."""
    if not _use_external_runtime():
        return
    env_file = _active_env_file("tests/env-AT")
    env = _load_env_file(env_file)
    api_host = _required_setting(env, "CLOUD_DOG__API_SERVER__HOST")
    web_host = _setting(env, "CLOUD_DOG__WEB_SERVER__HOST", api_host)
    mcp_host = _setting(env, "CLOUD_DOG__MCP_SERVER__HOST", api_host)
    a2a_host = _setting(env, "CLOUD_DOG__A2A_SERVER__HOST", api_host)
    api_port = _required_port(env, "CLOUD_DOG__API_SERVER__PORT")
    web_port = _required_port(env, "CLOUD_DOG__WEB_SERVER__PORT")
    mcp_port = _required_port(env, "CLOUD_DOG__MCP_SERVER__PORT")
    a2a_port = _required_port(env, "CLOUD_DOG__A2A_SERVER__PORT")
    base_url = _setting(env, "TEST_API_BASE_URL", "") or f"http://{api_host}:{api_port}"
    web_url = _setting(env, "TEST_WEB_BASE_URL", "") or f"http://{web_host}:{web_port}"
    mcp_url = _setting(env, "TEST_MCP_BASE_URL", "") or f"http://{mcp_host}:{mcp_port}"
    a2a_url = _setting(env, "TEST_A2A_BASE_URL", "") or f"http://{a2a_host}:{a2a_port}"
    timeout_seconds = _external_precheck_timeout_seconds()
    try:
        _wait_for(f"{base_url}/health", timeout_seconds=timeout_seconds)
        _wait_for(web_url, timeout_seconds=timeout_seconds)
        _wait_for(f"{mcp_url}/health", timeout_seconds=timeout_seconds)
        _wait_for(f"{a2a_url}/health", timeout_seconds=timeout_seconds)
    except Exception as exc:  # noqa: BLE001
        pytest.fail(
            "BLOCKED: external runtime endpoint precondition failed for application tests. "
            f"mode={_runtime_mode()} api={base_url} web={web_url} mcp={mcp_url} a2a={a2a_url} error={exc}"
        )


@pytest.fixture()
def application_server() -> str:
    env_file = _active_env_file("tests/env-AT")
    env = _load_env_file(env_file)
    api_host = _required_setting(env, "CLOUD_DOG__API_SERVER__HOST")
    web_host = _setting(env, "CLOUD_DOG__WEB_SERVER__HOST", api_host)
    mcp_host = _setting(env, "CLOUD_DOG__MCP_SERVER__HOST", api_host)
    a2a_host = _setting(env, "CLOUD_DOG__A2A_SERVER__HOST", api_host)
    api_port = _required_port(env, "CLOUD_DOG__API_SERVER__PORT")
    web_port = _required_port(env, "CLOUD_DOG__WEB_SERVER__PORT")
    mcp_port = _required_port(env, "CLOUD_DOG__MCP_SERVER__PORT")
    a2a_port = _required_port(env, "CLOUD_DOG__A2A_SERVER__PORT")
    base_url = _setting(env, "TEST_API_BASE_URL", "") or f"http://{api_host}:{api_port}"
    web_url = _setting(env, "TEST_WEB_BASE_URL", "") or f"http://{web_host}:{web_port}"
    mcp_url = _setting(env, "TEST_MCP_BASE_URL", "") or f"http://{mcp_host}:{mcp_port}"
    a2a_url = _setting(env, "TEST_A2A_BASE_URL", "") or f"http://{a2a_host}:{a2a_port}"
    key_file = Path(env.get("GIT_MCP_SEED_KEY_FILE", "./working/at/seed_api_key.txt"))
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

    if _use_external_runtime():
        yield base_url
        _restore_runtime_base_urls(previous_base_urls)
        return

    _start_servers_with_retry(
        env_file=env_file,
        base_url=base_url,
        web_url=web_url,
        mcp_url=mcp_url,
        a2a_url=a2a_url,
        key_file=key_file,
        server_control_env=server_control_env,
        attempts=3,
    )

    yield base_url

    _restore_runtime_base_urls(previous_base_urls)
    subprocess.run(
        ["./server_control.sh", "--env", env_file, "stop", "all"],
        check=False,
        env=server_control_env,
    )


@pytest.fixture()
def application_api_key(application_server: str) -> str:
    _ = application_server
    env_file = _active_env_file("tests/env-AT")
    env = _load_env_file(env_file)
    key_file = Path(env.get("GIT_MCP_SEED_KEY_FILE", "./working/at/seed_api_key.txt"))
    external = _use_external_runtime()
    sync_from_container = external and bool(_resolve_container_name())

    if sync_from_container:
        _sync_seed_api_key_from_container(key_file)

    deadline = time.time() + 15.0
    while time.time() < deadline:
        if key_file.exists():
            candidate = key_file.read_text(encoding="utf-8").strip()
            if candidate:
                try:
                    probe = httpx.get(
                        api_url(application_server, "/tools"),
                        headers={"x-api-key": candidate},
                        timeout=3.0,
                    )
                    if probe.status_code == 200:
                        return candidate
                except Exception:  # noqa: BLE001
                    pass
        if sync_from_container:
            _sync_seed_api_key_from_container(key_file)
        time.sleep(0.2)

    raise RuntimeError(f"Seed API key did not validate against running API: {key_file}")
