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

from typing import Any, Literal

from pydantic import BaseModel, Field


class RefSpec(BaseModel):
    """Ref selection input."""

    type: Literal["branch", "tag", "commit"]
    name: str


class WorkspaceInput(BaseModel):
    """Common workspace scoped input model."""

    workspace_id: str


class RepoOpenInput(BaseModel):
    """Input for repo_open tool."""

    profile: str
    session_id: str
    repo_source: str | None = None
    workspace_mode: Literal["ephemeral", "persistent"] = "ephemeral"
    ref: RefSpec | None = None
    workspace_id: str | None = None  # Reopen an existing workspace by ID


class RepoOpenOutput(BaseModel):
    """Output for repo_open tool."""

    workspace_id: str
    path: str
    mode: str
    resolved_ref: dict[str, Any] | None = None


class RepoCloseInput(WorkspaceInput):
    """Input for repo_close tool."""


class RepoSetRefInput(WorkspaceInput):
    """Input for repo_set_ref tool."""

    ref: RefSpec


class GitStatusInput(WorkspaceInput):
    """Input for git_status tool."""


class GitAddInput(WorkspaceInput):
    """Input for git_add tool."""

    paths: list[str]


class GitCommitInput(WorkspaceInput):
    """Input for git_commit tool."""

    message: str


class GitPushInput(WorkspaceInput):
    """Input for git_push tool."""

    remote: str = "origin"
    branch: str | None = None
    force_with_lease: bool = False


class GitPullInput(WorkspaceInput):
    """Input for git_pull tool."""

    remote: str = "origin"
    branch: str | None = None


class GitFetchInput(WorkspaceInput):
    """Input for git_fetch tool."""

    remote: str = "origin"


class GitLogInput(WorkspaceInput):
    """Input for git_log tool."""

    author: str | None = None
    since: str | None = None
    until: str | None = None
    path: str | None = None
    max_count: int | None = None


class GitDiffInput(WorkspaceInput):
    """Input for git_diff tool."""

    left: str = "HEAD~1"
    right: str = "HEAD"


class GitCheckoutInput(WorkspaceInput):
    """Input for git_checkout tool."""

    ref: str


class GitBranchListInput(WorkspaceInput):
    """Input for git_branch_list tool."""


class GitBranchCreateInput(WorkspaceInput):
    """Input for git_branch_create tool."""

    name: str
    from_ref: str = "HEAD"


class GitBranchDeleteInput(WorkspaceInput):
    """Input for git_branch_delete tool."""

    name: str
    force: bool = False


class GitBranchFromRefInput(WorkspaceInput):
    """Input for git_branch_from_ref tool."""

    from_ref: str
    new_branch: str


class GitMergeInput(WorkspaceInput):
    """Input for git_merge tool."""

    ref: str
    ff_only: bool = False


class GitMergeAbortInput(WorkspaceInput):
    """Input for git_merge_abort tool."""


class GitMergeContinueInput(WorkspaceInput):
    """Input for git_merge_continue tool."""


class GitRebaseInput(WorkspaceInput):
    """Input for git_rebase tool."""

    onto: str


class GitRebaseAbortInput(WorkspaceInput):
    """Input for git_rebase_abort tool."""


class GitRebaseContinueInput(WorkspaceInput):
    """Input for git_rebase_continue tool."""


class GitResetInput(WorkspaceInput):
    """Input for git_reset tool."""

    paths: list[str] = Field(default_factory=list)
    hard: bool = False


class GitStashSaveInput(WorkspaceInput):
    """Input for git_stash_save tool."""

    message: str


class GitStashListInput(WorkspaceInput):
    """Input for git_stash_list tool."""


class GitStashPopInput(WorkspaceInput):
    """Input for git_stash_pop tool."""


class GitTagCreateInput(WorkspaceInput):
    """Input for git_tag_create tool."""

    tag: str
    commit: str | None = None
    annotated: bool = False
    message: str | None = None


class GitTagDeleteInput(WorkspaceInput):
    """Input for git_tag_delete tool."""

    tag: str


class GitTagListInput(WorkspaceInput):
    """Input for git_tag_list tool."""

    pattern: str | None = None
    contains: str | None = None


class GitTagPushInput(WorkspaceInput):
    """Input for git_tag_push tool."""

    remote: str = "origin"
    tag: str | None = None
    all_tags: bool = False


class GitConflictsListInput(WorkspaceInput):
    """Input for git_conflicts_list tool."""


class GitConflictResolveInput(WorkspaceInput):
    """Input for git_conflict_resolve tool."""

    mode: Literal["ours", "theirs", "manual"]
    paths: list[str]
    manual_content: str | None = None


class GitConflictResolveManualInput(WorkspaceInput):
    """Input for git_conflict_resolve_manual tool."""

    path: str
    content: str


class FileReadInput(WorkspaceInput):
    """Input for file_read tool."""

    path: str


class FileWriteInput(WorkspaceInput):
    """Input for file_write tool."""

    path: str
    content: str
    overwrite: bool = True


class FileUploadInput(WorkspaceInput):
    """Input for file_upload tool."""

    path: str
    base64_content: str
    overwrite: bool = True


class FileDownloadInput(WorkspaceInput):
    """Input for file_download tool."""

    path: str


class FileMoveInput(WorkspaceInput):
    """Input for file_move tool."""

    src: str
    dst: str
    overwrite: bool = False


class FileCopyInput(WorkspaceInput):
    """Input for file_copy tool."""

    src: str
    dst: str
    overwrite: bool = False


class FileDeleteInput(WorkspaceInput):
    """Input for file_delete tool."""

    path: str


class DirListInput(WorkspaceInput):
    """Input for dir_list tool."""

    path: str = "."
    recursive: bool = False
    include_hidden: bool = False


class DirMkdirInput(WorkspaceInput):
    """Input for dir_mkdir tool."""

    path: str
    parents: bool = True


class DirRmdirInput(WorkspaceInput):
    """Input for dir_rmdir tool."""

    path: str
    recursive: bool = False


class SearchContentInput(WorkspaceInput):
    """Input for search_content tool."""

    query: str
    globs: list[str] | None = None
    regex: bool = False
    case_sensitive: bool = False
    max_results: int = 200


class SearchFilesInput(WorkspaceInput):
    """Input for search_files tool."""

    query: str
    globs: list[str] | None = None


class AdminProfileCreateInput(BaseModel):
    """Input for admin_profile_create tool."""

    name: str
    profile: dict[str, Any]


class AdminUserCreateInput(BaseModel):
    """Input for admin_user_create tool.

    Requirements: CFG-08, CFG-11.
    """

    user_id: str
    username: str
    email: str = ""
    group_ids: list[str] = Field(default_factory=list)


class AdminUserReadInput(BaseModel):
    """Input for admin_user_read tool.

    Requirements: CFG-08, CFG-11.
    """

    user_id: str


class AdminUserListInput(BaseModel):
    """Input for admin_user_list tool.

    Requirements: CFG-08, CFG-11.
    """


class AdminUserUpdateInput(BaseModel):
    """Input for admin_user_update tool.

    Requirements: CFG-08, CFG-11.
    """

    user_id: str
    username: str
    email: str = ""
    group_ids: list[str] = Field(default_factory=list)
    status: str = "active"


class AdminUserDeleteInput(BaseModel):
    """Input for admin_user_delete tool.

    Requirements: CFG-08, CFG-11.
    """

    user_id: str


class AdminGroupCreateInput(BaseModel):
    """Input for admin_group_create tool.

    Requirements: CFG-09, CFG-11.
    """

    group_id: str
    description: str = ""
    roles: list[str] = Field(default_factory=list)
    members: list[str] = Field(default_factory=list)


class AdminGroupReadInput(BaseModel):
    """Input for admin_group_read tool.

    Requirements: CFG-09, CFG-11.
    """

    group_id: str


class AdminGroupListInput(BaseModel):
    """Input for admin_group_list tool.

    Requirements: CFG-09, CFG-11.
    """


class AdminGroupUpdateInput(BaseModel):
    """Input for admin_group_update tool.

    Requirements: CFG-09, CFG-11.
    """

    group_id: str
    description: str = ""
    roles: list[str] = Field(default_factory=list)
    members: list[str] = Field(default_factory=list)


class AdminGroupDeleteInput(BaseModel):
    """Input for admin_group_delete tool.

    Requirements: CFG-09, CFG-11.
    """

    group_id: str


class AdminRbacBindInput(BaseModel):
    """Input for admin_rbac_bind tool."""

    user_id: str
    role: str


class AdminRbacUnbindInput(BaseModel):
    """Input for admin_rbac_unbind tool."""

    user_id: str
    role: str


class AdminCredentialsSetInput(BaseModel):
    """Input for admin_credentials_set tool."""

    name: str
    secret: str


class AdminApiKeyCreateInput(BaseModel):
    """Input for admin_api_key_create tool.

    Requirements: CFG-10, CFG-11.
    """

    name: str
    owner_user_id: str
    capabilities: list[str] = Field(default_factory=list)
    ttl_days: int | None = None


class AdminApiKeyListInput(BaseModel):
    """Input for admin_api_key_list tool.

    Requirements: CFG-10, CFG-11.
    """

    owner_user_id: str | None = None


class AdminApiKeyReadInput(BaseModel):
    """Input for admin_api_key_read tool.

    Requirements: CFG-10, CFG-11.
    """

    key_id: str


class AdminApiKeyRevokeInput(BaseModel):
    """Input for admin_api_key_revoke tool.

    Requirements: CFG-10, CFG-11.
    """

    key_id: str


class ToolDefinition(BaseModel):
    """Tool contract metadata used by MCP registry."""

    name: str
    description: str
    input_schema: dict[str, Any]
    output_schema: dict[str, Any]
