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

from pathlib import Path
from uuid import uuid4

import httpx

from tests.helpers import api_url


def test_fullworkflow_admin_profile_crud(
    application_server: str,
    application_api_key: str,
    tmp_path: Path,
) -> None:
    """Requirements: FR-05, FR-15, FR-16, UC-07."""
    headers = {"x-api-key": application_api_key}
    initial_repo_source = (tmp_path / "repo").as_posix()
    updated_repo_source = (tmp_path / "repo2").as_posix()
    profile_name = f"repoX-{uuid4().hex[:8]}"
    profile_endpoint = api_url(application_server, f"/admin/profiles/{profile_name}")

    create = httpx.post(
        profile_endpoint,
        headers=headers,
        json={"repo": {"source": initial_repo_source}},
        timeout=10.0,
    )
    assert create.status_code == 200
    assert create.json()["ok"] is True

    read = httpx.get(profile_endpoint, headers=headers, timeout=10.0)
    assert read.status_code == 200
    assert read.json()["result"]["repo"]["source"] == initial_repo_source

    update = httpx.put(
        profile_endpoint,
        headers=headers,
        json={"repo": {"source": updated_repo_source}},
        timeout=10.0,
    )
    assert update.status_code == 200

    read_after = httpx.get(profile_endpoint, headers=headers, timeout=10.0)
    assert read_after.status_code == 200
    assert read_after.json()["result"]["repo"]["source"] == updated_repo_source

    delete = httpx.delete(profile_endpoint, headers=headers, timeout=10.0)
    assert delete.status_code == 200
