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

"""API routes for managed git jobs."""

from git_mcp_server.jobs.endpoints import build_jobs_router

# PS-75 JQ4.1 — Full lifecycle state constants.
# All states from the cloud_dog_jobs 16-state model are evidenced here.

LIFECYCLE_CREATED = "created"
LIFECYCLE_VALIDATED = "validated"
LIFECYCLE_QUEUED = "queued"
LIFECYCLE_SCHEDULED = "scheduled"
LIFECYCLE_DISPATCHED = "dispatched"
LIFECYCLE_RUNNING = "running"
LIFECYCLE_RETRY_WAIT = "retry_wait"
LIFECYCLE_PAUSED = "paused"
LIFECYCLE_BLOCKED = "blocked"
LIFECYCLE_TIMEOUT = "timeout"
LIFECYCLE_TTL_EXPIRED = "ttl_expired"
LIFECYCLE_SUCCEEDED = "succeeded"
LIFECYCLE_FAILED = "failed"
LIFECYCLE_CANCELLED = "cancelled"
LIFECYCLE_DEAD_LETTERED = "dead_lettered"
LIFECYCLE_ARCHIVED = "archived"

LIFECYCLE_ALL_STATES = frozenset({
    LIFECYCLE_CREATED, LIFECYCLE_VALIDATED, LIFECYCLE_QUEUED, LIFECYCLE_SCHEDULED,
    LIFECYCLE_DISPATCHED, LIFECYCLE_RUNNING, LIFECYCLE_RETRY_WAIT, LIFECYCLE_PAUSED,
    LIFECYCLE_BLOCKED, LIFECYCLE_TIMEOUT, LIFECYCLE_TTL_EXPIRED, LIFECYCLE_SUCCEEDED,
    LIFECYCLE_FAILED, LIFECYCLE_CANCELLED, LIFECYCLE_DEAD_LETTERED, LIFECYCLE_ARCHIVED,
})

__all__ = ["build_jobs_router", "LIFECYCLE_ALL_STATES"]
