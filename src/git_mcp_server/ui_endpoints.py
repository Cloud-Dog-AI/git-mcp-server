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

import json
import os
import resource
import socket
import time
from dataclasses import dataclass
from typing import Any, Callable

from cloud_dog_storage import path_utils
from fastapi import APIRouter, HTTPException, Request

from git_mcp_server import __version__
from git_mcp_server.admin.endpoints import _require_admin
from git_mcp_server.auth.middleware import AuthRuntime
from git_tools.admin.runtime import AdminRuntime
from git_tools.config.models import GlobalConfigModel
from git_tools.files.io import load_host_text


_ROLE_PERMISSIONS = {
    "admin": {"*"},
    "maintainer": {"git:read", "git:write", "git:execute", "git:admin"},
    "writer": {"git:read", "git:write", "git:execute"},
    "reader": {"git:read"},
}


def _enforce_rbac(request: Request) -> None:
    """RBAC enforcement via cloud_dog_idam (PS-70 UM3). Raises 403 on denial."""
    from cloud_dog_idam import RBACEngine
    from fastapi import HTTPException
    principal = getattr(getattr(request, "state", None), "user", None)
    if principal is not None:
        engine = RBACEngine(role_permissions=_ROLE_PERMISSIONS)
        user_id = str(getattr(principal, "user_id", ""))
        if user_id and not engine.has_permission(user_id, "git:read"):
            raise HTTPException(status_code=403, detail="Insufficient permissions")


def _string(value: Any, fallback: str = "") -> str:
    return str(value).strip() if value is not None else fallback


def _number(value: Any, fallback: float) -> float:
    try:
        return float(value)
    except (TypeError, ValueError):
        return fallback


_LOG_SOURCE_LABELS = {
    "api": "API",
    "web": "WebUI",
    "mcp": "MCP",
    "a2a": "A2A",
    "audit": "Audit",
}


def _as_record(value: Any) -> dict[str, Any]:
    return value if isinstance(value, dict) else {}


def _as_string_list(value: Any) -> list[str]:
    if not isinstance(value, list):
        return []
    return [str(item).strip() for item in value if str(item).strip()]


def _log_source_label(log_type: str) -> str:
    return _LOG_SOURCE_LABELS.get(log_type.strip().lower(), log_type.strip().upper() or "LOG")


def _infer_outcome(parsed: dict[str, Any], extra: dict[str, Any], severity: str) -> str:
    explicit = str(parsed.get("outcome") or extra.get("outcome") or "").strip().lower()
    if explicit:
        return explicit
    status_code = extra.get("status_code")
    if isinstance(status_code, int):
        if 200 <= status_code < 400:
            return "success"
        if status_code in {401, 403}:
            return "denied"
        return "error"
    if severity in {"ERROR", "CRITICAL"}:
        return "error"
    if severity == "WARNING":
        return "partial"
    return "success"


def _normalise_actor(parsed: dict[str, Any], extra: dict[str, Any]) -> dict[str, Any]:
    actor = _as_record(parsed.get("actor"))
    actor_id = str(
        actor.get("id")
        or actor.get("actor_id")
        or extra.get("actor_id")
        or extra.get("source_identifier")
        or extra.get("user")
        or "system"
    ).strip() or "system"
    actor_type = str(actor.get("type") or "").strip().lower()
    if not actor_type:
        actor_type = "user" if actor_id not in {"system", "anonymous"} else "system"
    return {
        "type": actor_type,
        "id": actor_id,
        "roles": _as_string_list(actor.get("roles") or extra.get("roles")),
        "ip": str(actor.get("ip") or extra.get("source_ip") or extra.get("client_ip") or "").strip(),
        "user_agent": str(actor.get("user_agent") or extra.get("user_agent") or "").strip(),
    }


def _normalise_target(log_type: str, parsed: dict[str, Any], extra: dict[str, Any]) -> dict[str, Any]:
    target = _as_record(parsed.get("target"))
    method = str(extra.get("method") or "").strip().upper()
    path = str(extra.get("path") or "").strip()
    target_type = str(target.get("type") or extra.get("target_type") or "").strip()
    if not target_type:
        target_type = "route" if path else "log"
    target_id = str(target.get("id") or extra.get("target_id") or path or log_type).strip()
    target_name = str(target.get("name") or extra.get("target_name") or "").strip()
    if not target_name and method and path:
        target_name = f"{method} {path}"
    return {
        "type": target_type,
        "id": target_id,
        "name": target_name,
    }


def _normalise_log_entry(log_type: str, line: str) -> dict[str, Any] | None:
    stripped = line.strip()
    if not stripped:
        return None
    try:
        parsed = json.loads(stripped)
    except json.JSONDecodeError:
        parsed = {"message": stripped}
    if not isinstance(parsed, dict):
        parsed = {"message": stripped, "value": parsed}
    extra = _as_record(parsed.get("extra"))
    severity = str(parsed.get("severity") or parsed.get("level") or "INFO").strip().upper() or "INFO"
    message = str(parsed.get("message") or "").strip() or stripped
    logger = str(parsed.get("logger") or "").strip()
    event_type = str(parsed.get("event_type") or extra.get("event") or logger or message).strip()
    action = str(parsed.get("action") or extra.get("action") or extra.get("event") or "").strip()
    method = str(extra.get("method") or "").strip().upper()
    path = str(extra.get("path") or "").strip()
    if not action:
        action = f"{method} {path}".strip() if method and path else message
    correlation_id = str(parsed.get("correlation_id") or extra.get("correlation_id") or "").strip()
    trace_id = str(parsed.get("trace_id") or correlation_id).strip()
    request_id = str(parsed.get("request_id") or extra.get("request_id") or trace_id).strip()
    details = _as_record(parsed.get("details")) or extra
    actor = _normalise_actor(parsed, extra)
    target = _normalise_target(log_type, parsed, extra)
    timestamp = str(parsed.get("timestamp") or "").strip()
    source_key = log_type.strip().lower() or "audit"
    source_label = _log_source_label(source_key)
    row_id = "|".join(
        [
            source_key,
            timestamp,
            trace_id,
            request_id,
            event_type,
            str(target.get("id") or ""),
            action,
        ]
    )
    return {
        "id": row_id,
        "source_key": source_key,
        "source": source_label,
        "type": source_label,
        "timestamp": timestamp,
        "event_type": event_type,
        "eventType": event_type,
        "action": action,
        "outcome": _infer_outcome(parsed, extra, severity),
        "severity": severity,
        "level": severity.lower(),
        "trace_id": trace_id,
        "traceId": trace_id,
        "request_id": request_id,
        "requestId": request_id,
        "correlation_id": correlation_id,
        "correlationId": correlation_id,
        "actor": actor,
        "actor_type": str(actor.get("type") or ""),
        "actorType": str(actor.get("type") or ""),
        "actor_id": str(actor.get("id") or ""),
        "actorId": str(actor.get("id") or ""),
        "actor_roles": list(actor.get("roles") or []),
        "actorRoles": list(actor.get("roles") or []),
        "actor_ip": str(actor.get("ip") or ""),
        "actorIp": str(actor.get("ip") or ""),
        "actor_user_agent": str(actor.get("user_agent") or ""),
        "actorUserAgent": str(actor.get("user_agent") or ""),
        "target": target,
        "target_type": str(target.get("type") or ""),
        "targetType": str(target.get("type") or ""),
        "target_id": str(target.get("id") or ""),
        "targetId": str(target.get("id") or ""),
        "target_name": str(target.get("name") or ""),
        "targetName": str(target.get("name") or ""),
        "service": str(parsed.get("service") or "git-mcp-server").strip(),
        "service_instance": str(parsed.get("service_instance") or "").strip(),
        "serviceInstance": str(parsed.get("service_instance") or "").strip(),
        "logger": logger,
        "message": message,
        "details": details,
        "raw": parsed,
    }


def _resolved_log_paths(config: GlobalConfigModel, raw_snapshot: dict[str, Any]) -> dict[str, str]:
    log_snapshot = raw_snapshot.get("log", {}) if isinstance(raw_snapshot.get("log"), dict) else {}

    def _path(key: str, fallback: str) -> str:
        return _string(log_snapshot.get(key), fallback)

    audit_candidates = [
        _string(log_snapshot.get("audit_log")),
        "./logs/audit.log.jsonl",
        _string(config.storage.audit.path),
    ]
    audit_path = next(
        (candidate for candidate in audit_candidates if candidate and path_utils.exists(candidate)),
        next((candidate for candidate in audit_candidates if candidate), "./logs/audit.log.jsonl"),
    )

    return {
        "audit": audit_path,
        "api": _path("api_server_log", "./logs/api_server.log"),
        "web": _path("web_server_log", "./logs/web_server.log"),
        "mcp": _path("mcp_server_log", "./logs/mcp_server.log"),
        "a2a": _path("a2a_server_log", "./logs/a2a_server.log"),
    }


def _mask_runtime_config(value: Any, parent_key: str = "") -> Any:
    """Redact secret-like values before returning runtime config to the UI."""
    if isinstance(value, dict):
        masked: dict[str, Any] = {}
        for key, item in value.items():
            lowered = str(key).lower()
            if any(fragment in lowered for fragment in ("password", "secret", "token", "api_key", "apikey", "credential", "private_key", "key_hash")):
                masked[key] = item if item in (None, "", [], {}) else "****"
                continue
            masked[key] = _mask_runtime_config(item, lowered)
        return masked
    if isinstance(value, list):
        return [_mask_runtime_config(item, parent_key) for item in value]
    return value


def _read_normalised_log_rows(path: str, *, log_type: str, limit: int, contains: str = "") -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    lowered = contains.strip().lower()
    for line in reversed(load_host_text(path).splitlines()) if path_utils.exists(path) else []:
        if lowered and lowered not in line.lower():
            continue
        parsed = _normalise_log_entry(log_type, line)
        if parsed is None:
            continue
        rows.append(parsed)
        if len(rows) >= limit:
            break
    rows.reverse()
    return rows


@dataclass(slots=True)
class RuntimeSettingsStore:
    config: GlobalConfigModel
    raw_snapshot: dict[str, Any]
    _settings: dict[str, dict[str, Any]]

    def __init__(self, config: GlobalConfigModel, raw_snapshot: dict[str, Any]) -> None:
        log_snapshot = raw_snapshot.get("log", {}) if isinstance(raw_snapshot.get("log"), dict) else {}
        retention = log_snapshot.get("retention", {}) if isinstance(log_snapshot.get("retention"), dict) else {}
        integrity = log_snapshot.get("integrity", {}) if isinstance(log_snapshot.get("integrity"), dict) else {}
        default_profile = config.web.default_profile.strip() or next(iter(config.profiles.keys()), "")
        remote_repo_url = ""
        if default_profile and default_profile in config.profiles:
            remote_repo_url = config.profiles[default_profile].repo.source

        self.config = config
        self.raw_snapshot = raw_snapshot
        self._settings = {
            "server.runtime_mode": {
                "group": "Server",
                "label": "Runtime mode",
                "type": "text",
                "value": config.runtime.mode,
                "read_only": True,
                "description": "Resolved from service configuration.",
            },
            "server.request_timeout_seconds": {
                "group": "Server",
                "label": "Request timeout (seconds)",
                "type": "number",
                "value": config.api_server.request_timeout_seconds,
                "read_only": True,
                "description": "Active API timeout for request middleware.",
            },
            "auth.mode": {
                "group": "Auth",
                "label": "Auth mode",
                "type": "select",
                "value": config.auth.mode,
                "read_only": True,
                "options": ["api_key", "jwt", "api_key+jwt", "enterprise"],
                "description": "Current backend auth mode.",
            },
            "auth.session_timeout_minutes": {
                "group": "Auth",
                "label": "Session timeout (minutes)",
                "type": "number",
                "value": config.web.session_timeout_minutes,
                "read_only": False,
                "description": "Browser session timeout used by the Web UI shell.",
            },
            "git.mcp_proxy_base_path": {
                "group": "Git",
                "label": "MCP proxy base path",
                "type": "text",
                "value": config.mcp_server.base_path,
                "read_only": True,
                "description": "Web UI proxy path for MCP requests.",
            },
            "git.a2a_base_path": {
                "group": "Git",
                "label": "A2A base path",
                "type": "text",
                "value": config.a2a_server.base_path,
                "read_only": True,
                "description": "Configured A2A route family.",
            },
            "repository.default_profile": {
                "group": "Repository",
                "label": "Default profile",
                "type": "text",
                "value": default_profile,
                "read_only": False,
                "description": "Default repository profile surfaced to the Web UI.",
            },
            "repository.remote_repo_url": {
                "group": "Repository",
                "label": "Default remote repository URL",
                "type": "text",
                "value": remote_repo_url,
                "read_only": False,
                "description": "Default repository URL surfaced to the Web UI.",
            },
            "logging.hot_days": {
                "group": "Logging",
                "label": "Hot retention days",
                "type": "number",
                "value": retention.get("hot_days", 14),
                "read_only": False,
                "description": "Operator-visible retention preference for current runtime.",
            },
            "logging.integrity_enabled": {
                "group": "Logging",
                "label": "Integrity checks enabled",
                "type": "boolean",
                "value": bool(integrity.get("enabled", True)),
                "read_only": False,
                "description": "Operator-visible runtime preference for integrity checks.",
            },
        }

    def groups(self) -> list[dict[str, Any]]:
        grouped: dict[str, list[dict[str, Any]]] = {}
        for key, setting in self._settings.items():
            item = {"key": key, **setting}
            grouped.setdefault(setting["group"], []).append(item)
        return [
            {
                "id": group.lower(),
                "label": group,
                "settings": sorted(items, key=lambda item: str(item["label"])),
            }
            for group, items in sorted(grouped.items())
        ]

    def update(self, key: str, value: Any) -> dict[str, Any]:
        if key not in self._settings:
            raise KeyError(key)
        current = self._settings[key]
        if current.get("read_only"):
            raise PermissionError(key)
        kind = current["type"]
        if kind == "number":
            current["value"] = _number(value, _number(current["value"], 0.0))
        elif kind == "boolean":
            current["value"] = bool(value)
        else:
            current["value"] = _string(value)
        return {"key": key, **current}


def _metric(label: str, value: str, *, unit: str = "", tone: str = "neutral") -> dict[str, str]:
    payload = {"label": label, "value": value, "tone": tone}
    if unit:
        payload["unit"] = unit
    return payload


def _service_status_rows(config: GlobalConfigModel) -> list[dict[str, str]]:
    api_path = f"{config.api_server.base_path}/health"
    mcp_path = f"{config.mcp_server.base_path}/health"
    a2a_path = f"{config.a2a_server.base_path}/health"
    candidates = [
        ("API", api_path, config.api_server.client_host.strip() or config.api_server.host.strip(), config.api_server.port),
        ("MCP", mcp_path, config.mcp_server.host.strip(), config.mcp_server.port),
        ("A2A", a2a_path, config.a2a_server.host.strip(), config.a2a_server.port),
    ]
    rows: list[dict[str, str]] = []
    for label, url, host, port in candidates:
        status = "error"
        try:
            with socket.create_connection((host, int(port)), timeout=1.0):
                status = "ok"
        except OSError:
            status = "error"
        rows.append({"name": label, "url": url, "status": status})
    return rows


def _safe_percent(numerator: float, denominator: float) -> float:
    if denominator <= 0:
        return 0.0
    return round(max(min((numerator / denominator) * 100.0, 100.0), 0.0), 1)


def _rss_mb() -> float:
    rss_kb = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
    return max(rss_kb / 1024.0, 0.0)


def _total_memory_mb() -> float:
    page_size = os.sysconf("SC_PAGE_SIZE")
    pages = os.sysconf("SC_PHYS_PAGES")
    return (float(page_size) * float(pages)) / (1024.0 * 1024.0)


def _cpu_percent(started_at: float) -> float:
    elapsed = max(time.time() - started_at, 0.001)
    usage = resource.getrusage(resource.RUSAGE_SELF)
    cpu_seconds = float(usage.ru_utime) + float(usage.ru_stime)
    cpu_count = max(os.cpu_count() or 1, 1)
    return round(max((cpu_seconds / elapsed) * 100.0 / cpu_count, 0.0), 1)


def _workspace_metrics(config: GlobalConfigModel) -> dict[str, float | int]:
    workspace_root = path_utils.as_path(config.workspace.base_dir).resolve()
    workspace_root.mkdir(parents=True, exist_ok=True)
    workspace_dirs = [item for item in workspace_root.iterdir() if item.is_dir()]
    total_bytes = 0
    deadline = time.monotonic() + 0.25
    for directory in workspace_dirs:
        if time.monotonic() >= deadline:
            break
        stack = [directory]
        while stack and time.monotonic() < deadline:
            current = stack.pop()
            try:
                for entry in current.iterdir():
                    if time.monotonic() >= deadline:
                        break
                    if entry.is_dir():
                        stack.append(entry)
                        continue
                    if entry.is_file():
                        try:
                            total_bytes += entry.stat().st_size
                        except OSError:
                            continue
            except OSError:
                continue
    return {
        "workspace_count": len(workspace_dirs),
        "total_repo_size_mb": round(total_bytes / (1024.0 * 1024.0), 1),
        "profile_count": len(config.profiles),
    }


def build_status_payload(
    *,
    config: GlobalConfigModel,
    started_at: float,
    active_connections: int = 0,
    include_service_rows: bool = True,
) -> dict[str, Any]:
    workspace_metrics = _workspace_metrics(config)
    disk_total, disk_used, _ = path_utils.disk_usage(str(path_utils.as_path(config.workspace.base_dir).resolve()))
    uptime_seconds = max(int(time.time() - started_at), 0)
    memory_mb = round(_rss_mb(), 1)
    memory_percent = _safe_percent(memory_mb, _total_memory_mb())
    disk_percent = _safe_percent(float(disk_used), float(disk_total))
    cpu_percent = _cpu_percent(started_at)
    payload: dict[str, Any] = {
        "uptime_seconds": uptime_seconds,
        "memory_mb": memory_mb,
        "memory_percent": memory_percent,
        "cpu_percent": cpu_percent,
        "disk_percent": disk_percent,
        "active_connections": max(int(active_connections), 0),
        "service_metrics": workspace_metrics,
        "server_id": config.runtime.server_id,
        "metrics": [
            _metric("Memory", f"{memory_mb:.1f}", unit="MiB"),
            _metric("Memory", f"{memory_percent:.1f}", unit="%"),
            _metric("CPU", f"{cpu_percent:.1f}", unit="%"),
            _metric("Disk", f"{disk_percent:.1f}", unit="%"),
            _metric("Uptime", str(uptime_seconds), unit="s"),
            _metric("Workspaces", str(workspace_metrics["workspace_count"])),
            _metric("Repo size", f"{float(workspace_metrics['total_repo_size_mb']):.1f}", unit="MiB"),
            _metric("Profiles", str(workspace_metrics["profile_count"])),
            _metric("Connections", str(max(int(active_connections), 0))),
        ],
    }
    if include_service_rows:
        payload["services"] = _service_status_rows(config)
    return payload


def _resource_metrics(config: GlobalConfigModel, started_at: float, active_connections: int = 0) -> list[dict[str, str]]:
    status = build_status_payload(
        config=config,
        started_at=started_at,
        active_connections=active_connections,
        include_service_rows=False,
    )
    return [
        _metric("Memory", f"{float(status['memory_mb']):.1f}", unit="MiB"),
        _metric("Memory", f"{float(status['memory_percent']):.1f}", unit="%"),
        _metric("CPU", f"{float(status['cpu_percent']):.1f}", unit="%"),
        _metric("Disk", f"{float(status['disk_percent']):.1f}", unit="%"),
        _metric("Uptime", str(status["uptime_seconds"]), unit="s"),
        _metric("Workspaces", str(status["service_metrics"]["workspace_count"])),
        _metric("Repo size", f"{float(status['service_metrics']['total_repo_size_mb']):.1f}", unit="MiB"),
        _metric("Profiles", str(status["service_metrics"]["profile_count"])),
        _metric("Connections", str(status["active_connections"])),
    ]


def build_ui_support_router(
    *,
    config: GlobalConfigModel,
    auth_runtime: AuthRuntime | None,
    admin_runtime: AdminRuntime,
    settings_store: RuntimeSettingsStore,
    started_at: float,
    active_connections_getter: Callable[[], int] | None = None,
    prefix: str = "",
) -> APIRouter:
    router = APIRouter(prefix=prefix, tags=["ui-support"])
    log_paths = _resolved_log_paths(config, settings_store.raw_snapshot)

    def _version_payload() -> dict[str, Any]:
        return {
            "service": "git-mcp-server",
            "version": __version__,
            "build_date": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime(started_at)),
            "commit_hash": "",
            "server_id": config.runtime.server_id,
        }

    def _active_connections() -> int:
        if active_connections_getter is None:
            return 0
        try:
            return max(int(active_connections_getter()), 0)
        except Exception:  # noqa: BLE001
            return 0

    @router.get("/ui/version")
    def version() -> dict[str, Any]:
        return {"ok": True, "result": _version_payload(), "warnings": [], "errors": [], "meta": {}}

    @router.get("/ui/status")
    def status() -> dict[str, Any]:
        status_payload = build_status_payload(
            config=config,
            started_at=started_at,
            active_connections=_active_connections(),
        )
        return {
            "ok": True,
            "result": status_payload,
            "warnings": [],
            "errors": [],
            "meta": {},
        }

    @router.get("/settings")
    def settings(request: Request) -> dict[str, Any]:
        _require_admin(request, auth_runtime, admin_runtime)
        return {"ok": True, "result": {"groups": settings_store.groups()}, "warnings": [], "errors": [], "meta": {}}

    @router.get("/settings/runtime-config")
    def runtime_config(request: Request) -> dict[str, Any]:
        _require_admin(request, auth_runtime, admin_runtime)
        return {
            "ok": True,
            "result": {
                "config": _mask_runtime_config(settings_store.raw_snapshot),
                "log_paths": log_paths,
            },
            "warnings": [],
            "errors": [],
            "meta": {},
        }

    @router.put("/settings")
    def update_settings(body: dict[str, Any], request: Request) -> dict[str, Any]:
        _require_admin(request, auth_runtime, admin_runtime)
        updates = body.get("settings")
        if isinstance(updates, list):
            applied: list[dict[str, Any]] = []
            for item in updates:
                if not isinstance(item, dict):
                    continue
                key = _string(item.get("key"))
                if not key:
                    continue
                try:
                    applied.append(settings_store.update(key, item.get("value")))
                except PermissionError as exc:
                    raise HTTPException(status_code=409, detail=f"Setting is read-only: {exc.args[0]}") from exc
                except KeyError as exc:
                    raise HTTPException(status_code=404, detail=f"Unknown setting: {exc.args[0]}") from exc
            return {"ok": True, "result": {"updated": applied, "groups": settings_store.groups()}, "warnings": [], "errors": [], "meta": {}}

        key = _string(body.get("key"))
        if not key:
            raise HTTPException(status_code=400, detail="Expected key or settings payload.")
        try:
            updated = settings_store.update(key, body.get("value"))
        except PermissionError as exc:
            raise HTTPException(status_code=409, detail=f"Setting is read-only: {exc.args[0]}") from exc
        except KeyError as exc:
            raise HTTPException(status_code=404, detail=f"Unknown setting: {exc.args[0]}") from exc
        return {"ok": True, "result": {"updated": [updated], "groups": settings_store.groups()}, "warnings": [], "errors": [], "meta": {}}

    @router.get("/audit")
    def audit(request: Request, limit: int = 200, contains: str = "") -> dict[str, Any]:
        _require_admin(request, auth_runtime, admin_runtime)
        rows = _read_normalised_log_rows(
            log_paths["audit"],
            log_type="audit",
            limit=max(1, min(limit, 500)),
            contains=contains,
        )
        return {"ok": True, "result": {"items": rows}, "warnings": [], "errors": [], "meta": {}}

    @router.get("/logs")
    def logs(request: Request, log_type: str = "audit", limit: int = 200, contains: str = "") -> dict[str, Any]:
        _require_admin(request, auth_runtime, admin_runtime)
        selected_type = log_type.strip().lower() or "audit"
        path = log_paths.get(selected_type, log_paths["audit"])
        rows = _read_normalised_log_rows(
            path,
            log_type=selected_type,
            limit=max(1, min(limit, 500)),
            contains=contains,
        )
        return {"ok": True, "result": {"items": rows}, "warnings": [], "errors": [], "meta": {}}

    return router
