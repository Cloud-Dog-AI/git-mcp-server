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

from git_tools.admin.runtime import AdminRuntime


def test_admin_runtime_manages_profiles_users_groups_and_api_keys() -> None:
    """Requirements: FR-01, FR-15, FR-17, CFG-06, CFG-08, CFG-09, CFG-10, CFG-11."""
    runtime = AdminRuntime()
    queue = runtime.event_hub.subscribe()

    created_profile = runtime.create_profile("cfg-runtime", {"repo": {"source": "/tmp/repo"}}, actor="unit-admin")
    assert created_profile == {"name": "cfg-runtime", "created": True}
    created_event = queue.get_nowait()
    assert created_event["action"] == "create"
    assert created_event["profile_name"] == "cfg-runtime"
    assert created_event["actor"] == "unit-admin"

    updated_profile = runtime.update_profile("cfg-runtime", {"repo": {"source": "/tmp/repo-2"}}, actor="unit-admin")
    assert updated_profile == {"name": "cfg-runtime", "updated": True}
    updated_event = queue.get_nowait()
    assert updated_event["action"] == "update"

    user = runtime.create_user(
        user_id="cfg-user",
        username="cfg-user",
        email="cfg-user@example.test",
        group_ids=["cfg-group"],
    )
    assert user["user_id"] == "cfg-user"
    assert user["group_ids"] == ["cfg-group"]

    group = runtime.create_group(
        group_id="cfg-group",
        description="Config admins",
        roles=["admin", "writer"],
        members=["cfg-user"],
    )
    assert group["roles"] == ["admin", "writer"]
    assert group["members"] == ["cfg-user"]

    user_after_group = runtime.read_user("cfg-user")
    assert user_after_group["group_ids"] == ["cfg-group"]
    assert user_after_group["roles"] == ["admin", "writer"]

    api_key = runtime.create_api_key(
        name="cfg-runtime-key",
        owner_user_id="cfg-user",
        capabilities=["admin.profile", "admin.identity"],
    )
    assert api_key["name"] == "cfg-runtime-key"
    assert api_key["owner_user_id"] == "cfg-user"
    assert api_key["capabilities"] == ["admin.profile", "admin.identity"]
    assert api_key["raw_key"]

    listed_keys = runtime.list_api_keys(owner_user_id="cfg-user")
    assert len(listed_keys) == 1
    assert listed_keys[0]["key_id"] == api_key["key_id"]

    updated_key = runtime.update_api_key(api_key["key_id"], name="cfg-runtime-key-updated", capabilities=["tools:read"])
    assert updated_key["name"] == "cfg-runtime-key-updated"
    assert updated_key["capabilities"] == ["tools:read"]

    revoked = runtime.revoke_api_key(api_key["key_id"])
    assert revoked == {"key_id": api_key["key_id"], "revoked": True}
    assert runtime.read_api_key(api_key["key_id"])["status"] == "revoked"

    deleted_group = runtime.delete_group("cfg-group")
    assert deleted_group == {"group_id": "cfg-group", "deleted": True}
    assert runtime.read_user("cfg-user")["group_ids"] == []

    deleted_user = runtime.delete_user("cfg-user")
    assert deleted_user == {"user_id": "cfg-user", "deleted": True}

    deleted_profile = runtime.delete_profile("cfg-runtime", actor="unit-admin")
    assert deleted_profile == {"name": "cfg-runtime", "deleted": True}
    deleted_event = queue.get_nowait()
    assert deleted_event["action"] == "delete"
