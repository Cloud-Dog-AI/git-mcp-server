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

from collections.abc import Mapping, Sequence
from typing import Any

from cloud_dog_logging import setup_logging


def _materialise_config(value: Any) -> Any:
    """Convert immutable config snapshot containers into plain Python data."""
    if isinstance(value, Mapping):
        return {str(key): _materialise_config(item) for key, item in value.items()}
    if isinstance(value, Sequence) and not isinstance(value, (str, bytes, bytearray)):
        return [_materialise_config(item) for item in value]
    return value


_SURFACE_LOG_KEYS = {
    "api": "api_server_log",
    "web": "web_server_log",
    "mcp": "mcp_server_log",
    "a2a": "a2a_server_log",
}


def _resolve_surface_log(config: dict[str, Any], surface: str | None) -> str | None:
    """Return the configured application log path for the active server surface."""
    log_config = config.get("log", {})
    if not isinstance(log_config, dict):
        return None
    if surface:
        key = _SURFACE_LOG_KEYS.get(surface.strip().lower())
        if key:
            value = log_config.get(key)
            if value:
                return str(value)
    app_log = log_config.get("app_log")
    return str(app_log) if app_log else None


def configure_service_logging(raw_snapshot: Any, *, service_name: str, server_id: str, surface: str | None = None) -> None:
    """Configure cloud_dog_logging with the resolved server ID.

    Requirements: FR-02, FR-14.
    """
    if hasattr(raw_snapshot, "data"):
        config = _materialise_config(raw_snapshot.data)
    elif isinstance(raw_snapshot, dict):
        config = _materialise_config(raw_snapshot)
    else:
        config = {}
    log_config = config.get("log", {})
    if not isinstance(log_config, dict):
        log_config = {}
    log_config["service_instance"] = server_id
    app_log = _resolve_surface_log(config, surface)
    if app_log:
        log_config["app_log"] = app_log
    config["log"] = log_config
    config["service_name"] = service_name
    setup_logging(config)
