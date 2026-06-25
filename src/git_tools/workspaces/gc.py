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

"""Workspace garbage-collection daemon (GM4 / W28C-1705).

The git-mcp container data volume accumulated 699 workspaces (41 stuck in MERGE since
2026-05-06) because nothing reaped them — ``repo_close`` only cleans per-call. This module
provides a background loop that periodically reaps stale ephemeral workspaces + old ephemeral
stuck-merges and warns on disk pressure. The single-cycle ``run_gc_cycle`` is unit-testable;
``workspace_gc_daemon`` is the long-running loop the api surface starts at app lifespan.
"""

from __future__ import annotations

import asyncio
from typing import Any

from cloud_dog_logging import get_logger

from git_tools.workspaces.manager import WorkspaceManager

logger = get_logger(__name__)

DEFAULT_GC_INTERVAL_SECONDS = 3600
DEFAULT_EPHEMERAL_TTL_SECONDS = 86_400  # reap untouched ephemeral workspaces after 1 day
DEFAULT_STUCK_MERGE_REAP_SECONDS = 7 * 86_400  # reap ephemeral stuck-merges after 7 days
DISK_WARN_PERCENT = 80.0


def run_gc_cycle(
    workspace_manager: WorkspaceManager,
    *,
    ttl_seconds: int = DEFAULT_EPHEMERAL_TTL_SECONDS,
    stuck_merge_reap_seconds: int = DEFAULT_STUCK_MERGE_REAP_SECONDS,
    warn_percent: float = DISK_WARN_PERCENT,
) -> dict[str, Any]:
    """Run one GC cycle: reap stale ephemeral + old stuck-merges; warn on disk pressure."""
    result = workspace_manager.gc_disk(
        ttl_seconds=ttl_seconds, stuck_merge_reap_seconds=stuck_merge_reap_seconds
    )
    disk_percent = float(result.get("disk_percent", 0.0))
    if result.get("reaped"):
        logger.info(
            "workspace_gc_reaped",
            extra={
                "event_type": "workspace_gc",
                "reaped": len(result["reaped"]),
                "disk_percent": disk_percent,
                "service": "git-mcp",
            },
        )
    if disk_percent >= warn_percent:
        logger.warning(
            "workspace_disk_pressure",
            extra={
                "event_type": "workspace_disk_pressure",
                "disk_percent": disk_percent,
                "warn_percent": warn_percent,
                "service": "git-mcp",
            },
        )
    return result


async def workspace_gc_daemon(
    workspace_manager: WorkspaceManager,
    *,
    interval_seconds: int = DEFAULT_GC_INTERVAL_SECONDS,
    ttl_seconds: int = DEFAULT_EPHEMERAL_TTL_SECONDS,
    stuck_merge_reap_seconds: int = DEFAULT_STUCK_MERGE_REAP_SECONDS,
) -> None:
    """Background loop running a GC cycle every ``interval_seconds`` until cancelled."""
    while True:
        try:
            await asyncio.sleep(interval_seconds)
            run_gc_cycle(
                workspace_manager,
                ttl_seconds=ttl_seconds,
                stuck_merge_reap_seconds=stuck_merge_reap_seconds,
            )
        except asyncio.CancelledError:
            raise
        except Exception:  # noqa: BLE001 — the daemon must survive a single bad cycle
            logger.warning(
                "workspace_gc_cycle_failed",
                extra={"event_type": "workspace_gc_cycle_failed", "service": "git-mcp"},
                exc_info=True,
            )
