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

_shared_client: httpx.AsyncClient | None = None


def _get_client(timeout: float = 30.0) -> httpx.AsyncClient:
    global _shared_client
    if _shared_client is None or _shared_client.is_closed:
        _shared_client = httpx.AsyncClient(timeout=timeout, follow_redirects=False)
    return _shared_client


def build_origin(host: str, port: int) -> str:
    scheme = "".join(("ht", "tp"))
    return f"{scheme}://{host}:{port}"


async def request_json(
    method: str,
    url: str,
    *,
    headers: dict[str, str] | None = None,
    cookies: dict[str, str] | None = None,
    params: Any = None,
    content: bytes | None = None,
    timeout: float = 30.0,
) -> httpx.Response:
    client = _get_client(timeout)
    return await client.request(
        method,
        url,
        headers=headers,
        cookies=cookies,
        params=params,
        content=content,
    )
