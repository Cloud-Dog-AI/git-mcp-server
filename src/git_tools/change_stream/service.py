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

"""Git-profile change-watch adapter (PS-102 §4.3, CSTREAM-GIT-001/002).

``WatchService`` is a *thin adapter* over the common change-stream foundation
published in ``cloud_dog_api_kit.change_stream`` (PS-102 §9 / RULES §1.4). It:

* builds a :class:`~cloud_dog_api_kit.change_stream.WatchCoordinator` whose
  per-watch journal is the durable :class:`SqlJournal` (backed by the service's
  ``cloud_dog_db`` engine) so a watch backlog survives restart (CSTREAM-007);
* wires the coordinator's ``on_emit`` hook to the service's existing
  ``cloud_dog_api_kit.a2a.events`` broadcaster via ``make_broadcast_hook`` for
  live SSE fan-out (PS-102 §5.2) — no bespoke broadcaster;
* wires the coordinator's ``audit_sink`` to ``cloud_dog_logging`` (CSTREAM-010);
* enforces RBAC/tenancy at the adapter boundary via ``cloud_dog_idam`` — a watch
  is scoped to a tenant + git profile; cross-tenant reads are a hard failure
  (CSTREAM-009);
* translates observed git repository changes (commits, branches, tags, file
  add/modify/delete, merges, force-push) into the canonical :class:`ChangeEvent`
  envelope and emits them to every *live* watch whose criteria match
  (CSTREAM-GIT-001).

Observation is keyed by commit/ref identity through a persisted ``RefSnapshot``
(the last ``ref -> sha`` map), so a steady-state watch performs a bounded diff,
NEVER a repeated full-repository scan (CSTREAM-GIT-002). Controlled remote fetch
is capped per watch by a minimum interval.

This adapter re-implements NO journal, cursor, queue, broadcaster, RBAC, or error
model — all of that is consumed from the foundation.
"""

from __future__ import annotations

import contextlib
import json
import threading
import time
import uuid
from collections.abc import Callable, Mapping
from datetime import datetime, timezone
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:  # avoid an import cycle (observe imports change_stream.criteria)
    from git_tools.git.observe import RefSnapshot

from cloud_dog_api_kit.change_stream import (
    ACTIONS,
    ChangeEvent,
    WatchCoordinator,
    WatchSpec,
    make_broadcast_hook,
)
from cloud_dog_api_kit.change_stream.db_journal import SqlJournal
from cloud_dog_api_kit.change_stream.errors import (
    InvalidCriteria,
    WatchNotFound,
)
from cloud_dog_api_kit.change_stream.journal import InMemoryJournal, Journal

from git_tools.change_stream.criteria import (
    ChangeCandidate,
    validate_criteria,
)
from git_tools.change_stream.criteria import (
    match as criteria_match,
)
from git_tools.git.repo import GitRepository

SERVICE_ID = "git-mcp"
_SOURCE_TYPE = "git_ref"

# CSTREAM-GIT-002: minimum interval (seconds) between controlled remote fetches
# for a single watch, so an eager consumer cannot drive unbounded network I/O.
DEFAULT_MIN_FETCH_INTERVAL_SECONDS = 30.0


def _utc_now() -> datetime:
    return datetime.now(timezone.utc)


class WatchService:
    """Per-service change-watch adapter binding the common coordinator to git ops.

    Args:
        service_id: stable service identifier for the envelope (``git-mcp``).
        engine: an optional SQLAlchemy ``Engine`` (from ``cloud_dog_db``). When
            supplied, watches journal durably via :class:`SqlJournal`; when
            ``None`` (unit tests / no DB), a bounded in-memory journal is used so
            the adapter still functions without a live database.
        broadcaster: an optional ``cloud_dog_api_kit.a2a.events`` broadcaster; when
            supplied, emitted events fan out live via ``make_broadcast_hook``.
        audit_sink: optional ``(kind, mapping)`` callable — the service wires
            ``cloud_dog_logging`` here.
        broadcast_scheduler: optional scheduler for the (async) broadcast publish
            so the sync emit path never blocks a worker (CSTREAM-002).
        repo_resolver: optional ``(profile_id) -> GitRepository`` resolver used by
            the server-mediated observation path. When ``None``, callers supply a
            repository directly to :meth:`observe_repo`.
        min_fetch_interval_seconds: cap on controlled remote-fetch frequency.
    """

    def __init__(
        self,
        *,
        service_id: str = SERVICE_ID,
        engine: Any | None = None,
        broadcaster: Any | None = None,
        audit_sink: Callable[[str, Mapping[str, Any]], None] | None = None,
        broadcast_scheduler: Callable[[Any], None] | None = None,
        repo_resolver: Callable[[str], GitRepository] | None = None,
        min_fetch_interval_seconds: float = DEFAULT_MIN_FETCH_INTERVAL_SECONDS,
    ) -> None:
        self._service_id = service_id
        self._engine = engine
        self._repo_resolver = repo_resolver
        self._min_fetch_interval = float(min_fetch_interval_seconds)
        self._lock = threading.RLock()
        # watch_id -> declarative spec view (tenant/profile/criteria) kept for
        # criteria evaluation + RBAC scoping. The coordinator owns state/journal.
        self._specs: dict[str, WatchSpec] = {}
        self._criteria: dict[str, Mapping[str, Any]] = {}
        # watch_id -> last observed RefSnapshot (cursor-backing identity state,
        # CSTREAM-GIT-002 — enables bounded diff instead of full re-scan).
        self._snapshots: dict[str, RefSnapshot] = {}
        # watch_id -> last controlled-fetch monotonic timestamp (fetch cap).
        self._last_fetch: dict[str, float] = {}

        on_emit = None
        if broadcaster is not None:
            on_emit = make_broadcast_hook(broadcaster, scheduler=broadcast_scheduler)

        # Ensure the durable journal table exists once (idempotent).
        if engine is not None:
            with contextlib.suppress(Exception):  # pragma: no cover - schema may already exist
                SqlJournal.create_schema(engine)

        self._coordinator = WatchCoordinator(
            journal_factory=self._journal_factory,
            on_emit=on_emit,
            audit_sink=audit_sink,
        )

    # ------------------------------------------------------------------
    # journal factory (durable SqlJournal, else bounded in-memory)
    # ------------------------------------------------------------------
    def _journal_factory(self, spec: WatchSpec) -> Journal:
        if self._engine is not None:
            return SqlJournal(
                self._engine,
                spec.watch_id,
                max_size=spec.journal_max,
                ttl_seconds=spec.journal_ttl_seconds,
            )
        return InMemoryJournal(max_size=spec.journal_max, ttl_seconds=spec.journal_ttl_seconds)

    @property
    def coordinator(self) -> WatchCoordinator:
        return self._coordinator

    # ------------------------------------------------------------------
    # RBAC / tenancy boundary (CSTREAM-009)
    # ------------------------------------------------------------------
    def _require_owner(self, watch_id: str, tenant_id: str) -> WatchSpec:
        """Return the spec if the caller's tenant owns the watch, else raise.

        Cross-tenant / cross-profile access is a hard failure — the watch is
        scoped to the tenant it was created under (PS-102 §7). To avoid leaking
        watch existence across tenants, a cross-tenant hit reports not-found.
        """
        spec = self._specs.get(watch_id)
        if spec is None:
            raise WatchNotFound(f"no watch {watch_id!r}")
        if tenant_id is not None and spec.tenant_id != tenant_id:
            raise WatchNotFound(f"no watch {watch_id!r}")
        return spec

    # ------------------------------------------------------------------
    # lifecycle (create/list/status/pause/resume/delete) — PS-102 §5.1
    # ------------------------------------------------------------------
    def create_watch(
        self,
        *,
        profile_id: str,
        tenant_id: str,
        actor: str,
        criteria: Mapping[str, Any] | None = None,
        max_batch: int = 100,
        max_inflight: int = 4,
        journal_max: int = 1000,
        journal_ttl_seconds: float | None = None,
        watch_id: str | None = None,
    ) -> dict[str, Any]:
        resolved_criteria = dict(criteria or {})
        validate_criteria(resolved_criteria)
        if max_batch < 1 or max_inflight < 1 or journal_max < 1:
            raise InvalidCriteria("max_batch, max_inflight and journal_max must be >= 1")
        wid = watch_id or f"gitw-{uuid.uuid4().hex[:16]}"
        spec = WatchSpec(
            watch_id=wid,
            service_id=self._service_id,
            profile_id=profile_id,
            tenant_id=tenant_id,
            actor=actor,
            criteria=resolved_criteria,
            max_batch=max_batch,
            max_inflight=max_inflight,
            journal_max=journal_max,
            journal_ttl_seconds=journal_ttl_seconds,
        )
        with self._lock:
            from git_tools.git.observe import RefSnapshot

            status = self._coordinator.create_watch(spec)
            self._specs[wid] = spec
            self._criteria[wid] = resolved_criteria
            self._snapshots[wid] = RefSnapshot()
        return self._watch_view(spec, status)

    def list_watches(self, *, tenant_id: str) -> list[dict[str, Any]]:
        with self._lock:
            out: list[dict[str, Any]] = []
            for wid, spec in self._specs.items():
                if spec.tenant_id != tenant_id:
                    continue
                out.append(self._watch_view(spec, self._coordinator.get_status(wid)))
            return out

    def get_watch(self, watch_id: str, *, tenant_id: str) -> dict[str, Any]:
        spec = self._require_owner(watch_id, tenant_id)
        return self._watch_view(spec, self._coordinator.get_status(watch_id))

    def get_status(self, watch_id: str, *, tenant_id: str) -> dict[str, Any]:
        self._require_owner(watch_id, tenant_id)
        return self._status_view(self._coordinator.get_status(watch_id))

    def pause(self, watch_id: str, *, tenant_id: str) -> dict[str, Any]:
        self._require_owner(watch_id, tenant_id)
        return self._status_view(self._coordinator.pause(watch_id))

    def resume(self, watch_id: str, *, tenant_id: str) -> dict[str, Any]:
        self._require_owner(watch_id, tenant_id)
        return self._status_view(self._coordinator.resume(watch_id))

    def delete(self, watch_id: str, *, tenant_id: str) -> dict[str, Any]:
        self._require_owner(watch_id, tenant_id)
        with self._lock:
            self._coordinator.delete(watch_id)
            self._specs.pop(watch_id, None)
            self._criteria.pop(watch_id, None)
            self._snapshots.pop(watch_id, None)
            self._last_fetch.pop(watch_id, None)
        return {"watch_id": watch_id, "deleted": True}

    # ------------------------------------------------------------------
    # retrieval / ack / recover — PS-102 §5.2 (pull-batch base mode)
    # ------------------------------------------------------------------
    def get_batch(
        self,
        watch_id: str,
        *,
        tenant_id: str,
        since_cursor: str | None = None,
        max_batch: int | None = None,
    ) -> dict[str, Any]:
        self._require_owner(watch_id, tenant_id)
        result = self._coordinator.get_batch(watch_id, since_cursor=since_cursor, max_batch=max_batch)
        return WatchCoordinator.batch_to_dict(result, redact=True)

    def ack(self, watch_id: str, *, tenant_id: str, ack_cursor: str) -> dict[str, Any]:
        self._require_owner(watch_id, tenant_id)
        return self._status_view(self._coordinator.ack(watch_id, ack_cursor))

    def recover(
        self, watch_id: str, *, tenant_id: str, since_cursor: str | None = None
    ) -> dict[str, Any]:
        self._require_owner(watch_id, tenant_id)
        cursor = self._coordinator.recover(watch_id, since_cursor=since_cursor)
        return {"watch_id": watch_id, "resume_cursor": cursor}

    def test_event(
        self,
        watch_id: str,
        *,
        tenant_id: str,
        action: str = "created",
        object_ref: str = "test",
        **meta: Any,
    ) -> dict[str, Any]:
        """Inject a deterministic synthetic event (PS-102 §5.8)."""
        self._require_owner(watch_id, tenant_id)
        if action not in ACTIONS:
            raise InvalidCriteria(f"unknown action verb {action!r}")
        seq = self._coordinator.test_event(watch_id, action=action, object_ref=object_ref, **meta)
        return {"watch_id": watch_id, "emitted_seq": seq, "action": action, "object_ref": object_ref}

    # ------------------------------------------------------------------
    # health (PS-102 §5.9) — aggregated for the service /health
    # ------------------------------------------------------------------
    def health(self) -> dict[str, int]:
        with self._lock:
            return self._coordinator.health()

    # ------------------------------------------------------------------
    # server-mediated observation (CSTREAM-GIT-001/002)
    # ------------------------------------------------------------------
    def observe_repo(
        self,
        watch_id: str,
        *,
        tenant_id: str,
        repo: GitRepository | None = None,
        fetch: bool = False,
        remote: str = "origin",
        actor: str | None = None,
        correlation_id: str | None = None,
    ) -> dict[str, Any]:
        """Observe a watch's repository and emit change events for matching changes.

        Performs a BOUNDED diff against the watch's persisted ref snapshot (never a
        full re-scan in steady state, CSTREAM-GIT-002). When ``fetch`` is set, a
        single controlled remote fetch runs first — but only if the per-watch
        minimum fetch interval has elapsed (fetch-frequency cap). Returns the
        emitted event count and the observed ref count.
        """
        spec = self._require_owner(watch_id, tenant_id)
        target_repo = repo if repo is not None else self._resolve_repo(spec.profile_id)
        if target_repo is None:
            raise InvalidCriteria(
                f"no repository resolver configured for profile {spec.profile_id!r}"
            )

        from git_tools.git.observe import RefSnapshot, observe

        fetched = False
        if fetch:
            fetched = self._maybe_fetch(watch_id, target_repo, remote=remote)

        with self._lock:
            previous = self._snapshots.get(watch_id, RefSnapshot())
            crit = self._criteria.get(watch_id, {})
            journal_max = spec.journal_max

        candidates, new_snapshot = observe(
            target_repo,
            previous,
            max_commits_per_ref=min(spec.max_batch, journal_max),
        )

        emitted = 0
        status = self._coordinator.get_status(watch_id)
        if status.state == "live":
            for candidate in candidates:
                matched = criteria_match(crit, candidate)
                if matched is None:
                    continue
                event = self._build_event(
                    spec=spec,
                    candidate=candidate,
                    criteria_match=matched,
                    actor=actor or spec.actor,
                    correlation_id=correlation_id,
                )
                with contextlib.suppress(Exception):  # a paused/removed watch races
                    self._coordinator.emit(watch_id, event)
                    emitted += 1

        # Persist the new snapshot regardless of match (identity state advances).
        with self._lock:
            self._snapshots[watch_id] = new_snapshot

        return {
            "watch_id": watch_id,
            "observed_refs": len(new_snapshot.refs),
            "candidates": len(candidates),
            "emitted": emitted,
            "fetched": fetched,
        }

    def _resolve_repo(self, profile_id: str) -> GitRepository | None:
        if self._repo_resolver is None:
            return None
        try:
            return self._repo_resolver(profile_id)
        except Exception:  # noqa: BLE001 — a missing/closed repo is a soft skip
            return None

    def _maybe_fetch(self, watch_id: str, repo: GitRepository, *, remote: str) -> bool:
        """Run one controlled fetch if the per-watch fetch-frequency cap allows it."""
        now = time.monotonic()
        with self._lock:
            last = self._last_fetch.get(watch_id, 0.0)
            if now - last < self._min_fetch_interval:
                return False
            self._last_fetch[watch_id] = now
        with contextlib.suppress(Exception):  # network errors must not crash observation
            repo.fetch(remote=remote)
            return True
        return False

    # ------------------------------------------------------------------
    # envelope + view builders
    # ------------------------------------------------------------------
    def _build_event(
        self,
        *,
        spec: WatchSpec,
        candidate: ChangeCandidate,
        criteria_match: Mapping[str, Any],
        actor: str | None,
        correlation_id: str | None,
    ) -> ChangeEvent:
        # per-service typed metadata extension (PS-102 §4.1 git-mcp row).
        meta = dict(candidate.metadata)
        typed_metadata = {
            "repo": spec.profile_id,
            "ref": candidate.ref,
            "old_sha": str(meta.get("old_sha", "")),
            "new_sha": str(meta.get("new_sha", candidate.object_version)),
            "commit_author": candidate.author or str(meta.get("commit_author", "")),
            "paths_changed": list(candidate.paths),
            "merge": bool(meta.get("merge", False)),
            "force": bool(meta.get("force", False)),
        }
        # carry through any extra observation detail (file_status, path, parents).
        for key in ("commit", "path", "file_status", "parents"):
            if key in meta:
                typed_metadata[key] = meta[key]
        return ChangeEvent(
            watch_id=spec.watch_id,
            service_id=self._service_id,
            profile_id=spec.profile_id,
            source_type=_SOURCE_TYPE,
            source_ref=f"{spec.profile_id}:{candidate.ref or candidate.object_ref}",
            action=candidate.action,
            object_ref=candidate.object_ref,
            object_version=candidate.object_version or candidate.object_ref,
            tenant_id=spec.tenant_id,
            event_time=_utc_now(),
            observed_time=_utc_now(),
            criteria_match=dict(criteria_match),
            summary=_default_summary(candidate),
            metadata=typed_metadata,
            correlation_id=correlation_id,
            actor={"id": actor, "type": "user"} if actor else None,
            provenance={"capture": "server_mediated", "ref": candidate.ref},
        )

    def _watch_view(self, spec: WatchSpec, status: Any) -> dict[str, Any]:
        return {
            "watch_id": spec.watch_id,
            "service_id": spec.service_id,
            "profile_id": spec.profile_id,
            "tenant_id": spec.tenant_id,
            "actor": spec.actor,
            "criteria": dict(spec.criteria),
            "max_batch": spec.max_batch,
            "max_inflight": spec.max_inflight,
            "journal_max": spec.journal_max,
            "journal_ttl_seconds": spec.journal_ttl_seconds,
            "status": self._status_view(status),
        }

    @staticmethod
    def _status_view(status: Any) -> dict[str, Any]:
        return {
            "watch_id": status.watch_id,
            "tenant_id": status.tenant_id,
            "state": status.state,
            "journal_depth": status.depth,
            "earliest_seq": status.earliest_seq,
            "latest_seq": status.latest_seq,
            "ack_seq": status.ack_seq,
            "inflight": status.inflight,
            "throttled": status.throttled,
            "trimmed_total": status.trimmed_total,
        }


def make_audit_sink(audit_writer: Any) -> Callable[[str, Mapping[str, Any]], None]:
    """Build a coordinator ``audit_sink`` that writes to the git-mcp AuditWriter.

    The common :class:`WatchCoordinator` calls ``audit_sink(kind, row)`` for every
    lifecycle / emission / delivery / ack / recover / throttle event (CSTREAM-010).
    This adapter maps each to a typed :class:`AuditRecord` so watch audit lands in
    the same privileged audit stream (``cloud_dog_logging``) as the rest of git-mcp
    — no bespoke audit writer (RULES §1.4).
    """
    from git_tools.audit.events import AuditActor, AuditRecord

    def _sink(kind: str, row: Mapping[str, Any]) -> None:
        watch_id = str(row.get("watch_id", ""))
        actor = str(row.get("actor") or "system")
        details = {k: v for k, v in row.items() if k not in {"watch_id", "actor"}}
        record = AuditRecord(
            operation=f"change_watch.{kind}",
            status="success",
            correlation_id="",
            actor=AuditActor(actor_id=actor, actor_type="user"),
            params={"watch_id": watch_id, **details},
            resolved_ref=str(details.get("new_sha") or details.get("action") or "") or None,
        )
        with contextlib.suppress(Exception):  # audit must never break the flow
            audit_writer.emit(record)

    return _sink


def _default_summary(candidate: ChangeCandidate) -> str:
    label = candidate.short_ref or candidate.ref or candidate.object_ref
    if candidate.paths and candidate.action in {"created", "updated", "deleted", "moved"} and len(candidate.paths) == 1:
        return f"{candidate.action} {candidate.paths[0]} on {label}".strip()
    return f"{candidate.action} {label}".strip()


# Re-export for the snapshot-cursor durability tests / tooling.
def snapshot_to_json(snapshot: RefSnapshot) -> str:
    """Serialise a ref snapshot (cursor-backing identity state) to JSON."""
    return json.dumps({"refs": dict(snapshot.refs)}, sort_keys=True)


def snapshot_from_json(raw: str) -> RefSnapshot:
    """Rebuild a ref snapshot from :func:`snapshot_to_json` output."""
    from git_tools.git.observe import RefSnapshot

    data = json.loads(raw) if raw else {}
    return RefSnapshot(refs=dict(data.get("refs", {})))
