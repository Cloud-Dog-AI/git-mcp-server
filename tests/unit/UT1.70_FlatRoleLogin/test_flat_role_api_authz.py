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

"""W28A-731-R5 — flat-role enforcement on the API tier (the LIVE preprod path).

On preprod, Traefik routes ``/api/v1/*`` straight to the API server, bypassing
the web proxy. A cookie web session therefore reaches the API tier carrying only
its flat role on ``request.state.web_session_user`` (set by the CompatAuth cookie
fallback after validating against the web server's ``/auth/me``). The API server
authorises every ``call_tool`` with ``cloud_dog_idam.RBACEngine`` +
``config.rbac.roles`` (``admin`` / ``maintainer`` / ``writer`` / ``reader``),
which is keyed on tool names — NOT on the flat-role vocabulary.

R4 proved flat login only through the web tier (TestClient against the web
proxy), so it never exercised this path: a ``read-write`` / ``read-only`` cookie
display-name resolves to NO idam role-binding, so ``resolve_roles`` returns an
empty set and the default-deny RBAC engine blocks EVERY tool (a blank UI). These
tests lock the R5 fix: ``_roles_from_request`` maps the cookie flat role onto the
tool-RBAC vocabulary, and the resulting authorisation decision is proven against
the REAL shipped ``config.rbac.roles`` catalogue.
"""

from __future__ import annotations

from types import SimpleNamespace

import pytest
from cloud_dog_idam import RBACEngine

from git_mcp_server import api_server
from git_tools.config.loader import bind_global_config, load_raw_config
from git_tools.security.rbac import AccessDeniedError, can_execute_tool, require_tool_access


def _request(web_session_user: dict | None, *, api_key: str = "") -> SimpleNamespace:
    """Build a minimal stand-in Request carrying a cookie web-session principal."""
    headers = {"x-api-key": api_key} if api_key else {}
    return SimpleNamespace(
        headers=headers,
        state=SimpleNamespace(web_session_user=web_session_user),
    )


class _StubApiKeyManager:
    def validate(self, _key: str):  # noqa: D401 - test stub
        return None


_AUTH_RUNTIME = SimpleNamespace(api_key_manager=_StubApiKeyManager(), token_service=None)
# resolve_roles MUST NOT be the path that grants a cookie principal access; if the
# mapping branch is ever removed this stub returns [] and the tests fail loudly.
_ADMIN_RUNTIME = SimpleNamespace(
    resolve_roles=lambda actor, **_: [],
    api_key_metadata={},
)


@pytest.fixture(scope="module")
def tool_role_map() -> dict[str, list[str]]:
    """The REAL shipped tool-RBAC catalogue (config.rbac.roles from defaults.yaml)."""
    config = bind_global_config(load_raw_config(env_files=["tests/env-UT"]))
    roles = dict(config.rbac.roles)
    # Sanity: the vocabulary the flat roles bridge onto must exist.
    assert {"admin", "writer", "reader"} <= set(roles)
    return roles


def _decide(tool_role_map: dict[str, list[str]], roles: set[str], tool: str) -> bool:
    """Mirror api_server.call_tool's authorisation decision for one tool."""
    engine = RBACEngine(role_permissions={r: set(p) for r, p in tool_role_map.items()})
    actor = "flat-principal"
    for role in roles:
        engine.assign_role_to_user(actor, role)
    return can_execute_tool(engine, tool_role_map, actor, tool)


# --------------------------------------------------------------------------- #
# _roles_from_request maps the cookie flat role onto the tool-RBAC vocabulary
# --------------------------------------------------------------------------- #
# Covers: CS-1.2 (W28A-731 flat-role login + RBAC)
@pytest.mark.UT
@pytest.mark.mcp
@pytest.mark.req("FR-022")  # W28E-1804A semantic rebind
def test_admin_cookie_maps_to_admin_role() -> None:
    roles = api_server._roles_from_request(
        _request({"displayName": "admin", "roles": ["admin"]}),
        actor="admin",
        admin_runtime=_ADMIN_RUNTIME,
        auth_runtime=_AUTH_RUNTIME,
    )
    assert roles == {"admin"}


# Covers: CS-1.2 (W28A-731 flat-role login + RBAC)
@pytest.mark.UT
@pytest.mark.mcp
@pytest.mark.req("FR-022")  # W28E-1804A semantic rebind
def test_read_write_cookie_maps_to_writer_and_reader() -> None:
    roles = api_server._roles_from_request(
        _request({"displayName": "read-write", "roles": ["read-write"]}),
        actor="read-write",
        admin_runtime=_ADMIN_RUNTIME,
        auth_runtime=_AUTH_RUNTIME,
    )
    assert roles == {"writer", "reader"}


# Covers: CS-1.2 (W28A-731 flat-role login + RBAC)
@pytest.mark.UT
@pytest.mark.mcp
@pytest.mark.req("FR-022")  # W28E-1804A semantic rebind
def test_read_only_cookie_maps_to_reader_only() -> None:
    roles = api_server._roles_from_request(
        _request({"displayName": "read-only", "roles": ["read-only"]}),
        actor="read-only",
        admin_runtime=_ADMIN_RUNTIME,
        auth_runtime=_AUTH_RUNTIME,
    )
    assert roles == {"reader"}


# --------------------------------------------------------------------------- #
# The mapped roles authorise correctly against the REAL tool catalogue
# --------------------------------------------------------------------------- #
# Covers: CS-1.2 (W28A-731 flat-role login + RBAC)
@pytest.mark.UT
@pytest.mark.mcp
@pytest.mark.req("FR-022")  # W28E-1804A semantic rebind
def test_read_only_can_read_but_not_write(tool_role_map: dict[str, list[str]]) -> None:
    roles = api_server._roles_from_request(
        _request({"displayName": "read-only", "roles": ["read-only"]}),
        actor="read-only",
        admin_runtime=_ADMIN_RUNTIME,
        auth_runtime=_AUTH_RUNTIME,
    )
    # read-only (reader) may VIEW: never a blank UI.
    for read_tool in ("repo_open", "git_status", "git_log", "git_diff", "git_branch_list", "file_read"):
        assert _decide(tool_role_map, roles, read_tool), f"read-only denied read tool {read_tool}"
    # ...but every write tool resolves to a denial (the API tier raises 403).
    for write_tool in ("git_commit", "git_push", "git_add", "file_write", "file_delete", "git_tag_create"):
        assert not _decide(tool_role_map, roles, write_tool), f"read-only ALLOWED write tool {write_tool}"
        with pytest.raises(AccessDeniedError):
            engine = RBACEngine(role_permissions={r: set(p) for r, p in tool_role_map.items()})
            for role in roles:
                engine.assign_role_to_user("ro", role)
            require_tool_access(engine, tool_role_map, "ro", write_tool)


# Covers: CS-1.2 (W28A-731 flat-role login + RBAC)
@pytest.mark.UT
@pytest.mark.mcp
@pytest.mark.req("FR-022")  # W28E-1804A semantic rebind
def test_read_write_can_read_write_and_search(tool_role_map: dict[str, list[str]]) -> None:
    roles = api_server._roles_from_request(
        _request({"displayName": "read-write", "roles": ["read-write"]}),
        actor="read-write",
        admin_runtime=_ADMIN_RUNTIME,
        auth_runtime=_AUTH_RUNTIME,
    )
    for tool in ("git_status", "git_commit", "git_push", "file_write", "repo_open", "search_content"):
        assert _decide(tool_role_map, roles, tool), f"read-write denied {tool}"
    # read-write stays below admin: no identity-admin tools.
    assert not _decide(tool_role_map, roles, "admin_user_create")


# Covers: CS-1.2 (W28A-731 flat-role login + RBAC)
@pytest.mark.UT
@pytest.mark.mcp
@pytest.mark.req("FR-022")  # W28E-1804A semantic rebind
def test_admin_can_do_everything(tool_role_map: dict[str, list[str]]) -> None:
    roles = api_server._roles_from_request(
        _request({"displayName": "admin", "roles": ["admin"]}),
        actor="admin",
        admin_runtime=_ADMIN_RUNTIME,
        auth_runtime=_AUTH_RUNTIME,
    )
    for tool in ("git_commit", "git_push", "admin_user_create", "search_content", "file_write"):
        assert _decide(tool_role_map, roles, tool), f"admin denied {tool}"


# Covers: CS-1.2 (W28A-731 flat-role login + RBAC)
@pytest.mark.UT
@pytest.mark.mcp
@pytest.mark.req("FR-022")  # W28E-1804A semantic rebind
def test_read_write_superset_of_read_only(tool_role_map: dict[str, list[str]]) -> None:
    """Privilege ordering: every tool read-only can call, read-write can call too."""
    ro = api_server._roles_from_request(
        _request({"displayName": "read-only", "roles": ["read-only"]}),
        actor="read-only",
        admin_runtime=_ADMIN_RUNTIME,
        auth_runtime=_AUTH_RUNTIME,
    )
    rw = api_server._roles_from_request(
        _request({"displayName": "read-write", "roles": ["read-write"]}),
        actor="read-write",
        admin_runtime=_ADMIN_RUNTIME,
        auth_runtime=_AUTH_RUNTIME,
    )
    for tool in ("repo_open", "git_status", "git_log", "git_diff", "git_branch_list",
                 "git_tag_list", "file_read", "file_download", "dir_list", "search_content"):
        if _decide(tool_role_map, ro, tool):
            assert _decide(tool_role_map, rw, tool), f"read-write LOST read grant {tool}"
