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

from collections.abc import Callable
from dataclasses import dataclass
from fnmatch import fnmatch
from typing import Any, TypeVar, cast

from pydantic import BaseModel

from git_tools.admin.runtime import AdminRuntime
from git_tools.files.io import (
    copy_entry,
    ensure_directory,
    list_entries,
    load_text,
    move_entry,
    remove_directory,
    remove_entry,
    store_bytes_atomic,
    store_text_atomic,
)
from git_tools.files.search import search_content, search_files
from git_tools.files import file_to_base64
from git_tools.git.conflicts import list_conflicts, resolve_conflicts
from git_tools.git.operations import (
    git_diff,
    git_fetch,
    git_log,
    git_merge,
    git_merge_abort,
    git_merge_continue,
    git_pull,
    git_push,
    git_rebase,
    git_rebase_abort,
    git_rebase_continue,
    git_status,
)
from git_tools.git.repo import GitRepository
from git_tools.git.tags import TagService
from git_tools.tools.definitions import (
    AdminCredentialsSetInput,
    AdminApiKeyCreateInput,
    AdminApiKeyListInput,
    AdminApiKeyReadInput,
    AdminApiKeyRevokeInput,
    AdminGroupCreateInput,
    AdminGroupDeleteInput,
    AdminGroupListInput,
    AdminGroupReadInput,
    AdminGroupUpdateInput,
    AdminProfileCreateInput,
    AdminRbacBindInput,
    AdminRbacUnbindInput,
    AdminUserCreateInput,
    AdminUserDeleteInput,
    AdminUserListInput,
    AdminUserReadInput,
    AdminUserUpdateInput,
    DirListInput,
    DirMkdirInput,
    DirRmdirInput,
    FileCopyInput,
    FileDeleteInput,
    FileDownloadInput,
    FileMoveInput,
    FileReadInput,
    FileUploadInput,
    FileWriteInput,
    GitAddInput,
    GitBranchCreateInput,
    GitBranchDeleteInput,
    GitBranchFromRefInput,
    GitBranchListInput,
    GitCheckoutInput,
    GitCommitInput,
    GitConflictResolveInput,
    GitConflictResolveManualInput,
    GitConflictsListInput,
    GitDiffInput,
    GitFetchInput,
    GitLogInput,
    GitMergeAbortInput,
    GitMergeContinueInput,
    GitMergeInput,
    GitPullInput,
    GitPushInput,
    GitRebaseAbortInput,
    GitRebaseContinueInput,
    GitRebaseInput,
    GitResetInput,
    GitStashListInput,
    GitStashPopInput,
    GitStashSaveInput,
    GitStatusInput,
    GitTagCreateInput,
    GitTagDeleteInput,
    GitTagListInput,
    GitTagPushInput,
    RefSpec,
    RepoCloseInput,
    RepoOpenInput,
    RepoSetRefInput,
    SearchContentInput,
    SearchFilesInput,
)
from git_tools.workspaces.manager import Workspace, WorkspaceManager

ModelT = TypeVar("ModelT", bound=BaseModel)


@dataclass(slots=True)
class ToolContract:
    """Minimal MCP tool contract."""

    name: str
    description: str
    input_schema: dict[str, Any]
    output_schema: dict[str, Any]
    handler: Callable[[dict[str, Any]], dict[str, Any]]


class ToolRegistry:
    """Build and execute all git-mcp-server tools."""

    _MUTATION_TOOLS = {
        "file_write",
        "file_upload",
        "file_move",
        "file_copy",
        "file_delete",
        "dir_mkdir",
        "dir_rmdir",
        "git_add",
        "git_reset",
        "git_commit",
        "git_push",
        "git_pull",
        "git_checkout",
        "git_branch_create",
        "git_branch_delete",
        "git_branch_from_ref",
        "git_merge",
        "git_merge_abort",
        "git_merge_continue",
        "git_rebase",
        "git_rebase_abort",
        "git_rebase_continue",
        "git_stash_save",
        "git_stash_pop",
        "git_tag_create",
        "git_tag_delete",
        "git_tag_push",
        "git_conflict_resolve",
        "git_conflict_resolve_manual",
    }

    def __init__(
        self,
        workspace_manager: WorkspaceManager,
        admin_runtime: AdminRuntime | None = None,
        profile_store: dict[str, dict[str, Any]] | None = None,
        user_store: dict[str, dict[str, Any]] | None = None,
        group_store: dict[str, dict[str, Any]] | None = None,
        role_bindings: dict[str, set[str]] | None = None,
        credential_store: dict[str, str] | None = None,
    ) -> None:
        self.workspace_manager = workspace_manager
        self.admin_runtime = admin_runtime
        self.profile_store = profile_store if profile_store is not None else {}
        self.user_store = user_store if user_store is not None else {}
        self.group_store = group_store if group_store is not None else {}
        self.role_bindings = role_bindings if role_bindings is not None else {}
        self.credential_store = credential_store if credential_store is not None else {}
        if self.admin_runtime is not None:
            self.profile_store = self.admin_runtime.profile_store
            self.user_store = self.admin_runtime.user_store
            self.group_store = self.admin_runtime.group_store
            self.role_bindings = self.admin_runtime.role_bindings
        self._tools = self._build_registry()

    def _tool(
        self,
        name: str,
        description: str,
        input_model: type[BaseModel],
        handler: Callable[[dict[str, Any]], dict[str, Any]],
    ) -> ToolContract:
        return ToolContract(
            name=name,
            description=description,
            input_schema=input_model.model_json_schema(),
            output_schema={"type": "object"},
            handler=handler,
        )

    def _build_registry(self) -> dict[str, ToolContract]:
        tools = {
            "repo_open": self._tool(
                "repo_open",
                "Create workspace and open repository context.",
                RepoOpenInput,
                self._repo_access,
            ),
            "repo_close": self._tool(
                "repo_close",
                "Close and optionally clean workspace.",
                RepoCloseInput,
                self._repo_close,
            ),
            "repo_set_ref": self._tool(
                "repo_set_ref",
                "Switch workspace ref context.",
                RepoSetRefInput,
                self._repo_set_ref,
            ),
            "git_status": self._tool("git_status", "Read git status.", GitStatusInput, self._git_status),
            "git_log": self._tool("git_log", "Read filtered git log.", GitLogInput, self._git_log),
            "git_diff": self._tool("git_diff", "Read git diff between refs.", GitDiffInput, self._git_diff),
            "git_add": self._tool("git_add", "Stage files.", GitAddInput, self._git_add),
            "git_reset": self._tool("git_reset", "Reset staged changes.", GitResetInput, self._git_reset),
            "git_commit": self._tool("git_commit", "Create commit.", GitCommitInput, self._git_commit),
            "git_fetch": self._tool("git_fetch", "Fetch remote refs.", GitFetchInput, self._git_fetch),
            "git_pull": self._tool("git_pull", "Pull from remote.", GitPullInput, self._git_pull),
            "git_push": self._tool("git_push", "Push to remote.", GitPushInput, self._git_push),
            "git_checkout": self._tool(
                "git_checkout",
                "Checkout branch/tag/commit.",
                GitCheckoutInput,
                self._git_checkout,
            ),
            "git_branch_list": self._tool(
                "git_branch_list",
                "List branches.",
                GitBranchListInput,
                self._git_branch_list,
            ),
            "git_branch_create": self._tool(
                "git_branch_create",
                "Create branch.",
                GitBranchCreateInput,
                self._git_branch_create,
            ),
            "git_branch_delete": self._tool(
                "git_branch_delete",
                "Delete branch.",
                GitBranchDeleteInput,
                self._git_branch_delete,
            ),
            "git_branch_from_ref": self._tool(
                "git_branch_from_ref",
                "Create branch from a specific ref.",
                GitBranchFromRefInput,
                self._git_branch_from_ref,
            ),
            "git_merge": self._tool("git_merge", "Merge branch/ref.", GitMergeInput, self._git_merge),
            "git_merge_abort": self._tool("git_merge_abort", "Abort merge.", GitMergeAbortInput, self._git_merge_abort),
            "git_merge_continue": self._tool(
                "git_merge_continue",
                "Continue merge after conflict resolution.",
                GitMergeContinueInput,
                self._git_merge_continue,
            ),
            "git_rebase": self._tool("git_rebase", "Rebase branch.", GitRebaseInput, self._git_rebase),
            "git_rebase_abort": self._tool(
                "git_rebase_abort",
                "Abort rebase.",
                GitRebaseAbortInput,
                self._git_rebase_abort,
            ),
            "git_rebase_continue": self._tool(
                "git_rebase_continue",
                "Continue rebase after conflict resolution.",
                GitRebaseContinueInput,
                self._git_rebase_continue,
            ),
            "git_stash_save": self._tool("git_stash_save", "Stash changes.", GitStashSaveInput, self._git_stash_save),
            "git_stash_list": self._tool("git_stash_list", "List stashes.", GitStashListInput, self._git_stash_list),
            "git_stash_pop": self._tool("git_stash_pop", "Pop latest stash.", GitStashPopInput, self._git_stash_pop),
            "git_tag_create": self._tool("git_tag_create", "Create tag.", GitTagCreateInput, self._git_tag_create),
            "git_tag_delete": self._tool("git_tag_delete", "Delete tag.", GitTagDeleteInput, self._git_tag_delete),
            "git_tag_list": self._tool("git_tag_list", "List tags.", GitTagListInput, self._git_tag_list),
            "git_tag_push": self._tool("git_tag_push", "Push tag(s).", GitTagPushInput, self._git_tag_push),
            "git_conflicts_list": self._tool(
                "git_conflicts_list",
                "List unresolved conflicts.",
                GitConflictsListInput,
                self._git_conflicts_list,
            ),
            "git_conflict_resolve": self._tool(
                "git_conflict_resolve",
                "Resolve conflicts using ours/theirs/manual content.",
                GitConflictResolveInput,
                self._git_conflict_resolve,
            ),
            "git_conflict_resolve_manual": self._tool(
                "git_conflict_resolve_manual",
                "Resolve a single conflict with provided content.",
                GitConflictResolveManualInput,
                self._git_conflict_resolve_manual,
            ),
            "file_read": self._tool("file_read", "Read file content.", FileReadInput, self._file_read),
            "file_write": self._tool("file_write", "Write file content.", FileWriteInput, self._file_write),
            "file_upload": self._tool(
                "file_upload",
                "Upload base64 payload as file.",
                FileUploadInput,
                self._file_upload,
            ),
            "file_download": self._tool(
                "file_download",
                "Download file as base64 payload.",
                FileDownloadInput,
                self._file_download,
            ),
            "file_move": self._tool("file_move", "Move file/directory path.", FileMoveInput, self._file_move),
            "file_copy": self._tool("file_copy", "Copy file/directory path.", FileCopyInput, self._file_copy),
            "file_delete": self._tool("file_delete", "Delete file path.", FileDeleteInput, self._file_delete),
            "dir_list": self._tool("dir_list", "List directory entries.", DirListInput, self._dir_list),
            "dir_mkdir": self._tool("dir_mkdir", "Create directory.", DirMkdirInput, self._dir_mkdir),
            "dir_rmdir": self._tool("dir_rmdir", "Remove directory.", DirRmdirInput, self._dir_rmdir),
            "search_content": self._tool(
                "search_content",
                "Search file content.",
                SearchContentInput,
                self._search_content,
            ),
            "search_files": self._tool("search_files", "Search file paths.", SearchFilesInput, self._search_files),
            "admin_profile_create": self._tool(
                "admin_profile_create",
                "Create or replace profile configuration.",
                AdminProfileCreateInput,
                self._admin_profile_create,
            ),
            "admin_user_create": self._tool(
                "admin_user_create",
                "Create admin user record.",
                AdminUserCreateInput,
                self._admin_user_create,
            ),
            "admin_user_read": self._tool(
                "admin_user_read",
                "Read admin user record.",
                AdminUserReadInput,
                self._admin_user_read,
            ),
            "admin_user_list": self._tool(
                "admin_user_list",
                "List admin user records.",
                AdminUserListInput,
                self._admin_user_list,
            ),
            "admin_user_update": self._tool(
                "admin_user_update",
                "Update admin user record.",
                AdminUserUpdateInput,
                self._admin_user_update,
            ),
            "admin_user_delete": self._tool(
                "admin_user_delete",
                "Delete admin user record.",
                AdminUserDeleteInput,
                self._admin_user_delete,
            ),
            "admin_group_create": self._tool(
                "admin_group_create",
                "Create admin group record.",
                AdminGroupCreateInput,
                self._admin_group_create,
            ),
            "admin_group_read": self._tool(
                "admin_group_read",
                "Read admin group record.",
                AdminGroupReadInput,
                self._admin_group_read,
            ),
            "admin_group_list": self._tool(
                "admin_group_list",
                "List admin group records.",
                AdminGroupListInput,
                self._admin_group_list,
            ),
            "admin_group_update": self._tool(
                "admin_group_update",
                "Update admin group record.",
                AdminGroupUpdateInput,
                self._admin_group_update,
            ),
            "admin_group_delete": self._tool(
                "admin_group_delete",
                "Delete admin group record.",
                AdminGroupDeleteInput,
                self._admin_group_delete,
            ),
            "admin_rbac_bind": self._tool(
                "admin_rbac_bind",
                "Bind role to user.",
                AdminRbacBindInput,
                self._admin_rbac_bind,
            ),
            "admin_rbac_unbind": self._tool(
                "admin_rbac_unbind",
                "Unbind role from user.",
                AdminRbacUnbindInput,
                self._admin_rbac_unbind,
            ),
            "admin_credentials_set": self._tool(
                "admin_credentials_set",
                "Store named credential reference.",
                AdminCredentialsSetInput,
                self._admin_credentials_set,
            ),
            "admin_api_key_create": self._tool(
                "admin_api_key_create",
                "Create managed API key with capability scope metadata.",
                AdminApiKeyCreateInput,
                self._admin_api_key_create,
            ),
            "admin_api_key_list": self._tool(
                "admin_api_key_list",
                "List managed API keys.",
                AdminApiKeyListInput,
                self._admin_api_key_list,
            ),
            "admin_api_key_read": self._tool(
                "admin_api_key_read",
                "Read managed API key metadata.",
                AdminApiKeyReadInput,
                self._admin_api_key_read,
            ),
            "admin_api_key_revoke": self._tool(
                "admin_api_key_revoke",
                "Revoke managed API key.",
                AdminApiKeyRevokeInput,
                self._admin_api_key_revoke,
            ),
        }
        return tools

    def list_tools(self) -> list[dict[str, Any]]:
        """Return metadata for all registered tools."""
        return [
            {
                "name": tool.name,
                "description": tool.description,
                "input_schema": tool.input_schema,
                "output_schema": tool.output_schema,
            }
            for tool in self._tools.values()
        ]

    def call(self, name: str, payload: dict[str, Any]) -> dict[str, Any]:
        """Execute a registered tool handler."""
        if name not in self._tools:
            raise KeyError(f"Unknown tool: {name}")
        return self._call_with_audit(name, payload)

    def _call_with_audit(self, name: str, payload: dict[str, Any]) -> dict[str, Any]:
        """Execute tool with PS-50 audit logging and content redaction."""
        import logging as _log
        import time as _t
        _audit = _log.getLogger("git_mcp.tool_audit")
        _safe = {k: ("[REDACTED]" if k.lower() in ("content", "password", "secret", "token", "body") else v) for k, v in payload.items()}
        _t0 = _t.monotonic()
        try:
            result = self._tools[name].handler(payload)
            _audit.info("mcp_tool_call", extra={"event_type": "mcp_tool_call", "tool_name": name, "parameters": _safe, "outcome": "success", "duration_ms": round((_t.monotonic() - _t0) * 1000, 2), "service": "git-mcp"})
            return result
        except Exception:
            _audit.warning("mcp_tool_call", extra={"event_type": "mcp_tool_call", "tool_name": name, "parameters": _safe, "outcome": "error", "duration_ms": round((_t.monotonic() - _t0) * 1000, 2), "service": "git-mcp"})
            raise

    def call_with_access(
        self,
        name: str,
        payload: dict[str, Any],
        *,
        actor_id: str = "",
        roles: set[str] | None = None,
        capabilities: set[str] | None = None,
    ) -> dict[str, Any]:
        """Execute a registered tool handler with optional profile-scoped access enforcement."""
        if name not in self._tools:
            raise KeyError(f"Unknown tool: {name}")
        self._require_profile_access(
            name,
            payload,
            actor_id=actor_id,
            roles=roles or set(),
            capabilities=capabilities or set(),
        )
        return self._call_with_audit(name, payload)

    def contracts(self) -> dict[str, ToolContract]:
        """Return all tool contracts."""
        return self._tools

    def _validate(self, model: type[ModelT], payload: dict[str, Any]) -> ModelT:
        return model.model_validate(payload)

    @staticmethod
    def _profile_permission(profile: str) -> str:
        """Return the required profile-scoped permission label."""
        return f"profile:{profile}"

    def _profile_for_call(self, name: str, payload: dict[str, Any]) -> str | None:
        """Resolve the affected profile name from direct or workspace-backed tool payloads."""
        if name.startswith("admin_"):
            return None
        profile = str(payload.get("profile", "")).strip()
        if profile:
            return profile
        workspace_id = str(payload.get("workspace_id", "")).strip()
        if workspace_id:
            return self._workspace(workspace_id).profile
        return None

    def _require_profile_access(
        self,
        name: str,
        payload: dict[str, Any],
        *,
        actor_id: str,
        roles: set[str],
        capabilities: set[str],
    ) -> None:
        """Enforce profile-scoped access for tools that target a profile."""
        profile = self._profile_for_call(name, payload)
        if profile is None:
            return
        if not actor_id and not roles and not capabilities:
            return
        required = self._profile_permission(profile)
        effective_roles = {str(item).strip() for item in roles if str(item).strip()}
        if actor_id and self.admin_runtime is not None:
            effective_roles.update(self.admin_runtime.resolve_roles(actor_id))
        effective_capabilities = {str(item).strip() for item in capabilities if str(item).strip()}
        if (
            "*" in effective_roles
            or "admin" in {item.lower() for item in effective_roles}
            or required in effective_roles
            or "*" in effective_capabilities
            or required in effective_capabilities
        ):
            return
        raise PermissionError(f"Access denied to profile '{profile}'")

    def _resolve_repo_source(self, profile: str, repo_source: str | None) -> str:
        if repo_source:
            return repo_source
        profile_obj = self.profile_store.get(profile)
        if profile_obj is None:
            raise KeyError(f"Unknown profile: {profile}")
        source = profile_obj.get("repo", {}).get("source")
        if not source:
            raise KeyError(f"Profile {profile!r} has no repo.source")
        return cast(str, source)

    def _profile_policy_value(self, profile: str, *keys: str) -> Any:
        """Return a policy value with support for legacy top-level aliases."""
        profile_obj = self.profile_store.get(profile, {})
        policy = profile_obj.get("policy")
        if isinstance(policy, dict):
            for key in keys:
                if key in policy:
                    return policy[key]
        repo = profile_obj.get("repo")
        if isinstance(repo, dict):
            for key in keys:
                if key in repo:
                    return repo[key]
        for key in keys:
            if key in profile_obj:
                return profile_obj[key]
        return None

    def _profile_allowed_branches(self, profile: str) -> list[str]:
        """Return the configured branch allowlist for a profile, if any.

        Requirements: FR-01, FR-07.
        """
        raw = self._profile_policy_value(profile, "allowed_branches")
        if not isinstance(raw, list):
            return []
        allowed: list[str] = []
        for item in raw:
            candidate = str(item).strip()
            if candidate:
                allowed.append(candidate)
        return allowed

    def _profile_is_read_only(self, profile: str) -> bool:
        """Return whether the profile is configured as read-only.

        Requirements: FR-01, FR-07.
        """
        value = self._profile_policy_value(profile, "read_only")
        if isinstance(value, bool):
            return value
        if isinstance(value, str):
            return value.strip().lower() in {"1", "true", "yes", "on"}
        return False

    def _assert_branch_allowed(self, profile: str, branch_name: str) -> None:
        """Enforce per-profile branch allowlists for branch-scoped access.

        Requirements: FR-01, FR-07.
        """
        allowed = self._profile_allowed_branches(profile)
        if not allowed:
            return
        if any(fnmatch(branch_name, pattern) for pattern in allowed):
            return
        raise PermissionError(f"Branch {branch_name!r} is not allowed for profile {profile!r}")

    def _assert_ref_allowed(self, profile: str, ref: RefSpec | None) -> None:
        """Validate an explicit branch ref against the profile allowlist."""
        if ref is None or ref.type != "branch":
            return
        self._assert_branch_allowed(profile, ref.name)

    def _assert_checkout_allowed(self, workspace: Workspace, ref: str) -> None:
        """Block direct branch checkout when the target branch is not allowed."""
        repo = self._repo(workspace)
        if ref in repo.branch_list():
            self._assert_branch_allowed(workspace.profile, ref)

    def _workspace(self, workspace_id: str) -> Workspace:
        return self.workspace_manager.get_workspace(workspace_id)

    def _repo(self, workspace: Workspace) -> GitRepository:
        return GitRepository(workspace.path)

    def _assert_mutable(self, workspace: Workspace, tool_name: str) -> None:
        if tool_name not in self._MUTATION_TOOLS:
            return
        if self._profile_is_read_only(workspace.profile):
            raise PermissionError(f"Tool {tool_name} is blocked for read-only profile {workspace.profile!r}")
        if workspace.ref_context is not None and workspace.ref_context.mode == "ref_readonly":
            raise PermissionError(f"Tool {tool_name} is blocked for ref_readonly workspaces")

    def _workspace_for_tool(self, workspace_id: str, tool_name: str) -> Workspace:
        workspace = self._workspace(workspace_id)
        self._assert_mutable(workspace, tool_name)
        return workspace

    @staticmethod
    def _serialise_ref(ref: RefSpec) -> dict[str, str]:
        return {"type": ref.type, "name": ref.name}

    def _repo_access(self, payload: dict[str, Any]) -> dict[str, Any]:
        args = self._validate(RepoOpenInput, payload)
        self._assert_ref_allowed(args.profile, args.ref)
        source = self._resolve_repo_source(args.profile, args.repo_source)
        workspace = self.workspace_manager.create_workspace(
            profile=args.profile,
            repo_source=source,
            session_id=args.session_id,
            mode=args.workspace_mode,
            workspace_id=args.workspace_id,
        )

        try:
            resolved: dict[str, Any] | None = None
            if args.ref is not None:
                resolved_ctx = self.workspace_manager.set_ref(
                    workspace.workspace_id,
                    args.ref.type,
                    args.ref.name,
                )
                resolved = {
                    "type": resolved_ctx.ref_type,
                    "name": resolved_ctx.ref_name,
                    "resolved_commit": resolved_ctx.resolved_commit,
                    "mode": resolved_ctx.mode,
                }
            else:
                repo = self._repo(workspace)
                try:
                    default_branch = repo.repo.active_branch.name
                except Exception:  # noqa: BLE001
                    resolved = None
                else:
                    self._assert_branch_allowed(args.profile, default_branch)
                    resolved_ctx = self.workspace_manager.set_ref(workspace.workspace_id, "branch", default_branch)
                    resolved = {
                        "type": resolved_ctx.ref_type,
                        "name": resolved_ctx.ref_name,
                        "resolved_commit": resolved_ctx.resolved_commit,
                        "mode": resolved_ctx.mode,
                    }

            return {
                "workspace_id": workspace.workspace_id,
                "path": str(workspace.path),
                "mode": workspace.mode,
                "resolved_ref": resolved,
            }
        except Exception:
            self.workspace_manager.close_workspace(workspace.workspace_id)
            raise

    def _repo_close(self, payload: dict[str, Any]) -> dict[str, Any]:
        args = self._validate(RepoCloseInput, payload)
        self.workspace_manager.close_workspace(args.workspace_id)
        return {"workspace_id": args.workspace_id, "closed": True}

    def _repo_set_ref(self, payload: dict[str, Any]) -> dict[str, Any]:
        args = self._validate(RepoSetRefInput, payload)
        self._assert_ref_allowed(self._workspace(args.workspace_id).profile, args.ref)
        resolved_ctx = self.workspace_manager.set_ref(
            args.workspace_id,
            args.ref.type,
            args.ref.name,
        )
        return {
            "workspace_id": args.workspace_id,
            "resolved_ref": {
                "type": resolved_ctx.ref_type,
                "name": resolved_ctx.ref_name,
                "resolved_commit": resolved_ctx.resolved_commit,
                "mode": resolved_ctx.mode,
            },
        }

    def _git_status(self, payload: dict[str, Any]) -> dict[str, Any]:
        args = self._validate(GitStatusInput, payload)
        workspace = self._workspace(args.workspace_id)
        entries = [
            {
                "index_status": entry.index_status,
                "worktree_status": entry.worktree_status,
                "path": entry.path,
            }
            for entry in git_status(self._repo(workspace))
        ]
        return {"entries": entries}

    def _git_log(self, payload: dict[str, Any]) -> dict[str, Any]:
        args = self._validate(GitLogInput, payload)
        workspace = self._workspace(args.workspace_id)
        output = git_log(
            self._repo(workspace),
            author=args.author,
            since=args.since,
            until=args.until,
            path=args.path,
            max_count=args.max_count,
        )
        return {"log": output}

    def _git_diff(self, payload: dict[str, Any]) -> dict[str, Any]:
        args = self._validate(GitDiffInput, payload)
        workspace = self._workspace(args.workspace_id)
        return {"diff": git_diff(self._repo(workspace), left=args.left, right=args.right)}

    def _git_add(self, payload: dict[str, Any]) -> dict[str, Any]:
        args = self._validate(GitAddInput, payload)
        workspace = self._workspace_for_tool(args.workspace_id, "git_add")
        repo = self._repo(workspace)
        repo.add(*args.paths)
        return {"staged": args.paths}

    def _git_reset(self, payload: dict[str, Any]) -> dict[str, Any]:
        args = self._validate(GitResetInput, payload)
        workspace = self._workspace_for_tool(args.workspace_id, "git_reset")
        repo = self._repo(workspace)
        result = repo.reset(*args.paths, hard=args.hard)
        return {"result": result}

    def _git_commit(self, payload: dict[str, Any]) -> dict[str, Any]:
        args = self._validate(GitCommitInput, payload)
        workspace = self._workspace_for_tool(args.workspace_id, "git_commit")
        commit = self._repo(workspace).commit(args.message)
        return {"commit": commit}

    def _git_fetch(self, payload: dict[str, Any]) -> dict[str, Any]:
        args = self._validate(GitFetchInput, payload)
        workspace = self._workspace(args.workspace_id)
        return {"result": git_fetch(self._repo(workspace), remote=args.remote)}

    def _git_pull(self, payload: dict[str, Any]) -> dict[str, Any]:
        args = self._validate(GitPullInput, payload)
        workspace = self._workspace_for_tool(args.workspace_id, "git_pull")
        result = git_pull(self._repo(workspace), remote=args.remote, branch=args.branch)
        return {"result": result}

    def _git_push(self, payload: dict[str, Any]) -> dict[str, Any]:
        args = self._validate(GitPushInput, payload)
        workspace = self._workspace_for_tool(args.workspace_id, "git_push")
        result = git_push(
            self._repo(workspace),
            remote=args.remote,
            branch=args.branch,
            force_with_lease=args.force_with_lease,
        )
        return {"result": result}

    def _git_checkout(self, payload: dict[str, Any]) -> dict[str, Any]:
        args = self._validate(GitCheckoutInput, payload)
        workspace = self._workspace_for_tool(args.workspace_id, "git_checkout")
        self._assert_checkout_allowed(workspace, args.ref)
        repo = self._repo(workspace)
        repo.checkout(args.ref)
        return {"checked_out": args.ref}

    def _git_branch_list(self, payload: dict[str, Any]) -> dict[str, Any]:
        args = self._validate(GitBranchListInput, payload)
        workspace = self._workspace(args.workspace_id)
        return {"branches": self._repo(workspace).branch_list()}

    def _git_branch_create(self, payload: dict[str, Any]) -> dict[str, Any]:
        args = self._validate(GitBranchCreateInput, payload)
        workspace = self._workspace_for_tool(args.workspace_id, "git_branch_create")
        repo = self._repo(workspace)
        repo.branch_create(args.name, from_ref=args.from_ref)
        return {"branch": args.name, "from_ref": args.from_ref}

    def _git_branch_delete(self, payload: dict[str, Any]) -> dict[str, Any]:
        args = self._validate(GitBranchDeleteInput, payload)
        workspace = self._workspace_for_tool(args.workspace_id, "git_branch_delete")
        self._repo(workspace).branch_delete(args.name, force=args.force)
        return {"deleted": args.name}

    def _git_branch_from_ref(self, payload: dict[str, Any]) -> dict[str, Any]:
        args = self._validate(GitBranchFromRefInput, payload)
        workspace = self._workspace_for_tool(args.workspace_id, "git_branch_from_ref")
        repo = self._repo(workspace)
        repo.branch_create(args.new_branch, from_ref=args.from_ref)
        return {"branch": args.new_branch, "from_ref": args.from_ref}

    def _git_merge(self, payload: dict[str, Any]) -> dict[str, Any]:
        args = self._validate(GitMergeInput, payload)
        workspace = self._workspace_for_tool(args.workspace_id, "git_merge")
        return {"result": git_merge(self._repo(workspace), ref=args.ref, ff_only=args.ff_only)}

    def _git_merge_abort(self, payload: dict[str, Any]) -> dict[str, Any]:
        args = self._validate(GitMergeAbortInput, payload)
        workspace = self._workspace_for_tool(args.workspace_id, "git_merge_abort")
        return {"result": git_merge_abort(self._repo(workspace))}

    def _git_merge_continue(self, payload: dict[str, Any]) -> dict[str, Any]:
        args = self._validate(GitMergeContinueInput, payload)
        workspace = self._workspace_for_tool(args.workspace_id, "git_merge_continue")
        return {"result": git_merge_continue(self._repo(workspace))}

    def _git_rebase(self, payload: dict[str, Any]) -> dict[str, Any]:
        args = self._validate(GitRebaseInput, payload)
        workspace = self._workspace_for_tool(args.workspace_id, "git_rebase")
        return {"result": git_rebase(self._repo(workspace), onto=args.onto)}

    def _git_rebase_abort(self, payload: dict[str, Any]) -> dict[str, Any]:
        args = self._validate(GitRebaseAbortInput, payload)
        workspace = self._workspace_for_tool(args.workspace_id, "git_rebase_abort")
        return {"result": git_rebase_abort(self._repo(workspace))}

    def _git_rebase_continue(self, payload: dict[str, Any]) -> dict[str, Any]:
        args = self._validate(GitRebaseContinueInput, payload)
        workspace = self._workspace_for_tool(args.workspace_id, "git_rebase_continue")
        return {"result": git_rebase_continue(self._repo(workspace))}

    def _git_stash_save(self, payload: dict[str, Any]) -> dict[str, Any]:
        args = self._validate(GitStashSaveInput, payload)
        workspace = self._workspace_for_tool(args.workspace_id, "git_stash_save")
        return {"result": self._repo(workspace).stash_save(args.message)}

    def _git_stash_list(self, payload: dict[str, Any]) -> dict[str, Any]:
        args = self._validate(GitStashListInput, payload)
        workspace = self._workspace(args.workspace_id)
        return {"result": self._repo(workspace).stash_list()}

    def _git_stash_pop(self, payload: dict[str, Any]) -> dict[str, Any]:
        args = self._validate(GitStashPopInput, payload)
        workspace = self._workspace_for_tool(args.workspace_id, "git_stash_pop")
        return {"result": self._repo(workspace).stash_pop()}

    def _git_tag_create(self, payload: dict[str, Any]) -> dict[str, Any]:
        args = self._validate(GitTagCreateInput, payload)
        workspace = self._workspace_for_tool(args.workspace_id, "git_tag_create")
        repo = self._repo(workspace)
        if args.annotated or args.message:
            repo.repo.create_tag(args.tag, ref=args.commit or "HEAD", message=args.message or args.tag)
        else:
            repo.repo.create_tag(args.tag, ref=args.commit or "HEAD")
        return {"tag": args.tag}

    def _git_tag_delete(self, payload: dict[str, Any]) -> dict[str, Any]:
        args = self._validate(GitTagDeleteInput, payload)
        workspace = self._workspace_for_tool(args.workspace_id, "git_tag_delete")
        TagService(self._repo(workspace)).delete_tag(args.tag)
        return {"deleted": args.tag}

    def _git_tag_list(self, payload: dict[str, Any]) -> dict[str, Any]:
        args = self._validate(GitTagListInput, payload)
        workspace = self._workspace(args.workspace_id)
        tags = TagService(self._repo(workspace)).list_tags()
        if args.pattern:
            tags = [tag for tag in tags if fnmatch(tag, args.pattern)]
        if args.contains:
            repo = self._repo(workspace).repo
            containing = set(repo.git.tag("--contains", args.contains).splitlines())
            tags = [tag for tag in tags if tag in containing]
        return {"tags": tags}

    def _git_tag_push(self, payload: dict[str, Any]) -> dict[str, Any]:
        args = self._validate(GitTagPushInput, payload)
        workspace = self._workspace_for_tool(args.workspace_id, "git_tag_push")
        service = TagService(self._repo(workspace))
        if args.all_tags:
            return {"result": service.push_all_tags(remote=args.remote)}
        if not args.tag:
            raise ValueError("tag is required unless all_tags=true")
        return {"result": service.push_tag(remote=args.remote, name=args.tag)}

    def _git_conflicts_list(self, payload: dict[str, Any]) -> dict[str, Any]:
        args = self._validate(GitConflictsListInput, payload)
        workspace = self._workspace(args.workspace_id)
        return {"conflicts": list_conflicts(workspace.path)}

    def _git_conflict_resolve(self, payload: dict[str, Any]) -> dict[str, Any]:
        args = self._validate(GitConflictResolveInput, payload)
        workspace = self._workspace_for_tool(args.workspace_id, "git_conflict_resolve")
        resolve_conflicts(workspace.path, args.mode, args.paths, manual_content=args.manual_content)
        return {"resolved": args.paths, "mode": args.mode}

    def _git_conflict_resolve_manual(self, payload: dict[str, Any]) -> dict[str, Any]:
        args = self._validate(GitConflictResolveManualInput, payload)
        workspace = self._workspace_for_tool(args.workspace_id, "git_conflict_resolve_manual")
        resolve_conflicts(workspace.path, "manual", [args.path], manual_content=args.content)
        return {"resolved": [args.path], "mode": "manual"}

    def _file_read(self, payload: dict[str, Any]) -> dict[str, Any]:
        args = self._validate(FileReadInput, payload)
        workspace = self._workspace(args.workspace_id)
        return {"content": load_text(workspace.path, args.path)}

    def _file_write(self, payload: dict[str, Any]) -> dict[str, Any]:
        args = self._validate(FileWriteInput, payload)
        workspace = self._workspace_for_tool(args.workspace_id, "file_write")
        target = workspace.path / args.path
        if target.exists() and not args.overwrite:
            raise FileExistsError(f"File exists and overwrite=false: {args.path}")
        path = store_text_atomic(workspace.path, args.path, args.content)
        return {"path": str(path.relative_to(workspace.path))}

    def _file_upload(self, payload: dict[str, Any]) -> dict[str, Any]:
        args = self._validate(FileUploadInput, payload)
        workspace = self._workspace_for_tool(args.workspace_id, "file_upload")
        target = workspace.path / args.path
        if target.exists() and not args.overwrite:
            raise FileExistsError(f"File exists and overwrite=false: {args.path}")
        import base64

        data = base64.b64decode(args.base64_content.encode("ascii"))
        path = store_bytes_atomic(workspace.path, args.path, data)
        return {"path": str(path.relative_to(workspace.path)), "size_bytes": len(data)}

    def _file_download(self, payload: dict[str, Any]) -> dict[str, Any]:
        args = self._validate(FileDownloadInput, payload)
        workspace = self._workspace(args.workspace_id)
        path = workspace.path / args.path
        return {"base64_content": file_to_base64(path), "path": args.path}

    def _file_move(self, payload: dict[str, Any]) -> dict[str, Any]:
        args = self._validate(FileMoveInput, payload)
        workspace = self._workspace_for_tool(args.workspace_id, "file_move")
        moved = move_entry(workspace.path, args.src, args.dst, overwrite=args.overwrite)
        return {"path": str(moved.relative_to(workspace.path))}

    def _file_copy(self, payload: dict[str, Any]) -> dict[str, Any]:
        args = self._validate(FileCopyInput, payload)
        workspace = self._workspace_for_tool(args.workspace_id, "file_copy")
        copied = copy_entry(workspace.path, args.src, args.dst, overwrite=args.overwrite)
        return {"path": str(copied.relative_to(workspace.path))}

    def _file_delete(self, payload: dict[str, Any]) -> dict[str, Any]:
        args = self._validate(FileDeleteInput, payload)
        workspace = self._workspace_for_tool(args.workspace_id, "file_delete")
        remove_entry(workspace.path, args.path)
        return {"deleted": args.path}

    def _dir_list(self, payload: dict[str, Any]) -> dict[str, Any]:
        args = self._validate(DirListInput, payload)
        workspace = self._workspace(args.workspace_id)
        entries = list_entries(
            workspace.path,
            path=args.path,
            recursive=args.recursive,
            include_hidden=args.include_hidden,
        )
        return {"entries": entries}

    def _dir_mkdir(self, payload: dict[str, Any]) -> dict[str, Any]:
        args = self._validate(DirMkdirInput, payload)
        workspace = self._workspace_for_tool(args.workspace_id, "dir_mkdir")
        created = ensure_directory(workspace.path, args.path, parents=args.parents)
        return {"path": str(created.relative_to(workspace.path))}

    def _dir_rmdir(self, payload: dict[str, Any]) -> dict[str, Any]:
        args = self._validate(DirRmdirInput, payload)
        workspace = self._workspace_for_tool(args.workspace_id, "dir_rmdir")
        remove_directory(workspace.path, args.path, recursive=args.recursive)
        return {"removed": args.path}

    def _search_content(self, payload: dict[str, Any]) -> dict[str, Any]:
        args = self._validate(SearchContentInput, payload)
        workspace = self._workspace(args.workspace_id)
        results = search_content(
            workspace.path,
            query=args.query,
            globs=args.globs,
            regex=args.regex,
            case_sensitive=args.case_sensitive,
            max_results=args.max_results,
        )
        return {"results": results}

    def _search_files(self, payload: dict[str, Any]) -> dict[str, Any]:
        args = self._validate(SearchFilesInput, payload)
        workspace = self._workspace(args.workspace_id)
        return {"results": search_files(workspace.path, query=args.query, globs=args.globs)}

    def _admin_profile_create(self, payload: dict[str, Any]) -> dict[str, Any]:
        args = self._validate(AdminProfileCreateInput, payload)
        if self.admin_runtime is not None:
            return self.admin_runtime.create_profile(args.name, args.profile, actor="mcp-admin")
        self.profile_store[args.name] = args.profile
        return {"name": args.name, "created": True}

    def _admin_user_create(self, payload: dict[str, Any]) -> dict[str, Any]:
        args = self._validate(AdminUserCreateInput, payload)
        if self.admin_runtime is not None:
            return self.admin_runtime.create_user(
                user_id=args.user_id,
                username=args.username,
                email=args.email,
                group_ids=args.group_ids,
            )
        self.user_store[args.user_id] = args.model_dump(mode="json")
        return {"user_id": args.user_id, "created": True}

    def _admin_user_read(self, payload: dict[str, Any]) -> dict[str, Any]:
        args = self._validate(AdminUserReadInput, payload)
        if self.admin_runtime is not None:
            return self.admin_runtime.read_user(args.user_id)
        if args.user_id not in self.user_store:
            raise KeyError(f"Unknown user: {args.user_id}")
        return self.user_store[args.user_id]

    def _admin_user_list(self, payload: dict[str, Any]) -> dict[str, Any]:
        _ = self._validate(AdminUserListInput, payload)
        if self.admin_runtime is not None:
            return {"items": self.admin_runtime.list_users()}
        return {"items": self.user_store}

    def _admin_user_update(self, payload: dict[str, Any]) -> dict[str, Any]:
        args = self._validate(AdminUserUpdateInput, payload)
        if self.admin_runtime is not None:
            return self.admin_runtime.update_user(
                user_id=args.user_id,
                username=args.username,
                email=args.email,
                group_ids=args.group_ids,
                status=args.status,
            )
        if args.user_id not in self.user_store:
            raise KeyError(f"Unknown user: {args.user_id}")
        self.user_store[args.user_id] = args.model_dump(mode="json")
        return self.user_store[args.user_id]

    def _admin_user_delete(self, payload: dict[str, Any]) -> dict[str, Any]:
        args = self._validate(AdminUserDeleteInput, payload)
        if self.admin_runtime is not None:
            return self.admin_runtime.delete_user(args.user_id)
        self.user_store.pop(args.user_id, None)
        return {"user_id": args.user_id, "deleted": True}

    def _admin_group_create(self, payload: dict[str, Any]) -> dict[str, Any]:
        args = self._validate(AdminGroupCreateInput, payload)
        if self.admin_runtime is not None:
            return self.admin_runtime.create_group(
                group_id=args.group_id,
                description=args.description,
                roles=args.roles,
                members=args.members,
            )
        self.group_store[args.group_id] = args.model_dump(mode="json")
        return {"group_id": args.group_id, "created": True}

    def _admin_group_read(self, payload: dict[str, Any]) -> dict[str, Any]:
        args = self._validate(AdminGroupReadInput, payload)
        if self.admin_runtime is not None:
            return self.admin_runtime.read_group(args.group_id)
        if args.group_id not in self.group_store:
            raise KeyError(f"Unknown group: {args.group_id}")
        return self.group_store[args.group_id]

    def _admin_group_list(self, payload: dict[str, Any]) -> dict[str, Any]:
        _ = self._validate(AdminGroupListInput, payload)
        if self.admin_runtime is not None:
            return {"items": self.admin_runtime.list_groups()}
        return {"items": self.group_store}

    def _admin_group_update(self, payload: dict[str, Any]) -> dict[str, Any]:
        args = self._validate(AdminGroupUpdateInput, payload)
        if self.admin_runtime is not None:
            return self.admin_runtime.update_group(
                group_id=args.group_id,
                description=args.description,
                roles=args.roles,
                members=args.members,
            )
        if args.group_id not in self.group_store:
            raise KeyError(f"Unknown group: {args.group_id}")
        self.group_store[args.group_id] = args.model_dump(mode="json")
        return self.group_store[args.group_id]

    def _admin_group_delete(self, payload: dict[str, Any]) -> dict[str, Any]:
        args = self._validate(AdminGroupDeleteInput, payload)
        if self.admin_runtime is not None:
            return self.admin_runtime.delete_group(args.group_id)
        self.group_store.pop(args.group_id, None)
        return {"group_id": args.group_id, "deleted": True}

    def _admin_rbac_bind(self, payload: dict[str, Any]) -> dict[str, Any]:
        args = self._validate(AdminRbacBindInput, payload)
        self.role_bindings.setdefault(args.user_id, set()).add(args.role)
        return {"user_id": args.user_id, "roles": sorted(self.role_bindings[args.user_id])}

    def _admin_rbac_unbind(self, payload: dict[str, Any]) -> dict[str, Any]:
        args = self._validate(AdminRbacUnbindInput, payload)
        roles = self.role_bindings.setdefault(args.user_id, set())
        roles.discard(args.role)
        return {"user_id": args.user_id, "roles": sorted(roles)}

    def _admin_credentials_set(self, payload: dict[str, Any]) -> dict[str, Any]:
        args = self._validate(AdminCredentialsSetInput, payload)
        self.credential_store[args.name] = args.secret
        return {"name": args.name, "stored": True}

    def _admin_api_key_create(self, payload: dict[str, Any]) -> dict[str, Any]:
        args = self._validate(AdminApiKeyCreateInput, payload)
        if self.admin_runtime is None:
            raise RuntimeError("admin_api_key_create requires admin runtime")
        return self.admin_runtime.create_api_key(
            name=args.name,
            owner_user_id=args.owner_user_id,
            capabilities=args.capabilities,
            ttl_days=args.ttl_days,
        )

    def _admin_api_key_list(self, payload: dict[str, Any]) -> dict[str, Any]:
        args = self._validate(AdminApiKeyListInput, payload)
        if self.admin_runtime is None:
            raise RuntimeError("admin_api_key_list requires admin runtime")
        return {"items": self.admin_runtime.list_api_keys(owner_user_id=args.owner_user_id)}

    def _admin_api_key_read(self, payload: dict[str, Any]) -> dict[str, Any]:
        args = self._validate(AdminApiKeyReadInput, payload)
        if self.admin_runtime is None:
            raise RuntimeError("admin_api_key_read requires admin runtime")
        return self.admin_runtime.read_api_key(args.key_id)

    def _admin_api_key_revoke(self, payload: dict[str, Any]) -> dict[str, Any]:
        args = self._validate(AdminApiKeyRevokeInput, payload)
        if self.admin_runtime is None:
            raise RuntimeError("admin_api_key_revoke requires admin runtime")
        return self.admin_runtime.revoke_api_key(args.key_id)
