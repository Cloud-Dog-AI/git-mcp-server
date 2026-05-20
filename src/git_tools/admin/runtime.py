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

import asyncio
from dataclasses import dataclass
from datetime import datetime, timezone
import json
from typing import Any

from cloud_dog_idam import APIKeyManager
from cloud_dog_storage import path_utils

from git_tools.files.io import append_host_text, load_host_text


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def _string_list(values: list[str] | tuple[str, ...] | None) -> list[str]:
    if values is None:
        return []
    cleaned: list[str] = []
    seen: set[str] = set()
    for value in values:
        candidate = str(value).strip()
        if not candidate or candidate in seen:
            continue
        seen.add(candidate)
        cleaned.append(candidate)
    return cleaned


@dataclass(eq=False, slots=True)
class ConfigEventSubscription:
    """Bounded async event buffer for one config-change subscriber."""

    _buffer: list[dict[str, Any]]
    _max_events: int
    _journal_path: str | None
    _journal_offset: int
    _signal: asyncio.Event

    def __init__(self, *, max_events: int = 16, journal_path: str | None = None) -> None:
        self._buffer = []
        self._max_events = max_events
        self._journal_path = journal_path
        self._journal_offset = (
            path_utils.file_stat(self._journal_path).st_size
            if self._journal_path is not None and path_utils.exists(self._journal_path)
            else 0
        )
        self._signal = asyncio.Event()

    def push(self, event: dict[str, Any]) -> None:
        """Append one event and wake any async waiter."""
        self._buffer.append(dict(event))
        while len(self._buffer) > self._max_events:
            self._buffer.pop(0)
        self._signal.set()

    async def get(self) -> dict[str, Any]:
        """Return the next pending event, waiting until one is available."""
        while True:
            if self._buffer:
                event = self._buffer.pop(0)
                if not self._buffer:
                    self._signal.clear()
                return event
            self._signal.clear()
            self._read_from_journal()
            if self._buffer:
                continue
            try:
                await asyncio.wait_for(self._signal.wait(), timeout=float(self._max_events) / 64.0)  # config.get derived poll cadence
            except asyncio.TimeoutError:
                continue

    def get_nowait(self) -> dict[str, Any]:
        """Return the next pending event without waiting."""
        self._read_from_journal()
        if not self._buffer:
            raise LookupError("No config events available")
        event = self._buffer.pop(0)
        if not self._buffer:
            self._signal.clear()
        return event

    def _read_from_journal(self) -> None:
        """Read any new events appended by another process."""
        if self._journal_path is None or not path_utils.exists(self._journal_path):
            return
        content = load_host_text(self._journal_path)
        slice_text = content.encode("utf-8")[self._journal_offset :].decode("utf-8")
        for line in slice_text.splitlines():
            payload = line.strip()
            if not payload:
                continue
            self._buffer.append(json.loads(payload))
        self._journal_offset = len(content.encode("utf-8"))
        if self._buffer:
            self._signal.set()


@dataclass(slots=True)
class ConfigEventHub:
    """In-memory pub/sub hub for A2A config-change events."""

    _subscribers: set[ConfigEventSubscription]
    _journal_path: str | None

    def __init__(self, *, journal_path: str | Path | None = None) -> None:
        self._subscribers = set()
        self._journal_path = str(path_utils.as_path(str(journal_path)).resolve()) if journal_path else None
        if self._journal_path is not None:
            parent = path_utils.parent(self._journal_path)
            path_utils.mkdir(parent, parents=True, exist_ok=True)
            if not path_utils.exists(self._journal_path):
                append_host_text(self._journal_path, "")

    def subscribe(self) -> ConfigEventSubscription:
        """Register a subscriber buffer for config-change events."""
        subscription = ConfigEventSubscription(journal_path=self._journal_path)
        self._subscribers.add(subscription)
        return subscription

    def unsubscribe(self, subscription: ConfigEventSubscription) -> None:
        """Remove a subscriber buffer from the event hub."""
        self._subscribers.discard(subscription)

    def publish(self, event: dict[str, Any]) -> None:
        """Broadcast an event to all subscribers."""
        if self._journal_path is not None:
            append_host_text(self._journal_path, json.dumps(event, sort_keys=True) + "\n")
        for subscription in tuple(self._subscribers):
            subscription.push(event)


@dataclass(slots=True)
class AdminRuntime:
    """Shared admin state and lifecycle helpers used by API and MCP surfaces.

    Requirements: CFG-06, CFG-08, CFG-09, CFG-10, CFG-11.
    """

    profile_store: dict[str, dict[str, Any]]
    user_store: dict[str, dict[str, Any]]
    group_store: dict[str, dict[str, Any]]
    role_bindings: dict[str, set[str]]
    api_key_manager: APIKeyManager
    event_hub: ConfigEventHub
    api_key_metadata: dict[str, dict[str, Any]]

    def __init__(
        self,
        *,
        profile_store: dict[str, dict[str, Any]] | None = None,
        user_store: dict[str, dict[str, Any]] | None = None,
        group_store: dict[str, dict[str, Any]] | None = None,
        role_bindings: dict[str, set[str]] | None = None,
        api_key_manager: APIKeyManager | None = None,
        event_hub: ConfigEventHub | None = None,
        event_journal_path: str | Path | None = None,
        api_key_metadata: dict[str, dict[str, Any]] | None = None,
    ) -> None:
        self.profile_store = profile_store if profile_store is not None else {}
        self.user_store = user_store if user_store is not None else {}
        self.group_store = group_store if group_store is not None else {}
        self.role_bindings = role_bindings if role_bindings is not None else {}
        self.api_key_manager = api_key_manager if api_key_manager is not None else APIKeyManager()
        self.event_hub = event_hub if event_hub is not None else ConfigEventHub(journal_path=event_journal_path)
        self.api_key_metadata = api_key_metadata if api_key_metadata is not None else {}

    def _profile_event(self, action: str, profile_name: str, actor: str) -> dict[str, Any]:
        return {
            "event_type": "config_change",
            "entity_type": "profile",
            "action": action,
            "profile_id": profile_name,
            "profile_name": profile_name,
            "timestamp": _now_iso(),
            "actor": actor or "unknown",
        }

    def list_profiles(self) -> dict[str, dict[str, Any]]:
        """Return all stored repository profiles."""
        return self.profile_store

    def read_profile(self, name: str) -> dict[str, Any]:
        """Return one stored profile by name."""
        if name not in self.profile_store:
            raise KeyError(f"Unknown profile: {name}")
        return self.profile_store[name]

    def create_profile(self, name: str, body: dict[str, Any], actor: str) -> dict[str, Any]:
        """Create a profile and publish a config-change event."""
        if name in self.profile_store:
            raise ValueError(f"Profile already exists: {name}")
        self.profile_store[name] = body
        self.event_hub.publish(self._profile_event("create", name, actor))
        return {"name": name, "created": True}

    def update_profile(self, name: str, body: dict[str, Any], actor: str) -> dict[str, Any]:
        """Update a stored profile and publish a config-change event."""
        if name not in self.profile_store:
            raise KeyError(f"Unknown profile: {name}")
        self.profile_store[name] = body
        self.event_hub.publish(self._profile_event("update", name, actor))
        return {"name": name, "updated": True}

    def delete_profile(self, name: str, actor: str) -> dict[str, Any]:
        """Delete a profile and publish a config-change event."""
        if name not in self.profile_store:
            raise KeyError(f"Unknown profile: {name}")
        del self.profile_store[name]
        self.event_hub.publish(self._profile_event("delete", name, actor))
        return {"name": name, "deleted": True}

    def _sync_user_groups(self, user_id: str, group_ids: list[str]) -> None:
        target_groups = set(group_ids)
        for group_id, group in self.group_store.items():
            members = set(_string_list(group.get("members")))
            if group_id in target_groups:
                members.add(user_id)
            else:
                members.discard(user_id)
            group["members"] = sorted(members)

    def list_users(self) -> dict[str, dict[str, Any]]:
        """Return all users with resolved roles and group membership."""
        return {user_id: self.read_user(user_id) for user_id in sorted(self.user_store)}

    def read_user(self, user_id: str) -> dict[str, Any]:
        """Return one user with resolved roles and group IDs."""
        if user_id not in self.user_store:
            raise KeyError(f"Unknown user: {user_id}")
        item = dict(self.user_store[user_id])
        item["group_ids"] = _string_list(item.get("group_ids"))
        item["roles"] = self.resolve_roles(user_id, group_ids=item["group_ids"])
        return item

    def resolve_roles(self, user_id: str, *, group_ids: list[str] | None = None) -> list[str]:
        """Resolve direct and group-derived roles for one user."""
        roles = set(self.role_bindings.get(user_id, set()))
        target_groups = _string_list(group_ids)
        if not target_groups and user_id in self.user_store:
            target_groups = _string_list(self.user_store[user_id].get("group_ids"))
        for group_id in target_groups:
            group = self.group_store.get(group_id)
            if group is None:
                continue
            roles.update(_string_list(group.get("roles")))
        return sorted(roles)

    def create_user(
        self,
        *,
        user_id: str,
        username: str,
        email: str = "",
        group_ids: list[str] | None = None,
    ) -> dict[str, Any]:
        """Create a user and synchronise the related group memberships."""
        if user_id in self.user_store:
            raise ValueError(f"User already exists: {user_id}")
        groups = _string_list(group_ids)
        self.user_store[user_id] = {
            "user_id": user_id,
            "username": username,
            "email": email,
            "group_ids": groups,
            "status": "active",
        }
        self._sync_user_groups(user_id, groups)
        return self.read_user(user_id)

    def update_user(
        self,
        *,
        user_id: str,
        username: str,
        email: str = "",
        group_ids: list[str] | None = None,
        status: str = "active",
    ) -> dict[str, Any]:
        """Update a user record and synchronise the related group memberships."""
        if user_id not in self.user_store:
            raise KeyError(f"Unknown user: {user_id}")
        groups = _string_list(group_ids)
        self.user_store[user_id] = {
            "user_id": user_id,
            "username": username,
            "email": email,
            "group_ids": groups,
            "status": status or "active",
        }
        self._sync_user_groups(user_id, groups)
        return self.read_user(user_id)

    def delete_user(self, user_id: str) -> dict[str, Any]:
        """Delete a user, clear bindings, and revoke owned managed keys."""
        if user_id not in self.user_store:
            raise KeyError(f"Unknown user: {user_id}")
        del self.user_store[user_id]
        self.role_bindings.pop(user_id, None)
        for group in self.group_store.values():
            group["members"] = [member for member in _string_list(group.get("members")) if member != user_id]
        for key_id, meta in self.api_key_metadata.items():
            if meta.get("owner_user_id") == user_id:
                self.api_key_manager.revoke(key_id)
                meta["status"] = "revoked"
        return {"user_id": user_id, "deleted": True}

    def _sync_group_members(self, group_id: str, members: list[str]) -> None:
        member_set = set(members)
        for user_id, record in self.user_store.items():
            groups = set(_string_list(record.get("group_ids")))
            if user_id in member_set:
                groups.add(group_id)
            else:
                groups.discard(group_id)
            record["group_ids"] = sorted(groups)

    def list_groups(self) -> dict[str, dict[str, Any]]:
        """Return all groups with normalised roles and members."""
        return {group_id: self.read_group(group_id) for group_id in sorted(self.group_store)}

    def read_group(self, group_id: str) -> dict[str, Any]:
        """Return one group with normalised roles and members."""
        if group_id not in self.group_store:
            raise KeyError(f"Unknown group: {group_id}")
        item = dict(self.group_store[group_id])
        item["roles"] = _string_list(item.get("roles"))
        item["members"] = _string_list(item.get("members"))
        return item

    def create_group(
        self,
        *,
        group_id: str,
        description: str = "",
        roles: list[str] | None = None,
        members: list[str] | None = None,
    ) -> dict[str, Any]:
        """Create a group and synchronise the inverse user memberships."""
        if group_id in self.group_store:
            raise ValueError(f"Group already exists: {group_id}")
        clean_members = _string_list(members)
        self.group_store[group_id] = {
            "group_id": group_id,
            "description": description,
            "roles": _string_list(roles),
            "members": clean_members,
        }
        self._sync_group_members(group_id, clean_members)
        return self.read_group(group_id)

    def update_group(
        self,
        *,
        group_id: str,
        description: str = "",
        roles: list[str] | None = None,
        members: list[str] | None = None,
    ) -> dict[str, Any]:
        """Update a group and synchronise the inverse user memberships."""
        if group_id not in self.group_store:
            raise KeyError(f"Unknown group: {group_id}")
        clean_members = _string_list(members)
        self.group_store[group_id] = {
            "group_id": group_id,
            "description": description,
            "roles": _string_list(roles),
            "members": clean_members,
        }
        self._sync_group_members(group_id, clean_members)
        return self.read_group(group_id)

    def delete_group(self, group_id: str) -> dict[str, Any]:
        """Delete a group and remove it from all user memberships."""
        if group_id not in self.group_store:
            raise KeyError(f"Unknown group: {group_id}")
        del self.group_store[group_id]
        for user in self.user_store.values():
            user["group_ids"] = [item for item in _string_list(user.get("group_ids")) if item != group_id]
        return {"group_id": group_id, "deleted": True}

    def list_api_keys(self, owner_user_id: str | None = None) -> list[dict[str, Any]]:
        """List managed API keys, optionally filtered by owner."""
        rows: list[dict[str, Any]] = []
        for key in self.api_key_manager.list_keys(owner_id=owner_user_id):
            meta = self.api_key_metadata.get(key.api_key_id, {})
            rows.append(
                {
                    "key_id": key.api_key_id,
                    "name": str(meta.get("name", key.owner_user_id)),
                    "owner_user_id": key.owner_user_id,
                    "key_prefix": key.key_prefix,
                    "status": key.status,
                    "capabilities": _string_list(meta.get("capabilities")),
                    "created_at": str(meta.get("created_at", "")),
                    "expires_at": key.expires_at.isoformat() if key.expires_at is not None else None,
                }
            )
        rows.sort(key=lambda item: (str(item["owner_user_id"]), str(item["name"]), str(item["key_id"])))
        return rows

    def read_api_key(self, key_id: str) -> dict[str, Any]:
        """Return one managed API key record by key ID."""
        matches = [item for item in self.list_api_keys() if item["key_id"] == key_id]
        if not matches:
            raise KeyError(f"Unknown API key: {key_id}")
        return matches[0]

    def create_api_key(
        self,
        *,
        name: str,
        owner_user_id: str,
        capabilities: list[str] | None = None,
        ttl_days: int | None = None,
    ) -> dict[str, Any]:
        """Create a managed API key and return the one-time raw secret."""
        raw_key, metadata = self.api_key_manager.generate(owner_id=owner_user_id, ttl_days=ttl_days)
        self.api_key_metadata[metadata.api_key_id] = {
            "name": name,
            "owner_user_id": owner_user_id,
            "capabilities": _string_list(capabilities),
            "created_at": metadata.created_at.isoformat(),
            "status": "active",
        }
        record = self.read_api_key(metadata.api_key_id)
        record["raw_key"] = raw_key
        return record

    def revoke_api_key(self, key_id: str) -> dict[str, Any]:
        """Revoke a managed API key by key ID."""
        if not self.api_key_manager.revoke(key_id):
            raise KeyError(f"Unknown API key: {key_id}")
        self.api_key_metadata.setdefault(key_id, {})["status"] = "revoked"
        return {"key_id": key_id, "revoked": True}

    def update_api_key(
        self,
        key_id: str,
        *,
        name: str | None = None,
        capabilities: list[str] | None = None,
    ) -> dict[str, Any]:
        """Update editable managed API-key metadata."""
        _ = self.read_api_key(key_id)
        metadata = self.api_key_metadata.setdefault(key_id, {})
        if name is not None:
            metadata["name"] = name
        if capabilities is not None:
            metadata["capabilities"] = _string_list(capabilities)
        return self.read_api_key(key_id)
