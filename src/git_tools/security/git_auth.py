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

import subprocess
from collections.abc import MutableMapping
from urllib.parse import urlparse

from cloud_dog_cache import cache_key
from cloud_dog_config import get_config

# Module-level single-value cache for _load_gitlab_auth (sync equivalent of
# @cached(ttl=0)).  The cloud_dog_cache @cached decorator is async-only;
# since this function and its entire call-chain are synchronous we use the
# cache_key helper for consistent key generation and a simple sentinel.
_gitlab_auth_cache: dict[str, tuple[str, str] | None] = {}
_GITLAB_AUTH_CACHE_KEY = cache_key("git_tools.security.git_auth._load_gitlab_auth")


def _load_gitlab_auth() -> tuple[str, str] | None:
    """Return (hostname, token) from the compiled storage.gitlab config when available."""
    if _GITLAB_AUTH_CACHE_KEY in _gitlab_auth_cache:
        return _gitlab_auth_cache[_GITLAB_AUTH_CACHE_KEY]

    try:
        gitlab_url = str(get_config("storage.gitlab.url") or "").strip()
        gitlab_token = str(
            get_config("storage.gitlab.developer_token")
            or get_config("storage.gitlab.maintainer_token")
            or ""
        ).strip()
    except Exception:  # noqa: BLE001
        _gitlab_auth_cache[_GITLAB_AUTH_CACHE_KEY] = None
        return None
    parsed = urlparse(gitlab_url)
    if not parsed.hostname or not gitlab_token:
        _gitlab_auth_cache[_GITLAB_AUTH_CACHE_KEY] = None
        return None
    result = parsed.hostname, gitlab_token
    _gitlab_auth_cache[_GITLAB_AUTH_CACHE_KEY] = result
    return result


def _inject_git_config_env(env: MutableMapping[str, str], key: str, value: str) -> None:
    """Append GIT_CONFIG_* key/value to an env mapping idempotently."""
    raw_count = env.get("GIT_CONFIG_COUNT", "0").strip() or "0"
    try:
        count = int(raw_count)
    except ValueError:
        count = 0
    for index in range(count):
        if env.get(f"GIT_CONFIG_KEY_{index}") == key and env.get(f"GIT_CONFIG_VALUE_{index}") == value:
            return
    env[f"GIT_CONFIG_KEY_{count}"] = key
    env[f"GIT_CONFIG_VALUE_{count}"] = value
    env["GIT_CONFIG_COUNT"] = str(count + 1)


def prime_git_https_credentials(env: MutableMapping[str, str], remote_url: str) -> bool:
    """Prime git credential cache for Vault-managed GitLab HTTPS remotes."""
    parsed_remote = urlparse(remote_url)
    if parsed_remote.scheme not in {"http", "https"} or not parsed_remote.hostname:
        return False

    gitlab_auth = _load_gitlab_auth()
    if gitlab_auth is None:
        return False

    gitlab_hostname, gitlab_token = gitlab_auth
    if parsed_remote.hostname != gitlab_hostname:
        return False

    _inject_git_config_env(env, "credential.helper", "cache --timeout=900")
    _inject_git_config_env(env, "credential.useHttpPath", "true")
    env["GIT_CONFIG_GLOBAL"] = "/dev/null"
    env["GIT_TERMINAL_PROMPT"] = "0"

    path_value = parsed_remote.path.lstrip("/")
    approve_payload = (
        f"protocol={parsed_remote.scheme}\n"
        f"host={parsed_remote.hostname}\n"
        f"path={path_value}\n"
        "username=oauth2\n"
        f"password={gitlab_token}\n\n"
    )
    result = subprocess.run(
        ["git", "credential", "approve"],
        input=approve_payload,
        text=True,
        capture_output=True,
        timeout=10,
        check=False,
        env=dict(env),
    )
    return result.returncode == 0
