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

"""Shared test helpers for git-mcp-server."""

from __future__ import annotations

import os
from pathlib import Path

from git import Repo


def _normalise_base_path(raw: str, default: str) -> str:
    """Normalise route base paths from env contract keys."""
    value = raw.strip() or default
    if value == "/":
        return "/"
    value = value.rstrip("/")
    if not value.startswith("/"):
        value = f"/{value}"
    return value


def _route_path(base_path: str, suffix: str) -> str:
    route = suffix.strip()
    if route and not route.startswith("/"):
        route = f"/{route}"
    if base_path == "/":
        return route or "/"
    return f"{base_path}{route}"


def test_api_base_path() -> str:
    """Return API base path from env contract."""
    return _normalise_base_path(os.environ.get("TEST_API_BASE_PATH", ""), "/api/v1")


def test_mcp_base_path() -> str:
    """Return MCP base path from env contract."""
    return _normalise_base_path(os.environ.get("TEST_MCP_BASE_PATH", ""), "/mcp")


def test_web_base_path() -> str:
    """Return Web base path from env contract."""
    return _normalise_base_path(os.environ.get("TEST_WEB_BASE_PATH", ""), "/")


def test_a2a_base_path() -> str:
    """Return A2A base path from env contract."""
    return _normalise_base_path(os.environ.get("TEST_A2A_BASE_PATH", ""), "/a2a")


def api_url(base_url: str, suffix: str = "") -> str:
    """Build API URL from env-derived API base path."""
    return f"{base_url.rstrip('/')}{_route_path(test_api_base_path(), suffix)}"


def mcp_url(base_url: str, suffix: str = "") -> str:
    """Build MCP URL from env-derived MCP base path."""
    return f"{base_url.rstrip('/')}{_route_path(test_mcp_base_path(), suffix)}"


def a2a_url(base_url: str, suffix: str = "") -> str:
    """Build A2A URL from env-derived A2A base path."""
    target_base = os.environ.get("TEST_A2A_BASE_URL", "").strip() or base_url
    return f"{target_base.rstrip('/')}{_route_path(test_a2a_base_path(), suffix)}"


def legacy_api_url(base_url: str, suffix: str = "") -> str:
    """Build legacy compatibility URL for /app/v1 alias checks."""
    return f"{base_url.rstrip('/')}{_route_path('/app/v1', suffix)}"


def create_repo(path: Path) -> Repo:
    """Create a local git repository with a single initial commit."""
    path.mkdir(parents=True, exist_ok=True)
    repo = Repo.init(path)
    repo.git.config("user.email", "test@example.com")
    repo.git.config("user.name", "Test User")
    file_path = path / "README.md"
    file_path.write_text("hello\n", encoding="utf-8")
    repo.index.add(["README.md"])
    repo.index.commit("initial")
    return repo


def create_repo_with_remote(path: Path, remote_path: Path) -> tuple[Repo, Repo]:
    """Create local and bare remote repositories."""
    repo = create_repo(path)
    remote_path.mkdir(parents=True, exist_ok=True)
    bare = Repo.init(remote_path, bare=True)
    repo.create_remote("origin", remote_path.as_posix())
    repo.git.push("-u", "origin", "HEAD:main")
    bare.git.symbolic_ref("HEAD", "refs/heads/main")
    return repo, bare


def set_test_api_key(key: str) -> None:
    """Set x-api-key for integration tests."""
    os.environ["GIT_MCP_TEST_API_KEY"] = key
