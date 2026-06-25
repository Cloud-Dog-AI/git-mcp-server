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

"""Thread-a (PROGRAM-IDAM-RECOVERY-2) flat WebUI roles for git-mcp-server.

Thread a is the *simple, flat* login that gets the demo back: three roles —
``admin`` (full), ``read-write`` (use it), ``read-only`` (view). No
granularity (that is Thread b). Roles are computed via the ONE shared guard
(``cloud_dog_idam.RBACEngine`` + the canonical PS-82 §7 permission catalog) —
there is no per-service RBAC fork here; this module only *names* the three
flat roles and derives their permission sets from the shared catalog.

git-mcp's WebUI login surface is the *api_key* sign-in (``config.auth.mode`` is
``api_key``); the front-door is still public so the login box renders, and the
three flat roles below are what a session resolves to once authenticated. The
shared idam ships two baseline roles (``admin`` -> ``*`` and ``user`` -> the
PS-82 §7.2 default grant). The flat lane maps:

* ``admin``      -> the shared ``admin`` baseline (wildcard ``*``).
* ``read-write`` -> the shared ``user`` baseline PLUS the git write/execute
  permissions a demo operator needs to actually *use* the system.
* ``read-only``  -> the shared ``user`` baseline only (view + self-service);
  every write resolves to a 403 at the enforcement point (never a blank UI).
"""

from __future__ import annotations

from cloud_dog_idam import RBACEngine  # type: ignore[import-untyped]
from cloud_dog_idam.rbac import role_catalog as _rc  # type: ignore[import-untyped]

# The shared idam wildcard ("*") is the one stable, always-present symbol.
WILDCARD_PERMISSION: str = getattr(_rc, "WILDCARD_PERMISSION", "*")


def _shared_user_baseline() -> set[str]:
    """Return the shared idam ``user`` baseline grant.

    Thread a anchors read-write/read-only on the SAME ``user`` baseline every
    other service inherits, so the flat roles stay consistent with the central
    catalog and there is no per-service fork. The richer a0 catalog
    (``USER_BASELINE_PERMISSIONS`` + named git grants) is still landing on
    shared main; until it is published the deployed idam exposes the baseline
    via ``BASELINE_ROLE_PERMISSIONS["user"]`` (currently ``{"resources:read"}``).
    Resolve whichever the installed idam provides so a5 builds against both the
    current AND the post-a0 idam — never crashing on an import of a symbol that
    has not landed yet.
    """
    explicit = getattr(_rc, "USER_BASELINE_PERMISSIONS", None)
    if explicit:
        return set(explicit)
    baseline = getattr(_rc, "BASELINE_ROLE_PERMISSIONS", {}) or {}
    user_grant = baseline.get("user")
    if user_grant:
        return set(user_grant)
    # Last-resort floor: a read-only view grant so a read-only session is never
    # empty (fail-safe, still view-only).
    return {"resources:read"}


#: The three flat roles, in descending privilege order.
ADMIN_ROLE = "admin"
READ_WRITE_ROLE = "read-write"
READ_ONLY_ROLE = "read-only"

FLAT_ROLES: tuple[str, ...] = (ADMIN_ROLE, READ_WRITE_ROLE, READ_ONLY_ROLE)

#: Map each flat role onto git-mcp's own tool-RBAC vocabulary (``config.rbac.roles``
#: = ``admin`` / ``maintainer`` / ``writer`` / ``reader``, keyed by tool-name
#: glob patterns). This is what the API tier enforces on every ``call_tool``: on
#: the SPA reaches ``/api/v1`` straight through the reverse proxy (bypassing the web
#: proxy), so a cookie session carries only its flat role — the API server must
#: translate it into tool-RBAC role(s) to authorise tool calls. ``read-only`` maps
#: to ``reader`` (view tools only — every write tool resolves to a 403, never a
#: blank UI); ``read-write`` maps to BOTH ``writer`` AND ``reader`` (so the
#: read-write operator keeps every read grant — e.g. ``search_*``, which the
#: ``writer`` pattern set alone omits — strictly on top of write access, preserving
#: read-write >= read-only); ``admin`` stays ``admin`` (``*``). This is a NAMING
#: bridge onto the existing shared-guard catalogue, not a fork — no role patterns
#: are redefined here.
FLAT_TO_TOOL_ROLE: dict[str, tuple[str, ...]] = {
    ADMIN_ROLE: ("admin",),
    READ_WRITE_ROLE: ("writer", "reader"),
    READ_ONLY_ROLE: ("reader",),
}

# git-mcp use-permissions the read-write operator needs on top of the shared
# §7.2 user baseline. These are the canonical git RBAC verbs the service
# authorises on (see defaults.yaml rbac.roles). Kept minimal and flat; Thread b
# adds granularity.
_GIT_USE_PERMISSIONS: set[str] = {
    "git:read",
    "git:write",
    "git:execute",
}

#: Flat role -> permission set, built from the shared canonical catalog.
#: ``admin`` is the shared wildcard; ``read-write`` and ``read-only`` are both
#: anchored on the shared ``user`` baseline so they stay consistent with every
#: other service that inherits the same idam.
FLAT_ROLE_PERMISSIONS: dict[str, set[str]] = {
    ADMIN_ROLE: {WILDCARD_PERMISSION},
    READ_WRITE_ROLE: (_shared_user_baseline() | _GIT_USE_PERMISSIONS),
    READ_ONLY_ROLE: _shared_user_baseline(),
}


def normalise_flat_role(role: str | None) -> str:
    """Map an arbitrary role string onto one of the three flat roles.

    Anything that is not clearly admin / read-write resolves to the safest
    flat role (``read-only``) so an unknown role can never silently gain
    write access (fail-closed).
    """
    raw = str(role or "").strip().lower().replace("_", "-")
    if raw in {ADMIN_ROLE, "owner", "superuser", "super-admin"}:
        return ADMIN_ROLE
    if raw in {
        READ_WRITE_ROLE,
        "readwrite",
        "writer",
        "editor",
        "maintainer",
        "user",
        "member",
    }:
        return READ_WRITE_ROLE
    return READ_ONLY_ROLE


def flat_role_from_tool_roles(tool_roles: object) -> str:
    """Map a set of git-mcp tool-RBAC roles back onto a flat role (fail-safe).

    Inverse of [[FLAT_TO_TOOL_ROLE]] for the api_key sign-in (W28A-731): the API
    tier resolves a managed key to its tool roles (``admin`` / ``writer`` /
    ``maintainer`` / ``reader``); the web ``/auth/me`` calls this to present the
    flat role. Fail-safe to ``read-only`` (view-only) so an unrecognised/empty
    role set never yields a blank-or-elevated principal.
    """
    roles = {str(r).strip().lower() for r in (tool_roles or []) if str(r).strip()}
    if "admin" in roles:
        return ADMIN_ROLE
    if roles & {"writer", "maintainer"}:
        return READ_WRITE_ROLE
    return READ_ONLY_ROLE


def build_flat_rbac_engine() -> RBACEngine:
    """Return the ONE shared RBACEngine loaded with the flat role catalog."""
    return RBACEngine(
        role_permissions={name: set(perms) for name, perms in FLAT_ROLE_PERMISSIONS.items()}
    )


def permissions_for_role(role: str) -> list[str]:
    """Return the sorted effective permissions for a flat role via the shared engine."""
    flat = normalise_flat_role(role)
    engine = build_flat_rbac_engine()
    uid = f"flat:{flat}"
    engine.assign_role_to_user(uid, flat)
    return sorted(engine.get_effective_permissions(uid))


def role_can_write(role: str) -> bool:
    """True when the flat role may perform write/mutation operations."""
    return normalise_flat_role(role) in {ADMIN_ROLE, READ_WRITE_ROLE}


def role_is_admin(role: str) -> bool:
    """True when the flat role is the full-admin flat role."""
    return normalise_flat_role(role) == ADMIN_ROLE
