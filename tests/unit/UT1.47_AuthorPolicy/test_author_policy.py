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

from git import Repo

from tests.unit._tool_registry_harness import open_workspace_harness
import pytest
# FR-1.18 traceability marker for existing git-mcp coverage.
@pytest.mark.UT
@pytest.mark.mcp
@pytest.mark.req("FR-010")  # W28E-1804A semantic rebind


def test_commit_author_uses_repo_policy_config(tmp_path) -> None:
    """Requirements: FR-10. UCs: UC-037."""
    harness = open_workspace_harness(tmp_path)
    try:
        repo = Repo(harness.workspace_path)
        repo.git.config("user.name", "Policy User")
        repo.git.config("user.email", "policy@example.com")

        harness.registry.call(
            "file_write",
            {"workspace_id": harness.workspace_id, "path": "author.txt", "content": "author\n"},
        )
        harness.registry.call("git_add", {"workspace_id": harness.workspace_id, "paths": ["author.txt"]})
        harness.registry.call("git_commit", {"workspace_id": harness.workspace_id, "message": "author policy commit"})

        commit = repo.head.commit
        assert commit.author.name == "Policy User"
        assert commit.author.email == "policy@example.com"
    finally:
        harness.close()
# FR-1.18 traceability marker for existing git-mcp coverage.
@pytest.mark.UT
@pytest.mark.mcp
@pytest.mark.req("FR-010")  # W28E-1804A semantic rebind


def test_commit_author_per_call_override(tmp_path) -> None:
    """W28M-1602: per-call author_name/author_email override the workspace config.

    Lets the agentic audit-sink stamp commits with the real
    cloud_dog_idam kickoff principal (Demo demand: 'attribution is real')
    while the workspace config remains a safe service-identity fallback
    for unstamped commits.
    """
    harness = open_workspace_harness(tmp_path)
    try:
        repo = Repo(harness.workspace_path)
        repo.git.config("user.name", "Service Account")
        repo.git.config("user.email", "service@cloud-dog.net")

        harness.registry.call(
            "file_write",
            {"workspace_id": harness.workspace_id, "path": "run.txt", "content": "audit\n"},
        )
        harness.registry.call(
            "git_add", {"workspace_id": harness.workspace_id, "paths": ["run.txt"]}
        )
        harness.registry.call(
            "git_commit",
            {
                "workspace_id": harness.workspace_id,
                "message": "agentic run committed by real principal",
                "author_name": "Gary Seymour",
                "author_email": "gary@cloud-dog.net",
            },
        )

        commit = repo.head.commit
        assert commit.author.name == "Gary Seymour"
        assert commit.author.email == "gary@cloud-dog.net"
        # Without an explicit committer override, the author identity is
        # mirrored onto the committer (NOT silently fallen-through to the
        # service-account config), so blame/attribution is consistent.
        assert commit.committer.name == "Gary Seymour"
        assert commit.committer.email == "gary@cloud-dog.net"
    finally:
        harness.close()
# FR-1.18 traceability marker for existing git-mcp coverage.
@pytest.mark.UT
@pytest.mark.mcp
@pytest.mark.req("FR-010")  # W28E-1804A semantic rebind


def test_commit_separate_committer_override(tmp_path) -> None:
    """W28M-1602: when committer fields differ from author, both are stamped."""
    harness = open_workspace_harness(tmp_path)
    try:
        repo = Repo(harness.workspace_path)
        repo.git.config("user.name", "Service Account")
        repo.git.config("user.email", "service@cloud-dog.net")

        harness.registry.call(
            "file_write",
            {"workspace_id": harness.workspace_id, "path": "run.txt", "content": "v\n"},
        )
        harness.registry.call(
            "git_add", {"workspace_id": harness.workspace_id, "paths": ["run.txt"]}
        )
        harness.registry.call(
            "git_commit",
            {
                "workspace_id": harness.workspace_id,
                "message": "split author/committer",
                "author_name": "Author Person",
                "author_email": "author@cloud-dog.net",
                "committer_name": "Committer Bot",
                "committer_email": "bot@cloud-dog.net",
            },
        )

        commit = repo.head.commit
        assert commit.author.name == "Author Person"
        assert commit.author.email == "author@cloud-dog.net"
        assert commit.committer.name == "Committer Bot"
        assert commit.committer.email == "bot@cloud-dog.net"
    finally:
        harness.close()
