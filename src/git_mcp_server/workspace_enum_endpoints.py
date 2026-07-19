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

"""Dropdown-enumeration + owner-scoped workspace REST endpoints (W28J-1308).

License: Apache 2.0
Ownership: Cloud-Dog, Viewdeck Engineering Limited
Description: Powers the @cloud-dog/ui SelectionCriteriaPanel comboboxes — workspaces
  (list + create, owner-scoped per W28J-1302 F-1302-B), refs, paths, authors, stashes.
  Returns the `{value/id, label, secondary?}`-compatible shapes from W28J-1303 §5.
Requirements: FR1.19, FR1.20 (REQUIREMENTS.md v2.2 delta, W28J-1305)
Tasks: W28J-1308
"""

from __future__ import annotations

import subprocess
from typing import Any

from fastapi import APIRouter, HTTPException, Request

from git_tools.git.repo import GitRepository
from git_tools.process_env import current_process_env
from git_tools.security.git_auth import prime_git_https_credentials

_VALID_MODES = {"ephemeral", "persistent"}


def _is_remote_source(source: str) -> bool:
    return "://" in source or source.startswith("git@")


def build_workspace_enum_router(
    *,
    workspace_manager: Any,
    auth_runtime: Any,
    admin_runtime: Any,
    profile_store: dict[str, dict[str, Any]],
    tool_role_map: dict[str, list[str]],
    tool_default_deny: bool = True,
    prefix: str = "",
) -> APIRouter:
    """Build the workspace enumeration router (canonical + legacy prefixes)."""
    # Lazy import to avoid a circular import at module-load time
    # (api_server imports this module before its own helpers are defined).
    from cloud_dog_idam import RBACEngine

    from git_mcp_server.api_server import _actor_from_request, _roles_from_request, envelope
    from git_tools.security.rbac import can_execute_tool

    router = APIRouter(prefix=prefix, tags=["workspaces"])

    def _authorise(request: Request, tool_name: str) -> str:
        """Resolve the actor and enforce RBAC for a read/enumeration tool."""
        actor = _actor_from_request(request, auth_runtime, admin_runtime)
        if not actor:
            raise HTTPException(status_code=401, detail="Authentication required")
        engine = RBACEngine(role_permissions={r: set(p) for r, p in tool_role_map.items()})
        for role in _roles_from_request(request, actor, admin_runtime, auth_runtime):
            engine.assign_role_to_user(actor, role)
        if not can_execute_tool(engine, tool_role_map, actor, tool_name, default_deny=tool_default_deny):
            raise HTTPException(status_code=403, detail=f"Forbidden: requires access to {tool_name}")
        return actor

    def _workspace(workspace_id: str) -> Any:
        try:
            return workspace_manager.get_workspace(workspace_id)
        except KeyError as exc:
            raise HTTPException(status_code=404, detail=f"Unknown workspace: {workspace_id}") from exc

    @router.get("/workspaces")
    def list_workspaces(request: Request, profile_id: str = "", owner: str = "") -> dict[str, Any]:
        actor = _authorise(request, "repo_open")
        owner_clean = owner.strip()
        owner_filter = actor if owner_clean.lower() == "me" else (owner_clean or None)
        items: list[dict[str, Any]] = []
        for ws in workspace_manager.list_workspaces(owner=owner_filter, profile=(profile_id.strip() or None)):
            items.append(
                {
                    "workspace_id": ws.workspace_id,
                    "profile_id": ws.profile,
                    "mode": ws.mode,
                    "path": str(ws.path),
                    "last_used_at": ws.last_used_at.isoformat(),
                    "current_ref": (ws.ref_context.ref_name if ws.ref_context else None),
                    "is_open": workspace_manager.is_open(ws.workspace_id),
                    "owner": ws.owner,
                }
            )
        return envelope(result={"items": items}, request=request)

    @router.post("/workspaces")
    def create_workspace(body: dict[str, Any], request: Request) -> dict[str, Any]:
        actor = _authorise(request, "repo_open")
        profile_id = str(body.get("profile_id") or "").strip()
        if not profile_id:
            raise HTTPException(status_code=400, detail="profile_id is required")
        profile = profile_store.get(profile_id)
        if profile is None:
            raise HTTPException(status_code=404, detail=f"Unknown profile: {profile_id}")
        repo_cfg = profile.get("repo") if isinstance(profile.get("repo"), dict) else {}
        repo_source = str(repo_cfg.get("source") or "").strip()
        if not repo_source:
            raise HTTPException(status_code=400, detail=f"Profile {profile_id} has no repo source")
        mode = str(body.get("mode") or "persistent").strip().lower()
        if mode not in _VALID_MODES:
            raise HTTPException(status_code=400, detail="mode must be 'ephemeral' or 'persistent'")
        # W28J-1302 §3.5 / F-1302-B: session_id is derived from the authenticated owner so
        # a persistent workspace_id is deterministic + idempotent per (profile, owner). The
        # client never types it. repo_source is resolved server-side from the profile (GMC-W-04).
        try:
            ws = workspace_manager.create_workspace(
                profile=profile_id,
                repo_source=repo_source,
                session_id=actor,
                mode=mode,  # type: ignore[arg-type]
                owner=actor,
                default_branch=str(repo_cfg.get("default_branch") or "").strip() or None,
            )
        except Exception as exc:  # noqa: BLE001
            raise HTTPException(status_code=400, detail=f"Failed to create workspace: {exc}") from exc
        return envelope(result={"workspace_id": ws.workspace_id}, request=request)

    @router.get("/workspaces/{workspace_id}/refs")
    def list_refs(workspace_id: str, request: Request, type: str = "branch", prefix: str = "") -> dict[str, Any]:  # noqa: A002
        ref_type = type.strip().lower()
        tool = {"branch": "git_branch_list", "tag": "git_tag_list", "commit": "git_log"}.get(ref_type)
        if tool is None:
            raise HTTPException(status_code=400, detail="type must be 'branch', 'tag', or 'commit'")
        _authorise(request, tool)
        ws = _workspace(workspace_id)
        repo = GitRepository(ws.path)
        items: list[dict[str, Any]] = []
        if ref_type == "branch":
            # GMC-P-08: surface local AND remote branches so the dropdown lists every
            # available branch, not just the one checked out by a fresh clone.
            named: dict[str, dict[str, Any]] = {}
            for name in repo.branch_list():
                named[name] = {"ref_name": name, "ref_type": "branch", "ref_id": name, "secondary": "local"}
            for remote in repo.repo.remotes:
                for remote_ref in remote.refs:
                    short = getattr(remote_ref, "remote_head", "")
                    if short and short != "HEAD" and short not in named:
                        named[short] = {
                            "ref_name": short,
                            "ref_type": "branch",
                            "ref_id": remote_ref.name,
                            "secondary": "remote",
                        }
            items.extend(named.values())
        elif ref_type == "tag":
            for name in sorted({tag.name for tag in repo.repo.tags}):
                items.append({"ref_name": name, "ref_type": "tag", "ref_id": name})
        else:  # commit
            out = str(repo.repo.git.log("--format=%H%x09%s", "-n", "50"))
            for line in out.splitlines():
                sha, _, subject = line.partition("\t")
                if sha.strip():
                    items.append(
                        {"ref_name": sha[:12], "ref_type": "commit", "ref_id": sha.strip(), "secondary": subject.strip()}
                    )
        prefix_clean = prefix.strip()
        if prefix_clean:
            items = [i for i in items if str(i["ref_name"]).startswith(prefix_clean) or str(i["ref_id"]).startswith(prefix_clean)]
        return envelope(result={"items": items}, request=request)

    @router.get("/workspaces/{workspace_id}/paths")
    def list_paths(
        workspace_id: str, request: Request, ref: str = "", prefix: str = "", limit: int = 200
    ) -> dict[str, Any]:
        _authorise(request, "dir_list")
        ws = _workspace(workspace_id)
        repo = GitRepository(ws.path)
        target = ref.strip() or "HEAD"
        try:
            out = str(repo.repo.git.ls_tree("-r", "--name-only", target))
        except Exception as exc:  # noqa: BLE001
            raise HTTPException(status_code=400, detail=f"Cannot list paths at '{target}': {exc}") from exc
        files = [p for p in out.splitlines() if p.strip()]
        prefix_clean = prefix.strip()
        if prefix_clean:
            files = [p for p in files if p.startswith(prefix_clean)]
        dirs = sorted({"/".join(p.split("/")[: i + 1]) for p in files for i in range(len(p.split("/")) - 1)})
        if prefix_clean:
            dirs = [d for d in dirs if d.startswith(prefix_clean)]
        items: list[dict[str, Any]] = [{"path": d, "kind": "dir"} for d in dirs]
        items += [{"path": p, "kind": "file"} for p in files]
        cap = max(1, min(int(limit), 200))
        return envelope(result={"items": items[:cap]}, request=request)

    @router.get("/workspaces/{workspace_id}/authors")
    def list_authors(workspace_id: str, request: Request) -> dict[str, Any]:
        _authorise(request, "git_log")
        ws = _workspace(workspace_id)
        repo = GitRepository(ws.path)
        out = str(repo.repo.git.log("--format=%an%x09%ae%x09%aI", "-n", "500"))
        seen: dict[tuple[str, str], dict[str, Any]] = {}
        for line in out.splitlines():
            name, _, rest = line.partition("\t")
            email, _, when = rest.partition("\t")
            key = (name.strip(), email.strip())
            if key[0] and key not in seen:
                seen[key] = {"author": name.strip(), "email": email.strip(), "last_commit_at": when.strip()}
        items = list(seen.values())[:100]
        return envelope(result={"items": items}, request=request)

    @router.get("/workspaces/{workspace_id}/stashes")
    def list_stashes(workspace_id: str, request: Request) -> dict[str, Any]:
        _authorise(request, "git_stash_list")
        ws = _workspace(workspace_id)
        repo = GitRepository(ws.path)
        try:
            out = str(repo.repo.git.stash("list", "--format=%gd%x09%ci%x09%gs"))
        except Exception:  # noqa: BLE001
            out = ""
        items: list[dict[str, Any]] = []
        for line in out.splitlines():
            stash_id, _, rest = line.partition("\t")
            created_at, _, message = rest.partition("\t")
            if stash_id.strip():
                items.append(
                    {"stash_id": stash_id.strip(), "message": message.strip(), "created_at": created_at.strip()}
                )
        return envelope(result={"items": items}, request=request)

    # W28J-1327: profile-scoped branch enumeration WITHOUT an open workspace (GMC-P-08/11).
    @router.get("/profiles/{name}/branches")
    def list_profile_branches(name: str, request: Request, prefix: str = "") -> dict[str, Any]:
        _authorise(request, "git_branch_list")
        profile = profile_store.get(name)
        if profile is None:
            raise HTTPException(status_code=404, detail=f"Unknown profile: {name}")
        repo_cfg = profile.get("repo") if isinstance(profile.get("repo"), dict) else {}
        source = str(repo_cfg.get("source") or "").strip()
        if not source:
            raise HTTPException(status_code=400, detail=f"Profile {name} has no repo source")
        env = current_process_env()
        if _is_remote_source(source):
            prime_git_https_credentials(env, source)
        env["GIT_TERMINAL_PROMPT"] = "0"
        try:
            out = subprocess.run(
                ["git", "ls-remote", "--heads", source],
                env=env,
                capture_output=True,
                text=True,
                timeout=30,
                check=False,
            )
        except Exception as exc:  # noqa: BLE001
            raise HTTPException(status_code=502, detail=f"ls-remote failed for profile {name}: {exc}") from exc
        if out.returncode != 0:
            raise HTTPException(status_code=502, detail=f"ls-remote failed for profile {name}: {out.stderr.strip()[:200]}")
        default_branch = str(repo_cfg.get("default_branch") or "main").strip()
        items: list[dict[str, Any]] = []
        for line in out.stdout.splitlines():
            parts = line.split("\t")
            if len(parts) == 2 and parts[1].startswith("refs/heads/"):
                branch = parts[1][len("refs/heads/") :]
                items.append(
                    {"ref_name": branch, "ref_type": "branch", "ref_id": branch, "is_default": branch == default_branch}
                )
        prefix_clean = prefix.strip()
        if prefix_clean:
            items = [i for i in items if str(i["ref_name"]).startswith(prefix_clean)]
        return envelope(result={"items": items}, request=request)

    # W28J-1327: profile sync status (last_sync_at + ahead/behind) when a workspace is open (GMC-P-09).
    @router.get("/profiles/{name}/sync-status")
    def profile_sync_status(name: str, request: Request) -> dict[str, Any]:
        _authorise(request, "git_log")
        profile = profile_store.get(name)
        if profile is None:
            raise HTTPException(status_code=404, detail=f"Unknown profile: {name}")
        open_ws = next(
            (w for w in workspace_manager.list_workspaces(profile=name) if workspace_manager.is_open(w.workspace_id)),
            None,
        )
        if open_ws is None:
            return envelope(
                result={"last_sync_at": None, "remote_ahead": None, "remote_behind": None, "status": "no_open_workspace"},
                request=request,
            )
        repo = GitRepository(open_ws.path)
        ahead: int | None = None
        behind: int | None = None
        sync_state = "no_upstream"
        try:
            counts = str(repo.repo.git.rev_list("--left-right", "--count", "HEAD...@{upstream}")).split()
            if len(counts) == 2:
                ahead, behind = int(counts[0]), int(counts[1])
                sync_state = "ok"
        except Exception:  # noqa: BLE001
            ahead, behind = None, None
        return envelope(
            result={
                "last_sync_at": open_ws.last_used_at.isoformat(),
                "remote_ahead": ahead,
                "remote_behind": behind,
                "status": sync_state,
            },
            request=request,
        )

    return router
