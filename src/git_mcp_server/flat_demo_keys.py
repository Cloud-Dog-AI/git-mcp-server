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

"""W28A-731-R5 — the three flat-login demo api-keys, seeded on EVERY tier.

git-mcp is api_key-mode: the three flat roles (admin / read-write / read-only) log
in by api-key. Each tier (API server, MCP server) runs as a SEPARATE process with
its own ``APIKeyManager``, so the demo keys must be DETERMINISTIC — derived from a
stable shared seed (the configured ``git.api_key``) — for every process to register
the SAME key for each flat role. That makes a read-only key resolve to ``reader``
on the API tier AND the MCP tier, so a read-only WRITE is denied (403) on every
transport, not just the API tier.

The owner ids + tool-RBAC role bindings mirror ``web_flat_roles.FLAT_TO_TOOL_ROLE``
(admin -> admin; read-write -> writer+reader; read-only -> reader). The raw keys are
also written to a container-readable runtime path for the WebUI/Playwright demo
(NEVER committed — §9.2).
"""

from __future__ import annotations

import hashlib
import hmac
from pathlib import Path
from typing import Any
from uuid import uuid4

from cloud_dog_idam.api_keys.hashing import hash_api_key
from cloud_dog_idam.domain.models import ApiKey

from git_mcp_server.web_flat_roles import ADMIN_ROLE, READ_ONLY_ROLE, READ_WRITE_ROLE

#: (owner_user_id, flat-role, tool-RBAC roles) — one per flat role.
FLAT_DEMO_OWNERS: tuple[tuple[str, str, set[str]], ...] = (
    ("flat-admin", ADMIN_ROLE, {"admin"}),
    ("flat-read-write", READ_WRITE_ROLE, {"writer", "reader"}),
    ("flat-read-only", READ_ONLY_ROLE, {"reader"}),
)


def derive_flat_demo_keys(seed: str | None) -> dict[str, str]:
    """Deterministically derive the 3 flat demo api-keys from a stable seed.

    Seed = the configured ``git.api_key`` (identical across the API and MCP
    processes); falls back to a fixed label when unset so the keys are still stable
    within a run. Same seed -> same three keys in every process -> consistent
    cross-tier role resolution.
    """
    base = (str(seed or "").strip() or "git-mcp-flat-demo-seed").encode("utf-8")
    keys: dict[str, str] = {}
    for _owner, flat, _roles in FLAT_DEMO_OWNERS:
        digest = hmac.new(base, flat.encode("utf-8"), hashlib.sha256).hexdigest()
        keys[flat] = f"flatk-{flat}-{digest[:32]}"
    return keys


def register_flat_demo_keys(
    api_key_manager: Any,
    role_bindings: dict[str, set[str]],
    seed: str | None,
) -> dict[str, str]:
    """Register the 3 deterministic flat demo keys + their role bindings.

    Idempotent: skips a key already present (so re-deriving in another tier or on a
    re-run is safe). Returns ``{flat-role: raw-key}``.
    """
    keys = derive_flat_demo_keys(seed)
    for owner, flat, roles in FLAT_DEMO_OWNERS:
        role_bindings[owner] = set(roles)
        raw = keys[flat]
        if api_key_manager.validate(raw) is None:
            item = ApiKey(
                api_key_id=str(uuid4()),
                owner_user_id=owner,
                key_prefix=raw[:3],
                key_hash=hash_api_key(raw),
                status="active",
            )
            api_key_manager._keys[item.api_key_id] = item
    return keys


def write_flat_demo_keys(keys: dict[str, str], keys_dir: Path) -> None:
    """Write the 3 raw keys to a container-readable runtime dir (mode 0600).

    Best-effort: a write failure must never break startup (the keys still work
    in-memory; the demo just re-derives/reads from the running tier instead).
    """
    keys_dir.mkdir(parents=True, exist_ok=True)
    for flat, raw in keys.items():
        key_file = keys_dir / f"{flat}.key"
        key_file.write_text(raw + "\n", encoding="utf-8")
        key_file.chmod(0o600)
