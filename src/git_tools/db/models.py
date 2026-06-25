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

"""ORM models owned by git-mcp-server."""

from __future__ import annotations

from cloud_dog_db import PlatformBase, TimestampMixin
from sqlalchemy import Boolean, String, Text
from sqlalchemy.orm import Mapped, mapped_column


class GitPlatformDbState(PlatformBase, TimestampMixin):
    """Minimal service-owned table proving schema ownership and migrations."""

    __tablename__ = "git_platform_db_state"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    service: Mapped[str] = mapped_column(String(64), nullable=False, unique=True)
    status: Mapped[str] = mapped_column(String(32), nullable=False, default="ready")


class GitProfileRegistry(PlatformBase, TimestampMixin):
    """Durable repository-profile registry (W28C-1705 GM2 / 1603-unblocker).

    Single source of truth for git-mcp repository profiles across the api / mcp / a2a
    surfaces — which run as separate processes sharing the container data volume, so the
    DB is the only place they can agree. Mirrors file-mcp's ``file_storage_profiles``:
    the full ``ProfileConfig`` JSON per row, soft-delete via ``is_active``.
    """

    __tablename__ = "git_profile_registry"

    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    name: Mapped[str] = mapped_column(String(128), nullable=False, unique=True)
    display_name: Mapped[str] = mapped_column(String(256), nullable=False, default="")
    config_json: Mapped[str] = mapped_column(Text, nullable=False, default="{}")
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
