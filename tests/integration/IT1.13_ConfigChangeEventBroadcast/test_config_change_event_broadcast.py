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
from uuid import uuid4

import httpx
import websocket

from tests.helpers import api_url


def _ws_url(base_url: str, api_key: str) -> str:
    target_base = os.environ.get("TEST_A2A_BASE_URL", "").strip() or base_url
    ws_base = target_base.replace("http://", "ws://", 1).replace("https://", "wss://", 1)
    return f"{ws_base.rstrip('/')}/a2a/events/config?token={api_key}"


def test_profile_crud_broadcasts_a2a_config_events(
    integration_server: dict[str, str | bool],
    api_key: str,
) -> None:
    """Requirements: FR-01, FR-15, CFG-06, CFG-11."""
    base_url = str(integration_server["base_url"])
    headers = {"x-api-key": api_key}
    profile_name = f"cfg-event-{uuid4().hex[:8]}"
    endpoint = api_url(base_url, f"/admin/profiles/{profile_name}")

    client = websocket.create_connection(_ws_url(base_url, api_key), timeout=10)
    try:
        created = httpx.post(endpoint, headers=headers, json={"repo": {"source": "/tmp/cfg-event"}}, timeout=10.0)
        assert created.status_code == 200
        created_event = json.loads(client.recv())
        assert created_event["event_type"] == "config_change"
        assert created_event["entity_type"] == "profile"
        assert created_event["action"] == "create"
        assert created_event["profile_name"] == profile_name

        updated = httpx.put(endpoint, headers=headers, json={"repo": {"source": "/tmp/cfg-event-2"}}, timeout=10.0)
        assert updated.status_code == 200
        updated_event = json.loads(client.recv())
        assert updated_event["action"] == "update"
        assert updated_event["profile_name"] == profile_name

        deleted = httpx.delete(endpoint, headers=headers, timeout=10.0)
        assert deleted.status_code == 200
        deleted_event = json.loads(client.recv())
        assert deleted_event["action"] == "delete"
        assert deleted_event["profile_id"] == profile_name
    finally:
        client.close()
