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

import hashlib
import json
import shutil
import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from os import environ, getenv
from pathlib import Path
from typing import Literal

from cloud_dog_storage import path_utils
from git import Repo
from cloud_dog_logging import get_logger
from git_tools.files.io import load_host_text, store_host_text

from git_tools.security.git_auth import prime_git_https_credentials
from git_tools.workspaces.ref_context import RefContext, RefResolver, RefType

_log = get_logger(__name__)

_WORKSPACE_META_FILE = ".workspace-meta.json"

WorkspaceMode = Literal["ephemeral", "persistent"]


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


def _is_remote_source(repo_source: str) -> bool:
    """Return True when the repository source is a remote URL."""
    if "://" in repo_source:
        return True
    return repo_source.startswith("git@")


def _remote_clone_depth() -> int | None:
    """Resolve optional shallow clone depth for remote repositories."""
    raw = getenv("GIT_MCP_REMOTE_CLONE_DEPTH", "").strip()
    if not raw:
        return None
    try:
        value = int(raw)
    except ValueError:
        return None
    if value <= 0:
        return None
    return value


@dataclass(slots=True)
class Workspace:
    """Workspace metadata."""

    workspace_id: str
    profile: str
    mode: WorkspaceMode
    path: Path
    created_at: datetime = field(default_factory=_utcnow)
    last_used_at: datetime = field(default_factory=_utcnow)
    ref_context: RefContext | None = None


def _deterministic_workspace_id(profile: str, session_id: str) -> str:
    """Generate a deterministic workspace ID from profile + session_id.

    Same inputs always produce the same ID so persistent workspaces
    can be reopened across sessions and server restarts.
    """
    slug = hashlib.sha256(f"{profile}-{session_id}".encode()).hexdigest()[:12]
    return f"{profile}-{slug}"


class WorkspaceManager:
    """Manage workspace directories and git checkouts."""

    def __init__(self, base_dir: str | Path) -> None:
        self.base_dir = path_utils.as_path(str(base_dir)).resolve()
        self.base_dir.mkdir(parents=True, exist_ok=True)
        self._workspaces: dict[str, Workspace] = {}
        self._restore_persistent_workspaces()

    def _restore_persistent_workspaces(self) -> None:
        """Scan base_dir for workspace directories with metadata and reload them."""
        if not self.base_dir.exists():
            return
        for entry in self.base_dir.iterdir():
            if not entry.is_dir():
                continue
            meta_path = entry / _WORKSPACE_META_FILE
            if not meta_path.exists():
                continue
            try:
                meta = json.loads(load_host_text(meta_path))
                workspace = Workspace(
                    workspace_id=meta["workspace_id"],
                    profile=meta["profile"],
                    mode=meta.get("mode", "persistent"),
                    path=entry,
                    created_at=datetime.fromisoformat(meta["created_at"]),
                    last_used_at=datetime.fromisoformat(meta.get("last_used_at", meta["created_at"])),
                )
                self._workspaces[workspace.workspace_id] = workspace
                _log.info(f"Restored persistent workspace {workspace.workspace_id} from disk")
            except Exception:  # noqa: BLE001
                _log.warning(f"Skipping corrupt workspace metadata in {entry}")

    def create_workspace(
        self,
        profile: str,
        repo_source: str,
        session_id: str,
        mode: WorkspaceMode = "ephemeral",
        workspace_id: str | None = None,
    ) -> Workspace:
        """Create and initialise a workspace by cloning the source repository.

        For persistent workspaces, a deterministic ID is generated from
        profile + session_id so the same combination always maps to the
        same workspace.  If the workspace already exists (in-memory or on
        disk) it is returned directly without re-cloning.

        Callers may also supply an explicit *workspace_id* to reopen a
        known workspace.
        """
        if workspace_id is None:
            if mode == "persistent":
                workspace_id = _deterministic_workspace_id(profile, session_id)
            else:
                workspace_id = f"{profile}-{session_id}-{uuid.uuid4().hex[:8]}"

        # Return existing workspace if already tracked.
        existing = self._workspaces.get(workspace_id)
        if existing is not None and existing.path.exists():
            existing.last_used_at = _utcnow()
            self._save_metadata(existing)
            return existing

        workspace_path = (self.base_dir / workspace_id).resolve()

        # If the directory exists on disk with metadata but wasn't in-memory
        # (e.g. after a server restart), restore it instead of re-cloning.
        meta_path = workspace_path / _WORKSPACE_META_FILE
        if workspace_path.exists() and meta_path.exists():
            try:
                meta = json.loads(load_host_text(meta_path))
                workspace = Workspace(
                    workspace_id=workspace_id,
                    profile=meta["profile"],
                    mode=meta.get("mode", mode),
                    path=workspace_path,
                    created_at=datetime.fromisoformat(meta["created_at"]),
                    last_used_at=_utcnow(),
                )
                self._workspaces[workspace_id] = workspace
                self._save_metadata(workspace)
                _log.info(f"Restored workspace {workspace_id} from disk")
                return workspace
            except Exception:  # noqa: BLE001
                _log.warning(f"Corrupt metadata for {workspace_id} — re-cloning")
                path_utils.rmtree(str(workspace_path), ignore_errors=True)

        if _is_remote_source(repo_source):
            prime_git_https_credentials(environ, repo_source)

        clone_env: dict[str, str] = dict(environ)
        clone_env["GIT_TERMINAL_PROMPT"] = "0"
        if not clone_env.get("GIT_SSH_COMMAND"):
            clone_env["GIT_SSH_COMMAND"] = "ssh -o BatchMode=yes -o StrictHostKeyChecking=accept-new"

        clone_kwargs: dict[str, object] = {"env": clone_env}
        if _is_remote_source(repo_source):
            depth = _remote_clone_depth()
            if depth is not None:
                clone_kwargs["depth"] = depth

        repo = Repo.clone_from(repo_source, workspace_path, **clone_kwargs)
        repo.git.config("core.hooksPath", "/dev/null")

        workspace = Workspace(
            workspace_id=workspace_id,
            profile=profile,
            mode=mode,
            path=workspace_path,
        )
        self._workspaces[workspace_id] = workspace
        self._save_metadata(workspace)
        return workspace

    def _save_metadata(self, workspace: Workspace) -> None:
        """Persist workspace metadata to a JSON file alongside the workspace directory."""
        if workspace.mode != "persistent":
            return
        meta_path = workspace.path / _WORKSPACE_META_FILE
        try:
            store_host_text(
                meta_path,
                json.dumps(
                    {
                        "workspace_id": workspace.workspace_id,
                        "profile": workspace.profile,
                        "mode": workspace.mode,
                        "created_at": workspace.created_at.isoformat(),
                        "last_used_at": workspace.last_used_at.isoformat(),
                    },
                    indent=2,
                ),
            )
        except OSError:
            _log.warning(f"Failed to write workspace metadata for {workspace.workspace_id}")

    def get_workspace(self, workspace_id: str) -> Workspace:
        """Fetch workspace metadata."""
        workspace = self._workspaces.get(workspace_id)
        if workspace is None:
            raise KeyError(f"Unknown workspace: {workspace_id}")
        workspace.last_used_at = _utcnow()
        return workspace

    def close_workspace(self, workspace_id: str) -> None:
        """Close a workspace and clean ephemeral directories.

        Persistent workspaces keep their directory and metadata on disk
        so they can be restored on the next server start or re-open.
        """
        workspace = self.get_workspace(workspace_id)
        if workspace.mode == "ephemeral" and workspace.path.exists():
            path_utils.rmtree(str(workspace.path), ignore_errors=True)
        elif workspace.mode == "persistent":
            self._save_metadata(workspace)
        self._workspaces.pop(workspace_id, None)

    def cleanup_expired(self, ttl_seconds: int) -> list[str]:
        """Clean workspaces whose last-used timestamp exceeds TTL."""
        now = _utcnow()
        deleted: list[str] = []
        for workspace_id, workspace in list(self._workspaces.items()):
            elapsed = (now - workspace.last_used_at).total_seconds()
            if elapsed > ttl_seconds:
                self.close_workspace(workspace_id)
                deleted.append(workspace_id)
        return deleted

    @staticmethod
    def _ensure_local_branch(repo: Repo, branch_name: str) -> None:
        """Materialise a local branch from `origin/<branch>` when available.

        Requirements: FR-01, FR-07.
        """
        if branch_name in [branch.name for branch in repo.branches]:
            return
        for remote in repo.remotes:
            remote_ref = f"{remote.name}/{branch_name}"
            if remote_ref in [ref.name for ref in remote.refs]:
                repo.git.branch(branch_name, remote_ref)
                return

    def set_ref(self, workspace_id: str, ref_type: RefType, ref_name: str) -> RefContext:
        """Set the checked out ref for a workspace."""
        workspace = self.get_workspace(workspace_id)
        repo = Repo(workspace.path)
        if ref_type == "branch":
            self._ensure_local_branch(repo, ref_name)
        resolver = RefResolver(repo)
        resolved = resolver.resolve(ref_type=ref_type, ref_name=ref_name)

        if resolved.ref_type == "branch":
            repo.git.checkout(resolved.ref_name)
        else:
            repo.git.checkout(resolved.resolved_commit)

        workspace.ref_context = resolved
        workspace.last_used_at = _utcnow()
        return resolved
