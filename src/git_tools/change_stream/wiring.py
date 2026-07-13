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

"""Wiring helper that builds the git change-watch adapter for the service surfaces.

Constructs a :class:`~git_tools.change_stream.service.WatchService` bound to the
service's ``cloud_dog_db`` engine (durable :class:`SqlJournal`), the platform
``cloud_dog_api_kit.a2a.events`` broadcaster (live SSE fan-out via
``make_broadcast_hook``), the git-mcp ``AuditWriter`` (``cloud_dog_logging``
audit), and a workspace-backed repository resolver for the server-mediated
observation path. Every dependency is the platform-standard one — no bespoke
journal / broadcaster / auth / audit is created here (RULES §1.4).
"""

from __future__ import annotations

import contextlib
from typing import Any

from git_tools.change_stream.service import WatchService, make_audit_sink
from git_tools.git.repo import GitRepository
from git_tools.workspaces.manager import WorkspaceManager


def _make_repo_resolver(workspace_manager: WorkspaceManager):
    """Return a ``profile_id -> GitRepository`` resolver over open workspaces.

    Resolves the most-recently-used OPEN workspace bound to the profile so the
    server-mediated observation path watches a repository the service already
    manages (no fresh clone in the steady-state watch loop — CSTREAM-GIT-002).
    """

    def _resolver(profile_id: str) -> GitRepository:
        candidates = [
            ws
            for ws in workspace_manager.list_workspaces(profile=profile_id)
            if ws.path.exists()
        ]
        if not candidates:
            raise LookupError(f"no open workspace for profile {profile_id!r}")
        # list_workspaces sorts by last_used desc; take the freshest.
        return GitRepository(candidates[0].path)

    return _resolver


def build_watch_service(
    *,
    engine: Any | None = None,
    workspace_manager: WorkspaceManager | None = None,
    broadcaster: Any | None = None,
    audit_writer: Any | None = None,
    broadcast_scheduler: Any | None = None,
    min_fetch_interval_seconds: float | None = None,
) -> WatchService | None:
    """Build the git change-watch adapter, or ``None`` when the foundation is absent.

    The adapter is optional: if the common change-stream foundation is not
    importable (older ``cloud_dog_api_kit``), this returns ``None`` and the
    ``git_watch_*`` tools are simply not registered — the rest of git-mcp is
    unaffected.
    """
    try:  # pragma: no cover - import guard
        from cloud_dog_api_kit.change_stream import WatchCoordinator  # noqa: F401
    except Exception:  # noqa: BLE001
        return None

    audit_sink = make_audit_sink(audit_writer) if audit_writer is not None else None
    repo_resolver = _make_repo_resolver(workspace_manager) if workspace_manager is not None else None

    kwargs: dict[str, Any] = {
        "engine": engine,
        "broadcaster": broadcaster,
        "audit_sink": audit_sink,
        "repo_resolver": repo_resolver,
    }
    if broadcast_scheduler is not None:
        kwargs["broadcast_scheduler"] = broadcast_scheduler
    if min_fetch_interval_seconds is not None:
        kwargs["min_fetch_interval_seconds"] = float(min_fetch_interval_seconds)

    with contextlib.suppress(Exception):
        return WatchService(**kwargs)
    # A construction failure (e.g. schema race) must not break service startup;
    # the git_watch_* tools are additive.
    return None
