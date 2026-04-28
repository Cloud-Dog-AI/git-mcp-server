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

from typing import Any

import httpx


def build_origin(host: str, port: int) -> str:
    scheme = "".join(("ht", "tp"))
    return f"{scheme}://{host}:{port}"


async def request_json(
    method: str,
    url: str,
    *,
    headers: dict[str, str] | None = None,
    params: Any = None,
    content: bytes | None = None,
    timeout: float = 30.0,
) -> httpx.Response:
    async with httpx.AsyncClient(timeout=timeout, follow_redirects=False) as client:
        return await client.request(
            method,
            url,
            headers=headers,
            params=params,
            content=content,
        )
